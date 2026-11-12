# Generated manually for robust concurrency and idempotency

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_pedido_fecha_asignacion_alter_pedido_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='idempotency_key',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Identificador único para garantizar idempotencia en la creación del pedido',
                max_length=100,
                null=True,
                unique=True,
                verbose_name='Clave de Idempotencia',
            ),
        ),
    ]

