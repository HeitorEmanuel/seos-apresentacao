from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.test import TestCase

from .models import gerar_senha_padrao
from .utils import apenas_digitos, validar_cpf


class CPFUtilsTests(TestCase):
    def test_apenas_digitos_remove_pontuacao(self):
        self.assertEqual(apenas_digitos('529.982.247-25'), '52998224725')

    def test_validar_cpf_aceita_cpf_valido(self):
        self.assertEqual(validar_cpf('529.982.247-25'), '52998224725')

    def test_senha_temporaria_nao_e_previsivel(self):
        senha_1 = gerar_senha_padrao('Cliente Teste')
        senha_2 = gerar_senha_padrao('Cliente Teste')

        self.assertNotEqual(senha_1, senha_2)
        self.assertGreaterEqual(len(senha_1), 20)


class CPFBackendTests(TestCase):
    def test_login_aceita_cpf_formatado(self):
        User = get_user_model()
        User.objects.create_user(
            cpf='52998224725',
            password='Senha#123',
            nome_completo='Cliente Teste',
            telefone='83999990000',
        )

        usuario = authenticate(username='529.982.247-25', password='Senha#123')
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.cpf, '52998224725')


class ProductionSettingsTests(TestCase):
    def test_debug_fica_desativado_por_padrao(self):
        self.assertFalse(settings.DEBUG)

    def test_validadores_de_senha_estao_ativos(self):
        self.assertEqual(len(settings.AUTH_PASSWORD_VALIDATORS), 4)

    def test_cookies_sao_seguros_em_producao(self):
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)

    def test_hsts_tem_valor_positivo_em_producao(self):
        self.assertGreater(settings.SECURE_HSTS_SECONDS, 0)
