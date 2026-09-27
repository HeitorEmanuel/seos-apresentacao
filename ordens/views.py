from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import AtualizacaoTecnicoForm
from .models import Notificacao, OrdemServico, RegistroSistema, Usuario
from .permissions import ordem_do_tecnico_ou_404, ordens_do_tecnico
from django.utils import timezone


@login_required
def lista_ordens(request):
    ordens = (
        OrdemServico.objects
        .filter(cliente_usuario=request.user)
        .select_related('cliente_usuario', 'tecnico_responsavel')
        .prefetch_related('pecas_utilizadas__peca', 'historicos')
        .order_by('-data_entrada', '-id')
    )
    paginator = Paginator(ordens, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'lista_ordens.html', {
        'ordens': page_obj.object_list,
        'page_obj': page_obj,
        'tema_inicial': getattr(request.user, 'tema_preferido', Usuario.TEMA_ESCURO) or Usuario.TEMA_ESCURO,
    })


@login_required
def redirecionar_usuario(request):
    if request.user.eh_tecnico_operacional():
        return redirect('minha_fila')
    if request.user.is_staff:
        return redirect('/admin/')
    return redirect('lista_ordens')


@login_required
def minha_fila(request):
    if not request.user.eh_tecnico_operacional():
        raise Http404('Página não encontrada.')
    return render(request, 'ordens/minha_fila.html', {
        'ordens': ordens_do_tecnico(request.user),
        'tema_inicial': getattr(request.user, 'tema_preferido', Usuario.TEMA_ESCURO) or Usuario.TEMA_ESCURO,
    })


@login_required
def notificacoes(request):
    page_obj = Paginator(
        Notificacao.objects.filter(destinatario=request.user).select_related('ordem_servico', 'peca'),
        20,
    ).get_page(request.GET.get('page'))
    return render(request, 'ordens/notificacoes.html', {
        'page_obj': page_obj,
        'tema_inicial': getattr(request.user, 'tema_preferido', Usuario.TEMA_ESCURO) or Usuario.TEMA_ESCURO,
    })


@login_required
@require_POST
def marcar_notificacao_lida(request, notificacao_id):
    notificacao = get_object_or_404(Notificacao, pk=notificacao_id, destinatario=request.user)
    if not notificacao.lida_em:
        notificacao.lida_em = timezone.now()
        notificacao.save(update_fields=['lida_em'])
    return redirect('notificacoes')


@login_required
def detalhe_ordem_tecnico(request, ordem_id):
    ordem = ordem_do_tecnico_ou_404(request.user, ordem_id)
    return render(request, 'ordens/detalhe_ordem_tecnico.html', {
        'ordem': ordem,
        'form': AtualizacaoTecnicoForm(instance=ordem),
        'tema_inicial': getattr(request.user, 'tema_preferido', Usuario.TEMA_ESCURO) or Usuario.TEMA_ESCURO,
    })


@login_required
@require_POST
def atualizar_ordem_tecnico(request, ordem_id):
    ordem = ordem_do_tecnico_ou_404(request.user, ordem_id)
    form = AtualizacaoTecnicoForm(request.POST, instance=ordem)
    if form.is_valid():
        ordem = form.save()
        RegistroSistema.objects.create(
            tipo='ordem_servico',
            acao='alterado',
            descricao=f'OS #{ordem.pk} atualizada pelo técnico {request.user.nome_completo}.',
            usuario_responsavel=request.user,
            objeto_id=ordem.pk,
            objeto_referencia=f'OS #{ordem.pk}',
        )
        messages.success(request, 'Atualização registrada com sucesso.')
    else:
        messages.error(request, 'Não foi possível registrar a atualização.')
    return redirect('detalhe_ordem_tecnico', ordem_id=ordem_id)


@login_required
@require_GET
def tema_atual(request):
    """Retorna o tema salvo no banco para o usuário logado."""
    tema = getattr(request.user, 'tema_preferido', Usuario.TEMA_ESCURO) or Usuario.TEMA_ESCURO
    if tema not in {Usuario.TEMA_CLARO, Usuario.TEMA_ESCURO}:
        tema = Usuario.TEMA_ESCURO
    return JsonResponse({'ok': True, 'tema': tema})


@login_required
@require_POST
def salvar_tema(request):
    """Salva a preferência de tema no banco para clientes e equipe interna."""
    tema = (request.POST.get('tema') or '').strip().lower()
    if tema not in {Usuario.TEMA_CLARO, Usuario.TEMA_ESCURO}:
        return JsonResponse({'ok': False, 'erro': 'Tema inválido.'}, status=400)

    Usuario.objects.filter(pk=request.user.pk).update(tema_preferido=tema)
    request.user.tema_preferido = tema
    return JsonResponse({'ok': True, 'tema': tema})


@login_required
@require_http_methods(['GET', 'POST'])
def alterar_senha(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            usuario = form.save()
            usuario.senha_alterada_em = timezone.now()
            usuario.save(update_fields=['senha_alterada_em'])
            update_session_auth_hash(request, usuario)
            messages.success(request, 'Senha alterada com sucesso.')
            return redirect('lista_ordens')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'alterar_senha.html', {
        'form': form,
        'tema_inicial': getattr(request.user, 'tema_preferido', Usuario.TEMA_ESCURO) or Usuario.TEMA_ESCURO,
    })
