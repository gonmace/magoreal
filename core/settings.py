import os
from decouple import config, Csv

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJECT_DIR)

_SECRET_KEY_DEFAULT = 'django-insecure-default-only-for-dev-run-make-setup'
SECRET_KEY = config('SECRET_KEY', default=_SECRET_KEY_DEFAULT)

DEBUG = config('DEBUG', default=False, cast=bool)

# Validar solo cuando existe .env (entorno configurado) pero SECRET_KEY no fue definido.
# Sin .env = instalación inicial, el default es aceptable.
if SECRET_KEY == _SECRET_KEY_DEFAULT and os.path.exists(os.path.join(BASE_DIR, '.env')):
    raise ValueError("SECRET_KEY no está en .env. Ejecuta 'make setup' para generarlo.")

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
if DEBUG:
    # host.docker.internal: permite callbacks desde contenedores n8n en dev
    ALLOWED_HOSTS += ['host.docker.internal']

ADMIN_URL = config('ADMIN_URL', default='admin/')

# Application definition

INSTALLED_APPS = [
    'site_config',
    'portfolio',
    'html_translator',
    'landing',
    'landing.morph_banner',
    'home',
    'axes',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'site_config.middleware.SitePageMiddleware',
    'html_translator.middleware.LanguageMiddleware',
]

INSTALLED_APPS += ['tailwind', 'theme']
TAILWIND_APP_NAME = 'theme'

if DEBUG:
    INSTALLED_APPS += ['django_browser_reload']
    MIDDLEWARE += ['django_browser_reload.middleware.BrowserReloadMiddleware']
    INTERNAL_IPS = ['127.0.0.1', '::1']
    import sys
    if sys.platform == 'win32':
        NPM_BIN_PATH = r'C:\Program Files\nodejs\npm.cmd'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'site_config.context_processors.site_context',
                'portfolio.context_processors.proyectos_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database: SQLite por defecto en dev, PostgreSQL si se define POSTGRES_DB
