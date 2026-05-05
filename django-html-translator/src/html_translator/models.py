import hashlib
import json

from django.db import models


class TranslatorConfig(models.Model):
    """
    Configuración singleton del traductor, editable desde el panel de administración.

    Los valores aquí tienen prioridad sobre TRANSLATIONS_CONFIG en settings.py,
    excepto SECTIONS y PAGES que siguen viviendo en settings (apuntan a templates).
    """

    openai_api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='API Key de OpenAI',
        help_text='sk-... Deja en blanco para usar el valor de settings.py.',
    )
    openai_model = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='Modelo de OpenAI',
        help_text='Ej: gpt-4o-mini. Deja en blanco para usar el valor de settings.py.',
    )
    callback_token = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Token de callback',
        help_text='Token Bearer para el endpoint /translations/callback/.',
    )
    default_language = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Idioma por defecto',
        help_text='Ej: es. Deja en blanco para usar el valor de settings.py.',
    )
    available_languages = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Idiomas disponibles',
        help_text='Lista JSON de códigos ISO, ej: ["en", "pt-br"]. Lista vacía = sin restricción.',
    )

    class Meta:
        verbose_name = 'Configuración del traductor'
        verbose_name_plural = 'Configuración del traductor'

    def __str__(self):
        return 'Configuración del traductor'

    @classmethod
    def get_solo(cls):
        """Devuelve la instancia única, creándola si no existe."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        from .conf import invalidate_db_cache
        invalidate_db_cache()


class TranslationCache(models.Model):
    """
    Almacena el resultado de traducir una página a un idioma.

    page_key identifica la página: "home", "blog-mi-post", etc.
    content guarda el HTML traducido por sección.
    source_html guarda el HTML original (idioma base) por sección.
    source_hash detecta cambios en los templates y marca traducciones obsoletas.
    """

    page_key = models.CharField(
        max_length=80,
        verbose_name='Clave de página',
        help_text='Identificador del bloque traducido, ej: "home", "blog-intro"',
    )
    lang = models.CharField(
        max_length=10,
        verbose_name='Idioma',
        help_text='Código ISO: en, pt-br, fr...',
    )
    content = models.JSONField(
        default=dict,
        verbose_name='Contenido traducido',
        help_text='HTML traducido por sección, ej: {"hero": "<div>...</div>"}',
    )
    source_html = models.JSONField(
        default=dict,
        verbose_name='HTML origen',
        help_text='HTML original del idioma base por sección',
    )
    source_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Hash del origen',
        help_text='SHA-256 del source_html; si cambia, la traducción está obsoleta',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('page_key', 'lang')]
        verbose_name = 'Caché de traducción'
        verbose_name_plural = 'Cachés de traducción'
        ordering = ['page_key', 'lang']

    def __str__(self):
        return f'{self.page_key} → {self.lang}'

    def is_stale(self, current_hash: str) -> bool:
        """True si el contenido original cambió desde la última traducción."""
        if not self.source_hash:
            return True
        return self.source_hash != current_hash

    def stale_sections(self, current_sections_html: dict) -> list[str]:
        """
        Devuelve lista de claves de sección cuyo HTML ha cambiado.
        Compara el hash SHA-256 de cada sección individual.
        """
        stale = []
        for section_key, html in current_sections_html.items():
            old_html = self.source_html.get(section_key, '')
            if not old_html:
                stale.append(section_key)
                continue
            current_hash = self.compute_hash({section_key: html})
            old_hash = self.compute_hash({section_key: old_html})
            if current_hash != old_hash:
                stale.append(section_key)
        return stale

    @staticmethod
    def compute_hash(source: dict) -> str:
        """SHA-256 canónico del HTML/textos fuente para detectar cambios de template."""
        canonical = json.dumps(source, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
