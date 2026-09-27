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


def ordem_acessivel_ou_404(user, ordem_id):
    if not user.is_authenticated:
        raise Http404('Ordem de serviço não encontrada.')
    queryset = OrdemServico.objects.all()
    if user.is_superuser or user.cargo_sistema == user.CARGO_TECNICO_ADMIN:
        try:
            return queryset.get(pk=ordem_id)
        except OrdemServico.DoesNotExist as exc:
            raise Http404('Ordem de serviço não encontrada.') from exc
    if user.eh_tecnico_operacional():
        queryset = queryset.filter(tecnico_responsavel=user)
    else:
        queryset = queryset.filter(cliente_usuario=user)
    try:
        return queryset.get(pk=ordem_id)
    except OrdemServico.DoesNotExist as exc:
        raise Http404('Ordem de serviço não encontrada.') from exc
