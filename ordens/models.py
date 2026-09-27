import secrets

from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from .utils import apenas_digitos


def gerar_senha_padrao(nome_completo):
    """Gera uma senha temporária aleatória para comunicação única ao usuário."""
    return secrets.token_urlsafe(18)


def senha_ja_criptografada(valor):
    if not valor:
        return False
    try:
        identify_hasher(valor)
        return True
    except ValueError:
        return False


class UsuarioManager(BaseUserManager):
    def create_user(self, cpf, password=None, **extra_fields):
        if not cpf:
            raise ValueError('O CPF é obrigatório')

        cpf_limpo = apenas_digitos(cpf)
        user = self.model(cpf=cpf_limpo, username=cpf_limpo, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, cpf, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário precisa ter is_superuser=True.')

        return self.create_user(cpf, password, **extra_fields)


class Usuario(AbstractUser):
    CARGO_ATENDENTE = 'atendente'
    CARGO_TECNICO_ADMIN = 'tecnico_admin'
    CARGO_ALMOXARIFADO = 'almoxarifado'

    TEMA_ESCURO = 'dark'
    TEMA_CLARO = 'light'
    TEMA_CHOICES = [
        (TEMA_ESCURO, 'Modo escuro'),
        (TEMA_CLARO, 'Modo claro'),
    ]

    CARGO_CHOICES = [
        ('', 'Cliente comum / sem cargo'),
        (CARGO_ATENDENTE, 'Atendente'),
        (CARGO_TECNICO_ADMIN, 'Técnico/Admin'),
        (CARGO_ALMOXARIFADO, 'Almoxarifado'),
    ]

    nome_completo = models.CharField(max_length=255, verbose_name='Nome Completo')
    cpf = models.CharField(max_length=14, unique=True, verbose_name='CPF')
    telefone = models.CharField(max_length=15, verbose_name='Telefone')
    endereco = models.CharField(max_length=255, blank=True, null=True, verbose_name='Endereço')
    numero_serie_cliente = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Número de Série do Cliente',
        help_text='Código automático usado para identificar o cliente/equipamento nas OS e impressões.',
    )
    cargo_sistema = models.CharField(
        max_length=20,
        choices=CARGO_CHOICES,
        blank=True,
        default='',
        verbose_name='Cargo no Sistema',
        help_text='Use somente para equipe interna. Cliente comum deve ficar sem cargo.',
    )
    tema_preferido = models.CharField(
        max_length=10,
        choices=TEMA_CHOICES,
        default=TEMA_ESCURO,
        verbose_name='Tema preferido',
        help_text='Define se este usuário/cliente verá o sistema em modo claro ou escuro.',
    )
    login_tentativas_falhas = models.PositiveSmallIntegerField(default=0, verbose_name='Tentativas de login falhas')
    login_bloqueado_ate = models.DateTimeField(blank=True, null=True, verbose_name='Login bloqueado até')
    senha_alterada_em = models.DateTimeField(blank=True, null=True, verbose_name='Senha alterada em')

    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['nome_completo', 'telefone']

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def save(self, *args, **kwargs):
        if self.tema_preferido not in {self.TEMA_CLARO, self.TEMA_ESCURO}:
            self.tema_preferido = self.TEMA_ESCURO

        if self.cpf:
            self.cpf = apenas_digitos(self.cpf)

        nome = str(self.nome_completo or '').strip()
        if nome:
            nomes = nome.split(' ', 1)
            self.first_name = nomes[0].capitalize()
            self.last_name = nomes[1] if len(nomes) > 1 else ''

        if not self.username or self.username != self.cpf:
            self.username = self.cpf

        # Cliente comum fica sem acesso ao admin. Cargos internos entram no painel.
        if self.cargo_sistema:
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False

        senha_atual = self.password or ''
        if not self.pk and not senha_ja_criptografada(senha_atual):
            self.senha_temporaria = gerar_senha_padrao(self.nome_completo)
            self.set_password(self.senha_temporaria)

        precisa_gerar_serie = not self.numero_serie_cliente
        super().save(*args, **kwargs)

        if precisa_gerar_serie and self.pk:
            self.numero_serie_cliente = f'CLI-{self.pk:06d}'
            Usuario.objects.filter(pk=self.pk).update(numero_serie_cliente=self.numero_serie_cliente)


    def eh_somente_cliente(self):
        return bool(not self.is_superuser and not self.is_staff and not self.cargo_sistema)

    def login_esta_bloqueado(self):
        return bool(self.login_bloqueado_ate and self.login_bloqueado_ate > timezone.now())

    def limpar_bloqueio_login(self):
        if self.login_tentativas_falhas or self.login_bloqueado_ate:
            self.login_tentativas_falhas = 0
            self.login_bloqueado_ate = None
            self.save(update_fields=['login_tentativas_falhas', 'login_bloqueado_ate'])

    def __str__(self):
        return self.nome_completo or self.cpf


