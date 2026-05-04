"""
Vistas de detalle de proyectos. Implementación completa en Sprint 2.
"""
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings

from .context_processors import get_proyectos
from .models import ProjectSEO


def detalle(request, slug, lang=None):
    """Página de detalle de un proyecto. Sprint 2."""
    from html_translator.conf import get_default_language
    if lang and lang == get_default_language():
        return redirect(reverse('portfolio:detalle', args=[slug]), permanent=True)

    proyecto = next((p for p in get_proyectos() if p['slug'] == slug), None)
    if proyecto is None:
        raise Http404(f"Proyecto '{slug}' no encontrado")

    seo = ProjectSEO.objects.filter(slug=slug).first()
    return render(request, 'portfolio/proyecto_detalle.html', {
        'proyecto': proyecto,
        'seo': seo,
    })
