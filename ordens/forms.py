from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone

from .models import AnexoOrdemServico, OrdemServico, Usuario
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


class AtualizacaoTecnicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ('status', 'avaliacao_tecnico', 'servico_planejado')


class AnexoOrdemServicoForm(forms.ModelForm):
    class Meta:
        model = AnexoOrdemServico
        fields = ('arquivo',)

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']
        extensao = arquivo.name.rsplit('.', 1)[-1].lower() if '.' in arquivo.name else ''
        if f'.{extensao}' not in AnexoOrdemServico.EXTENSOES_PERMITIDAS:
            raise forms.ValidationError('Formato não permitido. Envie PDF, imagem ou documento Word.')
        if arquivo.size <= 0 or arquivo.size > AnexoOrdemServico.TAMANHO_MAXIMO:
            raise forms.ValidationError('O arquivo deve ter até 5 MB.')
        return arquivo
