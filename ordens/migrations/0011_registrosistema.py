# Generated manually for SEOS 12.0 - Etapa 7

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0010_ordemservico_numero_serie'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('usuario', 'Usuário'), ('ordem_servico', 'Ordem de Serviço'), ('historico', 'Histórico'), ('sistema', 'Sistema')], max_length=30, verbose_name='Tipo')),
                ('acao', models.CharField(choices=[('criado', 'Criado'), ('alterado', 'Alterado'), ('excluido', 'Excluído'), ('visualizado', 'Visualizado'), ('impressao', 'Impressão'), ('outro', 'Outro')], max_length=30, verbose_name='Ação')),
                ('descricao', models.TextField(verbose_name='Descrição')),
                ('objeto_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='ID do objeto')),
                ('objeto_referencia', models.CharField(blank=True, max_length=120, verbose_name='Referência')),
                ('data_registro', models.DateTimeField(auto_now_add=True, verbose_name='Data do registro')),
                ('usuario_responsavel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='registros_sistema', to=settings.AUTH_USER_MODEL, verbose_name='Usuário responsável')),
            ],
            options={
                'verbose_name': 'Registro do Sistema',
                'verbose_name_plural': 'Registros do Sistema',
                'ordering': ['-data_registro'],
            },
        ),
    ]
