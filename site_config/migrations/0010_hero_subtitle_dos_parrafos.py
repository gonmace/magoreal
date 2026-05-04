"""Divide el hero_subtitle en dos párrafos separados por \\n.

El template lo renderiza con un <p> por línea.
"""

from django.db import migrations, models

PREV_SUBTITLES = [
    # Pre-0007
    (
        'Implementamos tres motores de IA corriendo sobre tus propios datos: '
        'chatbot oficial de WhatsApp Business, automatización logística con '
        'tracking en vivo, y generación de pliegos de especificaciones y '
        'licitaciones a partir de tus documentos técnicos. Sin mandar tu '
        'información afuera.'
    ),
    # 0007
    (
        'Tres motores de IA sobre tus propios datos: atención 24/7 en '
        'WhatsApp Business, logística automatizada con tracking en vivo, '
        'y pliegos técnicos generados desde tus documentos. Sin mandar '
        'tu información afuera.'
    ),
    # 0008
    (
        'Tres ejemplos de IA corriendo sobre tus propios datos: un '
        'chatbot de WhatsApp, automatización logística con tracking en '
        'vivo, y generación de pliegos y licitaciones a partir de tu '
        'documentación. Todo local, sin que tu información salga de tu '
        'infraestructura.'
    ),
    # 0009 (una sola línea, sin \n)
    (
        'Tres ejemplos de IA corriendo sobre tus propios datos. '
        'Todo local, sin que tu información salga de tu infraestructura.'
    ),
]

NEW_HERO_SUBTITLE = (
    'Tres ejemplos de IA corriendo sobre tus propios datos.\n'
    'Todo local, sin que tu información salga de tu infraestructura.'
)

NEW_HELP_TEXT = 'Cada salto de línea genera un párrafo separado.'


def update_singleton(apps, schema_editor):
    SiteConfig = apps.get_model('site_config', 'SiteConfig')
    obj = SiteConfig.objects.filter(pk=1).first()
    if obj and obj.hero_subtitle in PREV_SUBTITLES:
        obj.hero_subtitle = NEW_HERO_SUBTITLE
        obj.save(update_fields=['hero_subtitle'])


def revert_singleton(apps, schema_editor):
    SiteConfig = apps.get_model('site_config', 'SiteConfig')
    obj = SiteConfig.objects.filter(pk=1).first()
    if obj and obj.hero_subtitle == NEW_HERO_SUBTITLE:
        obj.hero_subtitle = PREV_SUBTITLES[3]  # 0009
        obj.save(update_fields=['hero_subtitle'])


class Migration(migrations.Migration):

    dependencies = [
        ('site_config', '0009_hero_subtitle_conciso'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfig',
            name='hero_subtitle',
            field=models.TextField(
                default=NEW_HERO_SUBTITLE,
                verbose_name='Subtítulo del hero',
                help_text=NEW_HELP_TEXT,
            ),
        ),
        migrations.RunPython(update_singleton, revert_singleton),
    ]
