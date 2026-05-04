from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('morph_banner', '0006_alter_morphbanner_letter_colors'),
    ]

    operations = [
        migrations.AddField(
            model_name='morphbanner',
            name='neon_style',
            field=models.BooleanField(
                default=False,
                help_text='Añade un resplandor alrededor de cada glifo usando su propio color (efecto neón tipo cartel luminoso). Conviene con fondos oscuros.',
                verbose_name='Estilo neón',
            ),
        ),
    ]
