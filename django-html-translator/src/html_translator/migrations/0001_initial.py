from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='TranslationCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page_key', models.CharField(help_text='Identificador del bloque traducido, ej: "home", "blog-intro"', max_length=80, verbose_name='Clave de página')),
                ('lang', models.CharField(help_text='Código ISO: en, pt-br, fr...', max_length=10, verbose_name='Idioma')),
                ('content', models.JSONField(default=dict, help_text='HTML traducido por sección, ej: {"hero": "<div>...</div>"}', verbose_name='Contenido traducido')),
                ('source_html', models.JSONField(default=dict, help_text='HTML original del idioma base por sección', verbose_name='HTML origen')),
                ('source_hash', models.CharField(blank=True, help_text='SHA-256 del source_html; si cambia, la traducción está obsoleta', max_length=64, verbose_name='Hash del origen')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Caché de traducción',
                'verbose_name_plural': 'Cachés de traducción',
                'ordering': ['page_key', 'lang'],
                'unique_together': {('page_key', 'lang')},
            },
        ),
    ]