Usuario._meta.get_field('is_staff').verbose_name = 'Membro da Equipe'
Usuario._meta.get_field('is_superuser').verbose_name = 'Status de Superusuário'
Usuario._meta.get_field('is_active').verbose_name = 'Ativo'


class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ('aberto', 'Em Aberto'),
        ('aguardando_pecas', 'Aguardando Peças'),
        ('consertando', 'Consertando'),
        ('finalizado', 'Finalizado'),
        ('entregue', 'Entregue'),
    ]

    cliente_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='minhas_ordens',
        null=True,
        blank=True,
        verbose_name='Cliente',
    )
    cliente_nome_exibicao = models.CharField(max_length=100, verbose_name='Nome do Cliente (Exibição)')
    equipamento = models.CharField(max_length=100, verbose_name='Equipamento')
    numero_serie = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Número de Série do Cliente',
        help_text='Gerado automaticamente a partir do cliente vinculado para facilitar a identificação pelo técnico.',
    )
    descricao_problema = models.TextField(verbose_name='Descrição do Problema')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='aberto',
        verbose_name='Status',
    )
    tecnico_responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='servicos_atribuidos',
        limit_choices_to={'is_staff': True},
        verbose_name='Técnico Responsável',
    )
    data_entrada = models.DateTimeField(default=timezone.now, verbose_name='Data de Entrada do Produto')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    avaliacao_tecnico = models.TextField(verbose_name='Avaliação do Técnico', blank=True, null=True)
    servico_planejado = models.TextField(verbose_name='Serviço que será feito', blank=True, null=True)
    data_entrega_prevista = models.DateField(verbose_name='Possível Data de Entrega', blank=True, null=True)
    valor_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Valor Estimado (R$)',
    )

    class Meta:
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'

    def save(self, *args, **kwargs):
        criando = self.pk is None
        alteracoes = []

        if isinstance(self.data_entrada, str):
            data_entrada_convertida = parse_datetime(self.data_entrada)
            if data_entrada_convertida and timezone.is_naive(data_entrada_convertida):
                data_entrada_convertida = timezone.make_aware(data_entrada_convertida, timezone.get_current_timezone())
            if data_entrada_convertida:
                self.data_entrada = data_entrada_convertida

        if isinstance(self.data_entrega_prevista, str):
            data_entrega_convertida = parse_date(self.data_entrega_prevista)
            if data_entrega_convertida:
                self.data_entrega_prevista = data_entrega_convertida

        if self.cliente_usuario:
            if not self.cliente_usuario.numero_serie_cliente:
                self.cliente_usuario.save()
            self.numero_serie = self.cliente_usuario.numero_serie_cliente

        if self.numero_serie:
            self.numero_serie = str(self.numero_serie).strip().upper()

        if self.cliente_usuario and not self.cliente_nome_exibicao:
            self.cliente_nome_exibicao = self.cliente_usuario.nome_completo

        if not criando:
            os_antiga = OrdemServico.objects.filter(pk=self.pk).first()
            if os_antiga:
                if os_antiga.status != self.status:
                    alteracoes.append(
                        f"Status alterado de '{os_antiga.get_status_display()}' para '{self.get_status_display()}'."
                    )
                if os_antiga.tecnico_responsavel != self.tecnico_responsavel:
                    nome_antigo = os_antiga.tecnico_responsavel.nome_completo if os_antiga.tecnico_responsavel else 'Nenhum'
                    nome_novo = self.tecnico_responsavel.nome_completo if self.tecnico_responsavel else 'Nenhum'
                    alteracoes.append(f"Técnico alterado de '{nome_antigo}' para '{nome_novo}'.")
                if os_antiga.numero_serie != self.numero_serie:
                    serie_antiga = os_antiga.numero_serie or 'Não informado'
                    serie_nova = self.numero_serie or 'Não informado'
                    alteracoes.append(f"Número de série do cliente alterado de '{serie_antiga}' para '{serie_nova}'.")
                if os_antiga.data_entrega_prevista != self.data_entrega_prevista:
                    data = self.data_entrega_prevista.strftime('%d/%m/%Y') if self.data_entrega_prevista else 'A definir'
                    alteracoes.append(f'Previsão de entrega alterada para {data}.')
                if os_antiga.data_entrada != self.data_entrada:
                    data = timezone.localtime(self.data_entrada).strftime('%d/%m/%Y %H:%M') if self.data_entrada else 'Não informada'
                    alteracoes.append(f'Data de entrada alterada para {data}.')
                if os_antiga.valor_estimado != self.valor_estimado:
                    valor_antigo = f'R$ {os_antiga.valor_estimado}' if os_antiga.valor_estimado else 'Sob consulta'
                    valor_novo = f'R$ {self.valor_estimado}' if self.valor_estimado else 'Sob consulta'
                    alteracoes.append(f'Valor estimado alterado de {valor_antigo} para {valor_novo}.')

        super().save(*args, **kwargs)

        if criando:
            data_formatada = timezone.localtime(self.data_entrada).strftime('%d/%m/%Y às %H:%M')
            descricao_action = f'Ordem aberta. Produto deixado na assistência em: {data_formatada}.'
        elif alteracoes:
            descricao_action = ' '.join(alteracoes)
        else:
            return

        HistoricoOrdemServico.objects.create(
            ordem_servico=self,
            status_momento=self.status,
            descricao_alteracao=descricao_action,
        )

    def __str__(self):
        nome = self.cliente_usuario.nome_completo if self.cliente_usuario else self.cliente_nome_exibicao
        return f'OS #{self.id} - {nome} ({self.get_status_display()})'


