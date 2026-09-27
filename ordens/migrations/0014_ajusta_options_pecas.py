# Generated manually for SEOS 16.10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0013_peca_preco_varejo'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='peca',
            options={
                'verbose_name': 'Peça',
                'verbose_name_plural': 'Peças em Estoque',
                'ordering': ['nome'],
            },
        ),
        migrations.AlterModelOptions(
            name='movimentacaoestoque',
            options={
                'verbose_name': 'Movimentação de Estoque',
                'verbose_name_plural': 'Entrada e Saída de Peças',
                'ordering': ['-data_movimentacao'],
            },
        ),
    ]
