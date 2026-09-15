from decimal import Decimal
from django.db import transaction # type: ignore
from django.db.models import Count, Q # type: ignore
from django.utils import timezone  # type: ignore
from django.urls import reverse # type: ignore
from asgiref.sync import async_to_sync # type: ignore
from channels.layers import get_channel_layer # type: ignore
from apps.products.models import Producto
from apps.orders.models import Pedido, ItemPedido
from apps.payments.models import Pago
from apps.tracking.route_service import ensure_delivery_route_for_order


class CartService:
    SESSION_KEY = "cart"

    @staticmethod
    def _load_cart(request):
        return request.session.get(CartService.SESSION_KEY, {})

    @staticmethod
    def _save_cart(request, cart):
        request.session[CartService.SESSION_KEY] = cart
        request.session.modified = True

    @staticmethod
    def add_product(request, producto_id, quantity=1):
        cart = CartService._load_cart(request)
        key = str(producto_id)
        cart[key] = cart.get(key, 0) + max(1, int(quantity))
        CartService._save_cart(request, cart)

    @staticmethod
    def update_product(request, producto_id, quantity):
        cart = CartService._load_cart(request)
        key = str(producto_id)
        qty = int(quantity)
        if qty <= 0:
            cart.pop(key, None)
        else:
            cart[key] = qty
        CartService._save_cart(request, cart)

    @staticmethod
    def remove_product(request, producto_id):
        cart = CartService._load_cart(request)
        cart.pop(str(producto_id), None)
        CartService._save_cart(request, cart)

    @staticmethod
    def clear(request):
        request.session.pop(CartService.SESSION_KEY, None)
        request.session.modified = True

    @staticmethod
    def get_cart_items(request):
        cart = CartService._load_cart(request)
        if not cart:
            return []

        product_ids = [int(pid) for pid in cart.keys()]
        products = Producto.objects.filter(id__in=product_ids, activo=True)
        items = []

        for product in products:
            qty = int(cart.get(str(product.id), 0))
            if qty <= 0:
                continue
            subtotal = Decimal(product.precio) * qty
            items.append(
                {
                    "producto": product,
                    "cantidad": qty,
                    "subtotal": subtotal,
                }
            )

        return items

    @staticmethod
    def get_totals(request):
        items = CartService.get_cart_items(request)
        subtotal = sum(item["subtotal"] for item in items) if items else Decimal("0.00")
        shipping = Decimal("5.00") if items else Decimal("0.00")
        total = subtotal + shipping
        return {
            "items": items,
            "subtotal": subtotal,
            "shipping": shipping,
            "total": total,
            "count": sum(item["cantidad"] for item in items),
        }


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(*, user, request, direccion_entrega, telefono_contacto, metodo_pago, referencia="", notas="", datos_pago_adicionales=None):
        cart_summary = CartService.get_totals(request)
        if not cart_summary["items"]:
            raise ValueError("El carrito esta vacio.")

        order = Pedido.objects.create(
            cliente=user,
            direccion_entrega=direccion_entrega,
            telefono_contacto=telefono_contacto,
            notas=notas,
            subtotal=cart_summary["subtotal"],
            costo_envio=cart_summary["shipping"],
            total=cart_summary["total"],
            estado="pendiente_asignacion",
        )

        for item in cart_summary["items"]:
            product = item["producto"]
            quantity = item["cantidad"]
            if product.stock < quantity:
                raise ValueError(f"Stock insuficiente para {product.nombre}.")

            ItemPedido.objects.create(
                pedido=order,
                producto=product,
                cantidad=quantity,
                precio_unitario=product.precio,
            )
            product.reducir_stock(quantity)

        # Crear registro de pago con datos adicionales
        pago_notas = ""
        if datos_pago_adicionales:
            pago_items = []
            if datos_pago_adicionales.get('tipo_facturacion'):
                tipo_fact_map = {
                    'boleta_simple': 'Boleta Simple',
                    'boleta_dni': 'Boleta con DNI',
                    'factura': 'Factura',
                }
                pago_items.append(f"Facturación: {tipo_fact_map.get(datos_pago_adicionales['tipo_facturacion'], 'No especificado')}")
            
            if datos_pago_adicionales.get('numero_tarjeta_ultimos'):
                pago_items.append(f"Tarjeta (últimos 4): {datos_pago_adicionales['numero_tarjeta_ultimos']}")
            
            if datos_pago_adicionales.get('tipo_pos'):
                pago_items.append(f"Tipo POS: {datos_pago_adicionales['tipo_pos']}")
            
            if datos_pago_adicionales.get('recibir_promociones'):
                pago_items.append("Cliente desea recibir promociones y descuentos")
            
            pago_notas = " | ".join(pago_items) if pago_items else ""

        Pago.objects.create(
            pedido=order,
            metodo=metodo_pago,
            monto=order.total,
            estado="pendiente",
            referencia=referencia,
            notas=pago_notas,
        )

        ensure_delivery_route_for_order(order)

        CartService.clear(request)
        return order


