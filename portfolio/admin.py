from django.contrib import admin
from .models import ProjectSEO


@admin.register(ProjectSEO)
class ProjectSEOAdmin(admin.ModelAdmin):
    list_display = ('slug', 'seo_title', 'seo_description_preview')
    search_fields = ('slug', 'seo_title', 'seo_description')

    def seo_description_preview(self, obj):
        return obj.seo_description[:80] + '…' if len(obj.seo_description) > 80 else obj.seo_description
    seo_description_preview.short_description = 'Descripción SEO'
