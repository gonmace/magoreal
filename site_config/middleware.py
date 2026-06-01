"""
SitePageMiddleware — resuelve la página de cliente por dominio/subdominio.

Inyecta `request.sitepage` si el host coincide con un SitePage activo.
Si no hay match Y el host no es el principal de Magoreal, aplica el SitePage
marcado como `is_default` (útil para clientes sin dominio propio aún).
Si el host es de Magoreal (MAGOREAL_HOSTS), `request.sitepage = None` siempre.

SiteConfig (singleton pk=1) gestiona el sitio principal de Magoreal.
"""
from django.conf import settings
from .models import SitePage


class SitePageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        # 1. Buscar por dominio exacto (case-insensitive)
        page = SitePage.objects.filter(domain__iexact=host, is_active=True).first()
        # 2. Fallback is_default solo para dominios que NO son el host principal de Magoreal
        if not page and host not in getattr(settings, 'MAGOREAL_HOSTS', set()):
            page = SitePage.objects.filter(is_default=True, is_active=True).first()
        request.sitepage = page
        return self.get_response(request)
