"""
Template tags para renderizar imágenes responsive con <picture> + WebP fallback.

Uso:
    {% load portfolio_tags %}
    {% picture "proyectos/01-pozos-scz/screenshots/1.jpg" alt="Mapa operativo" class="w-full" %}

Busca automáticamente:
  - Variante .webp al lado del original → source type="image/webp"
  - Variante -800w.webp si existe → srcset responsive
"""
import os
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()


@register.filter
def label_key(value):
    """'clientes_atendidos' → 'Clientes Atendidos'"""
    return str(value).replace('_', ' ').title()


def _exists(media_path: str) -> bool:
    """Verifica si el archivo existe en MEDIA_ROOT."""
    if not media_path:
        return False
    abs_path = os.path.join(settings.MEDIA_ROOT, media_path)
    return os.path.isfile(abs_path)


def _webp_variant(path: str) -> str:
    """proyectos/foo/bar.jpg → proyectos/foo/bar.webp"""
    stem, _ = os.path.splitext(path)
    return f"{stem}.webp"


def _responsive_variant(path: str, width: int) -> str:
    """proyectos/foo/bar.jpg → proyectos/foo/bar-800w.webp"""
    stem, _ = os.path.splitext(path)
    return f"{stem}-{width}w.webp"


@register.simple_tag
def picture(path, alt='', css_class='', loading='lazy', sizes='(max-width: 768px) 100vw, 50vw', eager=False):
    """
    Renderiza <picture> con WebP + fallback al original.
    Si existe variante -800w.webp, se usa en srcset para viewports chicos.
    """
    if not path:
        return ''

    media_url = settings.MEDIA_URL.rstrip('/')
    orig_url = f"{media_url}/{path}"
    webp_rel = _webp_variant(path)
    webp_url = f"{media_url}/{webp_rel}"
    has_webp = _exists(webp_rel)

    resp_rel = _responsive_variant(path, 800)
    has_resp = _exists(resp_rel)
    resp_url = f"{media_url}/{resp_rel}" if has_resp else None

    loading_attr = 'eager' if eager else loading
    class_attr = f' class="{escape(css_class)}"' if css_class else ''
    alt_attr = escape(alt)

    parts = ['<picture>']

    if has_webp:
        srcset = f"{webp_url}"
        if resp_url:
            # 800w para viewports chicos, original para grandes
            srcset = f"{resp_url} 800w, {webp_url} 1600w"
            parts.append(
                f'<source type="image/webp" srcset="{srcset}" sizes="{escape(sizes)}">'
            )
        else:
            parts.append(f'<source type="image/webp" srcset="{srcset}">')

    parts.append(
        f'<img src="{orig_url}" alt="{alt_attr}" loading="{loading_attr}" '
        f'decoding="async"{class_attr}>'
    )
    parts.append('</picture>')
    return mark_safe(''.join(parts))
