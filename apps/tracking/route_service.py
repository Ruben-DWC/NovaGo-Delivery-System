import hashlib
import json
from decimal import Decimal
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from apps.tracking.map_service import NOVAGO_STORE_LAT, NOVAGO_STORE_LNG
from apps.tracking.models import RutaEntrega


def _fallback_coordinates(address: str) -> tuple[Decimal, Decimal]:
    # Fallback deterministico por direccion para no depender al 100% del proveedor externo.
    digest = hashlib.sha256(address.encode('utf-8')).hexdigest()
    lat_offset = (int(digest[:6], 16) % 1600) / 100000
    lng_offset = (int(digest[6:12], 16) % 1600) / 100000

    lat_sign = -1 if int(digest[12], 16) % 2 == 0 else 1
    lng_sign = -1 if int(digest[13], 16) % 2 == 0 else 1

    return (
        NOVAGO_STORE_LAT + Decimal(str(lat_sign * lat_offset)),
        NOVAGO_STORE_LNG + Decimal(str(lng_sign * lng_offset)),
    )


def geocode_address_to_coordinates(address: str) -> tuple[Decimal, Decimal]:
    normalized = f"{address}, Ate, Lima, Peru"
    url = f"https://nominatim.openstreetmap.org/search?q={quote_plus(normalized)}&format=json&limit=1"
    request = Request(
        url,
        headers={
            'User-Agent': 'NovaGoDelivery/1.0 (academic-project)',
            'Accept': 'application/json',
        },
    )

    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode('utf-8'))
            if payload:
                return Decimal(str(payload[0]['lat'])), Decimal(str(payload[0]['lon']))
    except Exception:
        pass

    return _fallback_coordinates(address)


def ensure_delivery_route_for_order(order):
    destination_lat, destination_lng = geocode_address_to_coordinates(order.direccion_entrega)

    RutaEntrega.objects.update_or_create(
        pedido=order,
        defaults={
            'origen_lat': NOVAGO_STORE_LAT,
            'origen_lng': NOVAGO_STORE_LNG,
            'destino_lat': destination_lat,
            'destino_lng': destination_lng,
        },
    )
