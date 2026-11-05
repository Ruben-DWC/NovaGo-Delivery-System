import os
import sys
import django

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.products.models import Categoria, Producto

print("=== INICIANDO SEEDING DE DATOS NOVAGO ===")

# 1. Configurar Roles y Usuarios Oficiales
users_data = [
    {
        'username': 'admin',
        'email': 'admin@novago.pe',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
        'first_name': 'Administrador',
        'last_name': 'Sistema',
        'password': 'AdminNovaGo2026'
    },
    {
        'username': 'admin_hdd',
        'email': 'admin@novago.local',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
        'first_name': 'Ruben',
        'last_name': 'Vivas Admin',
        'password': 'Admin2026!'
    },
    {
        'username': 'cliente_demo',
        'email': 'cliente_demo@novago.local',
        'role': 'cliente',
        'is_staff': False,
        'is_superuser': False,
        'first_name': 'Carlos',
        'last_name': 'Cliente Demo',
        'password': 'Cliente2026!'
    },
    {
        'username': 'moto_demo',
        'email': 'moto_demo@novago.local',
        'role': 'motorizado',
        'is_staff': False,
        'is_superuser': False,
        'first_name': 'Marcos',
        'last_name': 'Motorizado Demo',
        'password': 'Moto2026!'
    },
]

for u_info in users_data:
    u, created = User.objects.get_or_create(username=u_info['username'])
    u.email = u_info['email']
    u.role = u_info['role']
    u.is_staff = u_info['is_staff']
    u.is_superuser = u_info['is_superuser']
    u.first_name = u_info['first_name']
    u.last_name = u_info['last_name']
    u.set_password(u_info['password'])
    u.save()
    status = "CREADO" if created else "ACTUALIZADO"
    print(f"[{status}] Usuario: {u.username} | Rol: {u.role} | Superuser: {u.is_superuser}")

# 2. Categorias Oficiales
cats_data = [
    {'id': 1, 'nombre': 'Snacks QA', 'descripcion': 'Piqueos rapidos de prueba QA', 'icono': 'fas fa-cookie-bite', 'activa': True},
    {'id': 2, 'nombre': 'Bebidas', 'descripcion': 'Bebidas frias y calientes para acompanar tu pedido', 'icono': 'fas fa-mug-hot', 'activa': True},
    {'id': 3, 'nombre': 'Combos', 'descripcion': 'Paquetes completos para compartir', 'icono': 'fas fa-box-open', 'activa': True},
    {'id': 4, 'nombre': 'Postres', 'descripcion': 'Opciones dulces para cerrar perfecto', 'icono': 'fas fa-ice-cream', 'activa': True},
    {'id': 5, 'nombre': 'Snacks', 'descripcion': 'Piqueos rapidos para cualquier momento', 'icono': 'fas fa-cookie-bite', 'activa': True},
]

cats_map = {}
for c_info in cats_data:
    cat, _ = Categoria.objects.update_or_create(
        id=c_info['id'],
        defaults={
            'nombre': c_info['nombre'],
            'descripcion': c_info['descripcion'],
            'icono': c_info['icono'],
            'activa': c_info['activa']
        }
    )
    cats_map[cat.id] = cat
    print(f"[OK] Categoria: {cat.nombre}")

# 3. Productos Oficiales
prods_data = [
    {'id': 1, 'nombre': 'Papas QA', 'descripcion': 'Bolsa de papas crocantes', 'precio': 7.50, 'stock': 28, 'destacado': False, 'activo': True, 'cat': 1},
    {'id': 2, 'nombre': 'Combo Nova Burger', 'descripcion': 'Hamburguesa artesanal doble queso, papas crocantes y bebida mediana.', 'precio': 27.90, 'stock': 22, 'destacado': True, 'activo': True, 'cat': 3},
    {'id': 3, 'nombre': 'Pollo Crispy Box', 'descripcion': 'Trozos de pollo crispy con dip de ajo, papas y bebida fria.', 'precio': 24.50, 'stock': 17, 'destacado': True, 'activo': True, 'cat': 3},
    {'id': 4, 'nombre': 'Pizza Personal Pepperoni', 'descripcion': 'Pizza personal con salsa de tomate rustica y pepperoni premium.', 'precio': 19.90, 'stock': 15, 'destacado': False, 'activo': True, 'cat': 3},
    {'id': 5, 'nombre': 'Limonada Frozen Menta', 'descripcion': 'Limonada helada con toque de menta fresca y hielo frappe.', 'precio': 8.50, 'stock': 33, 'destacado': False, 'activo': True, 'cat': 2},
    {'id': 6, 'nombre': 'Cafe Latte Vainilla', 'descripcion': 'Cafe espresso doble con leche cremosa y esencia natural de vainilla.', 'precio': 9.20, 'stock': 27, 'destacado': False, 'activo': True, 'cat': 2},
    {'id': 7, 'nombre': 'Chocolate Frio Intenso', 'descripcion': 'Bebida de cacao premium con hielo y topping de chispas de chocolate.', 'precio': 10.90, 'stock': 20, 'destacado': True, 'activo': True, 'cat': 2},
    {'id': 8, 'nombre': 'Cheesecake Frutos Rojos', 'descripcion': 'Porcion de cheesecake horneado con salsa de frutos rojos casera.', 'precio': 12.90, 'stock': 12, 'destacado': True, 'activo': True, 'cat': 4},
    {'id': 9, 'nombre': 'Brownie Triple Cacao', 'descripcion': 'Brownie humedo con nuez, ganache oscuro y chips de chocolate.', 'precio': 11.40, 'stock': 16, 'destacado': False, 'activo': True, 'cat': 4},
    {'id': 10, 'nombre': 'Tarta de Manzana Canela', 'descripcion': 'Tarta artesanal con laminas de manzana y toque de canela.', 'precio': 10.80, 'stock': 10, 'destacado': False, 'activo': True, 'cat': 4},
    {'id': 11, 'nombre': 'Nachos Suprema', 'descripcion': 'Nachos con cheddar, guacamole, pico de gallo y crema acida.', 'precio': 16.90, 'stock': 20, 'destacado': True, 'activo': True, 'cat': 5},
    {'id': 12, 'nombre': 'Alitas BBQ x8', 'descripcion': 'Alitas jugosas glaseadas en salsa BBQ ahumada de la casa.', 'precio': 22.30, 'stock': 14, 'destacado': False, 'activo': True, 'cat': 5},
    {'id': 13, 'nombre': 'Tequenos de Queso x6', 'descripcion': 'Tequenos dorados rellenos de queso fundente con salsa de ajo.', 'precio': 15.20, 'stock': 19, 'destacado': False, 'activo': True, 'cat': 5},
]

for p_info in prods_data:
    prod, _ = Producto.objects.update_or_create(
        id=p_info['id'],
        defaults={
            'nombre': p_info['nombre'],
            'descripcion': p_info['descripcion'],
            'precio': p_info['precio'],
            'stock': p_info['stock'],
            'destacado': p_info['destacado'],
            'activo': p_info['activo'],
            'categoria': cats_map[p_info['cat']]
        }
    )
    print(f"[OK] Producto: {prod.nombre} (S/ {prod.precio})")

print(f"\n=== SEEDING COMPLETADO: {len(cats_data)} Categorias, {len(prods_data)} Productos, {len(users_data)} Usuarios ===")

