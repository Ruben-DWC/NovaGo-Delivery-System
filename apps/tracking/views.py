import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from asgiref.sync import async_to_sync # type: ignore
from channels.layers import get_channel_layer # type: ignore
from django.utils import timezone # pyright: ignore[reportMissingModuleSource]
from django.contrib import messages # pyright: ignore[reportMissingModuleSource]
from django.contrib.auth.mixins import LoginRequiredMixin # pyright: ignore[reportMissingModuleSource]
from django.http import JsonResponse # pyright: ignore[reportMissingModuleSource]
from django.shortcuts import get_object_or_404, redirect # pyright: ignore[reportMissingModuleSource]
from django.views import View # pyright: ignore[reportMissingModuleSource]
from django.views.generic import TemplateView # pyright: ignore[reportMissingModuleSource]
from django.db.models import Q # pyright: ignore[reportMissingModuleSource]
from django.core.paginator import Paginator # pyright: ignore[reportMissingModuleSource]
from apps.orders.models import Pedido
from apps.users.mixins import MotorizadoRequiredMixin
from .map_service import NOVAGO_STORE_LAT, NOVAGO_STORE_LNG, NOVAGO_STORE_NAME, get_motorizado_map_snapshot, get_order_map_snapshot_for_user
from .models import UbicacionTracking


def broadcast_order_tracking_snapshot(pedido):
	channel_layer = get_channel_layer()
	if not channel_layer:
		return

	payload = get_order_map_snapshot_for_user(pedido.cliente, pedido.id)
	async_to_sync(channel_layer.group_send)(
		f'order_tracking_{pedido.id}',
		{
			'type': 'tracking.location',
			'payload': payload,
		},
	)

class TrackOrderView(LoginRequiredMixin, TemplateView):
	template_name = 'tracking/track_order_map.html'

	def dispatch(self, request, *args, **kwargs):
		current_route = getattr(getattr(request, 'resolver_match', None), 'view_name', '')
		if getattr(request.user, 'role', '') == 'cliente' and request.method.lower() == 'get':
			if current_route == 'tracking:track_order':
				return redirect('users:portal_cliente_rastreo_pedido', pedido_id=kwargs['pedido_id'])
		if getattr(request.user, 'role', '') == 'motorizado' and request.method.lower() == 'get':
			if current_route == 'tracking:track_order':
				return redirect('tracking:motorizado_rastreo_pedido', pedido_id=kwargs['pedido_id'])
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		pedido = get_object_or_404(
			Pedido.objects.select_related('cliente', 'motorizado').prefetch_related('ubicaciones', 'ruta'),
			id=self.kwargs['pedido_id'],
		)

		user = self.request.user
		can_view = user.is_staff or user.role == 'admin' or pedido.cliente_id == user.id or pedido.motorizado_id == user.id
		if not can_view:
			messages.error(self.request, 'No tienes permisos para ver el rastreo de este pedido.')
			context['forbidden'] = True
			return context

		context['pedido'] = pedido
		context['forbidden'] = False
		context['tracking_points'] = pedido.ubicaciones.order_by('-timestamp')[:20]
		context['route'] = getattr(pedido, 'ruta', None)
		return context


class MotorizadoDashboardView(MotorizadoRequiredMixin, TemplateView):
	template_name = 'motorizado/dashboard.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		queryset = Pedido.objects.select_related('cliente').prefetch_related('ruta')
		if not self.request.user.is_staff:
			queryset = queryset.filter(motorizado=self.request.user)

		delivered_orders = queryset.filter(estado='entregado')
		total_earned_value = sum(order.total for order in delivered_orders) if delivered_orders.exists() else Decimal('0.00')

		perfil_motorizado = getattr(self.request.user, 'perfil_motorizado', None)
		rating_value = getattr(perfil_motorizado, 'calificacion', Decimal('0.00')) if perfil_motorizado else Decimal('0.00')

		active_orders = queryset.filter(estado__in=['confirmado', 'en_preparacion', 'en_camino']).order_by('-fecha_pedido')
		first_active_order = active_orders.first()

		context['active_orders'] = active_orders
		context['active_orders_count'] = context['active_orders'].count()
		context['completed_today'] = delivered_orders.filter(fecha_entrega__date=timezone.localdate()).count()
		context['rating'] = f"{rating_value:.2f}"
		context['total_earned'] = f"S/. {total_earned_value:.2f}"
		context['completed_orders'] = delivered_orders.order_by('-fecha_pedido')[:10]
		context['active_order_id'] = first_active_order.id if first_active_order else ''
		context['novago_store_name'] = NOVAGO_STORE_NAME
		context['novago_store_lat'] = f"{NOVAGO_STORE_LAT:.6f}"
		context['novago_store_lng'] = f"{NOVAGO_STORE_LNG:.6f}"
		context['perfil_motorizado'] = perfil_motorizado
		context['can_finalize_jornada'] = context['active_orders_count'] == 0
		return context


