"""
Pruebas automatizadas para el Asistente IA 'Nova' (apps/assistant).
Cubre herramientas ORM con aislamiento por rol, FAQ, restricciones anónimas,
rate-limit, manejo de LLMNoDisponible, emociones, historial en sesión y logs.
"""
import json
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import Client, override_settings

from apps.assistant.models import ConversacionLog
from apps.assistant.services import tools
from apps.assistant.services.llm_client import LLMNoDisponible
from apps.orders.models import Pedido
from apps.products.models import Categoria, Producto
from apps.tracking.models import UbicacionTracking
from apps.users.models import User


@pytest.fixture(autouse=True)
def clear_cache_and_fake_provider(settings):
    cache.clear()
    settings.NOVA_AI_PROVIDER = 'fake'
    settings.NOVA_AI_MODEL = 'fake-local'
    settings.NOVA_AI_API_KEY = ''
    yield
    cache.clear()


@pytest.fixture
def sample_catalog(db):
    cat_burgers = Categoria.objects.create(nombre='Hamburguesas', activa=True)
    cat_bebidas = Categoria.objects.create(nombre='Bebidas', activa=True)

    p1 = Producto.objects.create(
        nombre='Nova Burger Clásica',
        descripcion='Carne artesanal con queso cheddar',
        categoria=cat_burgers,
        precio=Decimal('22.00'),
        stock=10,
        destacado=True,
        activo=True,
    )
    p2 = Producto.objects.create(
        nombre='Limonada Frozen',
        descripcion='Bebida refrescante de limón',
        categoria=cat_bebidas,
        precio=Decimal('9.00'),
        stock=15,
        activo=True,
    )
    p_inactivo = Producto.objects.create(
        nombre='Burger Oculta',
        descripcion='Producto desactivado',
        categoria=cat_burgers,
        precio=Decimal('15.00'),
        stock=10,
        activo=False,
    )
    return {'p1': p1, 'p2': p2, 'p_inactivo': p_inactivo}


@pytest.fixture
def sample_orders(db):
    cliente1 = User.objects.create_user(username='cli_nova_1', password='Password123!', role='cliente')
    cliente2 = User.objects.create_user(username='cli_nova_2', password='Password123!', role='cliente')
    moto1 = User.objects.create_user(
        username='moto_nova_1',
        password='Password123!',
        role='motorizado',
        first_name='Carlos',
        last_name='Ruiz',
    )
    moto2 = User.objects.create_user(username='moto_nova_2', password='Password123!', role='motorizado')
    admin = User.objects.create_user(username='admin_nova', password='Password123!', role='admin', is_staff=True)

    pedido_camino = Pedido.objects.create(
        cliente=cliente1,
        motorizado=moto1,
        estado='en_camino',
        direccion_entrega='Av. Arequipa 1234',
        telefono_contacto='999888777',
        subtotal=Decimal('30.00'),
        costo_envio=Decimal('5.00'),
        total=Decimal('35.00'),
    )
    UbicacionTracking.objects.create(
        pedido=pedido_camino,
        motorizado=moto1,
        latitud=Decimal('-12.119100'),
        longitud=Decimal('-77.029200'),
    )

    pedido_entregado = Pedido.objects.create(
        cliente=cliente1,
        motorizado=moto1,
        estado='entregado',
        direccion_entrega='Av. Larco 400',
        telefono_contacto='999888777',
        subtotal=Decimal('25.00'),
        costo_envio=Decimal('5.00'),
        total=Decimal('30.00'),
    )

    pedido_otro = Pedido.objects.create(
        cliente=cliente2,
        motorizado=moto2,
        estado='confirmado',
        direccion_entrega='Av. Javier Prado 500',
        telefono_contacto='988777666',
        subtotal=Decimal('40.00'),
        costo_envio=Decimal('5.00'),
        total=Decimal('45.00'),
    )

    return {
        'cliente1': cliente1,
        'cliente2': cliente2,
        'moto1': moto1,
        'moto2': moto2,
        'admin': admin,
        'pedido_camino': pedido_camino,
        'pedido_entregado': pedido_entregado,
        'pedido_otro': pedido_otro,
    }


@pytest.mark.django_db
def test_active_products_only(sample_catalog):
    res = tools.buscar_producto(texto='', max=5)
    nombres = [p['nombre'] for p in res['productos']]
    assert 'Nova Burger Clásica' in nombres
    assert 'Limonada Frozen' in nombres
    assert 'Burger Oculta' not in nombres

    det_ok = tools.detalle_producto(sample_catalog['p1'].id)
    assert det_ok['encontrado'] is True
    assert det_ok['producto']['nombre'] == 'Nova Burger Clásica'

    det_hidden = tools.detalle_producto(sample_catalog['p_inactivo'].id)
    assert det_hidden['encontrado'] is False


