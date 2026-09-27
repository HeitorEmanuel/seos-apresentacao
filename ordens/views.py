from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import OrdemServico, Usuario
from django.utils import timezone


@login_required
def lista_ordens(request):
    ordens = (
        OrdemServico.objects
        .filter(cliente_usuario=request.user)
        .select_related('cliente_usuario', 'tecnico_responsavel')
        .prefetch_related('pecas_utilizadas__peca')
        .order_by('-data_entrada', '-id')
    )
    return render(request, 'lista_ordens.html', {
        'ordens': ordens,
        'tema_inicial': getattr(request.user, 'tema_preferido', Usuario.TEMA_ESCURO) or Usuario.TEMA_ESCURO,
    })


@login_required
def redirecionar_usuario(request):
    if request.user.is_staff:
        return redirect('/admin/')
    return redirect('lista_ordens')


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
