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
    sections_to_translate: list[str] | None = None,
) -> None:
    """
    Traduce las secciones especificadas de una página y guarda el resultado en TranslationCache.
    Si sections_to_translate es None, traduce todas las secciones.
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
    # Si no se especifica, traducir todas las secciones
    if sections_to_translate is None:
        sections_to_translate = list(sections_texts.keys())
    
    for section_key, texts in sections_texts.items():
        # Si la sección no está en la lista de traducción, usar HTML original
        if section_key not in sections_to_translate:
            translated_html[section_key] = sections_html[section_key]
            continue
        if not texts:
            # Si no hay textos, usar HTML original
            translated_html[section_key] = sections_html[section_key]
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
            # NO guardar el HTML original como traducción
            # Marcar como None para indicar que esta sección falló
            translated_html[section_key] = None

    try:
        tc = TranslationCache.objects.get(page_key=page_key, lang=lang)
        # Fusionar traducciones nuevas con contenido existente
        existing_content = tc.content.copy() if tc.content else {}
        merged_content = {}
        # Para cada sección en source_html, decidir qué contenido usar
        for section_key in tc.source_html.keys():
            if section_key in translated_html and translated_html[section_key] is not None:
                # Sección traducida exitosamente
                merged_content[section_key] = translated_html[section_key]
            elif section_key in existing_content and existing_content[section_key] != tc.source_html.get(section_key, ''):
                # Sección existente que no es el HTML original (traducción válida)
                merged_content[section_key] = existing_content[section_key]
            # Si la sección falló (None) o no hay traducción válida, no incluirla
            # Esto fuerza al sistema a usar el template original o reintentar
        
        # Si no hay ninguna traducción exitosa, marcar como fallido
        if not merged_content:
            logger.warning(
                'translate_page: TODAS las secciones fallaron para %s/%s — manteniendo contenido anterior',
                page_key, lang,
            )
            merged_content = existing_content if existing_content else {}
        else:
            tc.content = merged_content
            tc.save(update_fields=['content', 'updated_at'])
            logger.info(
                'translate_page: COMPLETADO %s/%s — %d secciones traducidas',
                page_key, lang, len(merged_content),
            )
    except TranslationCache.DoesNotExist:
        logger.error(
            'translate_page: TranslationCache no existe para %s/%s — descartando',
            page_key, lang,
        )
        return
    finally:
        cache.delete(pending_key)

    _invalidate_cache(page_key, specific_lang=lang)
    cache.set(f'tr_fresh:{page_key}:{lang}', True, 300)

    hook = conf.get_on_translation_updated()
    if hook:
        try:
            hook(page_key)
        except Exception as exc:
            logger.warning('translate_page: ON_TRANSLATION_UPDATED hook falló — %s', exc)
