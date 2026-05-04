from django.db import models


def letter_colors_default():
    """JSONField default: lista vacía (solo primary hasta que se configuren posiciones)."""
    return []


class MorphBanner(models.Model):
    """
    Banner morph configurado por sitio.
    
    - sitepage = None: Sitio principal (SiteConfig singleton)
    - sitepage = SitePage: Página white-label específica
    
    Solo un MorphBanner por sitio (OneToOneField con unique=True).
    """
    
    sitepage = models.OneToOneField(
        'site_config.SitePage',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Página del sitio',
        help_text='Vacío = sitio principal (Magoreal). Solo uno por sitio.',
    )
    
    word = models.CharField(
        max_length=50,
        default='MAGOREAL',
        verbose_name='Palabra',
        help_text=(
            'Texto morph (solo A–Z, a–z, 0–9 y espacios). '
            'Cada espacio deja hueco horizontal entre grupos de letras.'
        ),
    )

    EFFECT_YOYO      = 'yoyo'
    EFFECT_ALWAYS    = 'always'
    EFFECT_REVEAL    = 'reveal'
    EFFECT_CASCADE   = 'cascade'
    EFFECT_SPOTLIGHT = 'spotlight'
    EFFECT_CHOICES = [
        (EFFECT_YOYO,      'Yoyo (actual)'),
        (EFFECT_ALWAYS,    'Sin desaparecer'),
        (EFFECT_REVEAL,    'Morph global + reveal'),
        (EFFECT_CASCADE,   'Cascada (letra a letra)'),
        (EFFECT_SPOTLIGHT, 'Spotlight'),
    ]

    effect = models.CharField(
        max_length=20,
        choices=EFFECT_CHOICES,
        default=EFFECT_YOYO,
        verbose_name='Efecto',
        help_text='Tipo de animación del banner.',
    )

    neon_style = models.BooleanField(
        default=False,
        verbose_name='Estilo neón',
        help_text=(
            'Añade un resplandor alrededor de cada glifo usando su propio color (efecto neón tipo cartel '
            'luminoso). Conviene con fondos oscuros.'
        ),
    )

    letter_colors = models.JSONField(
        default=letter_colors_default,
        blank=True,
        verbose_name='Colores por posición',
        help_text='Lista JSON ordenada por cada glifo renderizado en la palabra (espacios y símbolos sin '
                  'fuente morph se omiten): ["primary","accent","#3366CC", …]. Índice 0 = primera letra '
                  'visible, etc.; dos letras repetidas pueden tener dos colores distintos. Formatos legacy '
                  'tipo {"M":"accent"} siguen funcionando hasta que guardes desde el admin. '
                  'Valores: paleta (primary…) o hex #RRGGBB.',
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Morph Banner'
        verbose_name_plural = 'Morph Banners'
        ordering = ['-updated_at']
    
    def __str__(self):
        site_name = self.sitepage.site_name if self.sitepage else 'Sitio principal'
        return f'{self.word} - {site_name}'
    
    @classmethod
    def get_for_sitepage(cls, sitepage=None):
        """
        Get the MorphBanner for a specific sitepage (or the main site if None).
        Returns None if not found.
        """
        try:
            return cls.objects.get(sitepage=sitepage, is_active=True)
        except cls.DoesNotExist:
            # Fallback to main site banner if looking for a sitepage
            if sitepage is not None:
                try:
                    return cls.objects.get(sitepage__isnull=True, is_active=True)
                except cls.DoesNotExist:
                    pass
            return None
    
    @classmethod
    def get_default_colors(cls):
        """Lista vacía: todas las posiciones usan primary."""
        return []
