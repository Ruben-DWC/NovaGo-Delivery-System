"""
Suite de Pruebas Automatizadas para Fases 1 a 3 (NovaGo Delivery System):
- Fase 1: Configuración de entorno, pyproject.toml y pytests.
- Fase 2: Concurrencia robusta, select_for_update(), idempotencia y excepciones de dominio.
- Fase 3: Modernización UI/UX con HTMX parciales, Alpine.js y diseño impecable.

Autores: Ruben Walter Vivas Jimenez (Ruben-DWC) & Conislla Lavado Cesar Jesus (umaten)
"""
from decimal import Decimal
import threading
import unittest
from django.test import TestCase, TransactionTestCase, Client, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from django.db import connection
from apps.users.models import User
from apps.products.models import Producto, Categoria
from apps.orders.models import Pedido
from apps.payments.models import Pago
from apps.orders.services import (
    CartService,
    OrderService,
    InsufficientStockError,
    EmptyCartError,
    OrderDomainError,
)
from apps.orders.forms import CheckoutForm


class ConcurrencyIdempotencyServiceTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='cliente_test_concurrency',
            email='cliente@test.com',
            password='TestPassword123!',
            role='cliente',
            first_name='Cliente',
            last_name='Prueba'
        )
        self.categoria = Categoria.objects.create(nombre="Pizzas", descripcion="Pizzas a la lena")
        self.producto = Producto.objects.create(
            nombre="Pizza Margherita Gourmet",
            descripcion="Masa madre, mozzarella fresca y albahaca",
            categoria=self.categoria,
            precio=Decimal("32.00"),
            stock=5,
            activo=True
        )

    def _get_request_with_session(self):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_insufficient_stock_error_raises_and_rolls_back(self):
        """Verifica que solicitar más stock del disponible lance InsufficientStockError sin alterar la DB."""
        request = self._get_request_with_session()
        CartService.add_product(request, self.producto.id, quantity=10)  # Solo hay 5

        with self.assertRaises(InsufficientStockError) as ctx:
            OrderService.create_order_from_cart(
                user=self.user,
                request=request,
                direccion_entrega="Av. Javier Prado 1234",
                telefono_contacto="987654321",
                metodo_pago="efectivo",
            )

        self.assertIn("Pizza Margherita Gourmet", str(ctx.exception))
        self.assertEqual(ctx.exception.stock_disponible, 5)
        self.assertEqual(ctx.exception.cantidad_solicitada, 10)
        self.assertTrue(issubclass(InsufficientStockError, OrderDomainError))
        self.assertTrue(issubclass(InsufficientStockError, ValueError))

        # Verificar que el stock no fue alterado y no se crearon pedidos
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertEqual(Pago.objects.count(), 0)

    def test_order_creation_with_pessimistic_locking_and_stock_deduction(self):
        """Verifica la creación atómica del pedido con reducción de stock y registro de pago."""
        request = self._get_request_with_session()
        CartService.add_product(request, self.producto.id, quantity=2)

        order = OrderService.create_order_from_cart(
            user=self.user,
            request=request,
            direccion_entrega="Av. Brasil 450, Dpto 302",
            telefono_contacto="912345678",
            metodo_pago="yape",
            referencia="OP-778899",
            notas="Sin cebolla por favor",
        )

        self.assertIsNotNone(order.id)
        self.assertEqual(order.cliente, self.user)
        self.assertEqual(order.estado, "pendiente_asignacion")
        self.assertEqual(order.subtotal, Decimal("64.00"))
        self.assertEqual(order.costo_envio, Decimal("5.00"))
        self.assertEqual(order.total, Decimal("69.00"))

        # El stock debe haber disminuido de 5 a 3
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)

        # El pago asociado debe existir
        self.assertTrue(hasattr(order, 'pago'))
        self.assertEqual(order.pago.metodo, 'yape')
        self.assertEqual(order.pago.monto, Decimal("69.00"))

        # El carrito en sesión debe haber sido vaciado
        cart_after = CartService.get_totals(request)
        self.assertEqual(cart_after['count'], 0)

    def test_idempotency_key_prevents_duplicate_orders(self):
        """Verifica que una clave de idempotencia repetida no duplique pedidos ni deduzca stock doble."""
        request = self._get_request_with_session()
        CartService.add_product(request, self.producto.id, quantity=1)
        idemp_key = "idemp-unique-uuid-9999"

        # Primer intento: crea el pedido
        order1 = OrderService.create_order_from_cart(
            user=self.user,
            request=request,
            direccion_entrega="Calle Los Sauces 120",
            telefono_contacto="999888777",
            metodo_pago="tarjeta",
            idempotency_key=idemp_key,
        )

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 4)
        self.assertEqual(order1.idempotency_key, idemp_key)
        self.assertEqual(Pedido.objects.count(), 1)

        # Segundo intento idéntico con la misma clave de idempotencia
        CartService.add_product(request, self.producto.id, quantity=1)
        order2 = OrderService.create_order_from_cart(
            user=self.user,
            request=request,
            direccion_entrega="Calle Los Sauces 120",
            telefono_contacto="999888777",
            metodo_pago="tarjeta",
            idempotency_key=idemp_key,
        )

        # Debe retornar la misma orden sin crear una nueva ni descontar más stock
        self.assertEqual(order1.id, order2.id)
        self.assertEqual(Pedido.objects.count(), 1)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 4)

    def test_empty_cart_error_raises(self):
        """Verifica que intentar crear pedido con carrito vacío lance EmptyCartError."""
        request = self._get_request_with_session()
        with self.assertRaises(EmptyCartError):
            OrderService.create_order_from_cart(
                user=self.user,
                request=request,
                direccion_entrega="Av. Larco 800",
                telefono_contacto="944555666",
                metodo_pago="efectivo",
            )

    def test_cancel_order_restocks_with_pessimistic_lock(self):
        """Verifica que cancelar un pedido devuelva el stock exacto al inventario."""
        request = self._get_request_with_session()
        CartService.add_product(request, self.producto.id, quantity=3)
        order = OrderService.create_order_from_cart(
            user=self.user,
            request=request,
            direccion_entrega="Av. Benavides 1500",
            telefono_contacto="933222111",
            metodo_pago="contra_entrega",
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 2)

        OrderService.cancel_order(order, reason="Cliente reprogramó compra")
        order.refresh_from_db()
        self.assertEqual(order.estado, 'cancelado')

        # Stock reintegrado
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

    def test_idempotency_concurrent_integrity_error_recovery(self):
        """
        Verifica que si ocurre una condición de carrera donde dos transacciones concurrentes
        intentan insertar la misma idempotency_key (disparando IntegrityError a nivel DB),
        OrderService lo maneje capturando IntegrityError dentro de una sub-transacción atómica,
        recupere el pedido preexistente y limpie el carrito sin lanzar excepción 500.
        """
        request = self._get_request_with_session()
        CartService.add_product(request, self.producto.id, quantity=1)
        idemp_key = "idemp-simulated-race-key-1"

        # Pre-creamos el pedido simulando la transacción ganadora
        winning_order = Pedido.objects.create(
            cliente=self.user,
            direccion_entrega="Av. Victoria 500",
            telefono_contacto="999111222",
            subtotal=Decimal("32.00"),
            costo_envio=Decimal("5.00"),
            total=Decimal("37.00"),
            estado="pendiente_asignacion",
            idempotency_key=idemp_key,
        )

        # Ahora la transacción perdedora intenta crear la orden con la misma clave
        result_order = OrderService.create_order_from_cart(
            user=self.user,
            request=request,
            direccion_entrega="Av. Victoria 500",
            telefono_contacto="999111222",
            metodo_pago="efectivo",
            idempotency_key=idemp_key,
        )

        self.assertEqual(result_order.id, winning_order.id)
        self.assertEqual(Pedido.objects.filter(idempotency_key=idemp_key).count(), 1)
        # El carrito debió ser vaciado
        self.assertEqual(CartService.get_totals(request)['count'], 0)

    def test_duplicate_order_error_raised_when_order_cannot_be_retrieved(self):
        """Verifica que DuplicateOrderError se lance si ocurre colisión pero no se encuentra la orden."""
        from apps.orders.services import DuplicateOrderError
        from unittest.mock import patch
        from django.db import IntegrityError

        request = self._get_request_with_session()
        CartService.add_product(request, self.producto.id, quantity=1)
        idemp_key = "idemp-unretrievable-test"

        # Forzamos IntegrityError en Pedido.objects.create pero hacemos que filter retorne None
        with patch('apps.orders.models.Pedido.objects.create', side_effect=IntegrityError("Duplicate key")):
            with patch('apps.orders.models.Pedido.objects.filter') as mock_filter:
                mock_filter.return_value.select_related.return_value.first.return_value = None
                with self.assertRaises(DuplicateOrderError) as ctx:
                    OrderService.create_order_from_cart(
                        user=self.user,
                        request=request,
                        direccion_entrega="Av. Test 123",
                        telefono_contacto="999000111",
                        metodo_pago="efectivo",
                        idempotency_key=idemp_key,
                    )
                self.assertEqual(ctx.exception.idempotency_key, idemp_key)


class HtmxAlpineUiUxTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria_comida = Categoria.objects.create(nombre="Almuerzos", descripcion="Platos fuertes")
        self.categoria_bebida = Categoria.objects.create(nombre="Bebidas", descripcion="Refrescos y jugos")

        self.p1 = Producto.objects.create(
            nombre="Lomo Saltado Criollo",
            descripcion="Carne de res con cebolla, tomate y papas fritas",
            categoria=self.categoria_comida,
            precio=Decimal("28.00"),
            stock=12,
            activo=True
        )
        self.p2 = Producto.objects.create(
            nombre="Chicha Morada Natural 1L",
            descripcion="Maíz morado con piña, manzana y canela",
            categoria=self.categoria_bebida,
            precio=Decimal("8.50"),
            stock=20,
            activo=True
        )

    def test_base_template_includes_htmx_and_alpine_cdn(self):
        """Verifica que base.html cargue HTMX 2.0.4, Alpine.js 3.14.8 y los tokens de seguridad CSRF."""
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("htmx.org@2.0.4", content)
        self.assertIn("alpinejs@3.14.8", content)
        self.assertIn("hx-headers", content)
        self.assertIn("X-CSRFToken", content)

    def test_htmx_request_returns_only_partial_product_grid(self):
        """Peticiones HTMX deben retornar únicamente el fragmento HTML del catálogo, sin etiquetas html completas."""
        url = reverse('products:product_list')
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        # Debe contener la estructura del grid parcial
        self.assertIn("catalog-grid-wrapper", content)
        self.assertIn("Lomo Saltado Criollo", content)
        self.assertIn("Chicha Morada Natural 1L", content)

        # NO debe contener el layout base exterior ni encabezados globales
        self.assertNotIn("<!DOCTYPE html>", content)
        self.assertNotIn("<html", content)
        self.assertNotIn("<body", content)

    def test_htmx_live_search_filters_instantly(self):
        """Búsqueda reactiva por query param retorna únicamente los productos coincidentes."""
        url = reverse('products:product_list')
        response = self.client.get(f"{url}?q=Chicha", HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        self.assertIn("Chicha Morada Natural 1L", content)
        self.assertNotIn("Lomo Saltado Criollo", content)

    def test_htmx_category_pill_filtering(self):
        """Filtrar por categoría vía HTMX debe devolver solo los productos correspondientes."""
        url = reverse('products:product_list_by_category', kwargs={'categoria_id': self.categoria_comida.id})
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        self.assertIn("Lomo Saltado Criollo", content)
        self.assertNotIn("Chicha Morada Natural 1L", content)

    def test_catalog_empty_state_with_call_to_action(self):
        """Búsqueda sin coincidencias debe renderizar un estado vacío refinado con CTA claro."""
        url = reverse('products:product_list')
        response = self.client.get(f"{url}?q=ProductoInexistenteXYZ", HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        self.assertIn("empty-state-card", content)
        self.assertIn("No encontramos platillos para tu búsqueda", content)
        self.assertIn("Restablecer Filtros", content)

    def test_quick_cart_drawer_has_alpine_reactive_markup(self):
        """Verifica que el Quick Cart Drawer contenga los bindings de Alpine.js y fallback estático."""
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        self.assertIn('x-data="alpineCartDrawer()"', content)
        self.assertIn('x-for="item in items"', content)
        self.assertIn('x-text="count"', content)
        self.assertIn('x-text="item.nombre"', content)
        self.assertIn('x-text="item.cantidad"', content)
        self.assertIn('updateQty(item.id', content)
        self.assertIn('removeItem(item.id)', content)

    def test_checkout_form_contains_idempotency_field(self):
        """Verifica que CheckoutForm declare el campo idempotency_key como campo oculto."""
        form = CheckoutForm()
        self.assertIn('idempotency_key', form.fields)
        self.assertTrue(form.fields['idempotency_key'].widget.is_hidden)
        self.assertFalse(form.fields['idempotency_key'].required)

    def test_checkout_form_generates_unique_idempotency_key_by_default(self):
        """Verifica que CheckoutForm genere automáticamente una clave de idempotencia UUID única si no se provee."""
        form1 = CheckoutForm()
        form2 = CheckoutForm()
        key1 = form1.initial.get('idempotency_key')
        key2 = form2.initial.get('idempotency_key')
        self.assertTrue(key1 and len(key1) >= 32)
        self.assertTrue(key2 and len(key2) >= 32)
        self.assertNotEqual(key1, key2)

    def test_payment_gateway_renders_idempotency_key_input(self):
        """Verifica que el formulario de pasarela de pago de cliente incluya el campo oculto idempotency_key."""
        user_cliente = User.objects.create_user(
            username='cliente_gw_test',
            email='clientegw@test.com',
            password='Password123!',
            role='cliente'
        )
        self.client.force_login(user_cliente)
        response = self.client.get(reverse('users:portal_cliente_pago'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="idempotency_key"', response.content.decode())

    def test_htmx_search_with_category_query_param(self):
        """Verifica que filtrar con query param 'categoria' mantenga la restricción de categoría correctamente."""
        url = reverse('products:product_list')
        response = self.client.get(f"{url}?categoria={self.categoria_comida.id}&q=Lomo", HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Lomo Saltado Criollo", content)
        self.assertNotIn("Chicha Morada Natural 1L", content)


@unittest.skipUnless(
    connection.features.has_select_for_update,
    "El bloqueo de filas select_for_update() y concurrencia multihilo sin contención de archivo completo requiere PostgreSQL (activo en Docker/Cloud)."
)
class MultiThreadConcurrencyTestCase(TransactionTestCase):
    """
    Pruebas de estrés y contención concurrente real multihilo sobre base de datos.
    Verifica locking pesimista, serialización de transacciones e idempotencia bajo carreras reales.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='cliente_multithread',
            email='mthread@novago.pe',
            password='MThreadPassword123!',
            role='cliente'
        )
        self.categoria = Categoria.objects.create(nombre="Hamburguesas", descripcion="Combos")
        self.producto = Producto.objects.create(
            nombre="Nova Ultra Burger",
            descripcion="Doble carne, queso cheddar artesanal",
            categoria=self.categoria,
            precio=Decimal("25.00"),
            stock=1,  # Stock crítico = 1 para provocar contención estricta
            activo=True
        )

    class DummySession(dict):
        modified = False

    def _create_request_with_session(self):
        request = self.factory.get('/')
        request.session = self.DummySession()
        return request

    def test_concurrent_idempotency_duplicate_requests_produce_single_order(self):
        """
        Dos hilos concurrentes envían pedidos con la MISMA idempotency_key simultáneamente.
        Debe crearse exactamente 1 pedido y descontarse el stock solo 1 vez sin colapso de base de datos.
        """
        idemp_key = "idemp-race-test-999"
        results = []
        errors = []

        def worker():
            # Crear conexión independiente por hilo
            req = self._create_request_with_session()
            CartService.add_product(req, self.producto.id, quantity=1)
            try:
                order = OrderService.create_order_from_cart(
                    user=self.user,
                    request=req,
                    direccion_entrega="Av. Concurrencia 100",
                    telefono_contacto="987111222",
                    metodo_pago="efectivo",
                    idempotency_key=idemp_key,
                )
                results.append(order.id)
            except Exception as e:
                errors.append(e)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker), threading.Thread(target=worker)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Ocurrieron errores inesperados: {errors}")
        self.assertEqual(len(results), 2)
        # Ambos hilos deben apuntar al MISMO ID de pedido
        self.assertEqual(results[0], results[1])

        # Exactamente 1 pedido persistido en base de datos
        self.assertEqual(Pedido.objects.filter(idempotency_key=idemp_key).count(), 1)

        # Stock reducido exactamente 1 vez (de 1 a 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)

    def test_concurrent_stock_race_condition_for_last_item(self):
        """
        Dos hilos concurrentes compiten por la última unidad disponible (stock=1) con claves distintas.
        Exactamente uno debe ganar la unidad y el otro debe fallar con InsufficientStockError.
        """
        successes = []
        insufficient_errors = []
        other_errors = []

        def worker(thread_idx):
            req = self._create_request_with_session()
            CartService.add_product(req, self.producto.id, quantity=1)
            try:
                order = OrderService.create_order_from_cart(
                    user=self.user,
                    request=req,
                    direccion_entrega=f"Calle Competencia #{thread_idx}",
                    telefono_contacto=f"90000000{thread_idx}",
                    metodo_pago="efectivo",
                    idempotency_key=f"unique-key-{thread_idx}",
                )
                successes.append(order.id)
            except InsufficientStockError as e:
                insufficient_errors.append(e)
            except Exception as e:
                other_errors.append(e)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker, args=(1,)), threading.Thread(target=worker, args=(2,))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(other_errors), 0, f"Errores no controlados: {other_errors}")
        self.assertEqual(len(successes), 1, "Exactamente un pedido debió concretarse")
        self.assertEqual(len(insufficient_errors), 1, "El segundo hilo debió detectar InsufficientStockError")

        # Stock final en 0, nunca negativo
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)
        self.assertEqual(Pedido.objects.count(), 1)


