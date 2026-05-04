"""Sprint 8 — Bloque 1: capa de mensaje del hero.

Actualiza defaults de hero_title y hero_subtitle al nuevo posicionamiento
(3 pilares: WhatsApp AI, logística, pliegos con IA) y migra el singleton
existente SOLO si conserva el texto del default anterior (no pisa cambios
hechos desde el admin).
"""

from django.db import migrations, models


OLD_HERO_TITLE = (
    'Automatizamos tus procesos con IA.\n'
    'En tu propio sistema, sin cobros por usuario.'
)
NEW_HERO_TITLE = (
    'IA que atiende tu WhatsApp,\n'
    'coordina tu logística\n'
    'y arma tus pliegos.'
)

OLD_HERO_SUBTITLE = (
    'Ayudamos a empresas de Latinoamérica y más allá a reemplazar '
    'servicios mensuales caros y desplegar sistemas con IA en su '
    'propio sistema — sin cobros por usuario, sin datos afuera.'
)
NEW_HERO_SUBTITLE = (
    'Implementamos tres motores de IA corriendo sobre tus propios datos: '
    'chatbot oficial de WhatsApp Business, automatización logística con '
    'tracking en vivo, y generación de pliegos de especificaciones y '
    'licitaciones a partir de tus documentos técnicos. Sin mandar tu '
    'información afuera.'
)

NEW_HERO_TITLE_HELP = (
    'Soporta saltos de línea. Se renderiza con <br>. '
    'Alternativas para A/B: '
    '(B) "WhatsApp 24/7, entregas automatizadas\\ny licitaciones en horas,'
    '\\nno semanas." · '
    '(C) "La IA que responde clientes,\\nrutea camiones\\ny escribe tus '
    'pliegos técnicos."'
)


def update_singleton(apps, schema_editor):
    SiteConfig = apps.get_model('site_config', 'SiteConfig')
    obj = SiteConfig.objects.filter(pk=1).first()
    if obj is None:
        return
    changed = False
    if obj.hero_title == OLD_HERO_TITLE:
        obj.hero_title = NEW_HERO_TITLE
        changed = True
    if obj.hero_subtitle == OLD_HERO_SUBTITLE:
        obj.hero_subtitle = NEW_HERO_SUBTITLE
        changed = True
    if changed:
        obj.save(update_fields=['hero_title', 'hero_subtitle'])


def revert_singleton(apps, schema_editor):
    SiteConfig = apps.get_model('site_config', 'SiteConfig')
    obj = SiteConfig.objects.filter(pk=1).first()
    if obj is None:
        return
    changed = False
    if obj.hero_title == NEW_HERO_TITLE:
        obj.hero_title = OLD_HERO_TITLE
        changed = True
    if obj.hero_subtitle == NEW_HERO_SUBTITLE:
        obj.hero_subtitle = OLD_HERO_SUBTITLE
        changed = True
    if changed:
        obj.save(update_fields=['hero_title', 'hero_subtitle'])


class Migration(migrations.Migration):

    dependencies = [
        ('site_config', '0003_siteconfig_contacto_webhook_secret'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfig',
            name='hero_title',
            field=models.TextField(
                default=NEW_HERO_TITLE,
                help_text=NEW_HERO_TITLE_HELP,
                verbose_name='Título del hero',
            ),
        ),
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
