import json

from django import forms
from django.forms import BaseInlineFormSet
from django.contrib import admin, messages
from django.contrib.messages import get_messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import models, transaction
from django.db.models import Count, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from .models import HistoricoOrdemServico, MovimentacaoEstoque, OrdemServico, Peca, RegistroSistema, Usuario, gerar_senha_padrao
from .utils import validar_cpf


def registrar_auditoria(request, tipo, acao, descricao, objeto=None, referencia=''):
    """Registra ações importantes feitas pelo painel admin."""
    try:
        usuario = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
        RegistroSistema.objects.create(
            tipo=tipo,
            acao=acao,
            descricao=descricao,
            usuario_responsavel=usuario,
            objeto_id=getattr(objeto, 'pk', None),
            objeto_referencia=referencia or str(objeto or ''),
        )
    except Exception:
        # Auditoria não pode quebrar o fluxo principal do sistema.
        pass


def cargo_usuario(user):
    return getattr(user, 'cargo_sistema', '') or ''


def eh_administrador_sistema(user):
    return bool(getattr(user, 'is_superuser', False))


def eh_supervisor_tecnico(user):
    return bool(not eh_administrador_sistema(user) and cargo_usuario(user) == Usuario.CARGO_TECNICO_ADMIN)


def eh_tecnico_admin(user):
    """Compatibilidade: quem supervisiona ordens, sem acesso total ao sistema."""
    return bool(eh_administrador_sistema(user) or eh_supervisor_tecnico(user))


def eh_atendente(user):
    return cargo_usuario(user) == Usuario.CARGO_ATENDENTE


def eh_almoxarifado(user):
    return cargo_usuario(user) == Usuario.CARGO_ALMOXARIFADO


def pode_gerir_ordens(user):
    return bool(eh_tecnico_admin(user) or eh_atendente(user))


def pode_gerir_estoque(user):
    return bool(eh_administrador_sistema(user) or eh_almoxarifado(user))


def tem_cargo_equipe(user):
    return bool(eh_tecnico_admin(user) or eh_atendente(user) or eh_almoxarifado(user))


def somente_cliente(obj):
    return bool(obj and obj.eh_somente_cliente())




class SafeDateTimeLocalInput(forms.DateTimeInput):
    input_type = 'datetime-local'

    def format_value(self, value):
        if isinstance(value, str):
            return value
        return super().format_value(value)


class SafeDateInput(forms.DateInput):
    input_type = 'date'

    def format_value(self, value):
        if isinstance(value, str):
            return value
        return super().format_value(value)

class UsuarioCreationForm(forms.ModelForm):
    password = forms.CharField(
        label='Senha',
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text='Opcional. Se ficar em branco, o sistema gera uma senha temporária aleatória.',
    )

    class Meta:
        model = Usuario
        fields = ('cpf', 'nome_completo', 'telefone', 'cargo_sistema', 'password')

    def clean_cpf(self):
        return validar_cpf(self.cleaned_data.get('cpf'))