class HistoricoOrdemServico(models.Model):
    STATUS_CHOICES = OrdemServico.STATUS_CHOICES

    ordem_servico = models.ForeignKey(
        OrdemServico,
        on_delete=models.CASCADE,
        related_name='historicos',
        verbose_name='Ordem de Serviço',
    )
    data_alteracao = models.DateTimeField(auto_now_add=True, verbose_name='Data da Movimentação')
    status_momento = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='Status no Momento',
    )
    descricao_alteracao = models.TextField(verbose_name='O que foi alterado?')

    class Meta:
        verbose_name = 'Histórico de Serviço'
        verbose_name_plural = 'Históricos de Serviço'
        ordering = ['-data_alteracao']

    def __str__(self):
        data = timezone.localtime(self.data_alteracao).strftime('%d/%m/%Y %H:%M')
        return f'Histórico OS #{self.ordem_servico.id} - {data}'



class RegistroSistema(models.Model):
    TIPO_CHOICES = [
        ('usuario', 'Usuário'),
        ('ordem_servico', 'Ordem de Serviço'),
        ('historico', 'Histórico'),
        ('sistema', 'Sistema'),
    ]

    ACAO_CHOICES = [
        ('criado', 'Criado'),
        ('alterado', 'Alterado'),
        ('excluido', 'Excluído'),
        ('visualizado', 'Visualizado'),
        ('impressao', 'Impressão'),
        ('outro', 'Outro'),
    ]

    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name='Tipo')
    acao = models.CharField(max_length=30, choices=ACAO_CHOICES, verbose_name='Ação')
    descricao = models.TextField(verbose_name='Descrição')
    usuario_responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros_sistema',
        verbose_name='Usuário responsável',
    )
    objeto_id = models.PositiveIntegerField(blank=True, null=True, verbose_name='ID do objeto')
    objeto_referencia = models.CharField(max_length=120, blank=True, verbose_name='Referência')
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name='Data do registro')

    class Meta:
        verbose_name = 'Registro do Sistema'
        verbose_name_plural = 'Auditoria do Sistema'
        ordering = ['-data_registro']

    def __str__(self):
        data = timezone.localtime(self.data_registro).strftime('%d/%m/%Y %H:%M')
        return f'{self.get_tipo_display()} - {self.get_acao_display()} - {data}'



