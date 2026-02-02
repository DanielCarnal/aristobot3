# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root (parent of backend/)
load_dotenv(BASE_DIR.parent / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# Configuration DEBUG
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Configuration DEBUG Aristobot (mode dev auto-login)
DEBUG_ARISTOBOT = os.getenv('DEBUG_ARISTOBOT', 'False') == 'True'

# Module 4 - Webhooks TradingView
WEBHOOK_TOKEN = os.getenv('WEBHOOK_TOKEN', 'CHANGE_ME_IN_PRODUCTION')

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    'apps.core',
    'apps.auth_custom',      # Nouvelle app auth
    'apps.accounts',  # Garder pour les autres fonctions user
    'apps.brokers',
    'apps.market_data',
    'apps.strategies',
    'apps.trading_engine',
    'apps.trading_manual',
    'apps.backtest',
    'apps.webhooks',
    'apps.stats',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aristobot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'aristobot.wsgi.application'
ASGI_APPLICATION = 'aristobot.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'aristobot3',
        'USER': 'postgres',
        'PASSWORD': 'aristobot',
        'HOST': '10.9.0.99',
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Configuration des logs pour debug
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        # Reduire les logs WebSocket/Channels verbeux
        'daphne': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'django.channels': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'apps.auth_custom': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps.accounts': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps.trading_manual': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps.core.services.exchange_client': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom SessionAuthentication sans CSRF pour API
from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Ne pas vérifier CSRF pour les API

# Configuration DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'aristobot.settings.CsrfExemptSessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS - Configuration plus permissive pour le développement
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vue dev server  
    "http://127.0.0.1:5173",  # Vue dev server alternative
    "http://localhost:3000",  # Autres ports possibles
    "http://127.0.0.1:3000",
    "http://localhost:8000",  # API elle-même (pour les tests)
    "http://127.0.0.1:8000",  # API elle-même (pour les tests)
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Gardons la sécurité

# Headers CORS pour les cookies
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Ne pas utiliser CORS_ALLOW_ALL_ORIGINS avec withCredentials
# if DEBUG:
#     CORS_ALLOW_ALL_ORIGINS = True

# Configuration d'authentification standard
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(os.getenv('REDIS_HOST', 'localhost'), int(os.getenv('REDIS_PORT', '6379')))],
        },
    },
}

BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')

# Configuration Async/Timeout pour les opérations de trading longues
ASYNC_TIMEOUT = 180  # 3 minutes pour les opérations de trading
APPLICATION_CLOSE_TIMEOUT = 180  # Timeout avant de tuer les connexions

# Terminal 1 — Loguru intercepteur Django logging vers terminal1.log
try:
    import logging as _logging
    import importlib.util as _importlib_util
    from loguru import logger as _loguru_logger

    # Charger loguru_config directement par chemin de fichier pour eviter
    # l'execution de apps/core/services/__init__.py (qui importe des models Django)
    _loguru_config_path = BASE_DIR / "apps" / "core" / "services" / "loguru_config.py"
    _spec = _importlib_util.spec_from_file_location("loguru_config", _loguru_config_path)
    _loguru_config_mod = _importlib_util.module_from_spec(_spec)
    _spec.loader.exec_module(_loguru_config_mod)

    # Uniquement dans le processus Daphne — les management commands (T2/T3/T5/T6)
    # appellent leur propre setup_loguru("terminalX") et ne doivent pas ouvrir terminal1.log
    import sys as _sys
    _is_daphne = 'daphne' in _sys.argv[0].lower() if _sys.argv else False
    if _is_daphne:
        _loguru_config_mod.setup_loguru("terminal1")

    class _LoguruInterceptHandler(_logging.Handler):
        """Intercepteur apps Aristobot -> Loguru"""
        def emit(self, record):
            try:
                level = _loguru_logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            # Binder terminal_name="terminal1" seulement dans Daphne ;
            # dans les management commands, loguru utilise le contexte
            # pose par leur propre setup_loguru("terminalX")
            if _is_daphne:
                _loguru_logger.opt(exception=record.exc_info).bind(
                    terminal_name="terminal1", component=record.name
                ).log(level, record.getMessage())
            else:
                _loguru_logger.opt(exception=record.exc_info).bind(
                    component=record.name
                ).log(level, record.getMessage())

    # Ajouter intercepteur uniquement aux loggers des apps Aristobot
    for _logger_name in [
        'apps.trading_manual', 'apps.webhooks', 'apps.accounts',
        'apps.brokers', 'apps.core', 'apps.trading_engine',
    ]:
        _app_logger = _logging.getLogger(_logger_name)
        _app_logger.addHandler(_LoguruInterceptHandler())
        _app_logger.setLevel(_logging.DEBUG)
        _app_logger.propagate = False
except ImportError:
    pass  # loguru non installe — logs Django standard uniquement