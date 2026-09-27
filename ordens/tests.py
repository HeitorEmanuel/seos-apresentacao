from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from .models import HistoricoOrdemServico, OrdemServico, RegistroSistema, Usuario, gerar_senha_padrao
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


class CargoTecnicoTests(TestCase):
    def criar_usuario(self, cpf, cargo=''):
        return Usuario.objects.create_user(
            cpf=cpf,
            password='Senha#123',
            nome_completo='Usuário de Teste',
            telefone='83999990000',
            cargo_sistema=cargo,
        )

    def test_tecnico_operacional_nao_recebe_acesso_admin(self):
        tecnico = self.criar_usuario('52998224725', Usuario.CARGO_TECNICO)

        self.assertFalse(tecnico.is_staff)
        self.assertTrue(tecnico.eh_tecnico_operacional())

    def test_apenas_tecnico_supervisor_ou_superusuario_podem_ser_responsaveis(self):
        tecnico = self.criar_usuario('52998224725', Usuario.CARGO_TECNICO)
        atendente = self.criar_usuario('11144477735', Usuario.CARGO_ATENDENTE)
        almoxarife = self.criar_usuario('12345678909', Usuario.CARGO_ALMOXARIFADO)
        supervisor = self.criar_usuario('93541134780', Usuario.CARGO_TECNICO_ADMIN)
        superusuario = self.criar_usuario('01234567890')
        superusuario.is_superuser = True
        superusuario.is_staff = True
        superusuario.save(update_fields=['is_superuser', 'is_staff'])

        self.assertTrue(tecnico.pode_ser_responsavel_tecnico())
        self.assertTrue(supervisor.pode_ser_responsavel_tecnico())
        self.assertTrue(superusuario.pode_ser_responsavel_tecnico())
        self.assertFalse(atendente.pode_ser_responsavel_tecnico())
        self.assertFalse(almoxarife.pode_ser_responsavel_tecnico())


class PortalAuthorizationTests(TestCase):
    def setUp(self):
        self.tecnico_a = Usuario.objects.create_user(
            cpf='52998224725', password='Senha#123', nome_completo='Técnico A',
            telefone='83999990000', cargo_sistema=Usuario.CARGO_TECNICO,
        )
        self.tecnico_b = Usuario.objects.create_user(
            cpf='11144477735', password='Senha#123', nome_completo='Técnico B',
            telefone='83999990001', cargo_sistema=Usuario.CARGO_TECNICO,
        )
        self.cliente = Usuario.objects.create_user(
            cpf='12345678909', password='Senha#123', nome_completo='Cliente Teste',
            telefone='83999990002',
        )
        self.os_tecnico_b = OrdemServico.objects.create(
            cliente_usuario=self.cliente,
            cliente_nome_exibicao=self.cliente.nome_completo,
            equipamento='Notebook',
            descricao_problema='Não liga',
            tecnico_responsavel=self.tecnico_b,
        )

    def test_tecnico_e_redirecionado_para_minha_fila(self):
        self.client.force_login(self.tecnico_a)

        response = self.client.get(reverse('redirecionar'), secure=True)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('minha_fila'))

    def test_tecnico_nao_obtem_ordem_de_outro_tecnico(self):
        self.client.force_login(self.tecnico_a)

        response = self.client.get(
            reverse('detalhe_ordem_tecnico', args=[self.os_tecnico_b.pk]),
            secure=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_atendente_nao_acessa_fila_tecnica(self):
        atendente = Usuario.objects.create_user(
            cpf='93541134780', password='Senha#123', nome_completo='Atendente',
            telefone='83999990003', cargo_sistema=Usuario.CARGO_ATENDENTE,
        )
        self.client.force_login(atendente)

        response = self.client.get(reverse('minha_fila'), secure=True)

        self.assertEqual(response.status_code, 404)


class FilaTecnicoTests(TestCase):
    def setUp(self):
        self.tecnico = Usuario.objects.create_user(
            cpf='52998224725', password='Senha#123', nome_completo='Técnico',
            telefone='83999990000', cargo_sistema=Usuario.CARGO_TECNICO,
        )
        self.outro_tecnico = Usuario.objects.create_user(
            cpf='11144477735', password='Senha#123', nome_completo='Outro Técnico',
            telefone='83999990001', cargo_sistema=Usuario.CARGO_TECNICO,
        )
        self.cliente = Usuario.objects.create_user(
            cpf='12345678909', password='Senha#123', nome_completo='Cliente Teste',
            telefone='83999990002',
        )
        self.minha_os = OrdemServico.objects.create(
            cliente_usuario=self.cliente, cliente_nome_exibicao=self.cliente.nome_completo,
            equipamento='Notebook', descricao_problema='Não liga', tecnico_responsavel=self.tecnico,
        )
        self.os_de_outro_tecnico = OrdemServico.objects.create(
            cliente_usuario=self.cliente, cliente_nome_exibicao=self.cliente.nome_completo,
            equipamento='Impressora', descricao_problema='Não imprime', tecnico_responsavel=self.outro_tecnico,
        )
        self.client.force_login(self.tecnico)

    def test_fila_exibe_apenas_ordens_atribuidas(self):
        response = self.client.get(reverse('minha_fila'), secure=True)

        self.assertContains(response, 'Notebook')
        self.assertNotContains(response, 'Impressora')

    def test_atualizacao_valida_status_e_registra_historico_e_auditoria(self):
        response = self.client.post(
            reverse('atualizar_ordem_tecnico', args=[self.minha_os.pk]),
            {'status': 'consertando', 'avaliacao_tecnico': 'Diagnóstico concluído', 'servico_planejado': 'Trocar fonte'},
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        self.minha_os.refresh_from_db()
        self.assertEqual(self.minha_os.status, 'consertando')
        self.assertTrue(HistoricoOrdemServico.objects.filter(
            ordem_servico=self.minha_os, status_momento='consertando',
        ).exists())
        self.assertTrue(RegistroSistema.objects.filter(
            usuario_responsavel=self.tecnico, objeto_id=self.minha_os.pk,
        ).exists())

    def test_tecnico_nao_atualiza_ordem_de_outro_tecnico(self):
        response = self.client.post(
            reverse('atualizar_ordem_tecnico', args=[self.os_de_outro_tecnico.pk]),
            {'status': 'consertando'}, secure=True,
        )

        self.assertEqual(response.status_code, 404)
        self.os_de_outro_tecnico.refresh_from_db()
        self.assertEqual(self.os_de_outro_tecnico.status, 'aberto')
