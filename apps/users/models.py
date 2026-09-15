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

    fecha_nacimiento = models.DateField(
        'Fecha de Nacimiento',
        blank=True,
        null=True
    )

    bio = models.TextField(
        'Biografía',
        blank=True,
        help_text='Descripción corta del usuario'
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
    
    jornada_activa = models.BooleanField(
        'Jornada Activa',
        default=False,
        help_text='¿El motorizado tiene una jornada laboral activa?'
    )
    
    fecha_inicio_jornada = models.DateTimeField(
        'Fecha de Inicio de Jornada',
        null=True,
        blank=True,
        help_text='Cuándo inició la jornada actual'
    )
    
    ubicacion_actual = models.JSONField(
        'Ubicación Actual',
        default=dict,
        blank=True,
        help_text='Última ubicación conocida en formato {"lat": ..., "lng": ..., "timestamp": ...}'
    )
    
    class Meta:
        verbose_name = 'Perfil de Motorizado'
        verbose_name_plural = 'Perfiles de Motorizados'
    
    def __str__(self):
        return f"Motorizado: {self.usuario.username} - {self.placa_vehiculo}"


class HistorialPerfilUsuario(models.Model):
    """Registro simple de cambios relevantes del perfil de usuario."""

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='historial_perfil',
    )

    campos_modificados = models.JSONField(
        'Campos Modificados',
        default=list,
        blank=True,
        help_text='Lista de campos que cambiaron en la actualización.'
    )

    actualizado_en = models.DateTimeField(
        'Actualizado En',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Historial de Perfil'
        verbose_name_plural = 'Historiales de Perfil'
        ordering = ['-actualizado_en']

    def __str__(self):
        return f"Historial perfil: {self.usuario.username} ({self.actualizado_en:%Y-%m-%d %H:%M})"


class AdminAuditLog(models.Model):
    """Bitacora de acciones administrativas para trazabilidad operativa."""

    ACTION_CHOICES = [
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('bulk_update', 'Actualizacion masiva'),
        ('export', 'Exportar'),
        ('login', 'Inicio de sesion'),
    ]

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_audit_logs',
        limit_choices_to={'role': 'admin'},
        verbose_name='Administrador',
    )

    action = models.CharField(
        'Accion',
        max_length=20,
        choices=ACTION_CHOICES,
        default='update',
    )

    target_model = models.CharField(
        'Modelo objetivo',
        max_length=80,
    )

    target_id = models.CharField(
        'ID objetivo',
        max_length=40,
        blank=True,
    )

    description = models.CharField(
        'Descripcion',
        max_length=255,
    )

    metadata = models.JSONField(
        'Metadatos',
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        'Fecha de evento',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Bitacora Administrativa'
        verbose_name_plural = 'Bitacoras Administrativas'
        ordering = ['-created_at']

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'sistema'
        return f"{actor_name} - {self.get_action_display()} - {self.target_model} ({self.created_at:%Y-%m-%d %H:%M})"

