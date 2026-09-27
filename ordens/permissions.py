from django.http import Http404

from .models import OrdemServico


def ordens_do_tecnico(user):
    if not user.is_authenticated or not user.eh_tecnico_operacional():
        return OrdemServico.objects.none()

    return (
        OrdemServico.objects
        .filter(tecnico_responsavel=user)
        .select_related('cliente_usuario', 'tecnico_responsavel')
        .prefetch_related('pecas_utilizadas__peca', 'historicos')
        .order_by('-data_entrada', '-id')
    )


def ordem_do_tecnico_ou_404(user, ordem_id):
    try:
        return ordens_do_tecnico(user).get(pk=ordem_id)
    except OrdemServico.DoesNotExist as exc:
        raise Http404('Ordem de serviço não encontrada.') from exc
