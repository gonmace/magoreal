"""
Django system checks para html_translator.

Se ejecutan automáticamente con `python manage.py check` y al arrancar el servidor.
Aparecen como errores/advertencias claros en la consola.
"""
from django.core.checks import Error, Warning, register


@register()
def check_translations_config(app_configs, **kwargs):
    from django.conf import settings

    errors = []
    cfg = getattr(settings, 'TRANSLATIONS_CONFIG', None)

    if cfg is None:
        errors.append(Warning(
            'TRANSLATIONS_CONFIG no está definido en settings.',
            hint=(
                'Como mínimo define TRANSLATIONS_CONFIG = {"SECTIONS": [...]} en settings.py. '
                'La API key y otros valores opcionales pueden configurarse desde el admin '
                '(HTML Translator → Configuración del traductor).'
            ),
            id='html_translator.W001',
        ))
        return errors

    if not isinstance(cfg, dict):
        errors.append(Error(
            'TRANSLATIONS_CONFIG debe ser un diccionario.',
            id='html_translator.E000',
        ))
        return errors

    api_key = cfg.get('OPENAI_API_KEY')
    try:
        resolved_key = api_key() if callable(api_key) else api_key
    except Exception:
        # La DB puede no existir todavía (primera migración). Omitir el check.
        resolved_key = True
    if not resolved_key:
        # También es válido configurarla desde el panel de administración (TranslatorConfig).
        db_key = ''
        try:
            from .models import TranslatorConfig
            db_obj = TranslatorConfig.objects.filter(pk=1).first()
            db_key = (db_obj.openai_api_key or '') if db_obj else ''
        except Exception:
            pass
        if not db_key:
            errors.append(Warning(
                'TRANSLATIONS_CONFIG["OPENAI_API_KEY"] no está configurado.',
                hint=(
                    'Configura la API key de OpenAI en el panel de administración '
                    '(HTML Translator → Configuración del traductor) '
                    'o en TRANSLATIONS_CONFIG["OPENAI_API_KEY"] en settings.py.'
                ),
                id='html_translator.W002',
            ))

    sections = cfg.get('SECTIONS', [])
    if not sections:
        errors.append(Error(
            'TRANSLATIONS_CONFIG["SECTIONS"] está vacío o no definido.',
            hint='Define al menos una sección: "SECTIONS": [("hero", "app/_hero.html")]',
            id='html_translator.E001',
        ))
    else:
        for i, item in enumerate(sections):
            if not (isinstance(item, (list, tuple)) and len(item) == 2):
                errors.append(Error(
                    f'TRANSLATIONS_CONFIG["SECTIONS"][{i}] debe ser una tupla (clave, ruta_template).',
                    hint=f'Correcto: ("hero", "app/_hero.html"). Recibido: {item!r}',
                    id='html_translator.E002',
                ))

    pages = cfg.get('PAGES')
    if pages is not None and not isinstance(pages, dict):
        errors.append(Error(
            'TRANSLATIONS_CONFIG["PAGES"] debe ser un diccionario.',
            id='html_translator.E003',
        ))

    # Verificar que las URLs de html_translator están incluidas en el URLconf.
    try:
        from django.urls import reverse
        reverse('html_translator:request')
    except Exception:
        errors.append(Warning(
            'Las URLs de html_translator no están registradas.',
            hint=(
                'Añade a tu urls.py: '
                'path("translations/", include("html_translator.urls"))'
            ),
            id='html_translator.W003',
        ))

    return errors
