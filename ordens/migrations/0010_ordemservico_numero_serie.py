# Generated manually for SEOS 8.0 - Etapa 3

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0009_alter_historicoordemservico_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordemservico',
            name='numero_serie',
            field=models.CharField(
                blank=True,
                help_text='Identificação física do equipamento, quando houver.',
                max_length=100,
                null=True,
                verbose_name='Número de Série',
            ),
        ),
    ]
