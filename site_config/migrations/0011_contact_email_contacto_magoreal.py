"""Email público de contacto: contacto@magoreal.com (sección 010)."""

from django.db import migrations, models


def forwards(apps, schema_editor):
    SiteConfig = apps.get_model('site_config', 'SiteConfig')
    SiteConfig.objects.filter(email='magoreal4@gmail.com').update(
        email='contacto@magoreal.com'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('site_config', '0010_hero_subtitle_dos_parrafos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfig',
            name='email',
            field=models.EmailField(
                default='contacto@magoreal.com',
                max_length=254,
                verbose_name='Email de contacto',
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
