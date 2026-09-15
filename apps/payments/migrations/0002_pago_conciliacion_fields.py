from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='pago',
            name='conciliado',
            field=models.BooleanField(default=False, help_text='Indica si el pago fue conciliado contablemente.', verbose_name='Conciliado'),
        ),
        migrations.AddField(
            model_name='pago',
            name='fecha_conciliacion',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Conciliacion'),
        ),
        migrations.AddField(
            model_name='pago',
            name='conciliado_por',
            field=models.ForeignKey(blank=True, limit_choices_to={'role': 'admin'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pagos_conciliados', to=settings.AUTH_USER_MODEL, verbose_name='Conciliado por'),
        ),
    ]
