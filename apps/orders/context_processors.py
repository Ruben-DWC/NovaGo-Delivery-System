from .services import CartService


def cart_context(request):
    """
    Context processor global para proveer información del carrito en todas las vistas,
    tanto para visitantes anónimos como usuarios autenticados.
    """
    try:
        totals = CartService.get_totals(request)
        return {
            'cart_count': totals.get('count', 0),
            'cart_items': totals.get('items', []),
            'cart_subtotal': totals.get('subtotal', 0),
            'cart_shipping': totals.get('shipping', 0),
            'cart_total': totals.get('total', 0),
        }
    except Exception:
        return {
            'cart_count': 0,
            'cart_items': [],
            'cart_subtotal': 0,
            'cart_shipping': 0,
            'cart_total': 0,
        }

