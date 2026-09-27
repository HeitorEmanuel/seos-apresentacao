# SEOS — Sistema de Emissão de Ordem de Serviço

Aplicação acadêmica em Python e Django para administrar clientes, ordens de
serviço, estoque de peças e atendimentos técnicos. O sistema mantém histórico
das alterações e registros de auditoria para apoiar o acompanhamento das
operações.

## Funcionalidades

- Cadastro de clientes, usuários, ordens de serviço e peças.
- Controle de entrada e saída de estoque.
- Histórico de cada ordem e registro de ações no sistema.
- Perfis de acesso para atendimento, técnico/administração, almoxarifado e
  cliente.
- Painel do cliente para consultar as próprias ordens.
- Impressão de ordem de serviço e etiquetas.
- Login por CPF, senhas armazenadas com hash e bloqueio temporário após
  tentativas inválidas.
- Senhas temporárias aleatórias, exibidas apenas no momento do cadastro.

## Tecnologias

- Python 3.12 ou 3.13
- Django 6
- SQLite para a demonstração
- HTML, CSS, JavaScript e Jazzmin

## Execução local

1. Crie e ative um ambiente virtual.
2. Instale as dependências: `pip install -r requirements.txt`.
3. Defina as variáveis de ambiente indicadas em `.env.example`. A chave
   `DJANGO_SECRET_KEY` é obrigatória.
4. Crie a pasta local do banco, aplique as migrações e crie seu próprio
   administrador:

   ```bash
   mkdir var
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Para desenvolvimento, defina `DJANGO_DEBUG=True` e execute
   `python manage.py runserver`.

Não há banco de dados, CPF, senha, chave secreta ou usuário de demonstração
versionado neste repositório. Cada instalação cria os próprios dados.

## Publicação no PythonAnywhere

O guia de configuração está em
[`docs/pythonanywhere.md`](docs/pythonanywhere.md). Antes de publicar, defina
uma chave secreta nova, o endereço permitido do seu aplicativo e um caminho
privado para o banco de dados.

## Autoria

- Heitor Emanuel da Silva Amorim
- Heitor Leoni Costa Bezerra
- Sony Jones da Silva Vitoriano
- José Damasceno Filho

Projeto desenvolvido para fins acadêmicos utilizando a metodologia RAD.
