"""
Template tags para el sistema de traducción por secciones.

{% load translations %}

Tags disponibles:
  {% section "hero" "app/_hero.html" %}
      Sirve el HTML traducido de la sección si existe en caché;
      si no, renderiza el template original como fallback.

  {% tr "field_key" fallback %}   (legado — campos individuales)
      Retorna un campo específico del caché de traducción.

  {% html_translator_assets %}
      Incluye el script lang-selector.js con el hash de collectstatic.

  {% hreflang_tags %}
      Genera <link rel="alternate" hreflang="..."> para todas las
      traducciones disponibles de la página actual. Requiere
      HREFLANG_URL_BUILDER en TRANSLATIONS_CONFIG.

  {% language_selector "desktop" %}
  {% language_selector "mobile" %}
  {% language_selector "desktop" page_key="mi-pagina" %}
      Renderiza el selector de idioma. El proyecto consumidor debe
      proveeer via context processor:
        - all_available_langs_labeled: lista de (code, label)
        - additional_latin_langs: lista de (code, name)
"""
import logging
import re

from django import template
from django.core.cache import cache
from django.utils.safestring import mark_safe

from ..models import TranslationCache

register = template.Library()
logger = logging.getLogger(__name__)

_CACHE_PREFIX = 'tr:'
_CACHE_TIMEOUT = 3600  # 1 hora

# Regex para remover prefijo de idioma existente: /en/, /pt-br/, etc.
_LANG_PREFIX_RE = re.compile(r'^/[a-z]{2}(?:-[a-z]{2})?/')


def _cache_key(page_key: str, lang: str) -> str:
    return f'{_CACHE_PREFIX}{page_key}:{lang}'


def _load_translations(page_key: str, lang: str) -> dict:
    key = _cache_key(page_key, lang)
    data = cache.get(key)
    if data is None:
        try:
            tc = TranslationCache.objects.get(page_key=page_key, lang=lang)
            data = tc.content or {}
        except TranslationCache.DoesNotExist:
            data = {}
        cache.set(key, data, _CACHE_TIMEOUT)
    return data


def _invalidate_cache(page_key: str = 'home') -> None:
    """Invalida el caché en memoria para un page_key en todos sus idiomas."""
    langs: set[str] = set()
    try:
        langs.update(
            TranslationCache.objects.filter(page_key=page_key)
            .values_list('lang', flat=True)
        )
    except Exception:
        pass

    from .. import conf
    available = conf.get_available_languages()
    if available:
        langs.update(available)
    else:
        # Default languages if not configured in TranslatorConfig
        langs.update(['en', 'pt', 'fr', 'de', 'it'])

    for lc in langs:
        cache.delete(_cache_key(page_key, lc))
        cache.delete(f'tr_fresh:{page_key}:{lc}')

    logger.debug('tr: caché invalidado para page=%s langs=%s', page_key, langs)


def _apply_url_rewrites(html: str, lang: str) -> str:
    """
    Aplica URL_REWRITE_PATTERNS definidos en TRANSLATIONS_CONFIG.
    El {lang} en el reemplazo es sustituido por el idioma actual.
    """
    from .. import conf
    for pattern, replacement in conf.get_url_rewrite_patterns():
        html = pattern.sub(replacement.replace('{lang}', lang), html)
    return html


def _detect_page_key(request) -> str:
    """
    Detecta el page_key desde el request.

    Si PAGE_KEY_PROVIDER está definido en TRANSLATIONS_CONFIG, lo usa.
    En caso contrario, aplica la detección genérica:
    - slug en kwargs → '{namespace}-{slug}' (ej. 'portfolio-mi-bot')
    - URL raíz → 'home'
    - Otros → '{namespace}-{url_name}' o url_name
    """
    if request is None:
        return 'home'

    from .. import conf
    provider = conf.get_page_key_provider()
    if provider:
        try:
            return provider(request)
        except Exception:
            pass

    rm = getattr(request, 'resolver_match', None)
    if rm is None:
        return 'home'

    slug = rm.kwargs.get('slug')
    if slug:
        prefix = rm.namespace or 'detail'
        return f'{prefix}-{slug}'

    url_name = rm.url_name or ''
    namespace = rm.namespace or ''

    if url_name in ('index', 'home', 'landing_lang', ''):
        return 'home'

    return f'{namespace}-{url_name}' if namespace else url_name or 'home'


# ── Tag principal: sección completa ────────────────────────────────────────────

