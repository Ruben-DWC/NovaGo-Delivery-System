from django.db import models
from apps.orders.models import Pedido

class Pago(models.Model):
    """
    Pagos realizados por los pedidos.
    """
    
    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('yape', 'Yape'),
        ('plin', 'Plin'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('rechazado', 'Rechazado'),
        ('reembolsado', 'Reembolsado'),
    ]
    
    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='pago',
        verbose_name='Pedido'
    )
    
    metodo = models.CharField(
        'Método de Pago',
        max_length=20,
        choices=METODO_CHOICES
    )
    
    monto = models.DecimalField(
        'Monto',
        max_digits=10,
        decimal_places=2
    )
    
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    
    referencia = models.CharField(
        'Número de Referencia',
        max_length=100,
        blank=True,
        help_text='Número de operación o transacción'
    )
    
    comprobante = models.ImageField(
        'Comprobante de Pago',
        upload_to='pagos/comprobantes/',
        blank=True,
        null=True,
        help_text='Captura del voucher o comprobante'
    )
    
    fecha_pago = models.DateTimeField(
        'Fecha de Pago',
        auto_now_add=True
    )
    
    fecha_confirmacion = models.DateTimeField(
        'Fecha de Confirmación',
        null=True,
        blank=True
    )
    
    notas = models.TextField(
        'Notas',
        blank=True
    )
    
    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago #{self.id} - Pedido #{self.pedido.id} - {self.get_metodo_display()}"
    
    def confirmar_pago(self):
        """Confirma el pago y actualiza el estado"""
        from django.utils import timezone
        self.estado = 'completado'
        self.fecha_confirmacion = timezone.now()
        self.save()
        
        # Actualizar estado del pedido
        if self.pedido.estado == 'pendiente':
            self.pedido.estado = 'confirmado'
            self.pedido.save()
    
    def rechazar_pago(self, motivo=''):
        """Rechaza el pago"""
        self.estado = 'rechazado'
        self.notas = motivo
        self.save()

