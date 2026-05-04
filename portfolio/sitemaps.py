import datetime
from pathlib import Path

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .loaders import load_proyectos


def _mtime(path) -> datetime.date | None:
    try:
        return datetime.date.fromtimestamp(Path(path).stat().st_mtime)
    except OSError:
        return None


class LandingSitemap(Sitemap):
    """La home en el idioma por defecto."""
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['landing:index']

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        # Usa el mtime del template principal como proxy de cambios de contenido
        return _mtime(
            Path(settings.BASE_DIR) / 'landing' / 'templates' / 'landing' / 'index.html'
        )


class ProyectoSitemap(Sitemap):
    """Páginas de detalle de cada proyecto del portfolio."""
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        proyectos = load_proyectos(settings.PROYECTOS_DIR)
        for p in proyectos:
            p['_mtime'] = _mtime(Path(settings.PROYECTOS_DIR) / p['slug'] / 'metadata.json')
        return proyectos

    def location(self, proyecto):
        return reverse('portfolio:detalle', args=[proyecto['slug']])

    def lastmod(self, proyecto):
        return proyecto.get('_mtime')


class LandingTranslatedSitemap(Sitemap):
    """Home en todos los idiomas con traducción completa disponible."""
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        from html_translator.models import TranslationCache
        from html_translator.conf import get_default_language
        return list(
            TranslationCache.objects
            .filter(page_key='home')
            .exclude(content={})
            .exclude(lang=get_default_language())
            .values('lang', 'updated_at')
        )

    def location(self, item):
        return f'/{item["lang"]}/'

    def lastmod(self, item):
        return item['updated_at'].date()


class ProyectoTranslatedSitemap(Sitemap):
    """Detalle de proyecto en todos los idiomas con traducción disponible."""
    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        from html_translator.models import TranslationCache
        from html_translator.conf import get_default_language
        return [
            {'slug': e['page_key'][len('portfolio-'):], 'lang': e['lang'], 'updated_at': e['updated_at']}
            for e in TranslationCache.objects
            .filter(page_key__startswith='portfolio-')
            .exclude(content={})
            .exclude(lang=get_default_language())
            .values('page_key', 'lang', 'updated_at')
        ]

    def location(self, item):
        return f'/{item["lang"]}/proyectos/{item["slug"]}/'

    def lastmod(self, item):
        return item['updated_at'].date()
