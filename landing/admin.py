import csv
import os

from django.contrib import admin, messages
from django.http import FileResponse, Http404, HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import ContactMessage, PliegoDemoLead


@admin.action(description='Exportar seleccionados a CSV')
def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="contactos.csv"'
    response.write('\ufeff')  # BOM para que Excel abra UTF-8 correctamente

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Creado', 'Nombre', 'Email', 'Empresa', 'Interes',
        'Mensaje', 'Origen', 'Enviado a n8n', 'Respondido',
    ])
    for m in queryset.order_by('creado_en'):
        writer.writerow([
            m.id,
            m.creado_en.strftime('%Y-%m-%d %H:%M'),
            m.nombre, m.email, m.empresa,
            m.get_interes_display(),
            m.mensaje,
            m.meta_origen,
            'Sí' if m.enviado_n8n else 'No',
            'Sí' if m.respondido else 'No',
        ])
    return response


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'empresa', 'interes', 'creado_en', 'enviado_n8n', 'respondido')
    list_filter = ('interes', 'respondido', 'enviado_n8n', 'creado_en')
    search_fields = ('nombre', 'email', 'empresa', 'mensaje')
    readonly_fields = ('creado_en', 'enviado_n8n', 'meta_origen')
    list_editable = ('respondido',)
    date_hierarchy = 'creado_en'
    actions = [export_to_csv]

    fieldsets = [
        ('Remitente', {
            'fields': ('nombre', 'email', 'empresa'),
        }),
        ('Consulta', {
            'fields': ('interes', 'mensaje'),
        }),
        ('Estado', {
            'fields': ('respondido', 'enviado_n8n', 'meta_origen', 'creado_en'),
        }),
    ]


@admin.action(description='Exportar leads de pliego a CSV')
def export_pliego_leads_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="pliego-leads.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Creado', 'Nombre', 'Email', 'Empresa', 'Teléfono',
        'PDF (nombre original)', 'Tamaño', 'Origen',
        'Enviado a n8n', 'Borrador entregado', 'Respondido',
    ])
    for lead in queryset.order_by('creado_en'):
        writer.writerow([
            lead.id,
            lead.creado_en.strftime('%Y-%m-%d %H:%M'),
            lead.nombre, lead.email, lead.empresa, lead.telefono,
            lead.pdf_filename_original, lead.pdf_size_bytes,
            lead.meta_origen,
            'Sí' if lead.enviado_n8n else 'No',
            'Sí' if lead.borrador_entregado else 'No',
            'Sí' if lead.respondido else 'No',
        ])
    return response


@admin.register(PliegoDemoLead)
class PliegoDemoLeadAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'email', 'empresa', 'creado_en',
        'enviado_n8n', 'borrador_entregado', 'respondido',
    )
    list_filter = ('borrador_entregado', 'enviado_n8n', 'respondido', 'creado_en')
    search_fields = ('nombre', 'email', 'empresa', 'pdf_filename_original')
    readonly_fields = (
        'creado_en', 'enviado_n8n', 'meta_origen',
        'pdf_filename_original', 'pdf_size_bytes', 'pdf_download_link',
    )
    list_editable = ('borrador_entregado', 'respondido')
    date_hierarchy = 'creado_en'
    actions = [export_pliego_leads_csv]

    fieldsets = [
        ('Prospecto', {
            'fields': ('nombre', 'email', 'empresa', 'telefono'),
        }),
        ('PDF subido', {
            'fields': (
                'pdf_original',
                'pdf_filename_original',
                'pdf_size_bytes',
                'pdf_download_link',
            ),
        }),
        ('Estado', {
            'fields': (
                'consentimiento',
                'borrador_entregado',
                'respondido',
                'enviado_n8n',
                'meta_origen',
                'creado_en',
            ),
        }),
    ]

    def pdf_download_link(self, obj):
        if not obj or not obj.pk or not obj.pdf_original:
            return '—'
        url = reverse('admin:landing_pliegodemolead_download', args=[obj.pk])
        label = obj.pdf_filename_original or os.path.basename(obj.pdf_original.name)
        return format_html(
            '<a href="{}" class="button">Descargar</a>'
            ' <span style="color:#666">{}</span>',
            url, label,
        )
    pdf_download_link.short_description = 'Descargar PDF'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:lead_id>/download/',
                self.admin_site.admin_view(self.download_pdf),
                name='landing_pliegodemolead_download',
            ),
        ]
        return custom + urls

    def download_pdf(self, request, lead_id):
        """Stream seguro del PDF — solo staff, vive fuera del MEDIA público."""
        try:
            lead = PliegoDemoLead.objects.get(pk=lead_id)
        except PliegoDemoLead.DoesNotExist:
            raise Http404
        if not lead.pdf_original:
            messages.error(request, 'Este lead no tiene PDF asociado.')
            raise Http404
        filename = lead.pdf_filename_original or 'pliego.pdf'
        return FileResponse(
            lead.pdf_original.open('rb'),
            as_attachment=True,
            filename=filename,
            content_type='application/pdf',
        )
