from django.db import models
from apps.users.models import User
from apps.products.models import Producto

class Pedido(models.Model):
    """
    Pedidos realizados por los clientes.
    """
    
    ESTADO_CHOICES = [
        ('pendiente_asignacion', 'Pendiente de Asignación'),
        ('confirmado', 'Confirmado'),
        ('en_preparacion', 'En Preparación'),
        ('en_camino', 'En Camino'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pedidos',
        limit_choices_to={'role': 'cliente'},
        verbose_name='Cliente'
    )
    
    motorizado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entregas',
        limit_choices_to={'role': 'motorizado'},
        verbose_name='Motorizado'
    )
    
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente_asignacion'
    )
    
    fecha_asignacion = models.DateTimeField(
        'Fecha de Asignación',
        null=True,
        blank=True,
        help_text='Fecha y hora cuando el pedido fue asignado a un motorizado'
    )
    
    direccion_entrega = models.TextField(
        'Dirección de Entrega'
    )
    
    telefono_contacto = models.CharField(
        'Teléfono de Contacto',
        max_length=15
    )
    
    notas = models.TextField(
        'Notas',
        blank=True,
        help_text='Instrucciones especiales para la entrega'
    )
    
    subtotal = models.DecimalField(
        'Subtotal',
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    costo_envio = models.DecimalField(
        'Costo de Envío',
        max_digits=10,
        decimal_places=2,
        default=5.00
    )
    
    total = models.DecimalField(
        'Total',
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    fecha_pedido = models.DateTimeField(
        'Fecha de Pedido',
        auto_now_add=True
    )
    
    fecha_entrega = models.DateTimeField(
        'Fecha de Entrega',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_pedido']
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.username}"
    
    def calcular_total(self):
        """Calcula el total del pedido"""
        self.subtotal = sum(item.subtotal for item in self.items.all())
        self.total = self.subtotal + self.costo_envio
        self.save()
    
    def puede_cancelar(self):
        """Verifica si el pedido puede ser cancelado"""
        return self.estado in ['pendiente', 'confirmado']


class ItemPedido(models.Model):
    """
    Items individuales de un pedido (productos y cantidades).
    """
    
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Pedido'
    )
    
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        verbose_name='Producto'
    )
    
    cantidad = models.PositiveIntegerField(
        'Cantidad',
        default=1
    )
    
    precio_unitario = models.DecimalField(
        'Precio Unitario',
        max_digits=10,
        decimal_places=2,
        help_text='Precio del producto al momento de la compra'
    )
    
    subtotal = models.DecimalField(
        'Subtotal',
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    class Meta:
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Items de Pedidos'
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
    def save(self, *args, **kwargs):
        """Calcula el subtotal antes de guardar"""
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        # Recalcular total del pedido
        self.pedido.calcular_total()

