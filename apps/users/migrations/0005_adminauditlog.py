from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_historialperfilusuario'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'Crear'), ('update', 'Actualizar'), ('delete', 'Eliminar'), ('bulk_update', 'Actualizacion masiva'), ('export', 'Exportar'), ('login', 'Inicio de sesion')], default='update', max_length=20, verbose_name='Accion')),
                ('target_model', models.CharField(max_length=80, verbose_name='Modelo objetivo')),
                ('target_id', models.CharField(blank=True, max_length=40, verbose_name='ID objetivo')),
                ('description', models.CharField(max_length=255, verbose_name='Descripcion')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadatos')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de evento')),
                ('actor', models.ForeignKey(blank=True, limit_choices_to={'role': 'admin'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin_audit_logs', to=settings.AUTH_USER_MODEL, verbose_name='Administrador')),
            ],
            options={
                'verbose_name': 'Bitacora Administrativa',
                'verbose_name_plural': 'Bitacoras Administrativas',
                'ordering': ['-created_at'],
            },
        ),
    ]
