from django.db import models

DEFAULT_LOGO_SVG = """<svg viewBox="0 0 58 40" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Magoreal">
  <text x="0"  y="30" font-family="Inter, system-ui, sans-serif" font-weight="800" font-size="26" fill="#38BDF8">&lt;</text>
  <text x="14" y="30" font-family="Inter, system-ui, sans-serif" font-weight="800" font-size="26" fill="#FFFFFF">M</text>
  <text x="32" y="30" font-family="Inter, system-ui, sans-serif" font-weight="800" font-size="26" fill="#38BDF8">/&gt;</text>
</svg>"""


class SiteConfig(models.Model):
    """
    Configuración global del sitio — patrón singleton (siempre pk=1).
    Editable desde el admin de Django.
    """

    # ── Identidad ──────────────────────────────────────────────
    site_name = models.CharField(
        max_length=80,
        default='Magoreal Tecnología',
        verbose_name='Nombre del sitio',
    )
    tagline = models.CharField(
        max_length=160,
        default='Automatizamos tus procesos con IA. En tu propio sistema.',
        verbose_name='Slogan corto',
        help_text='Frase de una línea usada en meta tags y footer',
    )
    hero_title = models.TextField(
        default=(
            'Atendé clientes en WhatsApp.\n'
            'Automatizá tu logística.\n'
            'Pliegos técnicos con IA.'
        ),
        verbose_name='Título del hero',
        help_text=(
            'Soporta saltos de línea. Se renderiza con <br>. '
            'Tres líneas independientes — un pilar por línea.'
        ),
    )
    hero_subtitle = models.TextField(
        default=(
            'Tres ejemplos de IA corriendo sobre tus propios datos.\n'
            'Todo local, sin que tu información salga de tu infraestructura.'
        ),
        verbose_name='Subtítulo del hero',
        help_text='Cada salto de línea genera un párrafo separado.',
    )
    logo_svg = models.TextField(
        blank=True,
        default=DEFAULT_LOGO_SVG,
        verbose_name='Logo SVG',
        help_text='Código SVG completo del logo. Se renderiza inline.',
    )
    favicon = models.ImageField(
        upload_to='site_favicons/',
        blank=True,
        verbose_name='Favicon',
        help_text='SVG, PNG o ICO. Vacío = usa /static/img/favicon.svg',
    )

    # ── Contacto ───────────────────────────────────────────────
    email = models.EmailField(
        default='contacto@magoreal.com',
        verbose_name='Email de contacto público',
        help_text=(
            'Correo visible en la web (sección contacto, footer, JSON-LD). '
            'Se edita solo desde este admin — no requiere deploy.'
        ),
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Teléfono',
        help_text='Formato con país, ej: +591 7X XXX XXXX',
    )
    whatsapp_number = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Número de WhatsApp',
        help_text="Formato E.164 sin el '+', ej: 59170000000",
    )
    calendar_url = models.URLField(
        blank=True,
        verbose_name='URL de calendario',
        help_text='Link Cal.com, Calendly o similar para agendar llamadas',
    )
    city = models.CharField(
        max_length=80,
        default='Santa Cruz de la Sierra',
        verbose_name='Ciudad / ubicación',
    )
    privacy_policy_url = models.URLField(
        blank=True,
        verbose_name='URL política de privacidad',
        help_text='Enlace del footer “Privacidad”. Vacío = enlace # hasta que cargues la página.',
    )
    terms_url = models.URLField(
        blank=True,
        verbose_name='URL términos y condiciones',
        help_text='Enlace del footer “Términos”. Vacío = #.',
    )

    # ── Redes sociales ─────────────────────────────────────────
    github_url = models.URLField(blank=True, verbose_name='GitHub')
    linkedin_url = models.URLField(blank=True, verbose_name='LinkedIn')
    twitter_url = models.URLField(blank=True, verbose_name='Twitter / X')

    # ── Scripts inyectados en base.html ────────────────────────
    scripts_head = models.TextField(
        blank=True,
        verbose_name='Scripts en <head>',
        help_text=(
            'HTML inyectado en <head>. Usar para verificación de Search Console, '
            'meta tags custom, etc. Se renderiza con |safe.'
        ),
    )
    scripts_body_start = models.TextField(
        blank=True,
        verbose_name='Scripts al inicio de <body>',
        help_text='Ideal para Google Tag Manager. Se renderiza con |safe.',
    )
    scripts_body_end = models.TextField(
        blank=True,
        verbose_name='Scripts al final de <body>',
        help_text=(
            'Ideal para Plausible, Umami, Facebook Pixel, AdSense. '
            'Se renderiza con |safe.'
        ),
    )

    multilingual = models.BooleanField(
        default=True,
        verbose_name='Multilenguaje activo',
        help_text='Si está desactivado, no se muestra el selector de idioma en el menú.',
    )
    available_languages = models.CharField(
        max_length=60,
        default='es,en',
        verbose_name='Idiomas disponibles',
        help_text="Códigos ISO separados por coma. Ejemplo: es,en,pt",
    )

    # ── Webhooks seguros (shared secret) ───────────────────────
    contacto_webhook_secret = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Shared secret para webhook de contacto',
        help_text=(
            'Django envía X-Webhook-Secret con este valor al webhook n8n. '
            'El workflow n8n valida que coincida antes de procesar. '
            'Dejar vacío desactiva el reenvío — el mensaje solo se guarda en DB.'
        ),
    )
    pliego_demo_webhook_secret = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Shared secret para webhook de demo de pliego',
        help_text=(
            'Idem anterior, para el webhook que procesa PDFs subidos en el '
            'lead magnet de licitaciones (genera borrador + mail de entrega). '
            'URL del webhook en PLIEGO_DEMO_WEBHOOK_URL (.env).'
        ),
    )

    class Meta:
        verbose_name = 'Configuración del sitio'
        verbose_name_plural = 'Configuración del sitio'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Singleton: siempre pk=1 — impide crear múltiples instancias
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Recupera (o crea con defaults) la única instancia del sitio."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def whatsapp_link(self):
        """URL wa.me completa o None si no hay número."""
        return f'https://wa.me/{self.whatsapp_number}' if self.whatsapp_number else None

    @property
    def languages_list(self):
        """Lista de códigos de idioma limpios."""
        return [lang.strip() for lang in self.available_languages.split(',') if lang.strip()]


