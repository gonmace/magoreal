from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('morph_banner', '0002_morph_banner_site_colors'),
    ]

    operations = [
        migrations.AddField(
            model_name='morphbanner',
            name='effect',
            field=models.CharField(
                choices=[
                    ('yoyo', 'Yoyo (actual)'),
                    ('always', 'Sin desaparecer'),
                    ('reveal', 'Morph global + reveal'),
                    ('cascade', 'Cascada (letra a letra)'),
                    ('spotlight', 'Spotlight'),
                ],
                default='yoyo',
                help_text='Tipo de animación del banner.',
                max_length=20,
                verbose_name='Efecto',
            ),
        ),
    ]
