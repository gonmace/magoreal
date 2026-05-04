import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone


# Storage aislado del MEDIA público: los PDFs del lead magnet de licitaciones
# viven fuera del MEDIA_ROOT que sirve nginx. Solo Django los toca.
# Callable: Django 5+ resuelve en cada operación, así los tests pueden usar
# override_settings(PLIEGOS_UPLOAD_ROOT=...) sin reimportar el módulo.
def _pliegos_storage():
    return FileSystemStorage(location=settings.PLIEGOS_UPLOAD_ROOT)


def _pliego_upload_to(instance, filename):
    """Path bajo el storage: YYYY/MM/uuid.pdf (descarta el nombre original)."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.pdf',):
        ext = '.pdf'
    ts = timezone.now()
    return f'{ts:%Y}/{ts:%m}/{uuid.uuid4().hex}{ext}'


class ContactMessage(models.Model):
    """Mensaje recibido del formulario de contacto."""

    INTERES_CHOICES = [
        ('web',  'Desarrollo web a medida'),
        ('ia',   'Automatización con IA'),
        ('infra', 'Infraestructura self-hosted'),
        ('chat', 'Integraciones & chatbots'),
        ('otro', 'Otro / no estoy seguro'),
    ]

    nombre        = models.CharField(max_length=120)
    email         = models.EmailField()
    empresa       = models.CharField(max_length=120, blank=True)
    interes       = models.CharField(max_length=10, choices=INTERES_CHOICES, default='otro')
    mensaje       = models.TextField(max_length=2000)
    meta_origen   = models.CharField(max_length=120, blank=True,
                                     help_text='Path de la página desde donde se envió')

    sitepage = models.ForeignKey(
        'site_config.SitePage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Página de origen',
        help_text='SitePage desde donde se envió el mensaje (si aplica).',
    )

    creado_en     = models.DateTimeField(auto_now_add=True)
    enviado_n8n   = models.BooleanField(default=False,
                                        help_text='True si el webhook n8n respondió 2xx')
    respondido    = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Mensaje de contacto'
        verbose_name_plural = 'Mensajes de contacto'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.nombre} <{self.email}> ({self.get_interes_display()})'


class PliegoDemoLead(models.Model):
    """
    Prospecto que subió un TDR/compulsa al lead magnet de licitaciones.
    El PDF se guarda en un storage separado del MEDIA público.
    """

    nombre = models.CharField(max_length=120)
    email = models.EmailField()
    empresa = models.CharField(max_length=120, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    consentimiento = models.BooleanField(
        default=False,
        verbose_name='Opt-in',
        help_text='Aceptó recibir el borrador + seguimiento comercial',
    )

    pdf_original = models.FileField(
        storage=_pliegos_storage,
        upload_to=_pliego_upload_to,
        max_length=255,
        verbose_name='PDF original',
        help_text='TDR/compulsa subido por el prospecto (fuera del MEDIA público)',
    )
    pdf_filename_original = models.CharField(
        max_length=255, blank=True,
        verbose_name='Nombre original',
        help_text='Filename tal como llegó (el archivo se guarda con UUID)',
    )
    pdf_size_bytes = models.PositiveIntegerField(
        default=0, verbose_name='Tamaño (bytes)',
    )

    meta_origen = models.CharField(
        max_length=120, blank=True,
        help_text='Path de la página desde donde se envió',
    )

    sitepage = models.ForeignKey(
        'site_config.SitePage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Página de origen',
        help_text='SitePage desde donde se envió el lead (si aplica).',
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    enviado_n8n = models.BooleanField(
        default=False,
        help_text='True si el webhook n8n respondió 2xx',
    )
    borrador_entregado = models.BooleanField(
        default=False,
        help_text='Marcar cuando el borrador de pliego fue enviado al prospecto',
    )
    respondido = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Lead de pliego (demo)'
        verbose_name_plural = 'Leads de pliego (demo)'
        ordering = ['-creado_en']

    def __str__(self):
        empresa = self.empresa or 'sin empresa'
        return f'{self.nombre} <{self.email}> · {empresa}'
