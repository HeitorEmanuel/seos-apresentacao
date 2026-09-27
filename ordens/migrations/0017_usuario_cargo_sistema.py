# Generated manually for SEOS 20.0

from django.db import migrations, models


def definir_cargos_iniciais(apps, schema_editor):
    Usuario = apps.get_model('ordens', 'Usuario')

    for usuario in Usuario.objects.all():
        if usuario.is_superuser or usuario.is_staff:
            if not usuario.cargo_sistema:
                usuario.cargo_sistema = 'tecnico_admin'
                usuario.save(update_fields=['cargo_sistema'])

    Usuario.objects.filter(cargo_sistema__in=['atendente', 'tecnico_admin', 'almoxarifado']).update(is_staff=True)
    Usuario.objects.filter(cargo_sistema='').exclude(is_superuser=True).update(is_staff=False)


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0016_usuario_numero_serie_cliente'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='cargo_sistema',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Cliente comum / sem cargo'),
                    ('atendente', 'Atendente'),
                    ('tecnico_admin', 'Técnico/Admin'),
                    ('almoxarifado', 'Almoxarifado'),
                ],
                default='',
                help_text='Use somente para equipe interna. Cliente comum deve ficar sem cargo.',
                max_length=20,
                verbose_name='Cargo no Sistema',
            ),
        ),
        migrations.RunPython(definir_cargos_iniciais, migrations.RunPython.noop),
    ]
