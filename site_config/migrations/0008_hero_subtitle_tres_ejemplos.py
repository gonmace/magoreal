"""Nuevo copy del hero_subtitle — 'Tres ejemplos de IA corriendo sobre...'.

Migra desde cualquiera de los dos textos anteriores (el del 0002/0004 y
el del 0007) al nuevo. Si el admin lo editó manualmente a otra cosa,
lo deja como está.
"""

from django.db import migrations, models

PREV_SUBTITLES = [
    # Default original (pre-0007)
    (
        'Implementamos tres motores de IA corriendo sobre tus propios datos: '
        'chatbot oficial de WhatsApp Business, automatización logística con '
        'tracking en vivo, y generación de pliegos de especificaciones y '
        'licitaciones a partir de tus documentos técnicos. Sin mandar tu '
        'información afuera.'
    ),
    # Default de 0007 (tres motores + atención 24/7)
    (
        'Tres motores de IA sobre tus propios datos: atención 24/7 en '
        'WhatsApp Business, logística automatizada con tracking en vivo, '
        'y pliegos técnicos generados desde tus documentos. Sin mandar '
        'tu información afuera.'
    ),
]

NEW_HERO_SUBTITLE = (
    'Tres ejemplos de IA corriendo sobre tus propios datos: un '
    'chatbot de WhatsApp, automatización logística con tracking en '
    'vivo, y generación de pliegos y licitaciones a partir de tu '
    'documentación. Todo local, sin que tu información salga de tu '
    'infraestructura.'
)


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
        # Volver al texto del 0007 (última iteración previa)
        obj.hero_subtitle = PREV_SUBTITLES[1]
        obj.save(update_fields=['hero_subtitle'])


class Migration(migrations.Migration):

    dependencies = [
        ('site_config', '0007_hero_subtitle_align'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfig',
            name='hero_subtitle',
            field=models.TextField(
                default=NEW_HERO_SUBTITLE,
                verbose_name='Subtítulo del hero',
            ),
        ),
        migrations.RunPython(update_singleton, revert_singleton),
    ]
