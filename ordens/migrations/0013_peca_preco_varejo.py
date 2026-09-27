# Generated manually for SEOS 16.9

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0012_peca_movimentacaoestoque'),
    ]

    operations = [
        migrations.AddField(
            model_name='peca',
            name='preco_varejo',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Preço sugerido/cobrado ao cliente, quando houver.', max_digits=10, verbose_name='Preço de Varejo (R$)'),
        ),
    ]
