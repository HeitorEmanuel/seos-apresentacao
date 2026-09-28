"""Serviços de notificação interna do SEOS."""

from django.db.models import Q
from django.utils import timezone

from .models import Notificacao, Usuario


def criar_notificacao(destinatario, tipo, mensagem, ordem=None, peca=None):
    """Cria uma notificação interna, sem repetir alerta aberto de estoque."""
    if not destinatario:
        return None

    if tipo == Notificacao.TIPO_ESTOQUE_BAIXO and peca:
        if Notificacao.objects.filter(
            destinatario=destinatario,
            tipo=tipo,
            peca=peca,
            resolvida_em__isnull=True,
        ).exists():
            return None

    return Notificacao.objects.create(
        destinatario=destinatario,
        tipo=tipo,
        mensagem=mensagem,
        ordem_servico=ordem,
        peca=peca,
    )


def atualizar_alerta_estoque(peca):
    """Abre alertas para estoque baixo e encerra o ciclo quando há reposição."""
    alertas_abertos = Notificacao.objects.filter(
        tipo=Notificacao.TIPO_ESTOQUE_BAIXO,
        peca=peca,
        resolvida_em__isnull=True,
    )
    if not peca.estoque_baixo:
        alertas_abertos.update(resolvida_em=timezone.now())
        return

    destinatarios = Usuario.objects.filter(
        Q(cargo_sistema__in=(Usuario.CARGO_TECNICO_ADMIN, Usuario.CARGO_ALMOXARIFADO))
        | Q(is_superuser=True),
    ).distinct()
    for destinatario in destinatarios:
        criar_notificacao(
            destinatario,
            Notificacao.TIPO_ESTOQUE_BAIXO,
            f'Estoque baixo: {peca.nome} ({peca.quantidade} un.).',
            peca=peca,
        )
