from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from portfolio.sitemaps import LandingSitemap, ProyectoSitemap, LandingTranslatedSitemap, ProyectoTranslatedSitemap
from portfolio import views as portfolio_views
from landing import views as landing_views

sitemaps = {
    'landing': LandingSitemap,
    'proyectos': ProyectoSitemap,
    'landing-translated': LandingTranslatedSitemap,
    'proyectos-translated': ProyectoTranslatedSitemap,
}

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt',
        content_type='text/plain',
        extra_context={'ADMIN_URL': settings.ADMIN_URL},
    )),
    path('proyectos/', include('portfolio.urls', namespace='portfolio')),
    path('translations/', include('html_translator.urls', namespace='html_translator')),
    re_path(r'^(?P<lang>[a-z]{2}(?:-[a-z]{2})?)/proyectos/(?P<slug>[\w-]+)/$', portfolio_views.detalle, name='portfolio_detalle_lang'),
    # Rutas con prefijo de idioma para SEO — 2 letras
    re_path(r'^(?P<lang>[a-z]{2}(?:-[a-z]{2})?)/$', landing_views.index, name='landing_lang'),
    path('', include('landing.urls', namespace='landing')),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__reload__/', include('django_browser_reload.urls'))]
