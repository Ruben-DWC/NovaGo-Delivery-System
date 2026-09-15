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

