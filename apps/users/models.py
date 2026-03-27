from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Usuario extendido con roles para el sistema de delivery.
    
    Hereda de AbstractUser para mantener funcionalidad básica de Django
    y agrega campos específicos del negocio.
    """
    
    ROLE_CHOICES = [
        ('cliente', 'Cliente'),
        ('motorizado', 'Motorizado'),
        ('admin', 'Administrador'),
    ]
    
    role = models.CharField(
        'Rol',
        max_length=20,
        choices=ROLE_CHOICES,
        default='cliente',
        help_text='Rol del usuario en el sistema'
    )
    
    telefono = models.CharField(
        'Teléfono',
        max_length=15,
        blank=True,
        help_text='Número de teléfono del usuario'
    )
    
    direccion = models.TextField(
        'Dirección',
        blank=True,
        help_text='Dirección principal del usuario'
    )
    
    foto_perfil = models.ImageField(
        'Foto de Perfil',
        upload_to='usuarios/perfiles/',
        blank=True,
        null=True
    )
    
    fecha_registro = models.DateTimeField(
        'Fecha de Registro',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def es_cliente(self):
        """Verifica si el usuario es cliente"""
        return self.role == 'cliente'
    
    def es_motorizado(self):
        """Verifica si el usuario es motorizado"""
        return self.role == 'motorizado'
    
    def es_admin(self):
        """Verifica si el usuario es administrador"""
        return self.role == 'admin'


class PerfilMotorizado(models.Model):
    """
    Perfil adicional para usuarios motorizados.
    
    Contiene información específica necesaria para los repartidores.
    """
    
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil_motorizado',
        limit_choices_to={'role': 'motorizado'}
    )
    
    placa_vehiculo = models.CharField(
        'Placa del Vehículo',
        max_length=10,
        help_text='Placa del vehículo del motorizado'
    )
    
    tipo_vehiculo = models.CharField(
        'Tipo de Vehículo',
        max_length=50,
        help_text='Ej: Moto, Bicicleta, Auto'
    )
    
    licencia = models.CharField(
        'Número de Licencia',
        max_length=20,
        help_text='Número de licencia de conducir'
    )
    
    disponible = models.BooleanField(
        'Disponible',
        default=True,
        help_text='Indica si el motorizado está disponible para entregas'
    )
    
    calificacion = models.DecimalField(
        'Calificación',
        max_digits=3,
        decimal_places=2,
        default=5.00,
        help_text='Calificación promedio del motorizado'
    )
    
    entregas_completadas = models.PositiveIntegerField(
        'Entregas Completadas',
        default=0
    )
    
    class Meta:
        verbose_name = 'Perfil de Motorizado'
        verbose_name_plural = 'Perfiles de Motorizados'
    
    def __str__(self):
        return f"Motorizado: {self.usuario.username} - {self.placa_vehiculo}"

