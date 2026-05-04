"""
Admin del singleton SiteConfig (siempre pk=1).

Qué va en SiteConfig (editable acá, sin redeploy de código):
  identidad, hero, logo, canales públicos, legales del footer, redes,
  scripts de terceros, idiomas + webhook de traducción, secrets de webhooks.

Qué suele quedarse en .env / settings:
  SECRET_KEY, base de datos, ALLOWED_HOSTS, URLs de webhooks (CONTACTO_WEBHOOK_URL),
  credenciales SMTP/Sentry, LEADS_NOTIFY_EMAIL si querés un inbox distinto al público,
  claves de APIs — rotación y entornos separados.
"""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import PasswordInput
from django.utils.safestring import mark_safe
from .models import SiteConfig, SitePage


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    save_on_top = True
    readonly_fields = ['logo_preview']

    fieldsets = [
        (
            'Contacto público (web, footer, schema.org)',
            {
                'fields': [
                    'email',
                    'phone',
                    'whatsapp_number',
                    'calendar_url',
                    'city',
                ],
                'description': (
                    'El email y los canales se muestran en la landing. '
                    'Modificá el correo aquí; al guardar se actualiza en toda la web.'
                ),
            },
        ),
        ('Identidad y logo', {
            'fields': ['site_name', 'tagline', 'logo_svg', 'logo_preview', 'favicon'],
        }),
        ('Hero', {
            'fields': ['hero_title', 'hero_subtitle'],
        }),
        ('Redes sociales', {
            'fields': ['github_url', 'linkedin_url', 'twitter_url'],
            'classes': ['collapse'],
        }),
        (
            'Legal (footer)',
            {
                'fields': ['privacy_policy_url', 'terms_url'],
                'description': (
                    'Enlaces del pie de página. Si quedan vacíos, el template sigue '
                    'mostrando las entradas con # hasta que publiques las páginas.'
                ),
            },
        ),
        ('Scripts inyectados (AdSense, Search Console, Pixel, Analytics, etc.)', {
            'fields': ['scripts_head', 'scripts_body_start', 'scripts_body_end'],
            'classes': ['collapse'],
            'description': (
                'HTML/JS inyectado en el template base. Se renderiza sin escape. '
                'NO pegar código de fuentes no confiables.'
            ),
        }),
        ('Traducción / OpenAI', {
            'fields': ['openai_api_key', 'openai_model', 'multilingual', 'available_languages'],
            'classes': ['collapse'],
        }),
        ('Webhooks — shared secrets', {
            'fields': ['contacto_webhook_secret', 'pliego_demo_webhook_secret'],
            'classes': ['collapse'],
            'description': (
                'Secretos compartidos entre Django y los scripts de webhook. '
                'Rotar con cuidado — hay que actualizar ambos lados simultáneamente.'
            ),
        }),
    ]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['openai_api_key'].widget = PasswordInput(render_value=True)
        return form

    def logo_preview(self, obj):
        if not obj or not obj.logo_svg:
            return '(sin logo SVG definido — usará fallback de texto)'
        return mark_safe(
            f'<div style="padding:16px;background:#0F141E;border-radius:8px;'
            f'display:inline-block;margin-top:4px;">{obj.logo_svg}</div>'
        )
    logo_preview.short_description = 'Preview del logo (dark bg)'

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteConfig.objects.first()
        if obj:
            from django.urls import reverse
            from django.shortcuts import redirect
            return redirect(reverse('admin:site_config_siteconfig_change', args=[obj.pk]))
        return super().changelist_view(request, extra_context)


# ── SitePage Admin ─────────────────────────────────────────────────────────

THEME_PREVIEW_CSS = {
    'tron': '#00D4FF',
    'ares': '#FF3333',
    'clu': '#FF6600',
    'athena': '#FFD700',
    'aphrodite': '#FF1493',
    'poseidon': '#0066FF',
}


class SitePageAdminForm(forms.ModelForm):
    class Meta:
        model = SitePage
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('is_default'):
            # Solo un default permitido
            qs = SitePage.objects.filter(is_default=True)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    'Ya existe una página marcada como default. '
                    'Desmarcá la otra antes de activar esta.'
                )
        return cleaned


@admin.register(SitePage)
class SitePageAdmin(admin.ModelAdmin):
    form = SitePageAdminForm
    save_on_top = True
    list_display = ['slug', 'site_name', 'theme', 'domain', 'is_active', 'is_default']
    list_filter = ['theme', 'is_active', 'is_default']
    search_fields = ['slug', 'site_name', 'domain']
    readonly_fields = ['logo_preview', 'theme_preview']

    fieldsets = [
        (
            'Resolución',
            {
                'fields': ['slug', 'domain', 'is_active', 'is_default'],
                'description': (
                    'El dominio activa esta página cuando el visitante accede '
                    'desde ese host. Si no hay match, se usa la página default.'
                ),
            },
        ),
        (
            'Tema e idioma',
            {
                'fields': ['theme', 'theme_preview', 'default_language', 'theme_color'],
            },
        ),
        (
            'Identidad y logo',
            {
                'fields': ['site_name', 'tagline', 'logo_svg', 'logo_preview'],
                'description': 'Vacío = hereda de SiteConfig (Magoreal).',
            },
        ),
        (
            'Hero',
            {
                'fields': ['hero_title', 'hero_subtitle'],
                'description': 'Vacío = hereda de SiteConfig.',
            },
        ),
        (
            'Contacto público',
            {
                'fields': [
                    'email', 'phone', 'whatsapp_number',
                    'calendar_url', 'city',
                ],
                'description': 'Vacío = hereda de SiteConfig.',
            },
        ),
        (
            'Legal',
            {
                'fields': ['privacy_policy_url', 'terms_url'],
                'classes': ['collapse'],
            },
        ),
        (
            'Redes sociales',
            {
                'fields': ['github_url', 'linkedin_url', 'twitter_url'],
                'classes': ['collapse'],
            },
        ),
        (
            'Media',
            {
                'fields': ['favicon', 'og_image'],
                'description': 'Vacío = usa los assets por defecto de Magoreal.',
            },
        ),
        (
            'Scripts inyectados',
            {
                'fields': ['scripts_head', 'scripts_body_start', 'scripts_body_end'],
                'classes': ['collapse'],
            },
        ),
        (
            'Traducción',
            {
                'fields': ['multilingual', 'available_languages'],
                'classes': ['collapse'],
            },
        ),
        (
            'Webhooks — shared secrets',
            {
                'fields': ['contacto_webhook_secret', 'pliego_demo_webhook_secret'],
                'classes': ['collapse'],
            },
        ),
    ]

    def logo_preview(self, obj):
        if not obj or not obj.logo_svg:
            return '(sin logo SVG — se usará el de SiteConfig)'
        return mark_safe(
            f'<div style="padding:16px;background:#0F141E;border-radius:8px;'
            f'display:inline-block;margin-top:4px;">{obj.logo_svg}</div>'
        )
    logo_preview.short_description = 'Preview del logo (dark bg)'

    def theme_preview(self, obj):
        color = THEME_PREVIEW_CSS.get(obj.theme, '#00D4FF')
        return mark_safe(
            f'<div style="display:flex;gap:8px;align-items:center;margin-top:4px;">'
            f'<div style="width:32px;height:32px;border-radius:6px;'
            f'background:{color};box-shadow:0 0 12px {color}80;"></div>'
            f'<span style="font-family:monospace;font-size:13px;">{obj.theme} — {color}</span>'
            f'</div>'
        )
    theme_preview.short_description = 'Preview del tema'
