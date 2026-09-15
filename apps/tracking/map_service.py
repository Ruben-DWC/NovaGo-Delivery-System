import math
from decimal import Decimal
from typing import Any

from apps.orders.models import Pedido
from apps.tracking.models import UbicacionTracking


NOVAGO_STORE_NAME = 'NovaGo Ate - Vitarte'
NOVAGO_STORE_LAT = Decimal('-12.026200')
NOVAGO_STORE_LNG = Decimal('-76.921200')


def compute_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * (math.sin(d_lng / 2) ** 2)
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def fallback_destination(pedido_id: int, origin_lat: Decimal, origin_lng: Decimal) -> tuple[Decimal, Decimal]:
    offsets = [
        (Decimal('0.010500'), Decimal('-0.008200')),
        (Decimal('-0.007800'), Decimal('0.009400')),
        (Decimal('0.006400'), Decimal('0.010800')),
    ]
    offset_lat, offset_lng = offsets[pedido_id % len(offsets)]
    return origin_lat + offset_lat, origin_lng + offset_lng


def _build_payload_for_order(pedido: Pedido) -> dict[str, Any]:
    ruta = getattr(pedido, 'ruta', None)

    origin_lat = Decimal(ruta.origen_lat) if ruta else NOVAGO_STORE_LAT
    origin_lng = Decimal(ruta.origen_lng) if ruta else NOVAGO_STORE_LNG

    if ruta:
        destination_lat = Decimal(ruta.destino_lat)
        destination_lng = Decimal(ruta.destino_lng)
    else:
        destination_lat, destination_lng = fallback_destination(pedido.id, origin_lat, origin_lng)

    latest_location = (
        UbicacionTracking.objects.filter(pedido=pedido)
        .order_by('-timestamp')
        .first()
    )

    history = list(
        UbicacionTracking.objects.filter(pedido=pedido)
        .order_by('-timestamp')
        .values('latitud', 'longitud', 'timestamp')[:100]
    )
    history.reverse()

    tracking_history = [
        {
            'lat': float(item['latitud']),
            'lng': float(item['longitud']),
            'timestamp': item['timestamp'].isoformat(),
        }
        for item in history
    ]

    motorizado_lat = Decimal(latest_location.latitud) if latest_location else origin_lat
    motorizado_lng = Decimal(latest_location.longitud) if latest_location else origin_lng

    distance_km = compute_distance_km(
        float(motorizado_lat),
        float(motorizado_lng),
        float(destination_lat),
        float(destination_lng),
    )

    eta_min = int(math.ceil(distance_km * 4))
    if ruta and ruta.tiempo_estimado_min:
        eta_min = int(ruta.tiempo_estimado_min)
    eta_min = max(1, eta_min)

    return {
        'ok': True,
        'has_active_order': True,
        'active_order_id': pedido.id,
        'order_status': pedido.estado,
        'order_delivery_address': pedido.direccion_entrega,
        'store': {
            'name': NOVAGO_STORE_NAME,
            'lat': float(origin_lat),
            'lng': float(origin_lng),
        },
        'motorizado': {
            'lat': float(motorizado_lat),
            'lng': float(motorizado_lng),
            'last_update': latest_location.timestamp.isoformat() if latest_location else None,
        },
        'destination': {
            'lat': float(destination_lat),
            'lng': float(destination_lng),
        },
        'distance_km': round(distance_km, 2),
        'eta_min': eta_min,
        'tracking_history': tracking_history,
    }


def get_motorizado_map_snapshot(user, pedido_id: int | None = None) -> dict[str, Any]:
    active_orders = Pedido.objects.filter(
        motorizado=user,
        estado__in=['confirmado', 'en_preparacion', 'en_camino'],
    ).order_by('-fecha_pedido')

    if not active_orders.exists():
        return {
            'ok': True,
            'has_active_order': False,
            'store': {
                'name': NOVAGO_STORE_NAME,
                'lat': float(NOVAGO_STORE_LAT),
                'lng': float(NOVAGO_STORE_LNG),
            },
            'tracking_history': [],
        }

    pedido = active_orders.first()
    if pedido_id:
        selected = active_orders.filter(id=pedido_id).first()
        if selected:
            pedido = selected

    return _build_payload_for_order(pedido)


def get_order_map_snapshot_for_user(user, pedido_id: int) -> dict[str, Any]:
    pedido = Pedido.objects.select_related('cliente', 'motorizado').filter(id=pedido_id).first()
    if not pedido:
        return {
            'ok': False,
            'error': 'Pedido no encontrado',
        }

    can_view = user.is_staff or getattr(user, 'role', '') == 'admin' or pedido.cliente_id == user.id or pedido.motorizado_id == user.id
    if not can_view:
        return {
            'ok': False,
            'error': 'No autorizado para este pedido',
        }

    return _build_payload_for_order(pedido)
