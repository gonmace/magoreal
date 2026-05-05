"""
Acceso centralizado a la configuración de html_translator.

Prioridad para cada valor:
  1. TranslatorConfig en base de datos (editable desde el admin)
  2. TRANSLATIONS_CONFIG en settings.py (soporta callables)
  3. Valor por defecto hardcoded en la librería

De esta forma el proyecto consumidor puede:
  a) Configurar todo desde el admin (sin tocar settings.py)
  b) Configurar todo desde settings.py (comportamiento anterior)
  c) Mezclar ambos: valores sensibles en admin, estructura en settings.py

Ejemplo mínimo en settings.py (solo lo que no puede ir en admin):
    TRANSLATIONS_CONFIG = {
        'SECTIONS': [('hero', 'app/_hero.html')],
        'PAGES': {'home': ['hero']},
    }
"""
import re

from django.conf import settings
from django.utils.module_loading import import_string

# Cache en memoria del registro DB para evitar queries en cada request.
# Se invalida automáticamente cuando TranslatorConfig se guarda desde el admin.
_db_cache: dict = {'config': None, 'valid': False}


def invalidate_db_cache() -> None:
    _db_cache['valid'] = False
    _db_cache['config'] = None


def _get_db_config():
    """Devuelve la instancia TranslatorConfig desde caché o DB. None si falla."""
    if _db_cache['valid']:
        return _db_cache['config']
    try:
        from .models import TranslatorConfig
        obj = TranslatorConfig.get_solo()
        _db_cache['config'] = obj
        _db_cache['valid'] = True
        return obj
    except Exception:
        _db_cache['valid'] = True  # evita reintentos si la tabla no existe aún
        _db_cache['config'] = None
        return None


def _cfg() -> dict:
    return getattr(settings, 'TRANSLATIONS_CONFIG', {})


def _resolve_setting(key: str, default=None):
    """Lee un valor de settings.py. Soporta callables."""
    v = _cfg().get(key, default)
    return v() if callable(v) else v


# ---------------------------------------------------------------------------
# Getters públicos
# ---------------------------------------------------------------------------

def get_openai_api_key() -> str:
    db = _get_db_config()
    if db and db.openai_api_key:
        return db.openai_api_key
    # No fallback to settings.py — only TranslatorConfig in admin
    return ''


def get_openai_model() -> str:
    db = _get_db_config()
    if db and db.openai_model:
        return db.openai_model
    # Default model if not configured in TranslatorConfig
    return 'gpt-4o-mini'


def get_callback_token() -> str:
    db = _get_db_config()
    if db and db.callback_token:
        return db.callback_token
    return _resolve_setting('CALLBACK_TOKEN', '')


def get_default_language() -> str:
    db = _get_db_config()
    if db and db.default_language:
        return db.default_language
    return _resolve_setting('DEFAULT_LANGUAGE', 'es')


def get_available_languages() -> list[str]:
    db = _get_db_config()
    if db and db.available_languages:
        return db.available_languages
    return _resolve_setting('AVAILABLE_LANGUAGES', [])


def get_sections_config() -> list[tuple[str, str]]:
    return _resolve_setting('SECTIONS', [])


def get_pages_config() -> dict:
    return _resolve_setting('PAGES', {})


def get_section_context_provider():
    """Callable opcional (request, page_key) -> dict."""
    path = _resolve_setting('SECTION_CONTEXT_PROVIDER')
    if not path:
        return None
    return import_string(path)


def get_page_renderer(page_key: str):
    """Callable opcional (request, page_key) -> (sections_html, sections_texts, source_hash)."""
    renderers = _resolve_setting('PAGE_RENDERERS', {})
    if page_key in renderers:
        return import_string(renderers[page_key])
    for pattern, path in renderers.items():
        if pattern.endswith('-*') and page_key.startswith(pattern[:-1]):
            return import_string(path)
    return None


def get_on_translation_updated():
    """Callable opcional (page_key) -> None, invocado tras actualizar caché."""
    path = _resolve_setting('ON_TRANSLATION_UPDATED')
    if not path:
        return None
    return import_string(path)


def get_page_key_provider():
    """Callable opcional (request) -> str para resolver el page_key."""
    path = _resolve_setting('PAGE_KEY_PROVIDER')
    if not path:
        return None
    return import_string(path)


def get_url_rewrite_patterns() -> list[tuple]:
    """Lista de (patron_compilado, reemplazo) para reescribir hrefs en HTML traducido."""
    raw = _resolve_setting('URL_REWRITE_PATTERNS', [])
    return [(re.compile(p), r) for p, r in raw]


def get_rate_limit(is_debug: bool) -> str:
    if is_debug:
        return _resolve_setting('RATE_LIMIT_DEBUG', '200/h')
    return _resolve_setting('RATE_LIMIT_PROD', '10/h')


def get_hreflang_url_builder():
    """Callable opcional (request, lang, page_key) -> str para construir URLs hreflang."""
    path = _resolve_setting('HREFLANG_URL_BUILDER')
    if not path:
        return None
    return import_string(path)


def get_ui_labels() -> dict:
    """Labels genéricos del selector de idioma. Override en TRANSLATIONS_CONFIG."""
    return _resolve_setting('UI_LABELS', {
        'otro_idioma': '+ otro idioma',
        'seleccionar': '— seleccionar —',
        'traduciendo': 'Traduciendo…',
        'primer_vez': '~60-90s primera vez',
        'fallo': 'Falló la traducción.',
        'reintentar': 'Reintentar',
        'idioma': 'Idioma',
        'otro': '+ otro',
    })
