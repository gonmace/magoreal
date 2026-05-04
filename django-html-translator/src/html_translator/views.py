"""
Endpoints HTTP para el sistema de traducción.

Flujo:
    1. Cliente POST /translations/request/ {page_key, lang}
    2. Django renderiza secciones, extrae textos visibles (HtmlTextExtractor)
    3. Persiste HTML fuente en TranslationCache y lanza thread de traducción
    4. Thread llama a OpenAI sección a sección y guarda HTML reconstruido
    5. Cliente sondea cada 5s; al recibir 'cached' navega a /{lang}/
"""
import json
import logging
import re
import threading

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from . import conf
from .models import TranslationCache
from .sections import get_sections, get_all_section_keys
from .templatetags.translations import _invalidate_cache
from .utils import HtmlTextExtractor

logger = logging.getLogger(__name__)

_STRIP_PATTERNS = [
    re.compile(r'<script\b[^>]*>.*?</script>', re.DOTALL | re.IGNORECASE),
    re.compile(r'<canvas\b[^>]*/?\s*>', re.IGNORECASE),
    re.compile(r'<svg\b[^>]*data-morph[^>]*>.*?</svg>', re.DOTALL | re.IGNORECASE),
]
_WHITESPACE = re.compile(r'\n{3,}')
# Matches CSRF hidden inputs whose value changes per-request
_CSRF_RE = re.compile(
    r"<input[^>]+name=['\"]csrfmiddlewaretoken['\"][^>]*>", re.IGNORECASE
)


def _strip_untranslatable(html: str) -> str:
    for pattern in _STRIP_PATTERNS:
        html = pattern.sub('', html)
    return _WHITESPACE.sub('\n\n', html).strip()


def _normalize_for_hash(html: str) -> str:
    """Strip request-specific content before hashing so the hash is deterministic."""
    return _CSRF_RE.sub('', html)


def _authorized(request) -> bool:
    expected = conf.get_callback_token()
    if not expected:
        logger.warning('CALLBACK_TOKEN no configurado — callback abierto')
        return True
    auth = request.headers.get('Authorization', '')
    return auth == f'Bearer {expected}'


def _render_sections(
    request,
    page_key: str = 'home',
) -> tuple[dict[str, str], dict[str, list[str]], str]:
    """
    Renderiza cada sección a HTML y extrae los textos visibles.

    El contexto base puede ser extendido por SECTION_CONTEXT_PROVIDER.
    Retorna (sections_html, sections_texts, source_hash).
    """
    ctx_provider = conf.get_section_context_provider()
    context: dict = ctx_provider(request, page_key) if ctx_provider else {}
    context.setdefault('lang_prefix', '/')

    sections_html: dict[str, str] = {}
    sections_texts: dict[str, list[str]] = {}
    total_chars = 0

    for section_key, template_path in get_sections(page_key):
        try:
            html = render_to_string(template_path, context, request=request)
            sections_html[section_key] = html
            extractor = HtmlTextExtractor(html)
            sections_texts[section_key] = extractor.get_texts()
            total_chars += len(html)
        except Exception as exc:
            logger.warning(
                'render_sections: error en %s (%s): %s',
                section_key, template_path, exc,
            )

    hash_payload = {k: _normalize_for_hash(v) for k, v in sections_html.items()}
    source_hash = TranslationCache.compute_hash(hash_payload)

    logger.info(
        'render_sections: %d secciones, %d KB, hash=%s...',
        len(sections_html), total_chars // 1024, source_hash[:16],
    )
    return sections_html, sections_texts, source_hash


def _render_for_page(
    request,
    page_key: str,
) -> tuple[dict[str, str], dict[str, list[str]], str]:
    """
    Selecciona el renderer correcto según el page_key.
    Si PAGE_RENDERERS define un renderer para este page_key (o wildcard), lo usa.
    En caso contrario, usa _render_sections con el SECTION_CONTEXT_PROVIDER.
    """
    renderer = conf.get_page_renderer(page_key)
    if renderer:
        return renderer(request, page_key)
    return _render_sections(request, page_key)


@csrf_exempt
@require_POST
def callback(request):
    """
    Recibe traducciones desde sistemas externos (n8n, webhooks).
    Requiere Authorization: Bearer {CALLBACK_TOKEN}.

    Body JSON esperado:
        {
          "page_key": "home",
          "lang": "en",
          "content": {
            "hero": ["Welcome", "Automate...", ...],
            ...
          }
        }
    """
    if not _authorized(request):
        logger.warning('Callback rechazado: token inválido')
        return JsonResponse({'error': 'unauthorized'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.error('Callback JSON inválido: %s', exc)
        return JsonResponse({'error': 'invalid json'}, status=400)

    page_key = payload.get('page_key')
    lang = payload.get('lang')
    content = payload.get('content')

    if not page_key or not lang or not isinstance(content, dict):
        return JsonResponse(
            {'error': 'missing fields: page_key, lang, content'},
            status=400,
        )

    unexpected = set(content.keys()) - get_all_section_keys()
    if unexpected:
        logger.warning(
            'Callback rechazado: claves desconocidas %s (page=%s lang=%s)',
            unexpected, page_key, lang,
        )
        return JsonResponse(
            {'error': 'schema mismatch', 'unexpected': list(unexpected)},
            status=400,
        )

    try:
        tc = TranslationCache.objects.get(page_key=page_key, lang=lang)
    except TranslationCache.DoesNotExist:
        return JsonResponse(
            {'error': 'no source_html found; call request_translation first'},
            status=409,
        )

    translated_html: dict[str, str] = {}
    for section_key, translated_texts in content.items():
        original_html = tc.source_html.get(section_key)
        if not original_html or not isinstance(translated_texts, list):
            continue
        try:
            extractor = HtmlTextExtractor(original_html)
            translated_html[section_key] = extractor.rebuild(translated_texts)
        except ValueError as exc:
            logger.error('Callback: error reconstruyendo %s: %s', section_key, exc)
            translated_html[section_key] = original_html

    tc.content = translated_html
    tc.save(update_fields=['content', 'updated_at'])
    _invalidate_cache(page_key)
    cache.delete(f'tr_pending:{page_key}:{lang}')

    hook = conf.get_on_translation_updated()
    if hook:
        try:
            hook(page_key)
        except Exception as exc:
            logger.warning('callback: ON_TRANSLATION_UPDATED hook falló — %s', exc)

    return JsonResponse({
        'ok': True,
        'page_key': tc.page_key,
        'lang': tc.lang,
        'sections': list(translated_html.keys()),
    })


def _translation_rate(group, request):
    return conf.get_rate_limit(settings.DEBUG)


@csrf_exempt
@require_POST
@ratelimit(key='ip', rate=_translation_rate, method='POST', block=True)
def request_translation(request):
    """
    Cliente pide generar traducción para un idioma.

    Body JSON:
        { "page_key": "home", "lang": "en" }

    Respuestas:
        { "status": "cached" }       — traducción lista, navegar a /{lang}/
        { "status": "generating" }   — en proceso, sondear de nuevo en 5s
        { "status": "base_language"} — es el idioma base, no se traduce
        { "status": "unavailable" }  — OPENAI_API_KEY no configurado
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'error': 'invalid json'}, status=400)

    page_key = payload.get('page_key')
    lang = payload.get('lang')

    if not page_key or not lang:
        return JsonResponse({'error': 'missing fields: page_key, lang'}, status=400)

    default_lang = conf.get_default_language()
    if lang == default_lang:
        return JsonResponse({'status': 'base_language'})

    _fresh_key = f'tr_fresh:{page_key}:{lang}'
    _pending_key = f'tr_pending:{page_key}:{lang}'

    # Shortcut rápido: traducción ya en caché y válida
    if cache.get(_fresh_key):
        try:
            tc = TranslationCache.objects.get(page_key=page_key, lang=lang)
            if tc.content:
                return JsonResponse({'status': 'cached'})
            # Fresh key obsoleto (thread falló o guardó vacío) — borrarlo y continuar
            cache.delete(_fresh_key)
        except TranslationCache.DoesNotExist:
            cache.delete(_fresh_key)

    # Shortcut rápido: traducción en curso — no re-renderizar ni lanzar otro thread
    if cache.get(_pending_key):
        return JsonResponse({'status': 'generating'})

    api_key = conf.get_openai_api_key()
    if not api_key:
        return JsonResponse(
            {'status': 'unavailable', 'reason': 'OPENAI_API_KEY not configured'},
            status=503,
        )

    _prerendered = None

    try:
        tc = TranslationCache.objects.get(page_key=page_key, lang=lang)

        sections_html, sections_texts, current_hash = _render_for_page(request, page_key)
        _prerendered = (sections_html, sections_texts, current_hash)

        if not tc.is_stale(current_hash):
            if tc.content:
                cache.set(_fresh_key, True, 300)  # válido 5 min
                return JsonResponse({'status': 'cached'})
            # Sin contenido y hash vigente: caer al flujo de _pending / nuevo thread
        else:
            logger.info(
                'Traducción obsoleta para %s/%s, regenerando...',
                page_key, lang,
            )
            cache.delete(_fresh_key)
            tc.source_html = sections_html
            tc.source_hash = current_hash
            tc.save(update_fields=['source_html', 'source_hash', 'updated_at'])
    except TranslationCache.DoesNotExist:
        pass

    if _prerendered:
        sections_html, sections_texts, current_hash = _prerendered
    else:
        sections_html, sections_texts, current_hash = _render_for_page(request, page_key)

    if not sections_html:
        return JsonResponse({'status': 'error', 'reason': 'no sections rendered'}, status=500)

    tc, created = TranslationCache.objects.get_or_create(
        page_key=page_key,
        lang=lang,
        defaults={
            'source_html': sections_html,
            'source_hash': current_hash,
            'content': {},
        },
    )
    if not created:
        tc.source_html = sections_html
        tc.source_hash = current_hash
        tc.save(update_fields=['source_html', 'source_hash', 'updated_at'])

    cache.set(_pending_key, True, 600)

    from .translator import translate_page
    threading.Thread(
        target=translate_page,
        args=(page_key, lang, sections_html, sections_texts),
        daemon=True,
    ).start()

    return JsonResponse({'status': 'generating'})
