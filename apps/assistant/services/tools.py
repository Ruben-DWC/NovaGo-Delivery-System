import re
from typing import Any, Optional

from django.db.models import Q

from apps.orders.models import Pedido
from apps.products.models import Producto
from apps.tracking.models import UbicacionTracking

from .faq import buscar_faq

PUBLIC_TOOLS = {'buscar_producto', 'detalle_producto', 'faq'}
ORDER_TOOLS = {'estado_pedido', 'mis_pedidos', 'entregas_asignadas', 'como_cancelar'}


def _login_required_response() -> dict[str, Any]:
    return {
        'encontrado': False,
        'requiere_login': True,
        'mensaje': 'Para consultar información de pedidos debes iniciar sesión en tu cuenta de NovaGo.',
        'acciones': [
            {
                'tipo': 'login',
                'label': 'Iniciar sesión',
                'url': '/users/login/',
            }
        ],
    }


def _parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    match = re.search(r'(\d+)', str(value))
    return int(match.group(1)) if match else None


def buscar_producto(texto: str = '', max: int = 5) -> dict[str, Any]:
    """Busca productos activos en el catálogo de NovaGo."""
    try:
        limite = min(max(int(max), 1), 10)
    except (TypeError, ValueError):
        limite = 5

    qs = (
        Producto.objects.filter(activo=True)
        .select_related('categoria')
        .order_by('-destacado', '-stock', 'precio', 'nombre')
    )

    clean_text = (texto or '').strip()
    if clean_text:
        qs = qs.filter(
            Q(nombre__icontains=clean_text)
            | Q(descripcion__icontains=clean_text)
            | Q(categoria__nombre__icontains=clean_text)
        )

    productos = []
    acciones = []
    for p in qs[:limite]:
        url = f'/products/{p.id}/'
        productos.append({
            'id': p.id,
            'nombre': p.nombre,
            'categoria': p.categoria.nombre if p.categoria else 'General',
            'precio': float(p.precio),
            'stock': p.stock,
            'destacado': p.destacado,
            'descripcion': (p.descripcion[:120] + '...') if len(p.descripcion) > 120 else p.descripcion,
            'url': url,
        })
        acciones.append({
            'tipo': 'ver_producto',
            'label': f"{p.nombre} (S/ {p.precio:.2f})",
            'url': url,
            'id': p.id,
        })

    if not productos:
        return {
            'encontrado': False,
            'total': 0,
            'productos': [],
            'acciones': [],
            'mensaje': 'No encontré productos activos con ese criterio en el catálogo.',
        }

    return {
        'encontrado': True,
        'total': len(productos),
        'productos': productos,
        'acciones': acciones[:3],
        'mensaje': f'Encontré {len(productos)} producto(s) disponible(s).',
    }


def detalle_producto(id: Any) -> dict[str, Any]:
    """Retorna el detalle de un producto activo por su ID."""
    prod_id = _parse_int(id)
    if not prod_id:
        return {
            'encontrado': False,
            'mensaje': 'Indica un ID de producto válido.',
            'acciones': [],
        }

    producto = (
        Producto.objects.filter(id=prod_id, activo=True)
        .select_related('categoria')
        .first()
    )
    if not producto:
        return {
            'encontrado': False,
            'mensaje': f'No encontré ningún producto activo con el ID #{prod_id}.',
            'acciones': [],
        }

    url = f'/products/{producto.id}/'
    data = {
        'id': producto.id,
        'nombre': producto.nombre,
        'categoria': producto.categoria.nombre if producto.categoria else 'General',
        'precio': float(producto.precio),
        'stock': producto.stock,
        'destacado': producto.destacado,
        'descripcion': producto.descripcion,
        'url': url,
    }
    return {
        'encontrado': True,
        'producto': data,
        'acciones': [{'tipo': 'ver_producto', 'label': producto.nombre, 'url': url, 'id': producto.id}],
        'mensaje': f"{producto.nombre} cuesta S/ {producto.precio:.2f} (stock: {producto.stock}).",
    }


