"""Serviços de notificação interna do SEOS."""

from .models import Notificacao


def criar_notificacao(destinatario, tipo, mensagem, ordem=None, peca=None):
    """Cria uma notificação interna, sem repetir alerta aberto de estoque."""
    if not destinatario:
        return None

    if tipo == Notificacao.TIPO_ESTOQUE_BAIXO and peca:
        if Notificacao.objects.filter(
            destinatario=destinatario,
            tipo=tipo,
            peca=peca,
            lida_em__isnull=True,
        ).exists():
            return None

    return Notificacao.objects.create(
        destinatario=destinatario,
        tipo=tipo,
        mensagem=mensagem,
        ordem_servico=ordem,
        peca=peca,
    )
