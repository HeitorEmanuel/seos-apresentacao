# Generated manually for SEOS 21.0

from django.db import migrations


def normalizar_hierarquia(apps, schema_editor):
    Usuario = apps.get_model('ordens', 'Usuario')

    # Superusuários pertencem ao papel Administrador do sistema, não ao papel
    # Supervisor Técnico. Assim, a interface e as permissões não misturam os
    # dois níveis de acesso.
    Usuario.objects.filter(is_superuser=True).exclude(cargo_sistema='').update(
        cargo_sistema='',
        is_staff=True,
    )

    # Técnico operacional não acessa o Django Admin; trabalha pela própria
    # fila. Os demais cargos internos continuam podendo entrar no painel
    # limitado pelos ModelAdmins.
    Usuario.objects.filter(cargo_sistema='tecnico', is_superuser=False).update(is_staff=False)
    Usuario.objects.filter(
        cargo_sistema__in=['atendente', 'tecnico_admin', 'almoxarifado'],
        is_superuser=False,
    ).update(is_staff=True)


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0023_anexos_privados'),
    ]

    operations = [
        migrations.RunPython(normalizar_hierarquia, migrations.RunPython.noop),
    ]