if config('POSTGRES_DB', default=''):
    _pg_host = config('POSTGRES_HOST', default='postgres')
    # Desde el host hacia Docker Desktop, el mapeo suele ser 127.0.0.1:puerto. Si usas
    # "localhost", el SO puede elegir ::1 primero y acabar en otro PostgreSQL (p. ej.
    # instalación local) → "password authentication failed". Forzar IPv4 para localhost.
    if _pg_host == 'localhost':
        _pg_host = '127.0.0.1'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_DB'),
            'USER': config('POSTGRES_USER'),
            'PASSWORD': config('POSTGRES_PASSWORD'),
            'HOST': _pg_host,
            'PORT': config('POSTGRES_HOST_PORT', default=config('POSTGRES_PORT', default='5432')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
WHITENOISE_MANIFEST_STRICT = not DEBUG  # True en prod: rechaza archivos sin entrada en manifest

STORAGES = {
    'staticfiles': {
        # CompressedManifestStaticFilesStorage: hashes en filenames (cache-busting seguro)
        # + archivos .gz pre-generados que nginx sirve con gzip_static on
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
}

MEDIA_URL = '/media/'
# Los screenshots de los proyectos viven fuera del repo Django en
# landing-automatizaciones/proyectos/*/screenshots/. Montamos ese directorio
# como MEDIA_ROOT para que {% get_media_prefix %} resuelva sin copiar archivos.
MEDIA_ROOT = os.path.normpath(os.path.join(BASE_DIR, '..', 'landing-automatizaciones'))

# Directorio donde viven los metadata.json del portfolio. Usado por
# portfolio.loaders.load_proyectos().
PROYECTOS_DIR = os.path.join(MEDIA_ROOT, 'proyectos')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email: consola en dev, SMTP en prod si se configura EMAIL_HOST
if config('EMAIL_HOST', default=''):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@example.com')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── Seguridad ──────────────────────────────────────────────────────────────────
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

X_FRAME_OPTIONS = 'DENY'

# ── Redis (cache, sesiones) ───────────────────────────────────────────────────
# En dev sin .env, se conecta a localhost:6379 (Docker Desktop expone el puerto al host).
# En producción, .env siempre define REDIS_URL=redis://redis:6379/0 (nombre del servicio Docker).
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ── django-axes (protección brute force) ──────────────────────────────────────
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hora
AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']

if DEBUG:
    # En desarrollo se usa el handler de base de datos para no depender de Redis.
    # Permite correr 'python manage.py runserver' sin contenedores activos.
    AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'
else:
    # En producción Redis siempre está disponible — más rápido bajo ataques.
    AXES_HANDLER = 'axes.handlers.cache.AxesCacheHandler'
    AXES_CACHE = 'default'

# ── Content Security Policy ───────────────────────────────────────────────────
CSP_DEFAULT_SRC = ("'self'",)
# 'unsafe-inline' en script-src porque el hero/nav/terminal usan JS inline
# (decisión explícita: evitar archivos JS separados para hero/nav de Sprint 1).
# jsdelivr para Alpine.js.
CSP_SCRIPT_SRC = (
    "'self'", "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
    "https://www.googletagmanager.com",
    "https://www.google-analytics.com",
    "https://ssl.google-analytics.com",
    "https://plausible.io",
)
# 'unsafe-inline' para los <style> inline del hero. Google Fonts para Geist Mono.
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'", "data:", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = (
    "'self'",
    "https://www.google-analytics.com",
    "https://region1.google-analytics.com",
    "https://stats.g.doubleclick.net",
    "https://plausible.io",
) if not DEBUG else (
    "'self'",
    "ws://localhost:*", "ws://127.0.0.1:*",
    "https://www.google-analytics.com",
    "https://region1.google-analytics.com",
    "https://stats.g.doubleclick.net",
    "https://plausible.io",
)

# ── Integración n8n (opcional) ───────────────────────────────────────────────
N8N_URL = config('N8N_URL', default='')
N8N_API_KEY = config('N8N_API_KEY', default='')
N8N_WEBHOOK_URL = config('N8N_WEBHOOK_URL', default='')

def _get_openai_api_key():
    from site_config.models import SiteConfig
    return SiteConfig.load().openai_api_key or ''


def _get_openai_model():
    from site_config.models import SiteConfig
    return SiteConfig.load().openai_model or 'gpt-4.1-mini'


# ── html_translator: configuración central ───────────────────────────────────
TRANSLATIONS_CONFIG = {
    # OpenAI — callables: se evalúan en cada traducción, leen desde SiteConfig admin
    'OPENAI_API_KEY': lambda: _get_openai_api_key(),
    'OPENAI_MODEL':   lambda: _get_openai_model(),

    'CALLBACK_TOKEN':   config('TRANSLATIONS_CALLBACK_TOKEN', default=''),
    'DEFAULT_LANGUAGE': 'es',

    # Lógica específica de este proyecto (formularios, portfolio, etc.)
    'SECTION_CONTEXT_PROVIDER': 'landing.translations_hooks.get_section_context',
    'PAGE_KEY_PROVIDER':        'landing.translations_hooks.detect_page_key',
    'PAGE_RENDERERS': {
        'portfolio-*': 'landing.translations_hooks.render_portfolio_detail',
    },
    'ON_TRANSLATION_UPDATED':  'landing.translations_hooks.on_translation_updated',
    'HREFLANG_URL_BUILDER':    'landing.translations_hooks.build_hreflang_url',

    # Reescritura de hrefs internos en HTML traducido para añadir prefijo de idioma
    'URL_REWRITE_PATTERNS': [
        (r'href="/(?:[a-z]{2}(?:-[a-z]{2})?/)?proyectos/', 'href="/{lang}/proyectos/'),
    ],

    # SECTIONS: todas las secciones disponibles para traducir
    'SECTIONS': [
        ('chat_hero',          'landing/_chat_hero_messages.html'),
        ('pliego',             'landing/_pliego_sections.html'),
        ('hero',               'landing/_000_hero.html'),
        ('social_proof',       'landing/_001_social_proof.html'),
        ('morph_banner',       'landing/_morph_banner.html'),
        ('screenshots',        'landing/_002_screenshots_real.html'),
        ('licitaciones',       'landing/_003_licitaciones.html'),
        ('proyectos',          'landing/_004_proyectos_grid.html'),
        ('servicios',          'landing/_005_servicios.html'),
        ('stack',              'landing/_006_stack.html'),
        ('proceso',            'landing/_007_proceso.html'),
        ('comparativa',        'landing/_008_comparativa.html'),
        ('faq',                'landing/_009_faq.html'),
        ('contacto',           'landing/_010_contacto.html'),
        ('footer',             'landing/_footer.html'),
        ('seo_schema',         'landing/_seo_schema.html'),
        # Secciones de detalle de proyectos (portfolio)
        ('chat_demo',             'portfolio/_proyecto_chat.html'),
        ('detalle_hero',          'portfolio/_proyecto_hero.html'),
        ('detalle_problemas',     'portfolio/_proyecto_problemas.html'),
        ('detalle_demo',          'portfolio/_proyecto_demo.html'),
        ('detalle_gallery',       'portfolio/_proyecto_gallery.html'),
        ('detalle_capacidades',   'portfolio/_proyecto_capacidades.html'),
        ('detalle_stack',         'portfolio/_proyecto_stack.html'),
        ('detalle_diferenciales', 'portfolio/_proyecto_diferenciales.html'),
        ('detalle_referencia',    'portfolio/_proyecto_referencia.html'),
        ('detalle_cta',           'portfolio/_proyecto_cta.html'),
    ],

    # PAGES: qué secciones se traducen en cada tipo de página
    'PAGES': {
        'home': [
            'chat_hero', 'pliego', 'hero', 'social_proof', 'morph_banner',
            'screenshots', 'licitaciones', 'proyectos', 'servicios',
            'stack', 'proceso', 'comparativa', 'faq', 'contacto', 'footer',
            'seo_schema',
        ],
        # Wildcard para páginas de detalle: portfolio-mi-bot, portfolio-otro, etc.
        'portfolio-*': [
            'chat_demo', 'detalle_hero', 'detalle_problemas', 'detalle_demo',
            'detalle_gallery', 'detalle_capacidades', 'detalle_stack',
            'detalle_diferenciales', 'detalle_referencia', 'detalle_cta',
        ],
    },
}

# Webhook n8n al que se reenvían los mensajes del formulario de contacto.
# Puede armar email, notificación Slack/Telegram, ticket en Linear, etc.
CONTACTO_WEBHOOK_URL = config('CONTACTO_WEBHOOK_URL', default='')

# ── Lead magnet de pliegos ───────────────────────────────────────────────────
# Los PDFs subidos por prospectos NO deben ser públicos: se guardan fuera del
# MEDIA_ROOT (que sí lo sirve nginx), en un volumen dedicado al que solo
# accede Django (y vos vía SSH al volumen para descargar manualmente).
PLIEGOS_UPLOAD_ROOT = config(
    'PLIEGOS_UPLOAD_ROOT',
    default=os.path.join(BASE_DIR, 'volumes', 'pliegos_demo'),
)
# Webhook n8n que procesa el PDF y genera el borrador. Opcional — si está
# vacío, el lead solo se guarda en DB y se notifica a sales por email.
PLIEGO_DEMO_WEBHOOK_URL = config('PLIEGO_DEMO_WEBHOOK_URL', default='')
# Email al que se notifica cada lead nuevo. Si vacío, usa siteconfig.email.
LEADS_NOTIFY_EMAIL = config('LEADS_NOTIFY_EMAIL', default='')

# ── Sentry (error monitoring) — opt-in vía env ────────────────────────────────
# Set SENTRY_DSN en .env para activar. Sin DSN, Sentry no se carga.
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN and not DEBUG:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=config('SENTRY_TRACES_RATE', default=0.1, cast=float),
            send_default_pii=False,     # privacy-first
            environment=config('SENTRY_ENV', default='production'),
            release=config('APP_VERSION', default='unknown'),
        )
    except ImportError:
        import logging
        logging.getLogger(__name__).warning(
            'SENTRY_DSN configured but sentry-sdk not installed. '
            'Run: pip install sentry-sdk[django]'
        )

# ── Admins y logging ──────────────────────────────────────────────────────────
ADMINS = [('Admin', 'admin@example.com')]
MANAGERS = ADMINS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'html_translator': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd"