"""Sprint 8 · Bloque 8: shared secret para el webhook del lead magnet de pliegos."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site_config', '0004_sprint8_hero_copy'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfig',
            name='pliego_demo_webhook_secret',
            field=models.CharField(
                blank=True,
                max_length=80,
                verbose_name='Shared secret para webhook de demo de pliego',
                help_text=(
                    'Idem anterior, para el webhook que procesa PDFs subidos en el '
                    'lead magnet de licitaciones (genera borrador + mail de entrega). '
                    'URL del webhook en PLIEGO_DEMO_WEBHOOK_URL (.env).'
                ),
            ),
        ),
    ]
