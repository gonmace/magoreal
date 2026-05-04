from django.db import models


class ProjectSEO(models.Model):
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug del proyecto',
        help_text='Debe coincidir exactamente con el nombre de la carpeta. Ej: 01-pozos-scz',
    )
    seo_title = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='Título SEO',
        help_text='Vacío = usa el título del proyecto. Máx 60 caracteres.',
    )
    seo_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name='Descripción SEO',
        help_text='Vacío = usa el subtítulo del proyecto. Máx 160 caracteres.',
    )

    class Meta:
        verbose_name = 'SEO de proyecto'
        verbose_name_plural = 'SEO de proyectos'
        ordering = ['slug']

    def __str__(self):
        return self.slug
