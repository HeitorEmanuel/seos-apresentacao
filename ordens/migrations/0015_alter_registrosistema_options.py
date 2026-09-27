# Generated manually for SEOS 16.11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0014_ajusta_options_pecas'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='registrosistema',
            options={
                'verbose_name': 'Registro do Sistema',
                'verbose_name_plural': 'Auditoria do Sistema',
                'ordering': ['-data_registro'],
            },
        ),
    ]
