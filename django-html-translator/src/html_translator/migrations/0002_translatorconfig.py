from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('html_translator', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TranslatorConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('openai_api_key', models.CharField(blank=True, help_text='sk-... Deja en blanco para usar el valor de settings.py.', max_length=255, verbose_name='API Key de OpenAI')),
                ('openai_model', models.CharField(blank=True, help_text='Ej: gpt-4o-mini. Deja en blanco para usar el valor de settings.py.', max_length=60, verbose_name='Modelo de OpenAI')),
                ('callback_token', models.CharField(blank=True, help_text='Token Bearer para el endpoint /translations/callback/.', max_length=120, verbose_name='Token de callback')),
                ('default_language', models.CharField(blank=True, help_text='Ej: es. Deja en blanco para usar el valor de settings.py.', max_length=10, verbose_name='Idioma por defecto')),
                ('available_languages', models.JSONField(blank=True, default=list, help_text='Lista JSON de códigos ISO, ej: ["en", "pt-br"]. Lista vacía = sin restricción.', verbose_name='Idiomas disponibles')),
            ],
            options={
                'verbose_name': 'Configuración del traductor',
                'verbose_name_plural': 'Configuración del traductor',
            },
        ),
    ]
