# SEOS — Sistema de Emissão de Ordem de Serviço

Aplicação acadêmica em Python e Django para administrar clientes, ordens de
serviço, estoque de peças e atendimentos técnicos. O sistema mantém histórico
das alterações e registros de auditoria para apoiar o acompanhamento das
operações.

## Funcionalidades

- Cadastro de clientes, usuários, ordens de serviço e peças.
- Controle de entrada e saída de estoque.
- Histórico de cada ordem e registro de ações no sistema.
- Perfis de acesso para atendimento, técnico operacional, supervisão técnica,
  almoxarifado e cliente.
- Painel do cliente para consultar somente as próprias ordens, com linha do
  tempo e paginação.
- Fila operacional do técnico, restrita às ordens a ele atribuídas.
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

## Perfis e permissões

| Perfil | Acesso principal |
| --- | --- |
| Cliente | Consulta exclusivamente suas próprias ordens e seus históricos. |
| Técnico | Acessa sua fila; atualiza somente status, avaliação e serviço planejado das OS atribuídas a ele. Não acessa o Admin. |
| Supervisor Técnico | Acessa o Admin para supervisionar, atribuir técnicos e administrar ordens. |
| Atendente | Acessa o Admin para atendimento e cadastro; não acessa a fila técnica. |
| Almoxarifado | Acessa o Admin para estoque; não acessa a fila técnica. |

O responsável técnico de uma OS pode ser um Técnico, um Supervisor Técnico ou
um superusuário. Todas as restrições também são verificadas no servidor; não
dependem apenas da interface.

## Publicação no PythonAnywhere

O guia de configuração está em
[`docs/pythonanywhere.md`](docs/pythonanywhere.md). Antes de publicar, defina
uma chave secreta nova, o endereço permitido do seu aplicativo e um caminho
privado para o banco de dados.

Depois de atualizar o código no PythonAnywhere, aplique as migrações, colete
os arquivos estáticos e clique em **Reload**. A sequência detalhada está no
guia de publicação.

## Autoria

- Heitor Emanuel da Silva Amorim
- Heitor Leoni Costa Bezerra
- Sony Jones da Silva Vitoriano
- José Damasceno Filho

Projeto desenvolvido para fins acadêmicos utilizando a metodologia RAD.
