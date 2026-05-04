"""
Traductor directo a OpenAI — una llamada por sección para logging granular.
Diseñado para ejecutarse en background thread desde views.request_translation().
"""
import json
import logging

from django.core.cache import cache
from openai import OpenAI

from . import conf
from .models import TranslationCache
from .templatetags.translations import _invalidate_cache
from .utils import HtmlTextExtractor

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a professional localizer, not a word-for-word translator.

Rules:
1. Return ONLY a JSON array of localized strings in EXACT SAME order as input
2. CRITICAL: Input has EXACTLY {n} items. Output MUST have EXACTLY {n} items
3. Use natural, idiomatic {lang} language
4. Preserve all placeholders ({{{{ }}}}, %, etc.)
5. Do NOT translate brand names or technical terms
6. COUNT INTEGRITY: HTML uses inline <span> tags; preserve exact item count
7. Output NOTHING else: no markdown, no explanation, no code fences"""


def _translate_section(client, model: str, texts: list[str], lang: str) -> list[str]:
    """Llama a OpenAI con la lista de textos. Valida conteo exacto."""
    n = len(texts)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': _SYSTEM_PROMPT.format(n=n, lang=lang)},
            {'role': 'user',   'content': json.dumps(texts, ensure_ascii=False)},
        ],
        temperature=0.1,
        max_tokens=16000,
    )
    raw = resp.choices[0].message.content.strip()
    translated = json.loads(raw)
    if not isinstance(translated, list):
        raise ValueError(f'respuesta no es lista: {type(translated).__name__}')
    if len(translated) != n:
        raise ValueError(f'conteo incorrecto: recibidos {len(translated)}, esperados {n}')
    return translated


def translate_page(
    page_key: str,
    lang: str,
    sections_html: dict[str, str],
    sections_texts: dict[str, list[str]],
) -> None:
    """
    Traduce todas las secciones de una página y guarda el resultado en TranslationCache.
    Ejecutar siempre en background thread — no retorna valor útil.
    """
    api_key = conf.get_openai_api_key()
    model = conf.get_openai_model()
    pending_key = f'tr_pending:{page_key}:{lang}'

    if not api_key:
        logger.error('translate_page: OPENAI_API_KEY no configurado')
        cache.delete(pending_key)
        return

    client = OpenAI(api_key=api_key)
    translated_html: dict[str, str] = {}

    for section_key, texts in sections_texts.items():
        if not texts:
            continue
        try:
            t_texts = _translate_section(client, model, texts, lang)
            extractor = HtmlTextExtractor(sections_html[section_key])
            translated_html[section_key] = extractor.rebuild(t_texts)
            logger.info(
                'translate_page: %s/%s [%s] OK — %d textos',
                page_key, lang, section_key, len(texts),
            )
        except Exception as exc:
            logger.error(
                'translate_page: %s/%s [%s] FALLO — %s',
                page_key, lang, section_key, exc,
            )
            translated_html[section_key] = sections_html.get(section_key, '')

    try:
        tc = TranslationCache.objects.get(page_key=page_key, lang=lang)
        tc.content = translated_html
        tc.save(update_fields=['content', 'updated_at'])
        logger.info(
            'translate_page: COMPLETADO %s/%s — %d secciones',
            page_key, lang, len(translated_html),
        )
    except TranslationCache.DoesNotExist:
        logger.error(
            'translate_page: TranslationCache no existe para %s/%s — descartando',
            page_key, lang,
        )
        return
    finally:
        cache.delete(pending_key)

    _invalidate_cache(page_key)
    cache.set(f'tr_fresh:{page_key}:{lang}', True, 300)

    hook = conf.get_on_translation_updated()
    if hook:
        try:
            hook(page_key)
        except Exception as exc:
            logger.warning('translate_page: ON_TRANSLATION_UPDATED hook falló — %s', exc)
