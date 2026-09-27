from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

from .utils import apenas_digitos


class CPFBackend(ModelBackend):
    """Autentica usuários pelo CPF, aceitando CPF com ou sem pontuação."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        cpf = kwargs.get(UserModel.USERNAME_FIELD) or username
        cpf = apenas_digitos(cpf)

        if not cpf or password is None:
            return None

        max_tentativas = getattr(settings, 'SEOS_LOGIN_MAX_TENTATIVAS', 5)
        bloqueio_minutos = getattr(settings, 'SEOS_LOGIN_BLOQUEIO_MINUTOS', 15)

        try:
            user = UserModel._default_manager.get(cpf=cpf)
        except UserModel.DoesNotExist:
            # Mantém custo semelhante quando o CPF não existe.
            UserModel().set_password(password)
            return None

        if user.login_esta_bloqueado():
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            user.limpar_bloqueio_login()
            return user

        novas_tentativas = min((user.login_tentativas_falhas or 0) + 1, max_tentativas)
        campos = ['login_tentativas_falhas']
        user.login_tentativas_falhas = novas_tentativas
        if novas_tentativas >= max_tentativas:
            user.login_bloqueado_ate = timezone.now() + timezone.timedelta(minutes=bloqueio_minutos)
            campos.append('login_bloqueado_ate')
        user.save(update_fields=campos)
        return None
