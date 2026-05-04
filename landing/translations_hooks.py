"""
Lógica específica de magoreal para el sistema de traducción (html_translator).

Este archivo actúa como puente entre la librería genérica y los modelos,
formularios y context processors propios del proyecto.

Referenciado desde TRANSLATIONS_CONFIG en settings.py.
"""
import logging

logger = logging.getLogger(__name__)


def get_section_context(request, page_key: str) -> dict:
    """
    Provee el contexto extra necesario al renderizar secciones.
    Referenciado como SECTION_CONTEXT_PROVIDER en TRANSLATIONS_CONFIG.
    """
    from landing.forms import ContactForm, PliegoDemoForm
    return {
        'contact_form': ContactForm(),
        'pliego_demo_form': PliegoDemoForm(),
        'lang_prefix': '/',
    }


def detect_page_key(request) -> str:
    """
    Detecta el page_key desde el request de forma consistente.
    Referenciado como PAGE_KEY_PROVIDER en TRANSLATIONS_CONFIG.

    Garantiza que /proyectos/{slug}/ y /en/proyectos/{slug}/ usen
    el mismo page_key ('portfolio-{slug}'), aunque tengan resolver_match
    distintos (uno tiene namespace='portfolio', el otro no).
    """
    rm = getattr(request, 'resolver_match', None)
    if rm is None:
        return 'home'

    slug = rm.kwargs.get('slug')
    if slug:
        return f'portfolio-{slug}'

    url_name = rm.url_name or ''
    if url_name in ('index', 'home', 'landing_lang', ''):
        return 'home'

    namespace = rm.namespace or ''
    return f'{namespace}-{url_name}' if namespace else url_name or 'home'


def render_portfolio_detail(request, page_key: str):
    """
    Renderiza las secciones de una página de detalle de proyecto (portfolio).
    Referenciado como PAGE_RENDERERS['portfolio-*'] en TRANSLATIONS_CONFIG.

    Signature requerida: (request, page_key) -> (sections_html, sections_texts, source_hash)
    """
    from django.template.loader import render_to_string
    from html_translator.models import TranslationCache
    from html_translator.sections import get_sections
    from html_translator.utils import HtmlTextExtractor
    from portfolio.context_processors import get_proyectos

    slug = page_key[len('portfolio-'):]
    proyecto = next((p for p in get_proyectos() if p['slug'] == slug), None)
    if proyecto is None:
        logger.warning('render_portfolio_detail: proyecto "%s" no encontrado', slug)
        return {}, {}, ''

    context = {'proyecto': proyecto}
    sections_html: dict[str, str] = {}
    sections_texts: dict[str, list[str]] = {}

    for section_key, template_path in get_sections(page_key):
        try:
            html = render_to_string(template_path, context, request=request)
            if not html.strip():
                continue
            sections_html[section_key] = html
            texts = HtmlTextExtractor(html).get_texts()
            if texts:
                sections_texts[section_key] = texts
        except Exception as exc:
            logger.warning(
                'render_portfolio_detail: error en %s (%s): %s',
                section_key, template_path, exc,
            )

    from html_translator.views import _normalize_for_hash
    source_hash = TranslationCache.compute_hash({k: _normalize_for_hash(v) for k, v in sections_html.items()})
    logger.info(
        'render_portfolio_detail: slug=%s, %d secciones, hash=%s...',
        slug, len(sections_html), source_hash[:16],
    )
    return sections_html, sections_texts, source_hash


def build_hreflang_url(request, lang: str, page_key: str) -> str:
    """
    Construye la URL absoluta para un idioma y page_key dados.
    Referenciado como HREFLANG_URL_BUILDER en TRANSLATIONS_CONFIG.
    """
    from html_translator.conf import get_default_language
    default_lang = get_default_language()

    if page_key.startswith('portfolio-'):
        slug = page_key[len('portfolio-'):]
        path = f'/proyectos/{slug}/' if lang == default_lang else f'/{lang}/proyectos/{slug}/'
    else:
        path = '/' if lang == default_lang else f'/{lang}/'

    return request.build_absolute_uri(path)


def on_translation_updated(page_key: str) -> None:
    """
    Hook invocado después de actualizar el caché de traducción.
    Referenciado como ON_TRANSLATION_UPDATED en TRANSLATIONS_CONFIG.
    """
    from site_config.context_processors import invalidate_available_langs
    invalidate_available_langs(page_key)
