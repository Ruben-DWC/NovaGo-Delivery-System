from django.db import models
from apps.users.models import User

class Categoria(models.Model):
    """
    Categorías de productos para organizar el catálogo.
    """
    
    nombre = models.CharField(
        'Nombre',
        max_length=100,
        unique=True
    )
    
    descripcion = models.TextField(
        'Descripción',
        blank=True
    )
    
    icono = models.CharField(
        'Icono',
        max_length=50,
        blank=True,
        help_text='Clase de icono Font Awesome (ej: fas fa-pizza-slice)'
    )
    
    activa = models.BooleanField(
        'Activa',
        default=True
    )
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Productos disponibles en el catálogo de la tienda.
    """
    
    nombre = models.CharField(
        'Nombre',
        max_length=200
    )
    
    descripcion = models.TextField(
        'Descripción'
    )
    
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        related_name='productos',
        verbose_name='Categoría'
    )
    
    precio = models.DecimalField(
        'Precio',
        max_digits=10,
        decimal_places=2,
        help_text='Precio en soles (PEN)'
    )
    
    stock = models.PositiveIntegerField(
        'Stock',
        default=0,
        help_text='Cantidad disponible en inventario'
    )
    
    imagen = models.ImageField(
        'Imagen',
        upload_to='productos/',
        blank=True,
        null=True
    )
    
    destacado = models.BooleanField(
        'Destacado',
        default=False,
        help_text='Marcar para mostrar en página principal'
    )
    
    activo = models.BooleanField(
        'Activo',
        default=True,
        help_text='Desactivar para ocultar del catálogo'
    )
    
    fecha_creacion = models.DateTimeField(
        'Fecha de Creación',
        auto_now_add=True
    )
    
    fecha_actualizacion = models.DateTimeField(
        'Última Actualización',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - S/ {self.precio}"
    
    def esta_disponible(self):
        """Verifica si el producto está disponible para la venta"""
        return self.activo and self.stock > 0
    
    def reducir_stock(self, cantidad):
        """Reduce el stock del producto"""
        if self.stock >= cantidad:
            self.stock -= cantidad
            self.save()
            return True
        return False
    
    def aumentar_stock(self, cantidad):
        """Aumenta el stock del producto"""
        self.stock += cantidad
        self.save()

    @property
    def imagen_url(self):
        """Retorna la URL de la imagen del producto, con fallback temático gastronómico realista."""
        if self.imagen:
            try:
                return self.imagen.url
            except Exception:
                pass
        food_fallbacks = {
            1: 'https://images.unsplash.com/photo-1576107232684-1279f3908594?w=640&auto=format&fit=crop&q=80',  # Papas QA
            2: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=640&auto=format&fit=crop&q=80',  # Combo Nova Burger
            3: 'https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=640&auto=format&fit=crop&q=80',  # Pollo Crispy Box
            4: 'https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=640&auto=format&fit=crop&q=80',  # Pizza Personal Pepperoni
            5: 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=640&auto=format&fit=crop&q=80',  # Limonada Frozen Menta
            6: 'https://images.unsplash.com/photo-1534778101976-62847782c213?w=640&auto=format&fit=crop&q=80',  # Cafe Latte Vainilla
            7: 'https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?w=640&auto=format&fit=crop&q=80',  # Chocolate Frio Intenso
            8: 'https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=640&auto=format&fit=crop&q=80',  # Cheesecake Frutos Rojos
            9: 'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=640&auto=format&fit=crop&q=80',  # Brownie Triple Cacao
            10: 'https://images.unsplash.com/photo-1568571780765-9276ac8b75a2?w=640&auto=format&fit=crop&q=80', # Tarta de Manzana Canela
            11: 'https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=640&auto=format&fit=crop&q=80', # Nachos Suprema
            12: 'https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=640&auto=format&fit=crop&q=80', # Alitas BBQ x8
            13: 'https://images.unsplash.com/photo-1608039829572-78524f79c4c7?w=640&auto=format&fit=crop&q=80', # Tequenos de Queso x6
        }
        return food_fallbacks.get(self.id, 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=640&auto=format&fit=crop&q=80')


