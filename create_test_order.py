#!/usr/bin/env python
import os
import django # type: ignore
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.orders.models import Pedido, ItemPedido
from apps.payments.models import Pago
from apps.products.models import Producto
from django.utils import timezone # type: ignore

# Obtener usuario moto_demo
motorizado = User.objects.get(id=17, username='moto_demo')
cliente = User.objects.filter(role='cliente').first()

if not cliente:
    print("❌ No hay cliente disponible")
    exit(1)

# Obtener un producto
producto = Producto.objects.first()
if not producto:
    print("❌ No hay productos en la BD")
    exit(1)

# Crear pedido
pedido = Pedido.objects.create(
    cliente=cliente,
    motorizado=motorizado,
    direccion_entrega="Calle Falsa 123, Lima",
    estado='confirmado',  # Estado activo
    total=Decimal('50.00'),
    fecha_pedido=timezone.now(),
)

# Agregar items
ItemPedido.objects.create(
    pedido=pedido,
    producto=producto,
    cantidad=2,
    precio_unitario=producto.precio,
)

# Crear pago (esto dispara el geocodificación)
Pago.objects.create(
    pedido=pedido,
    monto=Decimal('50.00'),
    metodo='efectivo',
    estado='completado',
)

print(f"✓ Pedido {pedido.id} creado exitosamente para moto_demo")
print(f"  - Cliente: {cliente.username}")
print(f"  - Motorizado: {motorizado.username}")
print(f"  - Estado: {pedido.estado}")
print(f"  - Dirección: {pedido.direccion_entrega}")
print(f"\nRecarga el dashboard para ver el pedido.")
