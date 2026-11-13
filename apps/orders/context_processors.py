from config.constants import NOVAGO_COVERAGE_RADIUS_KM, NOVAGO_STORE_LAT, NOVAGO_STORE_LNG
from .services import CartService


def cart_context(request):
    """
    Context processor global para proveer información del carrito y ubicación de entrega
    en todas las vistas, tanto para visitantes anónimos como usuarios autenticados.
    """
    delivery_location = None
    try:
        delivery_location = request.session.get('delivery_location')
    except Exception:
        delivery_location = None

    novago_store = {
        'lat': NOVAGO_STORE_LAT,
        'lng': NOVAGO_STORE_LNG,
        'radius_km': NOVAGO_COVERAGE_RADIUS_KM,
    }

    try:
        totals = CartService.get_totals(request)
        return {
            'cart_count': totals.get('count', 0),
            'cart_items': totals.get('items', []),
            'cart_subtotal': totals.get('subtotal', 0),
            'cart_shipping': totals.get('shipping', 0),
            'cart_total': totals.get('total', 0),
            'delivery_location': delivery_location,
            'novago_store': novago_store,
        }
    except Exception:
        return {
            'cart_count': 0,
            'cart_items': [],
            'cart_subtotal': 0,
            'cart_shipping': 0,
            'cart_total': 0,
            'delivery_location': delivery_location,
            'novago_store': novago_store,
        }

