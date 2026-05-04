from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('site_config', '0011_contact_email_contacto_magoreal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfig',
            name='email',
            field=models.EmailField(
                default='contacto@magoreal.com',
                help_text=(
                    'Correo visible en la web (sección contacto, footer, JSON-LD). '
                    'Se edita solo desde este admin — no requiere deploy.'
                ),
                max_length=254,
                verbose_name='Email de contacto público',
            ),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='privacy_policy_url',
            field=models.URLField(
                blank=True,
                help_text='Enlace del footer “Privacidad”. Vacío = enlace # hasta que cargues la página.',
                verbose_name='URL política de privacidad',
            ),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='terms_url',
            field=models.URLField(
                blank=True,
                help_text='Enlace del footer “Términos”. Vacío = #.',
                verbose_name='URL términos y condiciones',
            ),
        ),
    ]
