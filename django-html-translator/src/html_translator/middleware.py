"""
LanguageMiddleware — resuelve request.LANGUAGE_CODE con esta prioridad:
  1. Prefijo de URL (/en/, /pt-br/, …)  ← SEO-friendly, autoritativo
  2. Cookie `lang`                        ← preferencia persistida del usuario
  3. Idioma por defecto (DEFAULT_LANGUAGE en TRANSLATIONS_CONFIG, o 'es')
"""
import re as _re

from django.http import HttpResponseRedirect

from . import conf

COOKIE_NAME = 'lang'
_LANG_RE = _re.compile(r'^[a-z]{2}(?:-[a-z]{2})?$')


def _lang_from_path(path: str) -> str | None:
    """Extrae el código de idioma del primer segmento de la URL, o None."""
    segment = path.strip('/').split('/')[0]
    default = conf.get_default_language()
    if _LANG_RE.fullmatch(segment) and segment != default:
        return segment
    return None


def _parse_accept_language(header: str) -> list[str]:
    """Retorna lista de códigos de idioma ordenados por q-value descendente."""
    langs = []
    for item in header.split(','):
        parts = item.strip().split(';')
        code = parts[0].strip().lower()
        if not code:
            continue
        q = 1.0
        for part in parts[1:]:
            part = part.strip()
            if part.startswith('q='):
                try:
                    q = float(part[2:])
                except ValueError:
                    pass
        langs.append((code, q))
    langs.sort(key=lambda x: x[1], reverse=True)
    return [code for code, _ in langs]


def _find_best_language(preferred: list[str], available: list[str], default: str) -> str | None:
    """Primer idioma de `preferred` que esté en `available` (con fallback a base, e.g. fr-FR→fr)."""
    if not available:
        return None
    for code in preferred:
        if code in available:
            return code
        base = code.split('-')[0]
        if base in available:
            return base
    return None


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        default = conf.get_default_language()
        available = conf.get_available_languages()

        path_lang = _lang_from_path(request.path_info)
        cookie_lang = request.COOKIES.get(COOKIE_NAME, '')
        
        logger.debug('LanguageMiddleware: path=%s, path_lang=%s, cookie_lang=%s, default=%s',
                     request.path_info, path_lang, cookie_lang, default)

        if path_lang:
            lang = path_lang
            logger.debug('LanguageMiddleware: using PATH lang=%s', lang)
        elif cookie_lang and (not available or cookie_lang in available):
            lang = cookie_lang
            logger.debug('LanguageMiddleware: using COOKIE lang=%s', lang)
        else:
            # Accept-Language como fallback antes de servir en default
            accept_header = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            if accept_header:
                preferred = _parse_accept_language(accept_header)
                best = _find_best_language(preferred, available, default)
                if best and best != default:
                    logger.debug('LanguageMiddleware: redirecting to %s based on Accept-Language', best)
                    return HttpResponseRedirect(f'/{best}/')
            lang = default
            logger.debug('LanguageMiddleware: using DEFAULT lang=%s', lang)

        request.LANGUAGE_CODE = lang
        logger.debug('LanguageMiddleware: request.LANGUAGE_CODE set to %s', lang)
        response = self.get_response(request)

        if path_lang and cookie_lang != path_lang:
            response.set_cookie(
                COOKIE_NAME, path_lang,
                max_age=31536000, path='/', samesite='Lax',
            )

        return response