class AutoAsignmentService:
    """
    Servicio de asignación automática de pedidos a motorizados.
    
    Busca pedidos pendientes de asignación y los asigna automáticamente
    a motorizados disponibles que tengan jornada activa.
    """
    
    @staticmethod
    def asignar_pedidos_pendientes():
        """
        Asigna automáticamente pedidos pendientes a motorizados disponibles.
        
        Lógica:
        1. Busca todos los pedidos en estado 'pendiente_asignacion'
        2. Para cada pedido, busca un motorizado que cumpla:
           - disponible = True
           - jornada_activa = True
           - Sin pedidos activos en ese momento (confirmado, en_camino)
        3. Asigna el pedido y actualiza su estado a 'confirmado'
        4. Dispara geocodificación de la dirección si no existe
        
        Returns:
            dict: {'asignados': int, 'pendientes': int, 'errores': []}
        """
        from apps.users.models import PerfilMotorizado
        
        resultado = {
            'asignados': 0,
            'pendientes': 0,
            'errores': []
        }
        
        # Obtener pedidos pendientes de asignación
        pedidos_pendientes = Pedido.objects.filter(
            estado__in=['pendiente_asignacion', 'confirmado'],
            motorizado__isnull=True
        ).order_by('fecha_pedido')
        
        resultado['pendientes'] = pedidos_pendientes.count()
        
        for pedido in pedidos_pendientes:
            try:
                # Buscar motorizado disponible con jornada activa
                # que no tenga pedidos activos
                motorizado_perfil = PerfilMotorizado.objects.filter(
                    disponible=True,
                    jornada_activa=True,
                    usuario__role='motorizado'
                ).annotate(
                    pedidos_activos=Count(
                        'usuario__entregas',
                        filter=Q(usuario__entregas__estado__in=['confirmado', 'en_preparacion', 'en_camino'])
                    )
                ).filter(
                    pedidos_activos=0
                ).first()
                
                if motorizado_perfil:
                    # Asignar pedido al motorizado
                    pedido.motorizado = motorizado_perfil.usuario
                    pedido.estado = 'confirmado'
                    pedido.fecha_asignacion = timezone.now()
                    pedido.save(update_fields=['motorizado', 'estado', 'fecha_asignacion'])
                    JornadaService.broadcast_order_status(pedido)
                    
                    # Asegurar que tiene ruta geocodificada
                    ensure_delivery_route_for_order(pedido)
                    
                    # Notificar al motorizado (implementar en WebSocket después)
                    AutoAsignmentService._notificar_nuevo_pedido(pedido, motorizado_perfil)
                    
                    resultado['asignados'] += 1
                    
            except Exception as e:
                resultado['errores'].append({
                    'pedido_id': pedido.id,
                    'error': str(e)
                })
        
        return resultado
    
    @staticmethod
    def _notificar_nuevo_pedido(pedido, motorizado_perfil):
        """
        Notifica al motorizado sobre un nuevo pedido asignado.
        Usa WebSocket para enviar en tiempo real.
        """
        try:
            from asgiref.sync import async_to_sync # type: ignore
            from channels.layers import get_channel_layer # type: ignore
            
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'tracking_motorizado_{motorizado_perfil.usuario.id}',
                    {
                        'type': 'new.assignment',
                        'pedido_id': pedido.id,
                        'cliente': pedido.cliente.get_full_name() or pedido.cliente.username,
                        'direccion': pedido.direccion_entrega,
                        'total': str(pedido.total),
                    }
                )
        except Exception as e:
            # Fallar silenciosamente si Channels no está disponible
            pass