def estado_pedido(pedido_id: Any, user=None) -> dict[str, Any]:
    """Consulta el estado de un pedido respetando el rol y propiedad del usuario."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return _login_required_response()

    order_id = _parse_int(pedido_id)
    if not order_id:
        return {
            'encontrado': False,
            'mensaje': 'No pude identificar el número de pedido.',
            'acciones': [],
        }

    qs = Pedido.objects.select_related('cliente', 'motorizado').filter(id=order_id)
    role = getattr(user, 'role', 'cliente')
    is_admin = role == 'admin' or getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)

    if is_admin:
        pedido = qs.first()
    elif role == 'motorizado':
        pedido = qs.filter(motorizado=user).first()
    else:
        pedido = qs.filter(cliente=user).first()

    if not pedido:
        return {
            'encontrado': False,
            'pedido_id': order_id,
            'mensaje': f'No se encontró el pedido #{order_id}.',
            'acciones': [],
        }

    motorizado_nombre = (
        (pedido.motorizado.get_full_name() or pedido.motorizado.username)
        if pedido.motorizado
        else 'Por asignar'
    )

    ubicacion = None
    if pedido.estado == 'en_camino':
        ultima_ubi = (
            UbicacionTracking.objects.filter(pedido=pedido)
            .order_by('-timestamp')
            .first()
        )
        if ultima_ubi:
            ubicacion = {
                'latitud': float(ultima_ubi.latitud),
                'longitud': float(ultima_ubi.longitud),
            }

    url = f'/orders/{pedido.id}/'
    return {
        'encontrado': True,
        'pedido_id': pedido.id,
        'estado': pedido.estado,
        'estado_display': pedido.get_estado_display(),
        'total': float(pedido.total),
        'motorizado': motorizado_nombre,
        'fecha_pedido': pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M'),
        'puede_cancelar': pedido.puede_cancelar(),
        'ubicacion': ubicacion,
        'acciones': [{'tipo': 'ver_pedido', 'label': f'Ver pedido #{pedido.id}', 'url': url, 'id': pedido.id}],
        'mensaje': (
            f"Pedido #{pedido.id}: {pedido.get_estado_display()}. "
            f"Total: S/ {pedido.total:.2f}. Motorizado: {motorizado_nombre}."
        ),
    }


def mis_pedidos(limite: int = 5, user=None) -> dict[str, Any]:
    """Lista los pedidos recientes del cliente autenticado."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return _login_required_response()

    try:
        lim = min(max(int(limite), 1), 10)
    except (TypeError, ValueError):
        lim = 5

    pedidos_qs = Pedido.objects.filter(cliente=user).order_by('-fecha_pedido')[:lim]
    pedidos = []
    acciones = []
    for p in pedidos_qs:
        url = f'/orders/{p.id}/'
        pedidos.append({
            'id': p.id,
            'estado': p.estado,
            'estado_display': p.get_estado_display(),
            'total': float(p.total),
            'fecha_pedido': p.fecha_pedido.strftime('%d/%m/%Y %H:%M'),
            'url': url,
        })
        acciones.append({
            'tipo': 'ver_pedido',
            'label': f'Pedido #{p.id} ({p.get_estado_display()})',
            'url': url,
            'id': p.id,
        })

    if not pedidos:
        return {
            'encontrado': False,
            'pedidos': [],
            'acciones': [],
            'mensaje': 'Aún no tienes pedidos registrados en NovaGo.',
        }

    return {
        'encontrado': True,
        'pedidos': pedidos,
        'acciones': acciones[:3],
        'mensaje': f'Tienes {len(pedidos)} pedido(s) reciente(s).',
    }


def entregas_asignadas(user=None) -> dict[str, Any]:
    """Lista las entregas activas asignadas al motorizado autenticado."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return _login_required_response()

    role = getattr(user, 'role', '')
    if role not in ('motorizado', 'admin') and not getattr(user, 'is_superuser', False):
        return {
            'encontrado': False,
            'entregas': [],
            'acciones': [],
            'mensaje': 'Esta consulta está disponible solo para motorizados.',
        }

    entregas_qs = (
        Pedido.objects.filter(motorizado=user)
        .exclude(estado__in=['entregado', 'cancelado'])
        .order_by('-fecha_pedido')[:10]
    )
    entregas = []
    acciones = []
    for p in entregas_qs:
        url = f'/orders/{p.id}/'
        entregas.append({
            'id': p.id,
            'estado': p.estado,
            'estado_display': p.get_estado_display(),
            'direccion_entrega': p.direccion_entrega,
            'total': float(p.total),
            'url': url,
        })
        acciones.append({
            'tipo': 'ver_pedido',
            'label': f'Entrega #{p.id} ({p.get_estado_display()})',
            'url': url,
            'id': p.id,
        })

    if not entregas:
        return {
            'encontrado': False,
            'entregas': [],
            'acciones': [],
            'mensaje': 'No tienes entregas activas asignadas en este momento.',
        }

    return {
        'encontrado': True,
        'entregas': entregas,
        'acciones': acciones[:3],
        'mensaje': f'Tienes {len(entregas)} entrega(s) activa(s) asignada(s).',
    }


def como_cancelar(pedido_id: Any, user=None) -> dict[str, Any]:
    """Informa si un pedido del cliente puede cancelarse usando Pedido.puede_cancelar()."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return _login_required_response()

    order_id = _parse_int(pedido_id)
    if not order_id:
        return {
            'encontrado': False,
            'mensaje': 'Indica el número de pedido que deseas cancelar.',
            'acciones': [],
        }

    pedido = Pedido.objects.filter(id=order_id, cliente=user).first()
    if not pedido:
        return {
            'encontrado': False,
            'pedido_id': order_id,
            'mensaje': f'No se encontró el pedido #{order_id}.',
            'acciones': [],
        }

    url = f'/orders/{pedido.id}/'
    acciones = [{'tipo': 'ver_pedido', 'label': f'Ver pedido #{pedido.id}', 'url': url, 'id': pedido.id}]
    if pedido.puede_cancelar():
        return {
            'encontrado': True,
            'pedido_id': pedido.id,
            'puede_cancelar': True,
            'estado': pedido.estado,
            'acciones': acciones,
            'mensaje': (
                f"Tu pedido #{pedido.id} está en estado '{pedido.get_estado_display()}' "
                f"y sí puedes cancelarlo desde el detalle del pedido."
            ),
        }

    return {
        'encontrado': True,
        'pedido_id': pedido.id,
        'puede_cancelar': False,
        'estado': pedido.estado,
        'acciones': acciones,
        'mensaje': (
            f"Tu pedido #{pedido.id} ya está en estado '{pedido.get_estado_display()}', "
            f"por lo que ya no es posible cancelarlo."
        ),
    }


