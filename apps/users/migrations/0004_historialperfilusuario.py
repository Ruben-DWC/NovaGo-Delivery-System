from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_user_fecha_nacimiento_user_bio'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistorialPerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campos_modificados', models.JSONField(blank=True, default=list, help_text='Lista de campos que cambiaron en la actualización.', verbose_name='Campos Modificados')),
                ('actualizado_en', models.DateTimeField(auto_now_add=True, verbose_name='Actualizado En')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_perfil', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Historial de Perfil',
                'verbose_name_plural': 'Historiales de Perfil',
                'ordering': ['-actualizado_en'],
            },
        ),
    ]
