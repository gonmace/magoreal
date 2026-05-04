"""
SitePageMiddleware — resuelve la página de cliente por dominio/subdominio.

Inyecta `request.sitepage` si el host coincide con un SitePage activo.
Si no hay match, inyecta el SitePage marcado como `is_default`.
Si tampoco hay default, `request.sitepage = None`.

SiteConfig (singleton pk=1) sigue siendo el fallback principal de Magoreal.
"""
from .models import SitePage


class SitePageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        # 1. Buscar por dominio exacto (case-insensitive)
        page = SitePage.objects.filter(domain__iexact=host, is_active=True).first()
        # 2. Fallback: página marcada como default
        if not page:
            page = SitePage.objects.filter(is_default=True, is_active=True).first()
        request.sitepage = page
        return self.get_response(request)