def faq(tema: str = '') -> dict[str, Any]:
    """Consulta preguntas frecuentes de NovaGo (pagos, envío, zonas, horarios, cancelaciones)."""
    res = buscar_faq(tema)
    return {
        'encontrado': True,
        'tema': res['tema'],
        'contenido': res['contenido'],
        'acciones': [],
        'mensaje': res['contenido'],
    }


ALL_TOOL_SCHEMAS = [
    {
        'name': 'buscar_producto',
        'description': 'Busca productos activos en el catálogo de NovaGo por nombre, descripción o categoría.',
        'parameters': {
            'type': 'object',
            'properties': {
                'texto': {'type': 'string', 'description': 'Texto de búsqueda (opcional).'},
                'max': {'type': 'integer', 'description': 'Máximo de resultados (1 a 10).'},
            },
        },
    },
    {
        'name': 'detalle_producto',
        'description': 'Obtiene el detalle completo de un producto activo por su ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer', 'description': 'ID del producto.'},
            },
            'required': ['id'],
        },
    },
    {
        'name': 'faq',
        'description': 'Consulta preguntas frecuentes de NovaGo: pagos (Yape/Plin/Efectivo), envío (S/ 5.00), zonas en Lima, horarios y cancelaciones.',
        'parameters': {
            'type': 'object',
            'properties': {
                'tema': {'type': 'string', 'description': 'Tema a consultar (pagos, envio, zonas, horarios, cancelaciones).'},
            },
        },
    },
    {
        'name': 'estado_pedido',
        'description': 'Consulta el estado y seguimiento de un pedido por su ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'pedido_id': {'type': 'integer', 'description': 'Número o ID del pedido.'},
            },
            'required': ['pedido_id'],
        },
    },
    {
        'name': 'mis_pedidos',
        'description': 'Lista los pedidos recientes del cliente autenticado.',
        'parameters': {
            'type': 'object',
            'properties': {
                'limite': {'type': 'integer', 'description': 'Cantidad máxima de pedidos a listar.'},
            },
        },
    },
    {
        'name': 'entregas_asignadas',
        'description': 'Lista las entregas activas asignadas al motorizado autenticado.',
        'parameters': {
            'type': 'object',
            'properties': {},
        },
    },
    {
        'name': 'como_cancelar',
        'description': 'Verifica si el cliente puede cancelar un pedido específico.',
        'parameters': {
            'type': 'object',
            'properties': {
                'pedido_id': {'type': 'integer', 'description': 'Número o ID del pedido.'},
            },
            'required': ['pedido_id'],
        },
    },
]


def obtener_herramientas_para_usuario(user=None) -> list[dict[str, Any]]:
    """Retorna las declaraciones de herramientas permitidas para el usuario."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return [s for s in ALL_TOOL_SCHEMAS if s['name'] in PUBLIC_TOOLS]
    return list(ALL_TOOL_SCHEMAS)


def ejecutar_herramienta(nombre: str, argumentos: Optional[dict[str, Any]] = None, user=None) -> dict[str, Any]:
    """Ejecuta una herramienta de forma segura inyectando request.user desde el servidor."""
    args = dict(argumentos or {})
    args.pop('user_id', None)
    args.pop('user', None)

    is_auth = user is not None and getattr(user, 'is_authenticated', False)
    if not is_auth and nombre in ORDER_TOOLS:
        return _login_required_response()

    if nombre == 'buscar_producto':
        return buscar_producto(
            texto=str(args.get('texto', '')),
            max=args.get('max', 5),
        )
    if nombre == 'detalle_producto':
        return detalle_producto(id=args.get('id'))
    if nombre == 'faq':
        return faq(tema=str(args.get('tema', '')))
    if nombre == 'estado_pedido':
        return estado_pedido(pedido_id=args.get('pedido_id'), user=user)
    if nombre == 'mis_pedidos':
        return mis_pedidos(limite=args.get('limite', 5), user=user)
    if nombre == 'entregas_asignadas':
        return entregas_asignadas(user=user)
    if nombre == 'como_cancelar':
        return como_cancelar(pedido_id=args.get('pedido_id'), user=user)

    return {
        'encontrado': False,
        'mensaje': f'Herramienta desconocida: {nombre}.',
        'acciones': [],
    }
