from django.db import migrations, models

OLD_HERO_TITLE = (
    'IA que atiende tu WhatsApp,\n'
    'coordina tu logística\n'
    'y arma tus pliegos.'
)
NEW_HERO_TITLE = (
    'Atendé clientes en WhatsApp.\n'
    'Automatizá tu logística.\n'
    'Pliegos técnicos con IA.'
)


def update_singleton(apps, schema_editor):
    SiteConfig = apps.get_model('site_config', 'SiteConfig')
    obj = SiteConfig.objects.filter(pk=1).first()
    if obj and obj.hero_title == OLD_HERO_TITLE:
        obj.hero_title = NEW_HERO_TITLE
        obj.save(update_fields=['hero_title'])


def revert_singleton(apps, schema_editor):
    SiteConfig = apps.get_model('site_config', 'SiteConfig')
    obj = SiteConfig.objects.filter(pk=1).first()
    if obj and obj.hero_title == NEW_HERO_TITLE:
        obj.hero_title = OLD_HERO_TITLE
        obj.save(update_fields=['hero_title'])


class Migration(migrations.Migration):

    dependencies = [
        ('site_config', '0005_pliego_demo_webhook_secret'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfig',
            name='hero_title',
            field=models.TextField(
                default=NEW_HERO_TITLE,
                help_text=(
                    'Soporta saltos de línea. Se renderiza con <br>. '
                    'Tres líneas independientes — un pilar por línea.'
                ),
                verbose_name='Título del hero',
            ),
        ),
        migrations.RunPython(update_singleton, revert_singleton),
    ]