class MotorizadoHistoryView(MotorizadoRequiredMixin, TemplateView):
	template_name = 'motorizado/order_history.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		base_orders = (
			Pedido.objects.select_related('cliente', 'motorizado', 'pago', 'ruta')
			.prefetch_related('items__producto')
			.filter(motorizado=self.request.user)
		)
		orders = base_orders

		search_query = (self.request.GET.get('q') or '').strip()
		estado = (self.request.GET.get('estado') or '').strip()
		periodo = (self.request.GET.get('periodo') or '').strip()
		sort = (self.request.GET.get('sort') or 'fecha_desc').strip()
		page_size_raw = (self.request.GET.get('page_size') or '8').strip()
		valid_page_sizes = ['8', '12', '24']
		page_size = int(page_size_raw) if page_size_raw in valid_page_sizes else 8

		valid_states = ['confirmado', 'en_preparacion', 'en_camino', 'entregado', 'cancelado', 'pendiente_asignacion']
		if estado and estado in valid_states:
			orders = orders.filter(estado=estado)

		today = timezone.localdate()
		if periodo == 'hoy':
			orders = orders.filter(fecha_pedido__date=today)
		elif periodo == '7d':
			orders = orders.filter(fecha_pedido__gte=timezone.now() - timedelta(days=7))
		elif periodo == '30d':
			orders = orders.filter(fecha_pedido__gte=timezone.now() - timedelta(days=30))

		if search_query:
			orders = orders.filter(
				Q(cliente__username__icontains=search_query)
				| Q(cliente__first_name__icontains=search_query)
				| Q(cliente__last_name__icontains=search_query)
				| Q(telefono_contacto__icontains=search_query)
			)

		sort_options = {
			'fecha_desc': '-fecha_pedido',
			'fecha_asc': 'fecha_pedido',
			'total_desc': '-total',
			'total_asc': 'total',
			'estado_asc': 'estado',
			'estado_desc': '-estado',
		}
		order_by_value = sort_options.get(sort, '-fecha_pedido')
		orders = orders.order_by(order_by_value)

		active_states = ['confirmado', 'en_preparacion', 'en_camino']
		orders_total = orders.count()
		orders_active = orders.filter(estado__in=active_states).count()
		orders_delivered = orders.filter(estado='entregado').count()
		orders_cancelled = orders.filter(estado='cancelado').count()

		status_totals = {
			'all': base_orders.count(),
			'confirmado': base_orders.filter(estado='confirmado').count(),
			'en_preparacion': base_orders.filter(estado='en_preparacion').count(),
			'en_camino': base_orders.filter(estado='en_camino').count(),
			'entregado': base_orders.filter(estado='entregado').count(),
			'cancelado': base_orders.filter(estado='cancelado').count(),
		}

		paginator = Paginator(orders, page_size)
		page_number = self.request.GET.get('page')
		page_obj = paginator.get_page(page_number)

		query_params = self.request.GET.copy()
		if 'page' in query_params:
			query_params.pop('page')

		quick_state_query = self.request.GET.copy()
		if 'estado' in quick_state_query:
			quick_state_query.pop('estado')
		if 'page' in quick_state_query:
			quick_state_query.pop('page')

		context['orders'] = page_obj.object_list
		context['page_obj'] = page_obj
		context['paginator'] = paginator
		context['is_paginated'] = page_obj.has_other_pages()
		context['pagination_query'] = query_params.urlencode()
		context['orders_total'] = orders_total
		context['orders_active'] = orders_active
		context['orders_delivered'] = orders_delivered
		context['orders_cancelled'] = orders_cancelled
		context['active_states'] = active_states
		context['filter_q'] = search_query
		context['filter_estado'] = estado
		context['filter_periodo'] = periodo
		context['filter_sort'] = sort
		context['filter_page_size'] = str(page_size)
		context['has_filters'] = bool(search_query or estado or periodo or page_size != 8)
		context['status_totals'] = status_totals
		context['quick_state_query'] = quick_state_query.urlencode()
		context['page_size_options'] = [('8', '8 por página'), ('12', '12 por página'), ('24', '24 por página')]
		context['estado_options'] = [
			('confirmado', 'Confirmado'),
			('en_preparacion', 'En preparación'),
			('en_camino', 'En camino'),
			('entregado', 'Entregado'),
			('cancelado', 'Cancelado'),
			('pendiente_asignacion', 'Pendiente de asignación'),
		]
		context['sort_options'] = [
			('fecha_desc', 'Fecha (más reciente)'),
			('fecha_asc', 'Fecha (más antigua)'),
			('total_desc', 'Total (mayor a menor)'),
			('total_asc', 'Total (menor a mayor)'),
			('estado_asc', 'Estado (A-Z)'),
			('estado_desc', 'Estado (Z-A)'),
		]
		return context


