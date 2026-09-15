from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_perfilmotorizado_fecha_inicio_jornada_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='fecha_nacimiento',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de Nacimiento'),
        ),
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.TextField(blank=True, help_text='Descripción corta del usuario', verbose_name='Biografía'),
        ),
    ]
