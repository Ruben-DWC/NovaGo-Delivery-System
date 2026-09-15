from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView, FormView
from django.db.models import Count, Q
from .models import Pedido
from .forms import CheckoutForm
from .services import CartService, OrderService, AutoAsignmentService, JornadaService
from apps.users.mixins import AdminRequiredMixin


class CartView(TemplateView):
	template_name = 'orders/cart.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update(CartService.get_totals(self.request))
		return context


class AddToCartView(View):
	def post(self, request, producto_id):
		quantity = request.POST.get('quantity', 1)
		CartService.add_product(request, producto_id, quantity)
		messages.success(request, 'Producto agregado al carrito.')
		return redirect(request.META.get('HTTP_REFERER', 'orders:cart'))


class UpdateCartView(View):
	def post(self, request, item_id):
		quantity = request.POST.get('quantity')
		if quantity is None:
			return HttpResponseBadRequest('Cantidad invalida.')
		CartService.update_product(request, item_id, quantity)
		messages.success(request, 'Carrito actualizado.')
		return redirect('orders:cart')


class RemoveFromCartView(View):
	def post(self, request, item_id):
		CartService.remove_product(request, item_id)
		messages.info(request, 'Producto retirado del carrito.')
		return redirect('orders:cart')


class CheckoutView(LoginRequiredMixin, FormView):
	template_name = 'orders/checkout.html'
	form_class = CheckoutForm

	def dispatch(self, request, *args, **kwargs):
		if request.user.role != 'cliente':
			messages.warning(request, 'Solo los clientes pueden realizar pedidos.')
			return redirect('home')
		if request.method == 'GET':
			return redirect('users:portal_cliente_pago')
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update(CartService.get_totals(self.request))
		return context

	def form_valid(self, form):
		try:
			order = OrderService.create_order_from_cart(
				user=self.request.user,
				request=self.request,
				direccion_entrega=form.cleaned_data['direccion_entrega'],
				telefono_contacto=form.cleaned_data['telefono_contacto'],
				metodo_pago=form.cleaned_data['metodo_pago'],
				referencia=form.cleaned_data.get('referencia', ''),
				notas=form.cleaned_data.get('notas', ''),
			)
		except ValueError as exc:
			form.add_error(None, str(exc))
			return self.form_invalid(form)

		messages.success(self.request, 'Pedido generado correctamente.')
		return redirect('orders:order_detail', pedido_id=order.id)


class OrderListView(LoginRequiredMixin, TemplateView):
	template_name = 'orders/order_list.html'

	def dispatch(self, request, *args, **kwargs):
		if (
			request.method == 'GET'
			and getattr(request.user, 'role', '') == 'motorizado'
			and getattr(getattr(request, 'resolver_match', None), 'app_name', '') == 'orders'
		):
			return redirect('tracking:motorizado_historial')
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		active_states = ['pendiente_asignacion', 'confirmado', 'en_preparacion', 'en_camino']
		queryset = Pedido.objects.select_related('cliente', 'motorizado').prefetch_related('items__producto')

		if user.role == 'cliente':
			queryset = queryset.filter(cliente=user)
		elif user.role == 'motorizado':
			queryset = queryset.filter(motorizado=user)

		orders = queryset.order_by('-fecha_pedido')
		context['orders'] = orders
		context['active_states'] = active_states
		context['orders_total'] = orders.count()
		context['orders_active'] = orders.filter(estado__in=active_states).count()
		context['orders_delivered'] = orders.filter(estado='entregado').count()
		context['orders_cancelled'] = orders.filter(estado='cancelado').count()
		context['is_client_order_view'] = getattr(user, 'role', '') == 'cliente'
		return context


class OrderDetailView(LoginRequiredMixin, TemplateView):
	template_name = 'orders/order_detail.html'

	def dispatch(self, request, *args, **kwargs):
		if (
			request.method == 'GET'
			and getattr(request.user, 'role', '') == 'motorizado'
			and getattr(getattr(request, 'resolver_match', None), 'app_name', '') == 'orders'
		):
			return redirect('tracking:motorizado_pedido_detalle', pedido_id=kwargs['pedido_id'])
		if (
			request.method == 'GET'
			and getattr(request.user, 'role', '') == 'cliente'
			and getattr(getattr(request, 'resolver_match', None), 'app_name', '') == 'orders'
		):
			return redirect('users:portal_cliente_pedido_detalle', pedido_id=kwargs['pedido_id'])
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		pedido = get_object_or_404(
			Pedido.objects.select_related('cliente', 'motorizado').prefetch_related('items__producto', 'pago', 'ruta', 'ubicaciones'),
			id=self.kwargs['pedido_id'],
		)

		user = self.request.user
		can_view = user.is_staff or user.role == 'admin' or pedido.cliente_id == user.id or pedido.motorizado_id == user.id
		if not can_view:
			messages.error(self.request, 'No tienes permisos para ver este pedido.')
			context['forbidden'] = True
			return context

		context['order'] = pedido
		context['forbidden'] = False
		context['tracking_points'] = pedido.ubicaciones.order_by('-timestamp')[:20]
		return context