@register.simple_tag(takes_context=True)
def section(context, section_key: str, template_name: str):
    """
    Sirve el HTML traducido para una sección o renderiza el template original.

    Ejemplo:
        {% section "hero" "app/_hero.html" %}
    """
    request = context.get('request')
    lang = getattr(request, 'LANGUAGE_CODE', 'es') if request else 'es'

    from .. import conf
    default_lang = conf.get_default_language()

    if lang != default_lang:
        content = _load_translations(_detect_page_key(request), lang)
        translated_html = content.get(section_key)
        if translated_html:
            translated_html = _apply_url_rewrites(translated_html, lang)
            logger.debug(
                'section: %s lang=%s → translated HTML (%d chars)',
                section_key, lang, len(translated_html),
            )
            return mark_safe(translated_html)

    # Fallback: renderiza el template original
    from django.template.loader import render_to_string
    ctx = dict(context.flatten())

    ctx_provider = conf.get_section_context_provider()
    if ctx_provider:
        try:
            extra = ctx_provider(request, _detect_page_key(request))
            for k, v in extra.items():
                ctx.setdefault(k, v)
        except Exception as exc:
            logger.warning('section: SECTION_CONTEXT_PROVIDER falló — %s', exc)

    return mark_safe(render_to_string(template_name, ctx, request=request))


# ── Tag legado: campo individual ────────────────────────────────────────────────

@register.simple_tag(takes_context=True)
def tr(context, field_key: str, fallback: str = '', page=None):
    """Retorna un campo individual del caché (legado, pre-secciones)."""
    request = context.get('request')
    lang = getattr(request, 'LANGUAGE_CODE', 'es') if request else 'es'

    from .. import conf
    if lang == conf.get_default_language():
        return fallback

    page_key = page or _detect_page_key(request)
    content = _load_translations(page_key, lang)
    return content.get(field_key, fallback)


# ── Tag de assets ──────────────────────────────────────────────────────────────

@register.simple_tag
def html_translator_assets(defer: bool = False):
    """
    Incluye el script lang-selector.js.

    Ejemplo:
        {% html_translator_assets %}
        {% html_translator_assets defer=True %}
    """
    from django.templatetags.static import static
    url = static('html_translator/js/lang-selector.js')
    defer_attr = ' defer' if defer else ''
    return mark_safe(f'<script src="{url}"{defer_attr}></script>')


# ── Tag hreflang ──────────────────────────────────────────────────────────────

@register.simple_tag(takes_context=True)
def hreflang_tags(context):
    """
    Genera <link rel="alternate" hreflang="..."> para todas las traducciones
    disponibles de la página actual, incluyendo x-default apuntando al idioma base.

    Requiere HREFLANG_URL_BUILDER en TRANSLATIONS_CONFIG:
        def build_hreflang_url(request, lang: str, page_key: str) -> str

    No emite nada si HREFLANG_URL_BUILDER no está configurado o si solo
    existe el idioma base (sin traducciones disponibles aún).
    """
    from .. import conf

    builder = conf.get_hreflang_url_builder()
    if not builder:
        return ''

    request = context.get('request')
    if not request:
        return ''
    page_key = _detect_page_key(request)
    default_lang = conf.get_default_language()

    langs = [default_lang]
    try:
        translated = list(
            TranslationCache.objects
            .filter(page_key=page_key)
            .exclude(content={})
            .exclude(lang=default_lang)
            .values_list('lang', flat=True)
        )
        langs.extend(translated)
    except Exception as exc:
        logger.warning('hreflang_tags: error consultando TranslationCache — %s', exc)

    if len(langs) <= 1:
        return ''

    tags = []
    for lang in langs:
        try:
            url = builder(request, lang, page_key)
            tags.append(f'<link rel="alternate" hreflang="{lang}" href="{url}">')
        except Exception as exc:
            logger.warning('hreflang_tags: error construyendo URL para %s/%s — %s', page_key, lang, exc)

    try:
        default_url = builder(request, default_lang, page_key)
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{default_url}">')
    except Exception:
        pass

    return mark_safe('\n    '.join(tags))


# ── Tag del selector de idioma ────────────────────────────────────────────────

@register.simple_tag(takes_context=True)
def language_selector(context, variant: str = 'desktop', page_key: str = None):
    """
    Renderiza el selector de idioma.

    Uso:
        {% language_selector "desktop" %}
        {% language_selector "mobile" %}
        {% language_selector "desktop" page_key="mi-pagina" %}

    El proyecto consumidor debe proveeer via context processor:
        - all_available_langs_labeled: lista de (code, label)
        - additional_latin_langs: lista de (code, name)
    """
    from django.template.loader import render_to_string
    from .. import conf

    request = context.get('request')

    if page_key is None:
        page_key = _detect_page_key(request)

    all_available_langs_labeled = context.get('all_available_langs_labeled', [])
    additional_latin_langs = context.get('additional_latin_langs', [])
    ui_labels = conf.get_ui_labels()

    lang = getattr(request, 'LANGUAGE_CODE', 'es') if request else 'es'

    ctx = {
        'variant': variant,
        'page_key': page_key,
        'lang': lang,
        'all_available_langs_labeled': all_available_langs_labeled,
        'additional_latin_langs': additional_latin_langs,
        'ui_labels': ui_labels,
        'siteconfig': context.get('siteconfig'),
        'lang_prefix': f'/{lang}/' if lang != 'es' else '/',
    }

    return mark_safe(render_to_string('html_translator/_selector.html', ctx, request=request))