class UsuarioAdmin(BaseUserAdmin):
    actions = None
    change_list_template = 'admin/ordens/usuario/change_list.html'
    change_form_template = 'admin/ordens/usuario/change_form.html'
    add_form = UsuarioCreationForm
    add_form_template = 'admin/ordens/usuario/add_form.html'
    list_display = ('numero_serie_cliente_formatado', 'get_cpf', 'get_nome_completo', 'cargo_badge', 'get_telefone', 'get_is_staff', 'editar_perfil_botao')
    list_filter = ('cargo_sistema', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('cpf', 'nome_completo', 'telefone', 'email', 'numero_serie_cliente', 'cargo_sistema')
    ordering = ('nome_completo', 'cpf')
    readonly_fields = ('numero_serie_cliente',)
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('cpf', 'nome_completo', 'telefone', 'cargo_sistema', 'password')}),
    )
    fieldsets = (
        ('Acesso', {'fields': ('cpf', 'numero_serie_cliente', 'password')}),
        ('Pessoal', {'fields': ('nome_completo', 'email', 'telefone', 'endereco')}),
        ('Equipe e Permissões', {'fields': ('cargo_sistema', 'is_active', 'is_staff', 'is_superuser')}),
    )

    def get_cpf(self, obj):
        return obj.cpf

    get_cpf.short_description = 'CPF'
    get_cpf.admin_order_field = 'cpf'

    def numero_serie_cliente_formatado(self, obj):
        return format_html('<span class="seos-serial-badge">{}</span>', obj.numero_serie_cliente or 'Gerando...')

    numero_serie_cliente_formatado.short_description = 'Nº Cliente'
    numero_serie_cliente_formatado.admin_order_field = 'numero_serie_cliente'

    def cargo_badge(self, obj):
        label = 'Administrador do sistema' if obj.is_superuser else (obj.get_cargo_sistema_display() if getattr(obj, 'cargo_sistema', '') else 'Cliente')
        cores = {
            Usuario.CARGO_ATENDENTE: '#3498db',
            Usuario.CARGO_TECNICO_ADMIN: '#2ecc71',
            Usuario.CARGO_ALMOXARIFADO: '#f39c12',
            'admin': '#8e44ad',
            '': '#64748b',
        }
        cor = '#8e44ad' if obj.is_superuser else cores.get(getattr(obj, 'cargo_sistema', ''), '#64748b')
        return format_html('<span class="seos-cargo-badge" style="background:{};">{}</span>', cor, label)

    cargo_badge.short_description = 'Cargo'
    cargo_badge.admin_order_field = 'cargo_sistema'


    def get_nome_completo(self, obj):
        return obj.nome_completo or obj.username

    get_nome_completo.short_description = 'Nome Completo'
    get_nome_completo.admin_order_field = 'nome_completo'

    def get_telefone(self, obj):
        return obj.telefone or ''

    get_telefone.short_description = 'Telefone'

    def get_is_staff(self, obj):
        return obj.is_staff

    get_is_staff.short_description = 'Membro da Equipe'
    get_is_staff.boolean = True

    def editar_perfil_botao(self, obj):
        url = reverse('admin:ordens_usuario_change', args=[obj.pk])
        return format_html('<a class="seos-btn seos-btn-info" href="{}">📝 Editar Perfil</a>', url)

    editar_perfil_botao.short_description = 'Ações'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if eh_administrador_sistema(request.user):
            return qs
        if eh_atendente(request.user):
            return qs.filter(is_staff=False, is_superuser=False, cargo_sistema='')
        return qs.none()

    def get_fieldsets(self, request, obj=None):
        if eh_administrador_sistema(request.user):
            return super().get_fieldsets(request, obj)
        if eh_atendente(request.user):
            if obj is None:
                return (
                    (None, {'classes': ('wide',), 'fields': ('cpf', 'nome_completo', 'telefone', 'password')}),
                )
            return (
                ('Acesso', {'fields': ('cpf', 'numero_serie_cliente', 'password')}),
                ('Pessoal', {'fields': ('nome_completo', 'email', 'telefone', 'endereco')}),
            )
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if eh_administrador_sistema(request.user):
            return self.readonly_fields
        if eh_atendente(request.user):
            return ('numero_serie_cliente',)
        return self.readonly_fields

    def has_module_permission(self, request):
        return eh_administrador_sistema(request.user) or eh_atendente(request.user)

    def has_view_permission(self, request, obj=None):
        if eh_administrador_sistema(request.user):
            return True
        return eh_atendente(request.user) and (obj is None or somente_cliente(obj))

    def has_add_permission(self, request):
        return eh_administrador_sistema(request.user) or eh_atendente(request.user)

    def has_change_permission(self, request, obj=None):
        if eh_administrador_sistema(request.user):
            return True
        return eh_atendente(request.user) and (obj is None or somente_cliente(obj))

    def has_delete_permission(self, request, obj=None):
        return eh_administrador_sistema(request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.username = obj.cpf
            senha_informada = form.cleaned_data.get('password')

            if senha_informada:
                obj.set_password(senha_informada)
            else:
                senha_gerada = gerar_senha_padrao(obj.nome_completo)
                obj.set_password(senha_gerada)
                obj.senha_temporaria = senha_gerada

        if eh_atendente(request.user) and not eh_administrador_sistema(request.user):
            obj.cargo_sistema = ''
            obj.is_staff = False
            obj.is_superuser = False
            obj.is_active = True

        super().save_model(request, obj, form, change)

        if change:
            registrar_auditoria(
                request,
                tipo='usuario',
                acao='alterado',
                descricao=f"Usuário alterado: {obj.nome_completo or obj.cpf}.",
                objeto=obj,
                referencia=f"Usuário #{obj.pk}",
            )
        else:
            registrar_auditoria(
                request,
                tipo='usuario',
                acao='criado',
                descricao=f"Usuário criado: {obj.nome_completo or obj.cpf}.",
                objeto=obj,
                referencia=f"Usuário #{obj.pk}",
            )


    def _replace_success_messages(self, request, rich_message):
        # Remove a mensagem padrao do Django/Jazzmin e deixa apenas a notificacao
        # organizada do SEOS. O controle direto da fila evita duplicidade e evita
        # aplicar a mensagem de usuario em outros modelos como Peca ou OS.
        storage = get_messages(request)
        list(storage)
        storage.used = True
        if hasattr(storage, '_queued_messages'):
            storage._queued_messages = []
        messages.success(request, rich_message)

    def _render_message_chip(self, label, value):
        return format_html(
            '<span class="seos-message-chip"><span class="seos-message-label">{}</span><strong class="seos-message-value">{}</strong></span>',
            label,
            value,
        )

    def _render_rich_message(self, *, title, summary, chips):
        chips_html = format_html_join('', '{}', ((chip,) for chip in chips if chip))
        return format_html(
            '<div class="seos-message-card">'
            '<div class="seos-message-card__icon">✓</div>'
            '<div class="seos-message-card__content">'
            '<div class="seos-message-card__text">'
            '<strong class="seos-message-card__title">{}</strong>'
            '<p class="seos-message-card__summary">{}</p>'
            '</div>'
            '<div class="seos-message-card__meta">{}</div>'
            '</div>'
            '</div>',
            title,
            summary,
            chips_html,
        )

    def _build_user_created_message(self, obj):
        nome_usuario = getattr(obj, 'nome_completo', '') or getattr(obj, 'cpf', '') or str(obj)
        senha_resumo = getattr(obj, 'senha_temporaria', '') or 'Definida no cadastro'
        chips = [
            self._render_message_chip('Usuário', nome_usuario),
            self._render_message_chip('CPF', getattr(obj, 'cpf', '')),
            self._render_message_chip('Nº Cliente', getattr(obj, 'numero_serie_cliente', '') or 'Gerando'),
            self._render_message_chip('Senha temporária', senha_resumo),
        ]
        return self._render_rich_message(
            title='Usuário criado com sucesso',
            summary='O cadastro foi concluído e as informações principais já estão organizadas para conferência rápida.',
            chips=chips,
        )

    def _build_user_updated_message(self, obj):
        nome_usuario = getattr(obj, 'nome_completo', '') or getattr(obj, 'cpf', '') or str(obj)
        cargo = obj.get_cargo_sistema_display() if getattr(obj, 'cargo_sistema', '') else 'Cliente'
        chips = [
            self._render_message_chip('Usuário', nome_usuario),
            self._render_message_chip('CPF', getattr(obj, 'cpf', '')),
            self._render_message_chip('Nº Cliente', getattr(obj, 'numero_serie_cliente', '') or 'Gerando'),
            self._render_message_chip('Cargo', cargo),
        ]
        return self._render_rich_message(
            title='Usuário atualizado com sucesso',
            summary='As alterações foram salvas e o perfil já está sincronizado com o painel administrativo.',
            chips=chips,
        )

    def response_add(self, request, obj, post_url_continue=None):
        response = super().response_add(request, obj, post_url_continue)
        if isinstance(obj, Usuario):
            self._replace_success_messages(request, self._build_user_created_message(obj))
        return response

    def response_change(self, request, obj):
        response = super().response_change(request, obj)
        if isinstance(obj, Usuario):
            self._replace_success_messages(request, self._build_user_updated_message(obj))
        return response

    def delete_model(self, request, obj):
        registrar_auditoria(
            request,
            tipo='usuario',
            acao='excluido',
            descricao=f"Usuário excluído: {obj.nome_completo or obj.cpf}.",
            objeto=obj,
            referencia=f"Usuário #{obj.pk}",
        )
        super().delete_model(request, obj)


class OrdemServicoForm(forms.ModelForm):
    data_entrada = forms.CharField(
        label='Data de Entrada do Produto',
        required=True,
        widget=forms.TextInput(attrs={
            'type': 'datetime-local',
            'style': 'max-width: 220px;',
        }),
    )
    data_entrega_prevista = forms.CharField(
        label='Possível Data de Entrega',
        required=False,
        widget=forms.TextInput(attrs={
            'type': 'date',
            'style': 'max-width: 170px;',
        }),
    )

    movimentacao_peca_temp = forms.ModelChoiceField(
        label='Peça trocada',
        required=False,
        queryset=Peca.objects.none(),
        empty_label='---------',
        widget=forms.Select(attrs={
            'style': 'width: 100%; max-width: 100%;',
            'class': 'seos-peca-select seos-peca-temp-select',
            'data-preview-target': 'seos-peca-preview-temp',
        }),
        help_text='Escolha a peça trocada no reparo e clique em “Adicionar à lista”.',
    )
    movimentacao_quantidade_temp = forms.IntegerField(
        label='Quantidade',
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'min': '1',
            'style': 'width: 140px; max-width: 100%;',
            'class': 'seos-peca-temp-qtd',
        }),
    )
    movimentacao_observacao_temp = forms.CharField(
        label='Observação',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex.: usada na troca, substituição, teste etc.',
            'style': 'width: 100%; max-width: 100%;',
            'class': 'seos-peca-temp-obs',
        }),
    )
    pecas_usadas_json = forms.CharField(
        label='Peças temporárias',
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'id_pecas_usadas_json',
            'class': 'seos-pecas-json-field',
        }),
    )

    class Meta:
        model = OrdemServico
        fields = '__all__'
        widgets = {
            'descricao_problema': forms.Textarea(attrs={'rows': 4}),
            'avaliacao_tecnico': forms.Textarea(attrs={'rows': 4}),
            'servico_planejado': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cliente_nome_field = self.fields.get('cliente_nome_exibicao')
        if cliente_nome_field:
            cliente_nome_field.required = False

        pecas_ativas = list(Peca.objects.filter(ativo=True).order_by('nome'))
        pecas_json = json.dumps({
            str(peca.pk): {
                'id': peca.pk,
                'nome': peca.nome,
                'codigo': peca.codigo,
                'descricao': (peca.descricao or '').strip(),
                'valor_unitario': str(peca.valor_unitario),
                'preco_varejo': str(getattr(peca, 'preco_varejo', 0) or 0),
                'estoque': peca.quantidade,
                'estoque_minimo': peca.estoque_minimo,
            }
            for peca in pecas_ativas
        })

        peca_field = self.fields.get('movimentacao_peca_temp')
        if peca_field:
            peca_field.queryset = Peca.objects.filter(ativo=True).order_by('nome')
            peca_field.widget.attrs['data-pecas-json'] = pecas_json

            def rotulo_peca(peca):
                return f"{peca.nome} ({peca.codigo})"

            peca_field.label_from_instance = rotulo_peca

        if not self.is_bound:
            data_entrada = getattr(self.instance, 'data_entrada', None) or timezone.now()
            if data_entrada:
                if timezone.is_naive(data_entrada):
                    data_entrada = timezone.make_aware(data_entrada, timezone.get_current_timezone())
                self.initial['data_entrada'] = timezone.localtime(data_entrada).strftime('%Y-%m-%dT%H:%M')

            data_entrega = getattr(self.instance, 'data_entrega_prevista', None)
            if data_entrega:
                self.initial['data_entrega_prevista'] = data_entrega.strftime('%Y-%m-%d')

    def clean_data_entrada(self):
        valor = (self.cleaned_data.get('data_entrada') or '').strip()
        if not valor:
            raise forms.ValidationError('Informe a data de entrada do produto.')

        data = parse_datetime(valor)
        if data is None:
            raise forms.ValidationError('Use uma data e hora válidas.')

        if timezone.is_naive(data):
            data = timezone.make_aware(data, timezone.get_current_timezone())

        return data

    def clean_data_entrega_prevista(self):
        valor = (self.cleaned_data.get('data_entrega_prevista') or '').strip()
        if not valor:
            return None

        data = parse_date(valor)
        if data is None:
            raise forms.ValidationError('Use uma data válida.')

        return data

    def _parse_pecas_usadas_json(self):
        raw = (self.cleaned_data.get('pecas_usadas_json') or '').strip()
        if not raw:
            return []

        try:
            dados = json.loads(raw)
        except json.JSONDecodeError:
            raise forms.ValidationError('A lista temporária de peças está inválida. Recarregue a página e tente novamente.')

        if not isinstance(dados, list):
            raise forms.ValidationError('A lista temporária de peças está inválida.')

        return dados

    def clean(self):
        cleaned_data = super().clean()

        if 'cliente_usuario' not in self.fields and 'cliente_nome_exibicao' not in self.fields:
            return cleaned_data

        cliente_usuario = cleaned_data.get('cliente_usuario')
        cliente_nome = (cleaned_data.get('cliente_nome_exibicao') or '').strip()

        if not cliente_usuario and not cliente_nome:
            raise forms.ValidationError('Informe um cliente cadastrado ou preencha o nome de exibição do cliente.')

        if cliente_usuario and not cliente_nome:
            cleaned_data['cliente_nome_exibicao'] = cliente_usuario.nome_completo

        itens_json = self._parse_pecas_usadas_json()

        # Segurança: se o usuário selecionou uma peça, mas esqueceu de clicar em "Adicionar à lista",
        # o sistema aproveita essa seleção como um item da lista.
        peca_temp = cleaned_data.get('movimentacao_peca_temp')
        qtd_temp = cleaned_data.get('movimentacao_quantidade_temp')
        obs_temp = cleaned_data.get('movimentacao_observacao_temp')

        if peca_temp or qtd_temp or obs_temp:
            if not peca_temp or not qtd_temp:
                raise forms.ValidationError('Para adicionar a peça selecionada, preencha peça e quantidade ou limpe essa área.')
            itens_json.append({
                'peca_id': peca_temp.pk,
                'quantidade': qtd_temp,
                'observacao': obs_temp or '',
            })

        if not itens_json:
            cleaned_data['pecas_usadas_lista'] = []
            return cleaned_data

        acumulado_por_peca = {}
        itens_processados = []

        for posicao, item in enumerate(itens_json, start=1):
            try:
                peca_id = int(item.get('peca_id') or item.get('id'))
                quantidade = int(item.get('quantidade') or 0)
            except (TypeError, ValueError, AttributeError):
                raise forms.ValidationError(f'Item {posicao} da lista de peças está inválido.')

            if quantidade <= 0:
                raise forms.ValidationError(f'A quantidade do item {posicao} deve ser maior que zero.')

            peca = Peca.objects.filter(pk=peca_id, ativo=True).first()
            if not peca:
                raise forms.ValidationError(f'A peça do item {posicao} não foi encontrada ou está inativa.')

            observacao = str(item.get('observacao') or '').strip()

            acumulado_por_peca.setdefault(peca.pk, {'peca': peca, 'quantidade': 0})
            acumulado_por_peca[peca.pk]['quantidade'] += quantidade

            itens_processados.append({
                'peca': peca,
                'quantidade': quantidade,
                'observacao': observacao,
            })

        for dados in acumulado_por_peca.values():
            peca = dados['peca']
            quantidade_total = dados['quantidade']
            if quantidade_total > peca.quantidade:
                raise forms.ValidationError(
                    f'Estoque insuficiente para {peca.nome}. Solicitado: {quantidade_total} un. | Disponível: {peca.quantidade} un.'
                )

        cleaned_data['pecas_usadas_lista'] = itens_processados
        return cleaned_data


class PecaMovimentacaoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        descricao = (obj.descricao or '').strip()
        if len(descricao) > 36:
            descricao = descricao[:36].rstrip() + '...'
        detalhes = [f'R$ {obj.valor_unitario}', f'Estoque: {obj.quantidade}']
        if descricao:
            detalhes.insert(0, descricao)
        return f"{obj.nome} ({obj.codigo}) — {' | '.join(detalhes)}"


class MovimentacaoOSInlineForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ('tipo', 'peca', 'quantidade', 'observacao')
        widgets = {
            'tipo': forms.Select(attrs={'style': 'min-width: 140px;'}),
            'peca': forms.Select(attrs={'style': 'min-width: 380px;'}),
            'quantidade': forms.NumberInput(attrs={'min': '1', 'placeholder': 'Qtd.', 'style': 'max-width: 140px;'}),
            'observacao': forms.TextInput(attrs={'placeholder': 'Observação opcional', 'style': 'min-width: 240px;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].required = False
        self.fields['tipo'].choices = [
            ('', '---------'),
            ('entrada', 'Entrada'),
            ('saida', 'Saída'),
        ]
        self.fields['quantidade'].required = False
        self.fields['observacao'].required = False
        self.fields['peca'] = PecaMovimentacaoChoiceField(
            queryset=Peca.objects.filter(ativo=True).order_by('nome'),
            required=False,
            empty_label='---------',
            widget=self.fields['peca'].widget,
            label='Peça',
        )
        self.fields['peca'].help_text = 'Selecione a peça. O valor unitário e o estoque aparecem na própria lista.'


class MovimentacaoOSInlineFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if form.instance and form.instance.pk:
            for field in form.fields.values():
                field.disabled = True

    def clean(self):
        super().clean()
        erros = []

        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            if getattr(form.instance, 'pk', None):
                continue

            peca = form.cleaned_data.get('peca')
            tipo = form.cleaned_data.get('tipo')
            quantidade = form.cleaned_data.get('quantidade')

            if not any([peca, tipo, quantidade, form.cleaned_data.get('observacao')]):
                continue

            # Linha incompleta não deve estourar erro interno do Django.
            # Ela será ignorada se estiver vazia ou tratada como erro amigável se parcialmente preenchida.

            if not peca or not tipo or not quantidade:
                erros.append('Preencha peça, tipo e quantidade em cada movimentação adicionada.')
                continue

            if quantidade <= 0:
                erros.append('A quantidade da peça deve ser maior que zero.')
                continue

            if tipo == 'saida' and quantidade > peca.quantidade:
                erros.append(f'Estoque insuficiente para {peca.nome} ({peca.codigo}). Disponível: {peca.quantidade} un.')

        if erros:
            raise forms.ValidationError(erros)


class MovimentacaoEstoqueInline(admin.StackedInline):
    model = MovimentacaoEstoque
    form = MovimentacaoOSInlineForm
    formset = MovimentacaoOSInlineFormSet
    extra = 0
    min_num = 0
    can_delete = False
    show_change_link = False
    verbose_name = 'Movimentação de peça'
    verbose_name_plural = 'Peças da OS (opcional)'
    fields = ('tipo', 'peca', 'quantidade', 'observacao')
    readonly_fields = ()

    def get_extra(self, request, obj=None, **kwargs):
        return 0

    def has_add_permission(self, request, obj=None):
        if request.GET.get('modo') == 'visualizar':
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        form_field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'peca':
            form_field.widget.can_add_related = False
            form_field.widget.can_change_related = False
            form_field.widget.can_delete_related = False
            form_field.widget.can_view_related = False
        return form_field

    def data_movimentacao_formatada(self, obj):
        if not obj or not obj.pk or not obj.data_movimentacao:
            return 'Nova'
        return timezone.localtime(obj.data_movimentacao).strftime('%d/%m/%Y %H:%M')

    data_movimentacao_formatada.short_description = 'Data'

    def valor_unitario_inline(self, obj):
        if not obj or not getattr(obj, 'peca_id', None):
            return '—'
        return f'R$ {obj.peca.valor_unitario}'

    valor_unitario_inline.short_description = 'Valor unit.'

    def subtotal_inline(self, obj):
        if not obj or not getattr(obj, 'peca_id', None):
            return '—'
        return f'R$ {obj.subtotal}'

    subtotal_inline.short_description = 'Subtotal'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('peca', 'usuario_responsavel').order_by('-data_movimentacao')

class MesEntradaOrdemFilter(admin.SimpleListFilter):
    title = 'Data de entrada'
    parameter_name = 'mes_entrada'

    MESES_PT = {
        1: 'Janeiro',
        2: 'Fevereiro',
        3: 'Março',
        4: 'Abril',
        5: 'Maio',
        6: 'Junho',
        7: 'Julho',
        8: 'Agosto',
        9: 'Setembro',
        10: 'Outubro',
        11: 'Novembro',
        12: 'Dezembro',
    }

    def lookups(self, request, model_admin):
        opcoes = [('todas', 'Todas as datas')]
        meses = (
            model_admin.model.objects
            .exclude(data_entrada__isnull=True)
            .dates('data_entrada', 'month', order='DESC')[:18]
        )

        for mes in meses:
            chave = f'{mes.year}-{mes.month:02d}'
            rotulo = f'{self.MESES_PT.get(mes.month, mes.month)} de {mes.year}'
            opcoes.append((chave, rotulo))
        return opcoes

    def queryset(self, request, queryset):
        valor = self.value()
        if not valor or valor == 'todas':
            return queryset

        try:
            ano_txt, mes_txt = valor.split('-', 1)
            ano = int(ano_txt)
            mes = int(mes_txt)
        except (TypeError, ValueError):
            return queryset

        return queryset.filter(data_entrada__year=ano, data_entrada__month=mes)


class OrdemServicoAdmin(admin.ModelAdmin):
    actions = None
    change_list_template = 'admin/ordens/ordemservico/change_list.html'
    def has_module_permission(self, request):
        return pode_gerir_ordens(request.user)

    def has_view_permission(self, request, obj=None):
        return pode_gerir_ordens(request.user)

    def has_add_permission(self, request):
        return pode_gerir_ordens(request.user)

    def has_change_permission(self, request, obj=None):
        return pode_gerir_ordens(request.user)

    def has_delete_permission(self, request, obj=None):
        return eh_tecnico_admin(request.user)

    form = OrdemServicoForm
    change_form_template = 'admin/ordens/ordemservico/change_form.html'
    list_display = (
        'id',
        'status_colorido',
        'cliente_formatado',
        'equipamento',
        'numero_serie_formatado',
        'tecnico_responsavel',
        'data_entrada',
        'data_entrega_prevista',
        'botoes_acao',
    )
    list_display_links = None
    list_filter = ('status', 'tecnico_responsavel', MesEntradaOrdemFilter, 'data_entrega_prevista')
    search_fields = (
        'id',
        'cliente_usuario__nome_completo',
        'cliente_nome_exibicao',
        'equipamento',
        'numero_serie',
        'tecnico_responsavel__nome_completo',
        'descricao_problema',
    )
    ordering = ('-data_entrada', '-id')
    date_hierarchy = None
    list_per_page = 25

    def lookup_allowed(self, lookup, value, request=None):
        if lookup == 'mes_entrada':
            return True
        return super().lookup_allowed(lookup, value, request)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        mes_entrada = request.GET.get('mes_entrada')
        if mes_entrada:
            try:
                ano_txt, mes_txt = mes_entrada.split('-', 1)
                ano = int(ano_txt)
                mes = int(mes_txt)
            except (TypeError, ValueError):
                return queryset
            if 1 <= mes <= 12:
                queryset = queryset.filter(data_entrada__year=ano, data_entrada__month=mes)
        return queryset

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        meses = (
            self.model.objects
            .exclude(data_entrada__isnull=True)
            .dates('data_entrada', 'month', order='DESC')[:24]
        )
        extra_context['seos_meses_disponiveis'] = [
            {
                'valor': f'{mes.year}-{mes.month:02d}',
                'rotulo': f'{MesEntradaOrdemFilter.MESES_PT.get(mes.month, mes.month)} de {mes.year}',
            }
            for mes in meses
        ]
        extra_context['seos_mes_entrada'] = request.GET.get('mes_entrada', '')
        return super().changelist_view(request, extra_context=extra_context)

    inlines = []
    formfield_overrides = {
        models.DecimalField: {'widget': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'style': 'max-width: 170px;'})},
    }
    fieldsets = (
        ('Informações do Cliente', {
            'fields': ('cliente_usuario', 'cliente_nome_exibicao', 'equipamento', 'numero_serie', 'status', 'data_entrada', 'descricao_problema'),
        }),
        ('Responsável Técnico', {
            'fields': ('tecnico_responsavel',),
        }),
        ('Painel de Diagnóstico', {
            'fields': ('avaliacao_tecnico', 'servico_planejado', 'data_entrega_prevista', 'valor_estimado'),
        }),
        ('Peças da OS', {
            'classes': ('seos-pecas-fieldset',),
            'fields': (('movimentacao_peca_temp', 'movimentacao_quantidade_temp'), 'visual_detalhes_peca_temp', 'movimentacao_observacao_temp', 'pecas_usadas_json', 'visual_lista_pecas_temporarias', 'visual_pecas_movimentadas'),
            'description': 'Peças que entram no orçamento da OS. Selecione a peça, informe a quantidade e adicione à lista. O total das peças aparece abaixo da lista.',
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        form_field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'tecnico_responsavel':
            form_field.widget.can_add_related = False
            form_field.widget.can_change_related = False
            form_field.widget.can_delete_related = False
            form_field.widget.can_view_related = False
        return form_field

    campos_visualizacao = (
        'visual_status',
        'visual_cliente',
        'visual_equipamento',
        'visual_numero_serie',
        'visual_data_entrada',
        'visual_data_criacao',
        'visual_descricao_problema',
        'visual_tecnico',
        'visual_avaliacao_tecnico',
        'visual_servico_planejado',
        'visual_data_entrega_prevista',
        'visual_valor_estimado',
        'visual_pecas_movimentadas',
        'visual_historico',
        'visual_acoes_rapidas',
    )

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if request.method in ('POST', 'PUT', 'PATCH'):
            with transaction.atomic():
                return super().changeform_view(request, object_id, form_url, extra_context)
        return super().changeform_view(request, object_id, form_url, extra_context)

    def is_modo_visualizacao(self, request):
        return request.GET.get('modo') == 'visualizar'

    def get_readonly_fields(self, request, obj=None):
        if self.is_modo_visualizacao(request):
            return self.campos_visualizacao
        if eh_atendente(request.user) and not eh_tecnico_admin(request.user):
            return ('numero_serie',)
        return ('numero_serie', 'visual_detalhes_peca_temp', 'visual_lista_pecas_temporarias', 'visual_pecas_movimentadas')

    def get_fieldsets(self, request, obj=None):
        if self.is_modo_visualizacao(request):
            return (
                ('Resumo da Ordem de Serviço', {
                    'classes': ('seos-view-fieldset',),
                    'fields': ('visual_status', 'visual_cliente', 'visual_equipamento', 'visual_numero_serie', 'visual_data_entrada', 'visual_data_criacao'),
                }),
                ('Problema Relatado', {
                    'classes': ('seos-view-fieldset',),
                    'fields': ('visual_descricao_problema',),
                }),
                ('Diagnóstico e Serviço', {
                    'classes': ('seos-view-fieldset',),
                    'fields': ('visual_tecnico', 'visual_avaliacao_tecnico', 'visual_servico_planejado', 'visual_data_entrega_prevista', 'visual_valor_estimado'),
                }),
                ('Peças e Movimentações', {
                    'classes': ('seos-view-fieldset',),
                    'fields': ('visual_pecas_movimentadas',),
                }),
                ('Histórico da OS', {
                    'classes': ('seos-view-fieldset',),
                    'fields': ('visual_historico',),
                }),
                ('Ações rápidas', {
                    'classes': ('seos-view-fieldset',),
                    'fields': ('visual_acoes_rapidas',),
                }),
            )
        if eh_atendente(request.user) and not eh_tecnico_admin(request.user):
            return (
                ('Informações do Cliente', {
                    'fields': ('cliente_usuario', 'cliente_nome_exibicao', 'equipamento', 'numero_serie', 'status', 'data_entrada', 'descricao_problema'),
                }),
                ('Responsável Técnico', {
                    'fields': ('tecnico_responsavel',),
                }),
                ('Atendimento', {
                    'fields': ('data_entrega_prevista', 'valor_estimado'),
                }),
            )
        return super().get_fieldsets(request, obj)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if self.is_modo_visualizacao(request):
            if request.method == 'POST':
                messages.warning(request, 'Modo visualização: nenhuma alteração foi salva. Clique em "Editar" para alterar esta OS.')
                url = reverse('admin:ordens_ordemservico_change', args=[object_id]) + '?modo=visualizar'
                return redirect(url)

            extra_context.update({
                'is_modo_visualizar': True,
                'show_save': False,
                'show_save_and_select_another': False,
                'show_save_and_continue': False,
                'show_delete_link': False,
            })
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def _texto_padrao(self, valor, vazio='Não informado'):
        return str(valor).strip() if valor not in (None, '') and str(valor).strip() else vazio

    def _status_badge_html(self, status, label):
        cores = {
            'aberto': '#3498db',
            'aguardando_pecas': '#e67e22',
            'consertando': '#f1c40f',
            'finalizado': '#2ecc71',
            'entregue': '#95a5a6',
        }
        cor = cores.get(status, '#777')
        return format_html('<span class="seos-status-badge seos-status-view" style="background:{};">{}</span>', cor, label)

    def visual_status(self, obj):
        return self._status_badge_html(obj.status, obj.get_status_display())

    visual_status.short_description = 'Status'

    def visual_cliente(self, obj):
        if obj.cliente_usuario:
            telefone = self._texto_padrao(obj.cliente_usuario.telefone)
            cpf = self._texto_padrao(obj.cliente_usuario.cpf)
            return format_html(
                '<div class="seos-readonly-card">'
                '<strong>{}</strong>'
                '<span>Nº cliente: {}</span>'
                '<span>CPF: {}</span>'
                '<span>Telefone: {}</span>'
                '</div>',
                obj.cliente_usuario.nome_completo,
                obj.cliente_usuario.numero_serie_cliente or 'Não informado',
                cpf,
                telefone,
            )
        return format_html(
            '<div class="seos-readonly-card">'
            '<strong>{}</strong>'
            '<span>Cliente não vinculado a um usuário cadastrado.</span>'
            '</div>',
            self._texto_padrao(obj.cliente_nome_exibicao),
        )

    visual_cliente.short_description = 'Cliente'

    def visual_equipamento(self, obj):
        return format_html('<div class="seos-readonly-text seos-readonly-strong">{}</div>', self._texto_padrao(obj.equipamento))

    visual_equipamento.short_description = 'Equipamento'

    def visual_numero_serie(self, obj):
        return format_html(
            '<div class="seos-readonly-text seos-readonly-strong seos-serial-view">{}</div>',
            self._texto_padrao(obj.numero_serie, 'Não informado'),
        )

    visual_numero_serie.short_description = 'Nº cliente/equipamento'

    def visual_data_entrada(self, obj):
        if not obj.data_entrada:
            return 'Não informada'
        return timezone.localtime(obj.data_entrada).strftime('%d/%m/%Y às %H:%M')

    visual_data_entrada.short_description = 'Data de entrada'

    def visual_data_criacao(self, obj):
        if not obj.data_criacao:
            return 'Não informada'
        return timezone.localtime(obj.data_criacao).strftime('%d/%m/%Y às %H:%M')

    visual_data_criacao.short_description = 'Data de criação no sistema'

    def visual_descricao_problema(self, obj):
        return format_html('<div class="seos-readonly-text seos-readonly-box">{}</div>', self._texto_padrao(obj.descricao_problema))

    visual_descricao_problema.short_description = 'Descrição do problema'

    def visual_tecnico(self, obj):
        tecnico = obj.tecnico_responsavel.nome_completo if obj.tecnico_responsavel else 'Nenhum técnico definido'
        return format_html('<div class="seos-readonly-text seos-readonly-strong">{}</div>', tecnico)

    visual_tecnico.short_description = 'Técnico responsável'

    def visual_avaliacao_tecnico(self, obj):
        return format_html('<div class="seos-readonly-text seos-readonly-box">{}</div>', self._texto_padrao(obj.avaliacao_tecnico, 'Ainda sem avaliação técnica.'))

    visual_avaliacao_tecnico.short_description = 'Avaliação do técnico'

    def visual_servico_planejado(self, obj):
        return format_html('<div class="seos-readonly-text seos-readonly-box">{}</div>', self._texto_padrao(obj.servico_planejado, 'Ainda sem serviço planejado.'))

    visual_servico_planejado.short_description = 'Serviço planejado'

    def visual_data_entrega_prevista(self, obj):
        return obj.data_entrega_prevista.strftime('%d/%m/%Y') if obj.data_entrega_prevista else 'A definir'

    visual_data_entrega_prevista.short_description = 'Possível data de entrega'

    def visual_valor_estimado(self, obj):
        return format_html('<div class="seos-readonly-text seos-readonly-strong">R$ {}</div>', obj.valor_estimado) if obj.valor_estimado else 'Sob consulta'

    visual_valor_estimado.short_description = 'Valor estimado'

    def visual_fluxo_pecas_os(self, obj=None):
        return mark_safe(
            '<div class="seos-pecas-os-resumo">'
            '<strong>Peças trocadas na OS</strong>'
            '<span>Selecione a peça, informe a quantidade e adicione à lista. O total das peças ajuda a calcular o valor final para o cliente junto com a mão de obra.</span>'
            '</div>'
        )

    visual_fluxo_pecas_os.short_description = 'Resumo'

    def visual_detalhes_peca_temp(self, obj=None):
        return mark_safe(
            '<div id="seos-peca-preview-temp" class="seos-pecas-os-preview">'
            '<span>Selecione uma peça para ver estoque, valor unitário, preço de venda e subtotal.</span>'
            '</div>'
        )

    visual_detalhes_peca_temp.short_description = 'Valor da peça'

    def visual_lista_pecas_temporarias(self, obj=None):
        return mark_safe(
            '<div class="seos-pecas-os-lista">'
            '<div class="seos-pecas-os-lista-topo">'
            '<strong>Lista de peças</strong>'
            '<span>Use “Adicionar peça” caso seja necessário trocar outra peça fora do planejado.</span>'
            '</div>'
            '<div class="seos-pecas-os-actions">'
            '<button type="button" id="seos-add-peca-temp" class="seos-peca-add-btn">+ Adicionar peça</button>'
            '<button type="button" id="seos-confirmar-pecas" class="seos-peca-confirm-btn">✓ Salvar lista de peças</button>'
            '</div>'
            '<div id="seos-pecas-temp-status" class="seos-pecas-temp-status">Total das peças adicionadas: R$ 0,00</div>'
            '<div id="seos-pecas-temp-list" class="seos-pecas-temp-list"></div>'
            '<div class="seos-pecas-os-warning">Depois de conferir, clique em <strong>Salvar</strong> para gravar as peças na OS e baixar do estoque.</div>'
            '</div>'
        )

    visual_lista_pecas_temporarias.short_description = 'Lista e total'

    def visual_pecas_movimentadas(self, obj):
        if not obj or not obj.pk:
            return format_html('<div class="seos-empty-history seos-pecas-empty">{}</div>', 'Salve a OS para começar a registrar peças vinculadas a ela.')

        movimentacoes = list(obj.pecas_utilizadas.select_related('peca', 'usuario_responsavel').all()[:12])
        if not movimentacoes:
            return format_html('<div class="seos-empty-history seos-pecas-empty">{}</div>', 'Nenhuma peça vinculada a esta OS até o momento.')

        linhas = format_html_join(
            '',
            '<tr>'
            '<td>{}</td>'
            '<td><strong>{}</strong><br><span class="seos-muted">{}</span></td>'
            '<td>{}</td>'
            '<td>{} un.</td>'
            '<td>R$ {}</td>'
            '<td>R$ {}</td>'
            '<td>{}</td>'
            '</tr>',
            (
                (
                    timezone.localtime(m.data_movimentacao).strftime('%d/%m/%Y %H:%M'),
                    m.peca.nome,
                    m.peca.codigo,
                    m.get_tipo_display(),
                    m.quantidade,
                    m.peca.valor_unitario,
                    m.subtotal,
                    self._texto_padrao(m.observacao, '—'),
                )
                for m in movimentacoes
            ),
        )

        return format_html(
            '<div class="seos-inline-table-wrapper">'
            '<table class="seos-inline-table">'
            '<thead><tr><th>Data</th><th>Peça</th><th>Tipo</th><th>Qtd.</th><th>Valor unit.</th><th>Subtotal</th><th>Observação</th></tr></thead>'
            '<tbody>{}</tbody>'
            '</table>'
            '</div>',
            linhas,
        )

    visual_pecas_movimentadas.short_description = 'Peças já lançadas na OS'

    def visual_historico(self, obj):
        historicos = list(obj.historicos.all()[:8])
        if not historicos:
            return format_html('<div class="seos-empty-history">{}</div>', 'Nenhuma movimentação registrada para esta OS.')

        itens = format_html_join(
            '',
            '<li>'
            '<div class="seos-history-date">{}</div>'
            '<div class="seos-history-status">{}</div>'
            '<p>{}</p>'
            '</li>',
            (
                (
                    timezone.localtime(h.data_alteracao).strftime('%d/%m/%Y às %H:%M'),
                    self._status_badge_html(h.status_momento, h.get_status_momento_display()),
                    h.descricao_alteracao,
                )
                for h in historicos
            ),
        )
        return format_html('<ul class="seos-history-list">{}</ul>', itens)

    visual_historico.short_description = 'Histórico recente'

    def visual_acoes_rapidas(self, obj):
        url_editar = reverse('admin:ordens_ordemservico_change', args=[obj.pk])
        url_imprimir_a4 = reverse('admin:ordemservico_pdf', args=[obj.pk])
        url_etiqueta = reverse('admin:ordemservico_etiqueta', args=[obj.pk])
        url_lista = reverse('admin:ordens_ordemservico_changelist')
        return format_html(
            '<div class="seos-action-buttons seos-view-actions">'
            '<a class="seos-btn seos-btn-secondary" href="{}">← Lista</a>'
            '<a class="seos-btn seos-btn-primary" href="{}"><i class="fas fa-edit"></i> Editar</a>'
            '<a class="seos-btn seos-btn-info" href="{}" target="_blank" rel="noopener"><i class="far fa-file-alt"></i> Imprimir OS</a>'
            '<a class="seos-btn seos-btn-warning" href="{}" target="_blank" rel="noopener"><i class="fas fa-tag"></i> Etiqueta</a>'
            '</div>',
            url_lista,
            url_editar,
            url_imprimir_a4,
            url_etiqueta,
        )

    visual_acoes_rapidas.short_description = 'Ações'

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if obj.cliente_usuario and not obj.cliente_nome_exibicao:
                obj.cliente_nome_exibicao = obj.cliente_usuario.nome_completo
            super().save_model(request, obj, form, change)

            cliente = obj.cliente_usuario.nome_completo if obj.cliente_usuario else obj.cliente_nome_exibicao
            if change:
                acao = 'alterado'
                descricao = f"Ordem de serviço #{obj.pk} alterada para o cliente {cliente}."
            else:
                acao = 'criado'
                descricao = f"Ordem de serviço #{obj.pk} criada para o cliente {cliente}."

            registrar_auditoria(
                request,
                tipo='ordem_servico',
                acao=acao,
                descricao=descricao,
                objeto=obj,
                referencia=f"OS #{obj.pk}",
            )

            pecas_usadas = form.cleaned_data.get('pecas_usadas_lista') or []
            for item in pecas_usadas:
                movimentacao = MovimentacaoEstoque.objects.create(
                    ordem_servico=obj,
                    tipo='saida',
                    peca=item['peca'],
                    quantidade=item['quantidade'],
                    observacao=item.get('observacao') or '',
                    usuario_responsavel=request.user if request.user.is_authenticated else None,
                )

                registrar_auditoria(
                    request,
                    tipo='sistema',
                    acao='criado',
                    descricao=f"Peça trocada na OS #{obj.pk}: {movimentacao.quantidade} un. de {movimentacao.peca.nome}.",
                    objeto=movimentacao,
                    referencia=f"Mov. Estoque #{movimentacao.pk}",
                )

                HistoricoOrdemServico.objects.create(
                    ordem_servico=obj,
                    status_momento=obj.status,
                    descricao_alteracao=f"Peça trocada na OS: {movimentacao.quantidade} un. de {movimentacao.peca.nome} ({movimentacao.peca.codigo}).",
                )

            if pecas_usadas:
                messages.success(request, f'{len(pecas_usadas)} peça(s) lançada(s) nesta OS e baixada(s) do estoque.')

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        with transaction.atomic():
            if form.instance and not form.instance.pk:
                form.instance.save()

            for obj in instances:
                if isinstance(obj, MovimentacaoEstoque):
                    if not obj.peca_id or not obj.quantidade or not obj.tipo:
                        continue

                    novo_registro = obj.pk is None
                    if not obj.usuario_responsavel and request.user.is_authenticated:
                        obj.usuario_responsavel = request.user
                    if not obj.ordem_servico_id:
                        obj.ordem_servico = form.instance
                    if not obj.ordem_servico_id:
                        continue

                    obj.save()

                    if novo_registro:
                        detalhe_os = f" vinculada à OS #{obj.ordem_servico_id}" if obj.ordem_servico_id else ''
                        registrar_auditoria(
                            request,
                            tipo='sistema',
                            acao='criado',
                            descricao=f"Movimentação de estoque: {obj.get_tipo_display()} de {obj.quantidade} un. em {obj.peca.nome}{detalhe_os}.",
                            objeto=obj,
                            referencia=f"Mov. Estoque #{obj.pk}",
                        )
                        HistoricoOrdemServico.objects.create(
                            ordem_servico=obj.ordem_servico,
                            status_momento=obj.ordem_servico.status,
                            descricao_alteracao=f"Peças da OS: {obj.get_tipo_display()} de {obj.quantidade} un. da peça {obj.peca.nome} ({obj.peca.codigo}).",
                        )
                else:
                    obj.save()

            formset.save_m2m()

    def delete_model(self, request, obj):
        cliente = obj.cliente_usuario.nome_completo if obj.cliente_usuario else obj.cliente_nome_exibicao
        registrar_auditoria(
            request,
            tipo='ordem_servico',
            acao='excluido',
            descricao=f"Ordem de serviço #{obj.pk} excluída. Cliente: {cliente}.",
            objeto=obj,
            referencia=f"OS #{obj.pk}",
        )
        super().delete_model(request, obj)


    def status_colorido(self, obj):
        cores = {
            'aberto': '#3498db',
            'aguardando_pecas': '#e67e22',
            'consertando': '#f1c40f',
            'finalizado': '#2ecc71',
            'entregue': '#95a5a6',
        }
        cor = cores.get(obj.status, '#777')
        return format_html('<span class="seos-status-badge" style="background:{};">{}</span>', cor, obj.get_status_display())

    status_colorido.short_description = 'Status'
    status_colorido.admin_order_field = 'status'

    def cliente_formatado(self, obj):
        return obj.cliente_usuario.nome_completo if obj.cliente_usuario else obj.cliente_nome_exibicao

    cliente_formatado.short_description = 'Cliente'
    cliente_formatado.admin_order_field = 'cliente_nome_exibicao'

    def numero_serie_formatado(self, obj):
        if obj.numero_serie:
            return format_html('<span class="seos-serial-badge">{}</span>', obj.numero_serie)
        return format_html('<span class="seos-muted">{}</span>', 'Não informado')

    numero_serie_formatado.short_description = 'Nº Cliente'
    numero_serie_formatado.admin_order_field = 'numero_serie'

    def botoes_acao(self, obj):
        url_ver = reverse('admin:ordens_ordemservico_change', args=[obj.pk]) + '?modo=visualizar'
        url_editar = reverse('admin:ordens_ordemservico_change', args=[obj.pk])
        url_imprimir_a4 = reverse('admin:ordemservico_pdf', args=[obj.pk])
        url_etiqueta = reverse('admin:ordemservico_etiqueta', args=[obj.pk])
        return format_html(
            '<div class="seos-action-buttons">'
            '<a class="seos-btn seos-btn-secondary" href="{}" title="Visualizar sem editar"><i class="far fa-eye"></i> Ver</a>'
            '<a class="seos-btn seos-btn-primary" href="{}" title="Editar ordem de serviço"><i class="fas fa-edit"></i> Editar</a>'
            '<a class="seos-btn seos-btn-info" href="{}" target="_blank" rel="noopener" title="Imprimir OS em A4"><i class="far fa-file-alt"></i> OS</a>'
            '<a class="seos-btn seos-btn-warning" href="{}" target="_blank" rel="noopener" title="Imprimir etiqueta"><i class="fas fa-tag"></i> Etiqueta</a>'
            '</div>',
            url_ver,
            url_editar,
            url_imprimir_a4,
            url_etiqueta,
        )

    botoes_acao.short_description = 'Ações'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('cliente-rapido/', self.admin_site.admin_view(self.criar_cliente_rapido), name='ordemservico_cliente_rapido'),
            path('<int:object_id>/imprimir/a4/', self.admin_site.admin_view(self.imprimir_os_a4), name='ordemservico_pdf'),
            path('<int:object_id>/imprimir/etiqueta/', self.admin_site.admin_view(self.imprimir_etiqueta), name='ordemservico_etiqueta'),
        ]
        return custom_urls + urls

    def criar_cliente_rapido(self, request):
        if not self.has_add_permission(request):
            return JsonResponse({'ok': False, 'erro': 'Você não tem permissão para criar clientes.'}, status=403)

        if request.method != 'POST':
            return JsonResponse({'ok': False, 'erro': 'Método inválido.'}, status=405)

        cpf = request.POST.get('cpf', '')
        nome_completo = (request.POST.get('nome_completo') or '').strip()
        telefone = (request.POST.get('telefone') or '').strip()
        senha = request.POST.get('password') or ''

        try:
            cpf_limpo = validar_cpf(cpf)
        except Exception as exc:
            return JsonResponse({'ok': False, 'erro': str(exc)}, status=400)

        if not nome_completo:
            return JsonResponse({'ok': False, 'erro': 'Informe o nome completo do cliente.'}, status=400)

        if not telefone:
            return JsonResponse({'ok': False, 'erro': 'Informe o telefone do cliente.'}, status=400)

        if Usuario.objects.filter(cpf=cpf_limpo).exists():
            return JsonResponse({'ok': False, 'erro': 'Já existe um cliente cadastrado com esse CPF.'}, status=400)

        cliente = Usuario(
            cpf=cpf_limpo,
            username=cpf_limpo,
            nome_completo=nome_completo,
            telefone=telefone,
        )

        if senha:
            cliente.set_password(senha)
        else:
            senha_gerada = gerar_senha_padrao(nome_completo)
            cliente.set_password(senha_gerada)
            cliente.senha_temporaria = senha_gerada

        cliente.save()

        registrar_auditoria(
            request,
            tipo='usuario',
            acao='criado',
            descricao=f"Cliente criado pelo cadastro rápido da OS: {cliente.nome_completo or cliente.cpf}.",
            objeto=cliente,
            referencia=f"Usuário #{cliente.pk}",
        )

        return JsonResponse({
            'ok': True,
            'id': cliente.pk,
            'label': cliente.nome_completo or cliente.cpf,
            'cpf': cliente.cpf,
            'telefone': cliente.telefone,
            'numero_serie_cliente': cliente.numero_serie_cliente,
            'senha_temporaria': getattr(cliente, 'senha_temporaria', ''),
        })

    def imprimir_os_a4(self, request, object_id):
        ordem = get_object_or_404(OrdemServico.objects.select_related('cliente_usuario', 'tecnico_responsavel').prefetch_related('pecas_utilizadas__peca', 'pecas_utilizadas__usuario_responsavel'), pk=object_id)
        registrar_auditoria(
            request,
            tipo='ordem_servico',
            acao='impressao',
            descricao=f"Impressão A4 aberta para a OS #{ordem.pk}.",
            objeto=ordem,
            referencia=f"OS #{ordem.pk}",
        )
        return render(request, 'ordens/impressao_a4.html', {'os': ordem})

    def imprimir_etiqueta(self, request, object_id):
        ordem = get_object_or_404(OrdemServico.objects.select_related('cliente_usuario', 'tecnico_responsavel').prefetch_related('pecas_utilizadas__peca', 'pecas_utilizadas__usuario_responsavel'), pk=object_id)
        registrar_auditoria(
            request,
            tipo='ordem_servico',
            acao='impressao',
            descricao=f"Etiqueta aberta para a OS #{ordem.pk}.",
            objeto=ordem,
            referencia=f"OS #{ordem.pk}",
        )
        return render(request, 'ordens/impressao_etiqueta.html', {'os': ordem})


class HistoricoOrdemServicoAdmin(admin.ModelAdmin):
    actions = None
    def has_module_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return eh_tecnico_admin(request.user) or eh_atendente(request.user)

    list_display = ('ordem_servico_link', 'data_alteracao_formatada', 'status_badge', 'descricao_alteracao')
    list_filter = ('status_momento', 'data_alteracao')
    search_fields = ('ordem_servico__id', 'descricao_alteracao')
    ordering = ('-data_alteracao',)
    list_per_page = 30

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def ordem_servico_link(self, obj):
        url = reverse('admin:ordens_ordemservico_change', args=[obj.ordem_servico.pk])
        return format_html('<a class="seos-link-strong" href="{}">OS #{}</a>', url, obj.ordem_servico.id)

    ordem_servico_link.short_description = 'Ordem de Serviço'

    def data_alteracao_formatada(self, obj):
        return timezone.localtime(obj.data_alteracao).strftime('%d/%m/%Y às %H:%M:%S')

    data_alteracao_formatada.short_description = 'Data da Alteração'
    data_alteracao_formatada.admin_order_field = 'data_alteracao'

    def status_badge(self, obj):
        cores = {
            'aberto': '#3498db',
            'aguardando_pecas': '#e67e22',
            'consertando': '#f1c40f',
            'finalizado': '#2ecc71',
            'entregue': '#95a5a6',
        }
        cor = cores.get(obj.status_momento, '#777')
        return format_html('<span class="seos-status-badge seos-status-small" style="background:{};">{}</span>', cor, obj.get_status_momento_display())

    status_badge.short_description = 'Status'




class PecaAdmin(admin.ModelAdmin):
    actions = None
    def has_module_permission(self, request):
        return pode_gerir_estoque(request.user)

    def has_view_permission(self, request, obj=None):
        return pode_gerir_estoque(request.user)

    def has_add_permission(self, request):
        return pode_gerir_estoque(request.user)

    def has_change_permission(self, request, obj=None):
        return pode_gerir_estoque(request.user)

    def has_delete_permission(self, request, obj=None):
        return eh_administrador_sistema(request.user)

    change_list_template = 'admin/ordens/peca/change_list.html'
    change_form_template = 'admin/ordens/peca/change_form.html'
    list_display = (
        'codigo_formatado',
        'nome',
        'quantidade_formatada',
        'estoque_minimo',
        'valor_unitario_formatado',
        'preco_varejo_formatado',
        'valor_total_formatado',
        'status_estoque',
        'ativo',
        'botoes_estoque',
    )
    list_filter = ('ativo',)
    search_fields = ('nome', 'codigo', 'descricao')
    ordering = ('nome',)
    list_per_page = 30
    readonly_fields = ('data_criacao', 'data_atualizacao', 'valor_total_formatado')
    fieldsets = (
        ('Identificação da peça', {
            'fields': ('nome', 'codigo', 'descricao', 'ativo'),
        }),
        ('Controle de estoque', {
            'fields': ('quantidade', 'estoque_minimo', 'valor_unitario', 'preco_varejo', 'valor_total_formatado'),
        }),
        ('Controle interno', {
            'classes': ('collapse',),
            'fields': ('data_criacao', 'data_atualizacao'),
        }),
    )

    def codigo_formatado(self, obj):
        return format_html('<span class="seos-stock-code">{}</span>', obj.codigo)

    codigo_formatado.short_description = 'Código'
    codigo_formatado.admin_order_field = 'codigo'

    def quantidade_formatada(self, obj):
        classe = 'seos-stock-low' if obj.estoque_baixo else 'seos-stock-ok'
        return format_html('<span class="{}">{} un.</span>', classe, obj.quantidade)

    quantidade_formatada.short_description = 'Qtd.'
    quantidade_formatada.admin_order_field = 'quantidade'

    def valor_unitario_formatado(self, obj):
        return f'R$ {obj.valor_unitario}'

    valor_unitario_formatado.short_description = 'Valor unitário'
    valor_unitario_formatado.admin_order_field = 'valor_unitario'

    def preco_varejo_formatado(self, obj):
        return f'R$ {obj.preco_varejo}'

    preco_varejo_formatado.short_description = 'Preço varejo'
    preco_varejo_formatado.admin_order_field = 'preco_varejo'

    def valor_total_formatado(self, obj):
        return f'R$ {obj.valor_total_em_estoque}'

    valor_total_formatado.short_description = 'Valor total em estoque'

    def status_estoque(self, obj):
        if obj.estoque_baixo:
            return format_html('<span class="seos-stock-badge seos-stock-alert">{}</span>', 'Estoque baixo')
        return format_html('<span class="seos-stock-badge seos-stock-normal">{}</span>', 'OK')

    status_estoque.short_description = 'Status'

    def botoes_estoque(self, obj):
        url_entrada = reverse('admin:ordens_movimentacaoestoque_add') + f'?peca={obj.pk}&tipo=entrada'
        url_saida = reverse('admin:ordens_movimentacaoestoque_add') + f'?peca={obj.pk}&tipo=saida'
        url_editar = reverse('admin:ordens_peca_change', args=[obj.pk])
        return format_html(
            '<div class="seos-stock-action-group">'
            '<a class="seos-btn seos-btn-success" href="{}">+ Qtd</a>'
            '<a class="seos-btn seos-btn-warning" href="{}">− Qtd</a>'
            '<a class="seos-btn seos-btn-info" href="{}">Editar</a>'
            '</div>',
            url_entrada,
            url_saida,
            url_editar,
        )

    botoes_estoque.short_description = 'Ações'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        registrar_auditoria(
            request,
            tipo='sistema',
            acao='alterado' if change else 'criado',
            descricao=f"Peça {'alterada' if change else 'criada'}: {obj.nome} ({obj.codigo}).",
            objeto=obj,
            referencia=f"Peça #{obj.pk}",
        )

    def delete_model(self, request, obj):
        registrar_auditoria(
            request,
            tipo='sistema',
            acao='excluido',
            descricao=f"Peça excluída: {obj.nome} ({obj.codigo}).",
            objeto=obj,
            referencia=f"Peça #{obj.pk}",
        )
        super().delete_model(request, obj)


class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    actions = None
    change_list_template = 'admin/ordens/movimentacaoestoque/change_list.html'
    def has_module_permission(self, request):
        return pode_gerir_estoque(request.user)

    def has_view_permission(self, request, obj=None):
        return pode_gerir_estoque(request.user)

    def has_add_permission(self, request):
        return pode_gerir_estoque(request.user)

    change_form_template = 'admin/ordens/movimentacaoestoque/change_form.html'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ('peca', 'ordem_servico', 'usuario_responsavel'):
            kwargs['widget'] = forms.Select
        form_field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name in ('peca', 'ordem_servico', 'usuario_responsavel'):
            widget = form_field.widget
            for attr in ('can_add_related', 'can_change_related', 'can_delete_related', 'can_view_related'):
                if hasattr(widget, attr):
                    setattr(widget, attr, False)
        return form_field

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        form_field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in ('peca', 'ordem_servico', 'usuario_responsavel') and form_field is not None:
            widget = form_field.widget
            for attr in ('can_add_related', 'can_change_related', 'can_delete_related', 'can_view_related'):
                if hasattr(widget, attr):
                    setattr(widget, attr, False)
            inner_widget = getattr(widget, 'widget', None)
            if inner_widget is not None:
                for attr in ('can_add_related', 'can_change_related', 'can_delete_related', 'can_view_related'):
                    if hasattr(inner_widget, attr):
                        setattr(inner_widget, attr, False)
        return form_field

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if request.GET.get('peca'):
            initial['peca'] = request.GET.get('peca')
        if request.GET.get('tipo') in ('entrada', 'saida', 'ajuste'):
            initial['tipo'] = request.GET.get('tipo')
        return initial

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if request.GET.get('tipo') == 'saida':
            extra_context['seos_warning_message'] = 'Atenção: esta ação diminui o estoque. Confira peça e quantidade antes de salvar.'
        elif request.GET.get('tipo') == 'entrada':
            extra_context['seos_warning_message'] = 'Entrada de estoque: confira a quantidade antes de salvar.'
        return super().add_view(request, form_url, extra_context=extra_context)

    list_display = (
        'data_movimentacao_formatada',
        'tipo_badge',
        'peca_link',
        'quantidade',
        'ordem_servico_link',
        'usuario_responsavel',
        'observacao_curta',
    )
    list_filter = ('tipo', 'data_movimentacao', 'peca')
    search_fields = ('peca__nome', 'peca__codigo', 'observacao', 'ordem_servico__id')
    ordering = ('-data_movimentacao',)
    list_per_page = 40
    readonly_fields = ('data_movimentacao', 'usuario_responsavel')
    fieldsets = (
        ('Movimentação', {
            'fields': ('peca', 'tipo', 'quantidade', 'ordem_servico'),
        }),
        ('Observação', {
            'fields': ('observacao',),
        }),
        ('Controle interno', {
            'classes': ('collapse',),
            'fields': ('usuario_responsavel', 'data_movimentacao'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.usuario_responsavel and request.user.is_authenticated:
            obj.usuario_responsavel = request.user

        with transaction.atomic():
            super().save_model(request, obj, form, change)

        detalhe_os = f" vinculada à OS #{obj.ordem_servico_id}" if obj.ordem_servico_id else ""
        registrar_auditoria(
            request,
            tipo='sistema',
            acao='criado' if not change else 'alterado',
            descricao=f"Movimentação de estoque: {obj.get_tipo_display()} de {obj.quantidade} un. em {obj.peca.nome}{detalhe_os}.",
            objeto=obj,
            referencia=f"Mov. Estoque #{obj.pk}",
        )

        if obj.ordem_servico_id:
            HistoricoOrdemServico.objects.create(
                ordem_servico=obj.ordem_servico,
                status_momento=obj.ordem_servico.status,
                descricao_alteracao=f"Estoque: {obj.get_tipo_display()} de {obj.quantidade} un. da peça {obj.peca.nome} ({obj.peca.codigo}).",
            )

    def has_change_permission(self, request, obj=None):
        # Evita alterar movimentações antigas e aplicar estoque duas vezes.
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Movimentação é registro de controle. Não remove para não bagunçar o estoque.
        return False

    def data_movimentacao_formatada(self, obj):
        return timezone.localtime(obj.data_movimentacao).strftime('%d/%m/%Y às %H:%M:%S')

    data_movimentacao_formatada.short_description = 'Data'
    data_movimentacao_formatada.admin_order_field = 'data_movimentacao'

    def tipo_badge(self, obj):
        cores = {
            'entrada': '#2ecc71',
            'saida': '#e74c3c',
            'ajuste': '#f1c40f',
        }
        cor = cores.get(obj.tipo, '#777')
        return format_html('<span class="seos-stock-move" style="background:{};">{}</span>', cor, obj.get_tipo_display())

    tipo_badge.short_description = 'Tipo'
    tipo_badge.admin_order_field = 'tipo'

    def peca_link(self, obj):
        url = reverse('admin:ordens_peca_change', args=[obj.peca.pk])
        return format_html('<a class="seos-link-strong" href="{}">{} ({})</a>', url, obj.peca.nome, obj.peca.codigo)

    peca_link.short_description = 'Peça'

    def ordem_servico_link(self, obj):
        if not obj.ordem_servico:
            return 'Sem OS'
        url = reverse('admin:ordens_ordemservico_change', args=[obj.ordem_servico.pk])
        return format_html('<a class="seos-link-strong" href="{}">OS #{}</a>', url, obj.ordem_servico.id)

    ordem_servico_link.short_description = 'OS vinculada'

    def observacao_curta(self, obj):
        texto = obj.observacao or ''
        return texto if len(texto) <= 70 else texto[:67] + '...'

    observacao_curta.short_description = 'Observação'


class RegistroSistemaAdmin(admin.ModelAdmin):
    actions = None
    change_list_template = 'admin/ordens/registrosistema/change_list.html'
    change_form_template = 'admin/ordens/registrosistema/change_form.html'
    def has_module_permission(self, request):
        return eh_administrador_sistema(request.user)

    def has_view_permission(self, request, obj=None):
        return eh_administrador_sistema(request.user)

    list_display = ('data_registro_formatada', 'tipo_badge', 'acao_badge', 'objeto_referencia', 'usuario_formatado', 'descricao_curta')
    list_filter = ('tipo', 'acao', 'data_registro', 'usuario_responsavel')
    search_fields = (
        'descricao',
        'objeto_referencia',
        'usuario_responsavel__nome_completo',
        'usuario_responsavel__cpf',
    )
    ordering = ('-data_registro',)
    list_per_page = 40
    readonly_fields = (
        'tipo',
        'acao',
        'descricao',
        'usuario_responsavel',
        'objeto_id',
        'objeto_referencia',
        'data_registro_formatada',
    )
    fieldsets = (
        ('Resumo do Registro', {
            'fields': ('tipo', 'acao', 'data_registro_formatada', 'usuario_responsavel'),
        }),
        ('Objeto relacionado', {
            'fields': ('objeto_referencia', 'objeto_id'),
        }),
        ('Descrição', {
            'fields': ('descricao',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Permite abrir para consultar, mas os campos ficam somente leitura.
        return eh_administrador_sistema(request.user)

    def has_delete_permission(self, request, obj=None):
        return False

    def data_registro_formatada(self, obj):
        if not obj.data_registro:
            return 'Não informado'
        return timezone.localtime(obj.data_registro).strftime('%d/%m/%Y às %H:%M:%S')

    data_registro_formatada.short_description = 'Data'
    data_registro_formatada.admin_order_field = 'data_registro'

    def tipo_badge(self, obj):
        cores = {
            'usuario': '#8e44ad',
            'ordem_servico': '#3498db',
            'historico': '#16a085',
            'sistema': '#7f8c8d',
        }
        cor = cores.get(obj.tipo, '#777')
        return format_html('<span class="seos-audit-badge" style="background:{};">{}</span>', cor, obj.get_tipo_display())

    tipo_badge.short_description = 'Tipo'
    tipo_badge.admin_order_field = 'tipo'

    def acao_badge(self, obj):
        cores = {
            'criado': '#2ecc71',
            'alterado': '#f1c40f',
            'excluido': '#e74c3c',
            'visualizado': '#9b59b6',
            'impressao': '#1abc9c',
            'outro': '#95a5a6',
        }
        cor = cores.get(obj.acao, '#777')
        return format_html('<span class="seos-audit-badge seos-audit-action" style="background:{};">{}</span>', cor, obj.get_acao_display())

    acao_badge.short_description = 'Ação'
    acao_badge.admin_order_field = 'acao'

    def usuario_formatado(self, obj):
        if not obj.usuario_responsavel:
            return 'Sistema'
        return obj.usuario_responsavel.nome_completo or obj.usuario_responsavel.cpf

    usuario_formatado.short_description = 'Responsável'
    usuario_formatado.admin_order_field = 'usuario_responsavel__nome_completo'

    def descricao_curta(self, obj):
        texto = obj.descricao or ''
        return texto if len(texto) <= 95 else texto[:92] + '...'

    descricao_curta.short_description = 'Descrição'


admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(OrdemServico, OrdemServicoAdmin)
admin.site.register(Peca, PecaAdmin)
admin.site.register(MovimentacaoEstoque, MovimentacaoEstoqueAdmin)
admin.site.register(RegistroSistema, RegistroSistemaAdmin)


# Dashboard customizada do SEOS.
def seos_admin_index(self, request, extra_context=None):
    hoje = timezone.localdate()

    ordens_qs = OrdemServico.objects.select_related('cliente_usuario', 'tecnico_responsavel')
    contagem_status = dict(ordens_qs.values('status').annotate(total=Count('id')).values_list('status', 'total'))
    ordens_ativas = ordens_qs.exclude(status='entregue')
    pecas_baixas_qs = Peca.objects.filter(ativo=True, quantidade__lte=F('estoque_minimo')).order_by('quantidade', 'nome')
    os_sem_tecnico_qs = ordens_ativas.filter(tecnico_responsavel__isnull=True)

    pode_ordens = pode_gerir_ordens(request.user)
    pode_clientes = eh_administrador_sistema(request.user) or eh_atendente(request.user)
    pode_estoque = pode_gerir_estoque(request.user)
    pode_auditoria = eh_administrador_sistema(request.user)

    resumo_cards = [
        {
            'titulo': 'Em aberto',
            'valor': contagem_status.get('aberto', 0),
            'descricao': 'ordens aguardando início',
            'icone': '🟦',
            'classe': 'info',
            'url': reverse('admin:ordens_ordemservico_changelist') + '?status__exact=aberto',
        },
        {
            'titulo': 'Aguardando peças',
            'valor': contagem_status.get('aguardando_pecas', 0),
            'descricao': 'serviços parados por peça',
            'icone': '📦',
            'classe': 'warning',
            'url': reverse('admin:ordens_ordemservico_changelist') + '?status__exact=aguardando_pecas',
        },
        {
            'titulo': 'Consertando',
            'valor': contagem_status.get('consertando', 0),
            'descricao': 'ordens em execução',
            'icone': '🛠️',
            'classe': 'primary',
            'url': reverse('admin:ordens_ordemservico_changelist') + '?status__exact=consertando',
        },
        {
            'titulo': 'Finalizadas',
            'valor': contagem_status.get('finalizado', 0),
            'descricao': 'prontas para entrega',
            'icone': '✅',
            'classe': 'success',
            'url': reverse('admin:ordens_ordemservico_changelist') + '?status__exact=finalizado',
        },
        {
            'titulo': 'Estoque baixo',
            'valor': pecas_baixas_qs.count(),
            'descricao': 'peças abaixo do mínimo',
            'icone': '⚠️',
            'classe': 'danger',
            'url': reverse('admin:ordens_peca_changelist'),
        },
    ]

    ultimas_ordens = []
    for ordem in ordens_qs.order_by('-data_criacao')[:6]:
        ultimas_ordens.append({
            'id': ordem.pk,
            'cliente': ordem.cliente_usuario.nome_completo if ordem.cliente_usuario else ordem.cliente_nome_exibicao,
            'equipamento': ordem.equipamento,
            'status': ordem.get_status_display(),
            'status_key': ordem.status,
            'data': ordem.data_criacao,
            'url': reverse('admin:ordens_ordemservico_change', args=[ordem.pk]),
        })

    alertas = []

    estoque_baixo_count = pecas_baixas_qs.count()
    if estoque_baixo_count:
        alertas.append({
            'tipo': 'danger',
            'icone': '⚠️',
            'titulo': f'{estoque_baixo_count} peça(s) com estoque baixo',
            'descricao': 'Verifique reposição antes de abrir novas saídas.',
            'url': reverse('admin:ordens_peca_changelist'),
            'acao': 'Ver estoque',
        })

    aguardando_pecas = contagem_status.get('aguardando_pecas', 0)
    if aguardando_pecas:
        alertas.append({
            'tipo': 'warning',
            'icone': '📦',
            'titulo': f'{aguardando_pecas} OS aguardando peças',
            'descricao': 'Priorize compra, entrada ou substituição de peças.',
            'url': reverse('admin:ordens_ordemservico_changelist') + '?status__exact=aguardando_pecas',
            'acao': 'Ver ordens',
        })

    sem_tecnico = os_sem_tecnico_qs.count()
    if sem_tecnico:
        alertas.append({
            'tipo': 'info',
            'icone': '👤',
            'titulo': f'{sem_tecnico} OS sem técnico responsável',
            'descricao': 'Distribua as ordens para melhorar o acompanhamento.',
            'url': reverse('admin:ordens_ordemservico_changelist') + '?tecnico_responsavel__isnull=True',
            'acao': 'Atribuir',
        })

    entregas_hoje = ordens_ativas.filter(data_entrega_prevista=hoje).count()
    if entregas_hoje:
        alertas.append({
            'tipo': 'success',
            'icone': '📅',
            'titulo': f'{entregas_hoje} entrega(s) previstas para hoje',
            'descricao': 'Confira status e comunique o cliente.',
            'url': reverse('admin:ordens_ordemservico_changelist') + f'?data_entrega_prevista__exact={hoje.isoformat()}',
            'acao': 'Conferir',
        })

    if not pode_estoque:
        resumo_cards = [card for card in resumo_cards if card['titulo'] != 'Estoque baixo']
        alertas = [alerta for alerta in alertas if 'estoque' not in alerta['titulo'].lower()]

    if not pode_ordens:
        resumo_cards = [card for card in resumo_cards if card['titulo'] == 'Estoque baixo']
        ultimas_ordens = []
        alertas = [alerta for alerta in alertas if 'estoque' in alerta['titulo'].lower()]

    if not alertas:
        alertas.append({
            'tipo': 'success',
            'icone': '✅',
            'titulo': 'Nenhum alerta crítico agora',
            'descricao': 'Não há pendências urgentes para o seu cargo.',
            'url': reverse('admin:index'),
            'acao': 'OK',
        })

    context = {
        **self.each_context(request),
        'title': self.index_title,
        'app_list': self.get_app_list(request),
        'resumo_cards': resumo_cards,
        'ultimas_ordens': ultimas_ordens,
        'alertas_dashboard': alertas,
        'pecas_baixas_dashboard': list(pecas_baixas_qs[:5]),
        'pode_ordens': pode_ordens,
        'pode_clientes': pode_clientes,
        'pode_estoque': pode_estoque,
        'pode_auditoria': pode_auditoria,
        'cargo_atual': 'Administrador do sistema' if request.user.is_superuser else (request.user.get_cargo_sistema_display() if getattr(request.user, 'cargo_sistema', '') else 'Cliente'),
        **(extra_context or {}),
    }

    request.current_app = self.name
    return TemplateResponse(request, self.index_template, context)


admin.site.index = seos_admin_index.__get__(admin.site, admin.site.__class__)
admin.site.index_template = 'admin/seos_index.html'
