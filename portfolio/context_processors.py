from django.conf import settings

from .loaders import load_proyectos

_cache = None
_cache_key = None


def _build_cache_key():
    """
    En desarrollo, invalida cache si cambia algún metadata.json.
    En producción dejamos cache estable en memoria.
    """
    if not getattr(settings, "DEBUG", False):
        return "prod-static"
    root = settings.PROYECTOS_DIR
    try:
        from pathlib import Path

        p = Path(root)
        if not p.exists():
            return ("missing", 0.0)
        mtimes = [f.stat().st_mtime for f in p.glob("*/metadata.json") if f.is_file()]
        if not mtimes:
            return ("empty", 0.0)
        return ("debug", max(mtimes), len(mtimes))
    except OSError:
        return ("error", 0.0)


def get_proyectos():
    """Versión sin request — reutilizable en vistas. Usa el mismo caché."""
    global _cache, _cache_key
    key = _build_cache_key()
    if _cache is None or _cache_key != key:
        _cache = load_proyectos(settings.PROYECTOS_DIR)
        _cache_key = key
    return _cache


def proyectos_context(request):
    """
    Expone {{ proyectos }} a todos los templates. Cache de módulo — se
    recarga solo al reiniciar el proceso Gunicorn.
    """
    global _cache, _cache_key
    key = _build_cache_key()
    if _cache is None or _cache_key != key:
        _cache = load_proyectos(settings.PROYECTOS_DIR)
        _cache_key = key
    return {'proyectos': _cache}


def _reset_cache():
    """Helper para tests: limpia el cache en memoria."""
    global _cache, _cache_key
    _cache = None
    _cache_key = None
