from datetime import date

from django.db.models import Count

from .models import OrdemServico


def consultar_ordens_relatorio(params):
    queryset = OrdemServico.objects.select_related('tecnico_responsavel').order_by('-data_entrada', '-id')
    status = (params.get('status') or '').strip()
    if status in dict(OrdemServico.STATUS_CHOICES):
        queryset = queryset.filter(status=status)
    tecnico = (params.get('tecnico') or '').strip()
    if tecnico.isdigit():
        queryset = queryset.filter(tecnico_responsavel_id=int(tecnico))
    for chave, lookup in (('inicio', 'data_entrada__date__gte'), ('fim', 'data_entrada__date__lte')):
        valor = (params.get(chave) or '').strip()
        try:
            if valor:
                queryset = queryset.filter(**{lookup: date.fromisoformat(valor)})
        except ValueError:
            continue
    return queryset


def resumo_relatorio(queryset):
    return {
        'total': queryset.count(),
        'por_status': queryset.values('status').annotate(total=Count('id')).order_by('status'),
    }
