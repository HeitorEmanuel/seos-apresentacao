# Generated manually for SEOS 19.0

from django.db import migrations, models


def gerar_series_clientes(apps, schema_editor):
    Usuario = apps.get_model('ordens', 'Usuario')
    OrdemServico = apps.get_model('ordens', 'OrdemServico')

    for usuario in Usuario.objects.order_by('id'):
        if not usuario.numero_serie_cliente:
            usuario.numero_serie_cliente = f'CLI-{usuario.id:06d}'
            usuario.save(update_fields=['numero_serie_cliente'])

    for ordem in OrdemServico.objects.select_related('cliente_usuario').all():
        if ordem.cliente_usuario and ordem.cliente_usuario.numero_serie_cliente:
            ordem.numero_serie = ordem.cliente_usuario.numero_serie_cliente
            ordem.save(update_fields=['numero_serie'])


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0015_alter_registrosistema_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='numero_serie_cliente',
            field=models.CharField(
                blank=True,
                help_text='Código automático usado para identificar o cliente/equipamento nas OS e impressões.',
                max_length=20,
                null=True,
                unique=True,
                verbose_name='Número de Série do Cliente',
            ),
        ),
        migrations.AlterField(
            model_name='ordemservico',
            name='numero_serie',
            field=models.CharField(
                blank=True,
                help_text='Gerado automaticamente a partir do cliente vinculado para facilitar a identificação pelo técnico.',
                max_length=100,
                null=True,
                verbose_name='Número de Série do Cliente',
            ),
        ),
        migrations.RunPython(gerar_series_clientes, migrations.RunPython.noop),
    ]
