"""Settings específicos para pytest — override de DB/cache/email a backends in-memory."""
from .settings import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'
RATELIMIT_ENABLE = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable whitenoise manifest (no collectstatic in tests)
WHITENOISE_MANIFEST_STRICT = False
STORAGES = {
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
}

ALLOWED_HOSTS = ['*']
DEBUG = True
