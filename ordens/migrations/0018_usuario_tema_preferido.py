from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0017_usuario_cargo_sistema'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='tema_preferido',
            field=models.CharField(
                choices=[('dark', 'Modo escuro'), ('light', 'Modo claro')],
                default='dark',
                help_text='Define se este usuário/cliente verá o sistema em modo claro ou escuro.',
                max_length=10,
                verbose_name='Tema preferido',
            ),
        ),
    ]
