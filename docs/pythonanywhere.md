# Publicação do SEOS no PythonAnywhere

Este guia publica uma instância demonstrativa sem enviar banco de dados,
usuários, CPF, senhas ou chaves ao GitHub.

## 1. Criar o aplicativo web

No painel **Web** do PythonAnywhere, crie um novo aplicativo com configuração
manual e selecione Python 3.12. Anote o endereço fornecido, no formato
`https://seuusuario.pythonanywhere.com`.

## 2. Baixar e instalar

No console Bash do PythonAnywhere, substitua `seuusuario` pelo seu nome de
usuário:

```bash
cd ~
git clone https://github.com/SEU_USUARIO/seos-apresentacao.git
mkvirtualenv --python=/usr/bin/python3.12 seos-venv
workon seos-venv
pip install -r ~/seos-apresentacao/requirements.txt
mkdir -p ~/seos-data
```

No painel **Web**, configure o caminho do ambiente virtual como
`/home/seuusuario/.virtualenvs/seos-venv`.

## 3. Configurar o arquivo WSGI

No painel **Web**, abra o arquivo WSGI gerado pelo PythonAnywhere. Substitua
seu conteúdo pelo exemplo abaixo, alterando somente o nome de usuário, o nome
do repositório e a chave secreta. Gere uma chave longa e aleatória; ela não
deve ser compartilhada nem enviada ao GitHub.

```python
import os
import sys

PROJECT_PATH = '/home/seuusuario/seos-apresentacao'
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

os.environ['DJANGO_SETTINGS_MODULE'] = 'sistema_os.settings'
os.environ['DJANGO_SECRET_KEY'] = 'COLE_AQUI_UMA_CHAVE_NOVA_E_ALEATORIA'
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'seuusuario.pythonanywhere.com'
os.environ['SEOS_DATABASE_PATH'] = '/home/seuusuario/seos-data/seos.sqlite3'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## 4. Criar o banco local da hospedagem

Ainda no console, execute:

```bash
workon seos-venv
cd ~/seos-apresentacao
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

Crie um usuário administrador com dados próprios. Não reutilize senhas,
documentos ou bancos usados durante o desenvolvimento.

## 5. Arquivos estáticos e recarga

No painel **Web**, adicione um mapeamento de arquivos estáticos:

- URL: `/static/`
- Diretório: `/home/seuusuario/seos-apresentacao/staticfiles`

Clique em **Reload**. Abra o endereço do aplicativo e confirme o login. Se
ocorrer erro, consulte o log de erros na aba **Web**; não publique conteúdo
desse log se ele contiver caminhos, chaves ou dados pessoais.

## Atualização posterior

No console:

```bash
cd ~/seos-apresentacao
git pull
workon seos-venv
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Depois, clique em **Reload** na aba **Web**. O banco fica em
`~/seos-data/`, fora do repositório, e portanto não é alterado por `git pull`.

Quando esta atualização incluir o portal técnico, as migrações criam o cargo
**Técnico**. Crie ou edite os usuários pelo Admin e atribua cada OS ao técnico
responsável. O técnico entra na fila própria após o login; o Supervisor Técnico
continua usando o Admin. Não é necessário, nem recomendado, criar ou enviar
senhas, CPFs, banco SQLite ou variáveis de ambiente para o GitHub.

## Limites da conta grátis

A conta gratuita permite um aplicativo web e expira após um mês. Renove-a no
painel do PythonAnywhere antes do prazo para manter a demonstração ativa.
