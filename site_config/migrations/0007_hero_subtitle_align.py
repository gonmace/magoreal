"""Alinea el hero_subtitle con el nuevo H1 (tres pilares en mismo orden)."""

from django.db import migrations, models

OLD_HERO_SUBTITLE = (
    'Implementamos tres motores de IA corriendo sobre tus propios datos: '
    'chatbot oficial de WhatsApp Business, automatización logística con '
    'tracking en vivo, y generación de pliegos de especificaciones y '
    'licitaciones a partir de tus documentos técnicos. Sin mandar tu '
    'información afuera.'
)
NEW_HERO_SUBTITLE = (
    'Tres motores de IA sobre tus propios datos: atención 24/7 en '
    'WhatsApp Business, logística automatizada con tracking en vivo, '
    'y pliegos técnicos generados desde tus documentos. Sin mandar '
    'tu información afuera.'
)


def update_singleton(apps, schema_editor):
    SiteConfig = apps.get_model('site_config', 'SiteConfig')
    obj = SiteConfig.objects.filter(pk=1).first()
    if obj and obj.hero_subtitle == OLD_HERO_SUBTITLE:
        obj.hero_subtitle = NEW_HERO_SUBTITLE
        obj.save(update_fields=['hero_subtitle'])


def revert_singleton(apps, schema_editor):
    SiteConfig = apps.get_model('site_config', 'SiteConfig')
    obj = SiteConfig.objects.filter(pk=1).first()
    if obj and obj.hero_subtitle == NEW_HERO_SUBTITLE:
        obj.hero_subtitle = OLD_HERO_SUBTITLE
        obj.save(update_fields=['hero_subtitle'])


class Migration(migrations.Migration):

    dependencies = [
        ('site_config', '0006_hero_title_tres_pilares'),
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