class MotorizadoOrderDetailView(MotorizadoRequiredMixin, TemplateView):
	template_name = 'orders/order_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		pedido = get_object_or_404(
			Pedido.objects.select_related('cliente', 'motorizado').prefetch_related('items__producto', 'pago', 'ruta', 'ubicaciones'),
			id=self.kwargs['pedido_id'],
		)

		user = self.request.user
		can_view = user.is_staff or user.role == 'admin' or pedido.motorizado_id == user.id
		if not can_view:
			messages.error(self.request, 'No tienes permisos para ver este pedido.')
			context['forbidden'] = True
			return context

		context['order'] = pedido
		context['forbidden'] = False
		context['tracking_points'] = pedido.ubicaciones.order_by('-timestamp')[:20]
		return context


class MotorizadoMapDataView(MotorizadoRequiredMixin, View):
	def get(self, request):
		pedido_id = request.GET.get('pedido_id')
		pedido_int = None
		if pedido_id:
			try:
				pedido_int = int(pedido_id)
			except ValueError:
				pedido_int = None

		return JsonResponse(get_motorizado_map_snapshot(request.user, pedido_int))


class OrderTrackingSnapshotView(LoginRequiredMixin, View):
	def get(self, request, pedido_id):
		payload = get_order_map_snapshot_for_user(request.user, pedido_id)
		status_code = 200 if payload.get('ok') else 403
		if payload.get('error') == 'Pedido no encontrado':
			status_code = 404
		return JsonResponse(payload, status=status_code)


class UpdateLocationView(MotorizadoRequiredMixin, View):
	def post(self, request):
		if request.content_type and 'application/json' in request.content_type:
			try:
				payload = json.loads(request.body.decode('utf-8') or '{}')
			except json.JSONDecodeError:
				return JsonResponse({'ok': False, 'error': 'JSON invalido'}, status=400)
			pedido_id = payload.get('pedido_id')
			latitud = payload.get('latitud')
			longitud = payload.get('longitud')
			precision = payload.get('precision')
		else:
			pedido_id = request.POST.get('pedido_id')
			latitud = request.POST.get('latitud')
			longitud = request.POST.get('longitud')
			precision = request.POST.get('precision')

		if not pedido_id or not latitud or not longitud:
			return JsonResponse({'ok': False, 'error': 'Datos incompletos'}, status=400)

		pedido = get_object_or_404(Pedido, id=pedido_id)
		if pedido.motorizado_id != request.user.id:
			return JsonResponse({'ok': False, 'error': 'Pedido no asignado al motorizado'}, status=403)

		try:
			lat = Decimal(latitud)
			lng = Decimal(longitud)
			prec = float(precision) if precision else None
		except (InvalidOperation, ValueError):
			return JsonResponse({'ok': False, 'error': 'Coordenadas invalidas'}, status=400)

		UbicacionTracking.objects.create(
			pedido=pedido,
			motorizado=request.user,
			latitud=lat,
			longitud=lng,
			precision=prec,
		)

		from apps.orders.services import JornadaService
		JornadaService.marcar_en_camino(pedido, request.user)

		snapshot = get_motorizado_map_snapshot(request.user, pedido.id)
		channel_layer = get_channel_layer()
		if channel_layer:
			async_to_sync(channel_layer.group_send)(
				f'tracking_motorizado_{request.user.id}',
				{
					'type': 'tracking.location',
					'payload': snapshot,
				},
			)

		broadcast_order_tracking_snapshot(pedido)

		return JsonResponse({'ok': True})