class AdminDashboardView(AdminRequiredMixin, TemplateView):
	"""
	Dashboard de administrador con vista global de todos los pedidos,
	motorizados y opciones de supervisión.
	"""
	template_name = 'admin/dashboard_admin.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Estadísticas generales
		pedidos_hoy = Pedido.objects.filter(
			fecha_pedido__date=__import__('django.utils.timezone', fromlist=['now']).now().date()
		)
		
		context['stats'] = {
			'total_pedidos_hoy': pedidos_hoy.count(),
			'pedidos_entregados': pedidos_hoy.filter(estado='entregado').count(),
			'pedidos_en_camino': pedidos_hoy.filter(estado='en_camino').count(),
			'pedidos_pendientes_asignacion': Pedido.objects.filter(estado='pendiente_asignacion').count(),
			'motorizados_activos': self._contar_motorizados_activos(),
			'ingresos_hoy': sum(p.total for p in pedidos_hoy.filter(estado='entregado')) if pedidos_hoy.exists() else 0,
		}
		
		# Últimos 20 pedidos (para tabla)
		context['pedidos'] = Pedido.objects.select_related(
			'cliente', 'motorizado'
		).order_by('-fecha_pedido')[:20]
		
		# Motorizados con estadísticas
		from apps.users.models import PerfilMotorizado, User
		motorizados = PerfilMotorizado.objects.select_related('usuario').annotate(
			pedidos_hoy=Count(
				'usuario__entregas',
				filter=Q(usuario__entregas__fecha_pedido__date=__import__('django.utils.timezone', fromlist=['now']).now().date())
			),
			entregas_hoy=Count(
				'usuario__entregas',
				filter=Q(usuario__entregas__estado='entregado', usuario__entregas__fecha_pedido__date=__import__('django.utils.timezone', fromlist=['now']).now().date())
			)
		).order_by('-jornada_activa', '-usuario__last_login')
		
		context['motorizados'] = motorizados[:10]
		
		# Datos para mapa (ubicaciones de motorizados activos)
		context['motorizado_locations'] = self._obtener_ubicaciones_motorizados()
		
		return context
	
	@staticmethod
	def _contar_motorizados_activos():
		"""Cuenta motorizados con jornada activa actualmente."""
		from apps.users.models import PerfilMotorizado
		return PerfilMotorizado.objects.filter(jornada_activa=True).count()
	
	@staticmethod
	def _obtener_ubicaciones_motorizados():
		"""Retorna JSON de ubicaciones de motorizados para el mapa."""
		from apps.users.models import PerfilMotorizado
		motorizados = PerfilMotorizado.objects.filter(jornada_activa=True).select_related('usuario')
		
		ubicaciones = []
		for moto in motorizados:
			ubicacion = moto.ubicacion_actual
			if ubicacion and 'lat' in ubicacion and 'lng' in ubicacion:
				ubicaciones.append({
					'id': moto.usuario.id,
					'nombre': moto.usuario.get_full_name() or moto.usuario.username,
					'lat': ubicacion['lat'],
					'lng': ubicacion['lng'],
					'calificacion': float(moto.calificacion),
					'placa': moto.placa_vehiculo,
				})
		
		return ubicaciones


class AdminAsignarPedidoView(AdminRequiredMixin, View):
	"""
	AJAX endpoint para reasignar un pedido a un motorizado diferente.
	"""
	def post(self, request):
		pedido_id = request.POST.get('pedido_id')
		motorizado_id = request.POST.get('motorizado_id')
		
		if not pedido_id or not motorizado_id:
			return JsonResponse({'ok': False, 'error': 'Datos incompletos'}, status=400)
		
		try:
			pedido = Pedido.objects.get(id=pedido_id)
			from apps.users.models import User
			motorizado = User.objects.get(id=motorizado_id, role='motorizado')
			
			# Validar que el pedido está en estado apropiado
			if pedido.estado not in ['pendiente_asignacion', 'confirmado']:
				return JsonResponse(
					{'ok': False, 'error': f'No puedes reasignar un pedido en estado {pedido.estado}'},
					status=400
				)
			
			# Reasignar
			from django.utils import timezone
			pedido.motorizado = motorizado
			pedido.estado = 'confirmado'
			if not pedido.fecha_asignacion:
				pedido.fecha_asignacion = timezone.now()
			pedido.save(update_fields=['motorizado', 'estado', 'fecha_asignacion'])
			from apps.orders.services import JornadaService
			JornadaService.broadcast_order_status(pedido)
			
			return JsonResponse({'ok': True, 'message': 'Pedido reasignado correctamente'})
			
		except Pedido.DoesNotExist:
			return JsonResponse({'ok': False, 'error': 'Pedido no encontrado'}, status=404)
		except User.DoesNotExist:
			return JsonResponse({'ok': False, 'error': 'Motorizado no encontrado'}, status=404)
		except Exception as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class AdminAsignacionAutomaticaView(AdminRequiredMixin, View):
	"""
	AJAX endpoint para ejecutar asignación automática manualmente.
	"""
	def post(self, request):
		resultado = AutoAsignmentService.asignar_pedidos_pendientes()
		return JsonResponse(resultado)