class JornadaService:
    """
    Servicio para gestionar jornadas laborales de motorizados.
    """
    
    @staticmethod
    def _get_or_create_perfil_motorizado(motorizado_user):
        """Garantiza un perfil mínimo para motorizados heredados sin ficha completa."""
        from apps.users.models import PerfilMotorizado

        perfil, _ = PerfilMotorizado.objects.get_or_create(
            usuario=motorizado_user,
            defaults={
                'placa_vehiculo': 'PENDIENTE',
                'tipo_vehiculo': 'Moto',
                'licencia': 'PENDIENTE',
                'disponible': True,
            }
        )
        return perfil

    @staticmethod
    def iniciar_jornada(motorizado_user):
        """Inicia una jornada laboral para un motorizado."""
        perfil = JornadaService._get_or_create_perfil_motorizado(motorizado_user)
        perfil.jornada_activa = True
        perfil.fecha_inicio_jornada = timezone.now()
        perfil.save(update_fields=['jornada_activa', 'fecha_inicio_jornada'])
        
        # Intentar asignar pedidos pendientes
        return AutoAsignmentService.asignar_pedidos_pendientes()
    
    @staticmethod
    def finalizar_jornada(motorizado_user):
        """Finaliza la jornada laboral de un motorizado."""
        perfil = JornadaService._get_or_create_perfil_motorizado(motorizado_user)
        
        # No permitir finalizar si hay pedidos activos
        pedidos_activos = Pedido.objects.filter(
            motorizado=motorizado_user,
            estado__in=['confirmado', 'en_preparacion', 'en_camino']
        ).count()
        
        if pedidos_activos > 0:
            raise ValueError(f"No puedes finalizar tu jornada con {pedidos_activos} pedidos activos.")
        
        perfil.jornada_activa = False
        perfil.save(update_fields=['jornada_activa'])
        
        return True
    
    @staticmethod
    def marcar_entregado(pedido, motorizado_user):
        """Marca un pedido como entregado."""
        if pedido.motorizado_id != motorizado_user.id:
            raise ValueError("Este pedido no está asignado a ti.")
        
        if pedido.estado not in ['en_camino', 'en_preparacion', 'confirmado']:
            raise ValueError(f"No puedes entregar un pedido en estado {pedido.estado}.")
        
        pedido.estado = 'entregado'
        pedido.fecha_entrega = timezone.now()
        pedido.save(update_fields=['estado', 'fecha_entrega'])
        JornadaService.broadcast_order_status(pedido)
        
        # Actualizar contador de entregas completadas
        perfil = JornadaService._get_or_create_perfil_motorizado(motorizado_user)
        perfil.entregas_completadas += 1
        perfil.save(update_fields=['entregas_completadas'])
        
        return pedido

    @staticmethod
    def marcar_en_preparacion(pedido, motorizado_user):
        """Marca un pedido asignado como en preparación."""
        if pedido.motorizado_id != motorizado_user.id:
            raise ValueError("Este pedido no está asignado a ti.")

        if pedido.estado in ['entregado', 'cancelado']:
            raise ValueError(f"No puedes preparar un pedido en estado {pedido.estado}.")

        if pedido.estado == 'en_preparacion':
            return pedido

        pedido.estado = 'en_preparacion'
        pedido.save(update_fields=['estado'])
        JornadaService.broadcast_order_status(pedido)
        return pedido

    @staticmethod
    def marcar_en_camino(pedido, motorizado_user):
        """Marca un pedido asignado como en camino."""
        if pedido.motorizado_id != motorizado_user.id:
            raise ValueError("Este pedido no está asignado a ti.")

        if pedido.estado in ['entregado', 'cancelado']:
            raise ValueError(f"No puedes iniciar ruta para un pedido en estado {pedido.estado}.")

        if pedido.estado == 'en_camino':
            return pedido

        pedido.estado = 'en_camino'
        pedido.save(update_fields=['estado'])
        JornadaService.broadcast_order_status(pedido)
        return pedido

    @staticmethod
    def broadcast_order_status(pedido):
        """Publica el estado del pedido por WebSocket para vistas cliente/motorizado."""
        status_step_map = {
            'pendiente': 1,
            'pendiente_asignacion': 1,
            'confirmado': 1,
            'en_preparacion': 2,
            'en_camino': 3,
            'entregado': 4,
            'cancelado': 0,
        }
        status_progress_map = {
            0: 0,
            1: 15,
            2: 45,
            3: 75,
            4: 100,
        }
        eta_default_by_state = {
            'pendiente': 30,
            'pendiente_asignacion': 28,
            'confirmado': 24,
            'en_preparacion': 18,
            'en_camino': 11,
        }

        route = getattr(pedido, 'ruta', None)
        eta_minutes = route.tiempo_estimado_min if route and getattr(route, 'tiempo_estimado_min', None) else eta_default_by_state.get(pedido.estado, 20)
        step = status_step_map.get(pedido.estado, 1)
        payload = {
            'pedido_id': pedido.id,
            'estado': pedido.estado,
            'estado_display': pedido.get_estado_display(),
            'progress_step': step,
            'progress_percent': status_progress_map.get(step, 15),
            'eta_minutes': eta_minutes,
            'payment_status_display': pedido.pago.get_estado_display() if getattr(pedido, 'pago', None) else 'Sin pago',
            'tracking_url': reverse('users:portal_cliente_rastreo_pedido', kwargs={'pedido_id': pedido.id}),
            'orders_url': reverse('users:portal_cliente_pedidos'),
            'detail_url': reverse('users:portal_cliente_pedido_detalle', kwargs={'pedido_id': pedido.id}),
            'portal_url': reverse('users:portal_cliente'),
        }

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'order_status_{pedido.id}',
                {
                    'type': 'order.status',
                    'payload': payload,
                }
            )

        # Mantiene sincronizado el mapa de rastreo del cliente cuando cambia el estado.
        try:
            from apps.tracking.views import broadcast_order_tracking_snapshot

            broadcast_order_tracking_snapshot(pedido)
        except Exception:
            # Evita romper el flujo principal si tracking/channels no está disponible.
            pass