class SitePage(models.Model):
    """
    Página de cliente white-label — resuelta por dominio/subdominio.

    SiteConfig (singleton pk=1) sigue siendo el sitio principal de Magoreal.
    SitePage solo se activa cuando el request.get_host() coincide con `domain`.
    """

    # ── Resolución ─────────────────────────────────────────────
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug',
        help_text='Identificador único. Ej: cliente-a',
    )
    domain = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        verbose_name='Dominio',
        help_text='Dominio o subdominio que activa esta página. Ej: cliente.magoreal.com',
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_default = models.BooleanField(
        default=False,
        verbose_name='Por defecto',
        help_text='Si no hay coincidencia de dominio, usar esta página. Solo una puede ser default.',
    )

    # ── Identidad ──────────────────────────────────────────────
    site_name = models.CharField(
        max_length=80,
        default='',
        verbose_name='Nombre del sitio',
    )
    tagline = models.CharField(
        max_length=160,
        blank=True,
        verbose_name='Slogan corto',
    )
    hero_title = models.TextField(
        blank=True,
        verbose_name='Título del hero',
        help_text='Soporta saltos de línea. Se renderiza con <br>.',
    )
    hero_subtitle = models.TextField(
        blank=True,
        verbose_name='Subtítulo del hero',
        help_text='Cada salto de línea genera un párrafo separado.',
    )
    logo_svg = models.TextField(
        blank=True,
        verbose_name='Logo SVG',
        help_text='Código SVG completo del logo. Vacío = usa el de SiteConfig.',
    )

    # ── Tema ───────────────────────────────────────────────────
    THEME_CHOICES = [
        ('tron', 'Tron (Cyan)'),
        ('ares', 'Ares (Red)'),
        ('clu', 'Clu (Orange)'),
        ('athena', 'Athena (Gold)'),
        ('aphrodite', 'Aphrodite (Pink)'),
        ('poseidon', 'Poseidon (Blue)'),
    ]
    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default='tron',
        verbose_name='Tema visual',
    )
    default_language = models.CharField(
        max_length=5,
        default='es',
        verbose_name='Idioma por defecto',
        help_text='Código ISO. Ej: es, en, pt',
    )
    theme_color = models.CharField(
        max_length=7,
        default='#050A14',
        verbose_name='Theme color (meta tag)',
        help_text='Color para <meta name="theme-color"> y móviles.',
    )

    # ── Contacto ───────────────────────────────────────────────
    email = models.EmailField(
        blank=True,
        verbose_name='Email de contacto público',
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Teléfono',
        help_text='Formato con país, ej: +591 7X XXX XXXX',
    )
    whatsapp_number = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Número de WhatsApp',
        help_text="Formato E.164 sin el '+', ej: 59170000000",
    )
    calendar_url = models.URLField(
        blank=True,
        verbose_name='URL de calendario',
        help_text='Link Cal.com, Calendly o similar para agendar llamadas',
    )
    city = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Ciudad / ubicación',
    )
    privacy_policy_url = models.URLField(
        blank=True,
        verbose_name='URL política de privacidad',
    )
    terms_url = models.URLField(
        blank=True,
        verbose_name='URL términos y condiciones',
    )

    # ── Redes sociales ─────────────────────────────────────────
    github_url = models.URLField(blank=True, verbose_name='GitHub')
    linkedin_url = models.URLField(blank=True, verbose_name='LinkedIn')
    twitter_url = models.URLField(blank=True, verbose_name='Twitter / X')

    # ── Scripts inyectados ─────────────────────────────────────
    scripts_head = models.TextField(
        blank=True,
        verbose_name='Scripts en <head>',
        help_text='HTML inyectado en <head>. Se renderiza con |safe.',
    )
    scripts_body_start = models.TextField(
        blank=True,
        verbose_name='Scripts al inicio de <body>',
        help_text='Ideal para Google Tag Manager. Se renderiza con |safe.',
    )
    scripts_body_end = models.TextField(
        blank=True,
        verbose_name='Scripts al final de <body>',
        help_text='Ideal para Plausible, Umami, Pixel. Se renderiza con |safe.',
    )

    # ── Traducción ─────────────────────────────────────────────
    multilingual = models.BooleanField(
        default=True,
        verbose_name='Multilenguaje activo',
        help_text='Si está desactivado, no se muestra el selector de idioma en el menú.',
    )
    available_languages = models.CharField(
        max_length=60,
        default='es,en',
        verbose_name='Idiomas disponibles',
        help_text="Códigos ISO separados por coma. Ejemplo: es,en,pt",
    )

    # ── Webhooks seguros ───────────────────────────────────────
    contacto_webhook_secret = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Shared secret para webhook de contacto',
    )
    pliego_demo_webhook_secret = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Shared secret para webhook de demo de pliego',
    )

    # ── Media ──────────────────────────────────────────────────
    favicon = models.ImageField(
        upload_to='site_favicons/',
        blank=True,
        verbose_name='Favicon',
    )
    og_image = models.ImageField(
        upload_to='site_og/',
        blank=True,
        verbose_name='Imagen Open Graph',
        help_text='1200x630 recomendado. Se usa para og:image y Twitter Card.',
    )

    class Meta:
        verbose_name = 'Página de cliente'
        verbose_name_plural = 'Páginas de clientes'

    def __str__(self):
        return f"{self.site_name or self.slug} ({self.domain or 'sin dominio'})"

    @property
    def languages_list(self):
        return [lang.strip() for lang in self.available_languages.split(',') if lang.strip()]

    @property
    def whatsapp_link(self):
        return f'https://wa.me/{self.whatsapp_number}' if self.whatsapp_number else None

    @property
    def primary_rgb(self):
        """RGB array para el canvas JS. Ej: '0,212,255'"""
        return {
            'tron': '0,212,255',
            'ares': '255,51,51',
            'clu': '255,102,0',
            'athena': '255,215,0',
            'aphrodite': '255,20,147',
            'poseidon': '0,102,255',
        }.get(self.theme, '0,212,255')

    @property
    def accent_rgb(self):
        return {
            'tron': '0,255,136',
            'ares': '255,102,0',
            'clu': '255,51,51',
            'athena': '255,102,0',
            'aphrodite': '255,51,51',
            'poseidon': '0,255,136',
        }.get(self.theme, '0,255,136')