class MarcarEnPreparacionView(MotorizadoRequiredMixin, View):
	"""Marca un pedido como en preparación."""
	def post(self, request):
		pedido_id = request.POST.get('pedido_id')

		if not pedido_id:
			return JsonResponse({'ok': False, 'error': 'Falta pedido_id'}, status=400)

		try:
			from apps.orders.services import JornadaService
			pedido = Pedido.objects.get(id=pedido_id)

			JornadaService.marcar_en_preparacion(pedido, request.user)
			broadcast_order_tracking_snapshot(pedido)

			return JsonResponse({
				'ok': True,
				'message': 'Pedido marcado en preparación',
				'estado': pedido.estado,
			})
		except Pedido.DoesNotExist:
			return JsonResponse({'ok': False, 'error': 'Pedido no encontrado'}, status=404)
		except ValueError as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=400)
		except Exception as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class MarcarEnCaminoView(MotorizadoRequiredMixin, View):
	"""Marca un pedido como en camino."""
	def post(self, request):
		pedido_id = request.POST.get('pedido_id')

		if not pedido_id:
			return JsonResponse({'ok': False, 'error': 'Falta pedido_id'}, status=400)

		try:
			from apps.orders.services import JornadaService
			pedido = Pedido.objects.get(id=pedido_id)

			JornadaService.marcar_en_camino(pedido, request.user)
			broadcast_order_tracking_snapshot(pedido)

			return JsonResponse({
				'ok': True,
				'message': 'Pedido marcado en camino',
				'estado': pedido.estado,
			})
		except Pedido.DoesNotExist:
			return JsonResponse({'ok': False, 'error': 'Pedido no encontrado'}, status=404)
		except ValueError as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=400)
		except Exception as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=500)

class IniciarJornadaView(MotorizadoRequiredMixin, View):
	"""Inicia una jornada laboral para el motorizado."""
	def post(self, request):
		try:
			from apps.orders.services import JornadaService
			
			resultado = JornadaService.iniciar_jornada(request.user)
			
			return JsonResponse({
				'ok': True,
				'message': 'Jornada iniciada correctamente',
				'asignados': resultado.get('asignados', 0),
			})
		except Exception as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=400)


class FinalizarJornadaView(MotorizadoRequiredMixin, View):
	"""Finaliza la jornada laboral del motorizado."""
	def post(self, request):
		try:
			from apps.orders.services import JornadaService
			
			JornadaService.finalizar_jornada(request.user)
			
			return JsonResponse({
				'ok': True,
				'message': 'Jornada finalizada correctamente',
			})
		except ValueError as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=400)
		except Exception as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class MarcarEntregadoView(MotorizadoRequiredMixin, View):
	"""Marca un pedido como entregado."""
	def post(self, request):
		pedido_id = request.POST.get('pedido_id')
		
		if not pedido_id:
			return JsonResponse({'ok': False, 'error': 'Falta pedido_id'}, status=400)
		
		try:
			from apps.orders.services import JornadaService
			pedido = Pedido.objects.get(id=pedido_id)
			
			JornadaService.marcar_entregado(pedido, request.user)
			broadcast_order_tracking_snapshot(pedido)
			
			return JsonResponse({
				'ok': True,
				'message': 'Pedido marcado como entregado',
				'entrega_timestamp': timezone.now().isoformat(),
			})
		except Pedido.DoesNotExist:
			return JsonResponse({'ok': False, 'error': 'Pedido no encontrado'}, status=404)
		except ValueError as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=400)
		except Exception as e:
			return JsonResponse({'ok': False, 'error': str(e)}, status=500)