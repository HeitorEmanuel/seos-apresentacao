import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in {'1', 'true', 'yes', 'on'}

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('Defina DJANGO_SECRET_KEY antes de iniciar o SEOS.')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    if host.strip()
]

# --- APPLICATION DEFINITION ---

INSTALLED_APPS = [
    'jazzmin',  # O Jazzmin DEVE vir antes do admin para sobrescrever o visual
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ordens.apps.OrdensConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sistema_os.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema_os.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('SEOS_DATABASE_PATH', BASE_DIR / 'var' / 'db.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

SEOS_LOGIN_MAX_TENTATIVAS = int(os.environ.get('SEOS_LOGIN_MAX_TENTATIVAS', '5'))
SEOS_LOGIN_BLOQUEIO_MINUTOS = int(os.environ.get('SEOS_LOGIN_BLOQUEIO_MINUTOS', '15'))

AUTHENTICATION_BACKENDS = [
    'ordens.backends.CPFBackend',
]

# --- INTERNATIONALIZATION (Ajustado para Português) ---

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = Path(os.environ.get('SEOS_MEDIA_ROOT', BASE_DIR / 'var' / 'media'))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))

AUTH_USER_MODEL = 'ordens.Usuario'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/redirecionar/'
LOGOUT_REDIRECT_URL = 'login'

# --- CONFIGURAÇÕES EXCLUSIVAS DO JAZZMIN ---

JAZZMIN_SETTINGS = {
    "site_title": "SEOS Admin",
    "site_header": "SEOS",
    "site_brand": "SEOS - Gestão",
    "welcome_sign": "Bem-vindo ao Painel SEOS",
    "copyright": "SEOS - Sistema de Ordem de Serviço",
    "user_avatar": None,
    "show_sidebar": True,
    "navigation_expanded": True,

    # O histórico de serviço continua funcionando dentro da OS,
    # mas não aparece mais como item separado no menu lateral.
    "hide_models": [
        "ordens.HistoricoOrdemServico",
        "ordens.historicoordemservico",
        "auth.Group",
        "auth.group",
    ],

    # Ordem real do menu lateral. Grupos/permissões crus do Django ficam escondidos.
    "order_with_respect_to": [
        "ordens",
        "ordens.OrdemServico",
        "ordens.ordemservico",
        "ordens.Usuario",
        "ordens.usuario",
        "ordens.Peca",
        "ordens.peca",
        "ordens.MovimentacaoEstoque",
        "ordens.movimentacaoestoque",
        "ordens.RegistroSistema",
        "ordens.registrosistema",
    ],

    "custom_links": {
        "ordens": [
            {
                "name": "Painel do Cliente",
                "url": "lista_ordens",
                "icon": "fas fa-arrow-left",
            },
        ],
    },

    "icons": {
        "auth": "fas fa-lock",
        "auth.Group": "fas fa-user-shield",
        "auth.group": "fas fa-user-shield",

        "ordens": "fas fa-layer-group",
        "ordens.Usuario": "fas fa-users",
        "ordens.usuario": "fas fa-users",
        "ordens.OrdemServico": "fas fa-tools",
        "ordens.ordemservico": "fas fa-tools",
        "ordens.Peca": "fas fa-boxes",
        "ordens.peca": "fas fa-boxes",
        "ordens.MovimentacaoEstoque": "fas fa-exchange-alt",
        "ordens.movimentacaoestoque": "fas fa-exchange-alt",
        "ordens.RegistroSistema": "fas fa-clipboard-list",
        "ordens.registrosistema": "fas fa-clipboard-list",
    },

    "custom_css": "admin/css/custom_admin.css",
    "custom_js": "admin/js/seos_sidebar.js",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-white",
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-light-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_styled": False,
    "sidebar_nav_legacy_styled": False,
    "sidebar_nav_flat_style": False,
    "theme": "flatly",
    "dark_mode_theme": "darkly",
}

# --- CONFIGURAÇÃO DE ARQUIVOS ESTÁTICOS GLOBAIS ---
STATICFILES_DIRS = [
    BASE_DIR / "ordens" / "static",
]