class Peca(models.Model):
    nome = models.CharField(max_length=120, verbose_name='Nome da Peça')
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código',
        help_text='Código interno para identificar a peça no estoque.',
    )
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    quantidade = models.PositiveIntegerField(default=0, verbose_name='Quantidade em Estoque')
    estoque_minimo = models.PositiveIntegerField(default=1, verbose_name='Estoque Mínimo')
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor Unitário (R$)',
    )
    preco_varejo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Preço de Varejo (R$)',
        help_text='Preço sugerido/cobrado ao cliente, quando houver.',
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')

    class Meta:
        verbose_name = 'Peça'
        verbose_name_plural = 'Peças em Estoque'
        ordering = ['nome']

    @property
    def estoque_baixo(self):
        return self.quantidade <= self.estoque_minimo

    @property
    def valor_total_em_estoque(self):
        return self.quantidade * self.valor_unitario

    def save(self, *args, **kwargs):
        if self.codigo:
            self.codigo = str(self.codigo).strip().upper()
        if self.nome:
            self.nome = str(self.nome).strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome} ({self.codigo})'


class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste'),
    ]

    peca = models.ForeignKey(
        Peca,
        on_delete=models.CASCADE,
        related_name='movimentacoes',
        verbose_name='Peça',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    quantidade = models.PositiveIntegerField(verbose_name='Quantidade')
    ordem_servico = models.ForeignKey(
        OrdemServico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pecas_utilizadas',
        verbose_name='Ordem de Serviço',
        help_text='Opcional. Use quando a saída estiver ligada a uma OS.',
    )
    observacao = models.TextField(blank=True, null=True, verbose_name='Observação')
    usuario_responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_estoque',
        verbose_name='Usuário Responsável',
    )
    data_movimentacao = models.DateTimeField(auto_now_add=True, verbose_name='Data da Movimentação')

    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Entrada e Saída de Peças'
        ordering = ['-data_movimentacao']

    @property
    def subtotal(self):
        if not self.peca_id:
            return 0
        valor_unitario = getattr(self.peca, 'valor_unitario', 0) or 0
        return self.quantidade * valor_unitario

    def clean(self):
        super().clean()

        # Em formulários inline, a peça pode ainda não ter sido escolhida.
        # Usar self.peca diretamente nesse momento causa RelatedObjectDoesNotExist.
        if not self.peca_id or not self.quantidade:
            return

        if self.quantidade <= 0:
            raise ValidationError({'quantidade': 'Informe uma quantidade maior que zero.'})

        if self.tipo == 'saida':
            peca = Peca.objects.filter(pk=self.peca_id).first()
            if not peca:
                return

            quantidade_disponivel = peca.quantidade
            if self.pk:
                quantidade_anterior = (
                    MovimentacaoEstoque.objects.filter(pk=self.pk)
                    .values_list('quantidade', flat=True)
                    .first()
                    or 0
                )
                quantidade_disponivel += quantidade_anterior

            if self.quantidade > quantidade_disponivel:
                raise ValidationError({
                    'quantidade': f'Estoque insuficiente para {peca.nome}. Disponível: {quantidade_disponivel} un.'
                })

    def aplicar_no_estoque(self):
        if not self.peca_id:
            return

        if self.tipo == 'entrada':
            Peca.objects.filter(pk=self.peca_id).update(quantidade=F('quantidade') + self.quantidade, data_atualizacao=timezone.now())
        elif self.tipo == 'saida':
            atualizadas = Peca.objects.filter(pk=self.peca_id, quantidade__gte=self.quantidade).update(
                quantidade=F('quantidade') - self.quantidade,
                data_atualizacao=timezone.now(),
            )
            if not atualizadas:
                peca = Peca.objects.filter(pk=self.peca_id).only('nome', 'quantidade').first()
                disponivel = peca.quantidade if peca else 0
                nome = peca.nome if peca else 'a peça selecionada'
                raise ValidationError({'quantidade': f'Estoque insuficiente para {nome}. Disponível: {disponivel} un.'})
        elif self.tipo == 'ajuste':
            Peca.objects.filter(pk=self.peca_id).update(quantidade=self.quantidade, data_atualizacao=timezone.now())

        self.peca.refresh_from_db(fields=['quantidade', 'data_atualizacao'])

    def save(self, *args, **kwargs):
        criando = self.pk is None
        with transaction.atomic():
            if self.peca_id:
                Peca.objects.select_for_update().filter(pk=self.peca_id).first()
            super().save(*args, **kwargs)
            if criando:
                self.aplicar_no_estoque()

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.peca} - {self.quantidade}'
