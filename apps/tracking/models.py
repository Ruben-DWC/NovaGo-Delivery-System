from django.db import models
from apps.orders.models import Pedido
from apps.users.models import User

class UbicacionTracking(models.Model):
    """
    Ubicaciones GPS del motorizado durante la entrega.
    """
    
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='ubicaciones',
        verbose_name='Pedido'
    )
    
    motorizado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'motorizado'},
        verbose_name='Motorizado'
    )
    
    latitud = models.DecimalField(
        'Latitud',
        max_digits=9,
        decimal_places=6,
        help_text='Coordenada de latitud GPS'
    )
    
    longitud = models.DecimalField(
        'Longitud',
        max_digits=9,
        decimal_places=6,
        help_text='Coordenada de longitud GPS'
    )
    
    precision = models.FloatField(
        'Precisión',
        null=True,
        blank=True,
        help_text='Precisión en metros'
    )
    
    timestamp = models.DateTimeField(
        'Fecha y Hora',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Ubicación de Tracking'
        verbose_name_plural = 'Ubicaciones de Tracking'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['pedido', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Tracking Pedido #{self.pedido.id} - {self.timestamp}"
    
    def obtener_coordenadas(self):
        """Retorna tupla de coordenadas (lat, lng)"""
        return (float(self.latitud), float(self.longitud))


class RutaEntrega(models.Model):
    """
    Ruta completa de la entrega desde la tienda hasta el cliente.
    """
    
    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='ruta',
        verbose_name='Pedido'
    )
    
    origen_lat = models.DecimalField(
        'Latitud Origen',
        max_digits=9,
        decimal_places=6,
        help_text='Latitud de la tienda'
    )
    
    origen_lng = models.DecimalField(
        'Longitud Origen',
        max_digits=9,
        decimal_places=6,
        help_text='Longitud de la tienda'
    )
    
    destino_lat = models.DecimalField(
        'Latitud Destino',
        max_digits=9,
        decimal_places=6,
        help_text='Latitud del cliente'
    )
    
    destino_lng = models.DecimalField(
        'Longitud Destino',
        max_digits=9,
        decimal_places=6,
        help_text='Longitud del cliente'
    )
    
    distancia_km = models.DecimalField(
        'Distancia (km)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    tiempo_estimado_min = models.PositiveIntegerField(
        'Tiempo Estimado (minutos)',
        null=True,
        blank=True
    )
    
    fecha_inicio = models.DateTimeField(
        'Fecha de Inicio',
        null=True,
        blank=True
    )
    
    fecha_finalizacion = models.DateTimeField(
        'Fecha de Finalización',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Ruta de Entrega'
        verbose_name_plural = 'Rutas de Entregas'
    
    def __str__(self):
        return f"Ruta Pedido #{self.pedido.id}"
    
    def calcular_duracion(self):
        """Calcula la duración real de la entrega"""
        if self.fecha_inicio and self.fecha_finalizacion:
            duracion = self.fecha_finalizacion - self.fecha_inicio
            return int(duracion.total_seconds() / 60)  # minutos
        return None
    
    def obtener_origen(self):
        """Retorna tupla de coordenadas del origen"""
        return (float(self.origen_lat), float(self.origen_lng))
    
    def obtener_destino(self):
        """Retorna tupla de coordenadas del destino"""
        return (float(self.destino_lat), float(self.destino_lng))

