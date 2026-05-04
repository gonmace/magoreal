from django.contrib import admin, messages
from django.forms import PasswordInput

from .models import TranslationCache, TranslatorConfig
from .templatetags.translations import _invalidate_cache


# ---------------------------------------------------------------------------
# TranslatorConfig — singleton de configuración
# ---------------------------------------------------------------------------

@admin.register(TranslatorConfig)
class TranslatorConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('OpenAI', {
            'fields': ('openai_api_key', 'openai_model'),
            'description': (
                'Deja en blanco para usar los valores de settings.py. '
                'Los valores aquí tienen prioridad sobre settings.py.'
            ),
        }),
        ('Idiomas', {
            'fields': ('default_language', 'available_languages'),
        }),
        ('Webhook / Callback', {
            'fields': ('callback_token',),
            'classes': ('collapse',),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['openai_api_key'].widget = PasswordInput(render_value=True)
        form.base_fields['callback_token'].widget = PasswordInput(render_value=True)
        return form

    def has_add_permission(self, request):
        return not TranslatorConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirige directamente a la edición del singleton."""
        obj, _ = TranslatorConfig.objects.get_or_create(pk=1)
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(
            reverse('admin:html_translator_translatorconfig_change', args=[obj.pk])
        )


# ---------------------------------------------------------------------------
# TranslationCache — caché de traducciones
# ---------------------------------------------------------------------------

@admin.action(description='Invalidar caché en memoria (fuerza reload próximo request)')
def invalidate_cache(modeladmin, request, queryset):
    for obj in queryset:
        _invalidate_cache(obj.page_key)
    messages.success(
        request,
        'Caché de traducciones invalidado. Próximo page load recargará desde DB.',
    )


@admin.action(description='Borrar y forzar regeneración')
def delete_and_regenerate(modeladmin, request, queryset):
    page_keys = set(queryset.values_list('page_key', flat=True))
    count = queryset.count()
    queryset.delete()
    for pk in page_keys:
        _invalidate_cache(pk)
    messages.success(
        request,
        f'{count} traducción(es) borrada(s). La próxima visita en ese idioma disparará una nueva.',
    )


@admin.register(TranslationCache)
class TranslationCacheAdmin(admin.ModelAdmin):
    list_display = ('page_key', 'lang', 'updated_at', 'content_preview', 'status_badge')
    list_filter = ('lang',)
    search_fields = ('page_key',)
    readonly_fields = ('updated_at', 'source_hash')
    actions = [invalidate_cache, delete_and_regenerate]

    def content_preview(self, obj):
        keys = list((obj.content or {}).keys())
        joined = ', '.join(keys[:3])
        suffix = '...' if len(keys) > 3 else ''
        return f'{len(keys)} sección(es): {joined}{suffix}'
    content_preview.short_description = 'Secciones traducidas'

    def status_badge(self, obj):
        if not obj.content:
            return 'Pendiente' if obj.source_hash else 'Vacío'
        return 'OK'
    status_badge.short_description = 'Estado'
