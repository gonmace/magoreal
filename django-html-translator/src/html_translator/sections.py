"""
Resolución de secciones traducibles por página.

Soporta múltiples formatos en PAGES:
  lista        → include explícito: ['hero', 'footer']
  '__all__'    → todas las secciones declaradas
  dict include → {'include': ['hero', 'footer']}
  dict exclude → {'exclude': ['sidebar']}
  wildcard     → 'blog-*' aplica a blog-foo, blog-bar, etc.

Registro dinámico de secciones (desde AppConfig.ready()):
  from html_translator.sections import register_section
  register_section('mi_banner', 'myapp/templates/_banner.html')
"""
from django.conf import settings

_extra_sections: list[tuple[str, str]] = []


def register_section(key: str, template_path: str) -> None:
    """
    Registra una sección adicional en tiempo de ejecución.
    Llamar desde AppConfig.ready() del proyecto consumidor.
    """
    _extra_sections.append((key, template_path))


def _get_all_sections() -> list[tuple[str, str]]:
    cfg = getattr(settings, 'TRANSLATIONS_CONFIG', {})
    return list(cfg.get('SECTIONS', [])) + _extra_sections


def _match_page(pages: dict, page_key: str):
    """Coincidencia exacta primero, luego wildcard (ej. 'blog-*')."""
    if page_key in pages:
        return pages[page_key]
    for pattern, cfg in pages.items():
        if pattern.endswith('-*') and page_key.startswith(pattern[:-1]):
            return cfg
    return None


def get_sections(page_key: str) -> list[tuple[str, str]]:
    """
    Retorna [(section_key, template_path), ...] para un page_key.

    Si PAGES no define el page_key (ni wildcard), devuelve todas las SECTIONS.
    """
    cfg = getattr(settings, 'TRANSLATIONS_CONFIG', {})
    pages = cfg.get('PAGES', {})
    all_sections = _get_all_sections()
    section_map = dict(all_sections)
    all_keys = [k for k, _ in all_sections]

    page_cfg = _match_page(pages, page_key)

    if page_cfg is None:
        keys = all_keys
    elif page_cfg == '__all__':
        keys = all_keys
    elif isinstance(page_cfg, list):
        keys = page_cfg
    elif isinstance(page_cfg, dict):
        include = page_cfg.get('include', '__all__')
        exclude = set(page_cfg.get('exclude', []))
        if include == '__all__':
            keys = [k for k in all_keys if k not in exclude]
        else:
            keys = [k for k in include if k not in exclude]
    else:
        keys = all_keys

    return [(k, section_map[k]) for k in keys if k in section_map]


def get_all_section_keys() -> frozenset:
    """Todas las claves declaradas (settings + registradas dinámicamente)."""
    return frozenset(k for k, _ in _get_all_sections())
