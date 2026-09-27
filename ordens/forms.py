from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone

from .models import Usuario
from .utils import apenas_digitos


class CPFAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='CPF')

    def clean(self):
        cpf = apenas_digitos(self.cleaned_data.get('username'))
        usuario = Usuario.objects.filter(cpf=cpf).only('login_bloqueado_ate').first()
        if usuario and usuario.login_esta_bloqueado():
            desbloqueio = timezone.localtime(usuario.login_bloqueado_ate).strftime('%H:%M')
            raise forms.ValidationError(
                f'Muitas tentativas incorretas. Tente novamente após {desbloqueio}.',
                code='login_bloqueado',
            )
        return super().clean()
