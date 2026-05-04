from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ProjectSEO',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(help_text='Debe coincidir exactamente con el nombre de la carpeta. Ej: 01-pozos-scz', unique=True, verbose_name='Slug del proyecto')),
                ('seo_title', models.CharField(blank=True, help_text='Vacío = usa el título del proyecto. Máx 60 caracteres.', max_length=60, verbose_name='Título SEO')),
                ('seo_description', models.CharField(blank=True, help_text='Vacío = usa el subtítulo del proyecto. Máx 160 caracteres.', max_length=160, verbose_name='Descripción SEO')),
            ],
            options={
                'verbose_name': 'SEO de proyecto',
                'verbose_name_plural': 'SEO de proyectos',
                'ordering': ['slug'],
            },
        ),
    ]
