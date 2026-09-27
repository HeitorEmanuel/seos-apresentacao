# Generated manually for SEOS 14.0 - Etapa 9

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0011_registrosistema'),
    ]

    operations = [
        migrations.CreateModel(
            name='Peca',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120, verbose_name='Nome da Peça')),
                ('codigo', models.CharField(help_text='Código interno para identificar a peça no estoque.', max_length=50, unique=True, verbose_name='Código')),
                ('descricao', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('quantidade', models.PositiveIntegerField(default=0, verbose_name='Quantidade em Estoque')),
                ('estoque_minimo', models.PositiveIntegerField(default=1, verbose_name='Estoque Mínimo')),
                ('valor_unitario', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Valor Unitário (R$)')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
                ('data_atualizacao', models.DateTimeField(auto_now=True, verbose_name='Última Atualização')),
            ],
            options={
                'verbose_name': 'Peça',
                'verbose_name_plural': 'Peças',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='MovimentacaoEstoque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('entrada', 'Entrada'), ('saida', 'Saída'), ('ajuste', 'Ajuste')], max_length=20, verbose_name='Tipo')),
                ('quantidade', models.PositiveIntegerField(verbose_name='Quantidade')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Observação')),
                ('data_movimentacao', models.DateTimeField(auto_now_add=True, verbose_name='Data da Movimentação')),
                ('ordem_servico', models.ForeignKey(blank=True, help_text='Opcional. Use quando a saída estiver ligada a uma OS.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pecas_utilizadas', to='ordens.ordemservico', verbose_name='Ordem de Serviço')),
                ('peca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimentacoes', to='ordens.peca', verbose_name='Peça')),
                ('usuario_responsavel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentacoes_estoque', to=settings.AUTH_USER_MODEL, verbose_name='Usuário Responsável')),
            ],
            options={
                'verbose_name': 'Movimentação de Estoque',
                'verbose_name_plural': 'Movimentações de Estoque',
                'ordering': ['-data_movimentacao'],
            },
        ),
    ]
