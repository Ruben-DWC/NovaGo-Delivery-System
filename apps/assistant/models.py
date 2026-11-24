from django.conf import settings
from django.db import models


class ConversacionLog(models.Model):
    """Registro de auditoría y telemetría de interacciones con Nova IA."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversaciones_nova',
        verbose_name='Usuario',
    )
    session_key = models.CharField(
        'Clave de Sesión',
        max_length=64,
        blank=True,
        default='',
        db_index=True,
    )
    mensaje = models.TextField('Mensaje del usuario')
    respuesta = models.TextField('Respuesta de Nova', blank=True, default='')
    herramientas_usadas = models.JSONField(
        'Herramientas usadas',
        default=list,
        blank=True,
    )
    proveedor = models.CharField(
        'Proveedor LLM',
        max_length=32,
        blank=True,
        default='',
    )
    latencia_ms = models.PositiveIntegerField(
        'Latencia (ms)',
        default=0,
    )
    error = models.TextField(
        'Error',
        null=True,
        blank=True,
    )
    fecha = models.DateTimeField(
        'Fecha',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Log de Conversación Nova'
        verbose_name_plural = 'Logs de Conversaciones Nova'
        ordering = ['-fecha']

    def __str__(self):
        user_label = self.usuario.username if self.usuario else (self.session_key[:8] or 'anon')
        return f"NovaLog({user_label} @ {self.fecha:%Y-%m-%d %H:%M})"
