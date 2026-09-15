from asgiref.sync import sync_to_async # type: ignore
from channels.generic.websocket import AsyncJsonWebsocketConsumer # type: ignore
from django.shortcuts import get_object_or_404 # type: ignore
from django.urls import reverse # type: ignore

from apps.orders.models import Pedido

from apps.tracking.map_service import get_motorizado_map_snapshot, get_order_map_snapshot_for_user


class MotorizadoTrackingConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        user_role = getattr(user, 'role', '')
        if user_role not in ('motorizado', 'admin') and not user.is_staff:
            await self.close(code=4403)
            return

        self.group_name = f'tracking_motorizado_{user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        snapshot = await sync_to_async(get_motorizado_map_snapshot)(user)
        await self.send_json({
            'type': 'tracking.snapshot',
            'payload': snapshot,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        event = content.get('type')
        if event != 'tracking.request_snapshot':
            return

        user = self.scope.get('user')
        pedido_id = content.get('pedido_id')
        pedido_int = None
        if pedido_id is not None:
            try:
                pedido_int = int(pedido_id)
            except (TypeError, ValueError):
                pedido_int = None

        snapshot = await sync_to_async(get_motorizado_map_snapshot)(user, pedido_int)
        await self.send_json({
            'type': 'tracking.snapshot',
            'payload': snapshot,
        })

    async def tracking_location(self, event):
        await self.send_json({
            'type': 'tracking.location',
            'payload': event.get('payload', {}),
        })


def _order_progress_payload(order):
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

    current_step = status_step_map.get(order.estado, 1)
    route = getattr(order, 'ruta', None)
    eta_minutes = route.tiempo_estimado_min if route and getattr(route, 'tiempo_estimado_min', None) else eta_default_by_state.get(order.estado, 20)

    return {
        'pedido_id': order.id,
        'estado': order.estado,
        'estado_display': order.get_estado_display(),
        'progress_step': current_step,
        'progress_percent': status_progress_map.get(current_step, 15),
        'eta_minutes': eta_minutes,
        'payment_status_display': order.pago.get_estado_display() if getattr(order, 'pago', None) else 'Sin pago',
        'tracking_url': reverse('users:portal_cliente_rastreo_pedido', kwargs={'pedido_id': order.id}),
        'orders_url': reverse('users:portal_cliente_pedidos'),
        'detail_url': reverse('users:portal_cliente_pedido_detalle', kwargs={'pedido_id': order.id}),
        'portal_url': reverse('users:portal_cliente'),
    }


class OrderStatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        try:
            self.pedido_id = int(self.scope['url_route']['kwargs']['pedido_id'])
        except (TypeError, ValueError, KeyError):
            await self.close(code=4400)
            return

        has_access = await sync_to_async(self._user_can_access_order)(user, self.pedido_id)
        if not has_access:
            await self.close(code=4403)
            return

        self.group_name = f'order_status_{self.pedido_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        payload = await sync_to_async(self._get_order_payload)(self.pedido_id)
        await self.send_json({
            'type': 'order.status',
            'payload': payload,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        event = content.get('type')
        if event != 'order.request_snapshot':
            return

        payload = await sync_to_async(self._get_order_payload)(self.pedido_id)
        await self.send_json({
            'type': 'order.status',
            'payload': payload,
        })

    async def order_status(self, event):
        await self.send_json({
            'type': 'order.status',
            'payload': event.get('payload', {}),
        })

    @staticmethod
    def _user_can_access_order(user, pedido_id):
        pedido = get_object_or_404(Pedido, id=pedido_id)
        if user.is_staff or getattr(user, 'role', '') == 'admin':
            return True
        return pedido.cliente_id == user.id or pedido.motorizado_id == user.id

    @staticmethod
    def _get_order_payload(pedido_id):
        pedido = get_object_or_404(
            Pedido.objects.select_related('ruta', 'pago'),
            id=pedido_id,
        )
        return _order_progress_payload(pedido)


class OrderTrackingConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        try:
            self.pedido_id = int(self.scope['url_route']['kwargs']['pedido_id'])
        except (TypeError, ValueError, KeyError):
            await self.close(code=4400)
            return

        snapshot = await sync_to_async(get_order_map_snapshot_for_user)(user, self.pedido_id)
        if not snapshot.get('ok'):
            await self.close(code=4403)
            return

        self.group_name = f'order_tracking_{self.pedido_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({
            'type': 'tracking.snapshot',
            'payload': snapshot,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get('type') != 'tracking.request_snapshot':
            return

        user = self.scope.get('user')
        snapshot = await sync_to_async(get_order_map_snapshot_for_user)(user, self.pedido_id)
        await self.send_json({
            'type': 'tracking.snapshot',
            'payload': snapshot,
        })

    async def tracking_location(self, event):
        await self.send_json({
            'type': 'tracking.location',
            'payload': event.get('payload', {}),
        })
