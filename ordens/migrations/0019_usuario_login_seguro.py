# Generated manually for SEOS security improvements.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0018_usuario_tema_preferido'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='login_tentativas_falhas',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Tentativas de login falhas'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='login_bloqueado_ate',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Login bloqueado até'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='senha_alterada_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Senha alterada em'),
        ),
    ]