@pytest.mark.django_db
def test_customer_isolation(sample_orders):
    p1 = sample_orders['pedido_camino']
    p_otro = sample_orders['pedido_otro']
    c1 = sample_orders['cliente1']

    own = tools.estado_pedido(p1.id, user=c1)
    assert own['encontrado'] is True
    assert own['ubicacion'] == {'latitud': -12.1191, 'longitud': -77.0292}

    other = tools.estado_pedido(p_otro.id, user=c1)
    assert other['encontrado'] is False

    mis = tools.mis_pedidos(limite=5, user=c1)
    ids = [p['id'] for p in mis['pedidos']]
    assert p1.id in ids
    assert p_otro.id not in ids

    cancel_other = tools.como_cancelar(p_otro.id, user=c1)
    assert cancel_other['encontrado'] is False


@pytest.mark.django_db
def test_motorizado_and_role_isolation(sample_orders):
    moto1 = sample_orders['moto1']
    admin = sample_orders['admin']
    c1 = sample_orders['cliente1']
    p1 = sample_orders['pedido_camino']
    p_otro = sample_orders['pedido_otro']

    assert tools.estado_pedido(p1.id, user=moto1)['encontrado'] is True
    assert tools.estado_pedido(p_otro.id, user=moto1)['encontrado'] is False

    entregas = tools.entregas_asignadas(user=moto1)
    assert entregas['encontrado'] is True
    assert [e['id'] for e in entregas['entregas']] == [p1.id]

    assert tools.entregas_asignadas(user=c1)['encontrado'] is False
    assert tools.estado_pedido(p_otro.id, user=admin)['encontrado'] is True


@pytest.mark.django_db
def test_anonymous_restriction(sample_catalog, sample_orders):
    client = Client()

    # Visitante anónimo SÍ puede buscar productos y consultar FAQ
    r_prod = client.post(
        '/assistant/chat/',
        data=json.dumps({'message': 'Buscar hamburguesa'}),
        content_type='application/json',
    )
    assert r_prod.status_code == 200
    assert 'Nova Burger' in r_prod.json()['respuesta']

    r_faq = client.post(
        '/assistant/chat/',
        data=json.dumps({'message': '¿Aceptan Yape y cuál es el costo de envío?'}),
        content_type='application/json',
    )
    assert r_faq.status_code == 200
    assert 'Yape' in r_faq.json()['respuesta']

    # Visitante anónimo NO puede consultar pedidos -> recibe acción login
    r_order = client.post(
        '/assistant/chat/',
        data=json.dumps({'message': f"Estado de mi pedido #{sample_orders['pedido_camino'].id}"}),
        content_type='application/json',
    )
    assert r_order.status_code == 200
    data = r_order.json()
    assert data['emocion'] == 'disculpa'
    assert any(a['tipo'] == 'login' for a in data['acciones'])


@pytest.mark.django_db
def test_csrf_validation_length_and_reset(sample_catalog):
    csrf_client = Client(enforce_csrf_checks=True)
    no_csrf = csrf_client.post(
        '/assistant/chat/',
        data=json.dumps({'message': 'hola'}),
        content_type='application/json',
    )
    assert no_csrf.status_code == 403

    client = Client()
    assert client.post('/assistant/chat/', data=json.dumps({'message': '   '}), content_type='application/json').status_code == 400
    assert client.post('/assistant/chat/', data=json.dumps({'message': 'x' * 501}), content_type='application/json').status_code == 400

    ok = client.post('/assistant/chat/', data=json.dumps({'message': 'Buscar limonada'}), content_type='application/json')
    assert ok.status_code == 200
    assert len(client.session.get('nova_historial', [])) == 2

    rst = client.post('/assistant/reset/')
    assert rst.status_code == 200
    assert client.session.get('nova_historial') == []


@pytest.mark.django_db
@override_settings(NOVA_RATE_LIMIT=2, NOVA_RATE_WINDOW_SECONDS=600)
def test_rate_limit_returns_429(sample_catalog):
    client = Client()
    for _ in range(2):
        resp = client.post('/assistant/chat/', data=json.dumps({'message': 'hola'}), content_type='application/json')
        assert resp.status_code == 200

    blocked = client.post('/assistant/chat/', data=json.dumps({'message': 'hola'}), content_type='application/json')
    assert blocked.status_code == 429


@pytest.mark.django_db
def test_llm_no_disponible_returns_200_disculpa_and_logs():
    client = Client()
    with patch('apps.assistant.views.llm_client.generar', side_effect=LLMNoDisponible('API key faltante')):
        resp = client.post('/assistant/chat/', data=json.dumps({'message': 'hola nova'}), content_type='application/json')

    assert resp.status_code == 200
    data = resp.json()
    assert data['emocion'] == 'disculpa'

    log = ConversacionLog.objects.order_by('-id').first()
    assert log is not None
    assert log.mensaje == 'hola nova'
    assert log.error == 'API key faltante'


@pytest.mark.django_db
def test_entregado_order_returns_celebrando(sample_orders):
    client = Client()
    client.force_login(sample_orders['cliente1'])
    pedido = sample_orders['pedido_entregado']

    resp = client.post(
        '/assistant/chat/',
        data=json.dumps({'message': f'Estado de mi pedido #{pedido.id}'}),
        content_type='application/json',
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['emocion'] == 'celebrando'
    assert data['pedido']['id'] == pedido.id
    assert data['pedido']['estado'] == 'entregado'
