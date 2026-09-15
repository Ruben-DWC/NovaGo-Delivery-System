#!/usr/bin/env python
import os
import django # type: ignore

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.orders.models import Pedido
from apps.users.models import User

# Verificar pedidos activos
active_states = ['confirmado', 'en_preparacion', 'en_camino']
pedidos = Pedido.objects.filter(estado__in=active_states)

print("\n=== PEDIDOS ACTIVOS ===")
print(f"Total de pedidos activos: {pedidos.count()}\n")

if pedidos.count() > 0:
    for p in pedidos:
        print(f"Pedido {p.id}:")
        print(f"  - Estado: {p.estado}")
        print(f"  - Cliente: {p.cliente_id}")
        print(f"  - Motorizado: {p.motorizado_id}")
        print()
else:
    print("❌ NO HAY PEDIDOS ACTIVOS")
    print("\nCreando pedido de prueba...\n")
    
    # Obtener usuarios de prueba
    try:
        cliente = User.objects.filter(role='cliente').first()
        motorizado = User.objects.filter(role='motorizado').first()
        
        if not cliente:
            print("❌ No hay cliente registrado")
        elif not motorizado:
            print("❌ No hay motorizado registrado")
        else:
            print(f"✓ Cliente: {cliente.username} (ID: {cliente.id})")
            print(f"✓ Motorizado: {motorizado.username} (ID: {motorizado.id})")
            
            # Intentar crear un pedido de prueba
            # (Nota: esto requiere products, carts, etc.)
            print("\nNota: Para crear un pedido necesitas ir a la tienda y hacer una compra completa")
            print("O usar el admin para crear un pedido de prueba manualmente")
    except Exception as e:
        print(f"Error: {e}")
