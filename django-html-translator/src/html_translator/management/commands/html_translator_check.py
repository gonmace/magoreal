"""
python manage.py html_translator_check

Diagnóstico completo de la configuración de django-html-translator.
Útil para verificar el setup antes de entrar a producción.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Verifica la configuración de django-html-translator'

    def handle(self, *args, **options):
        from django.conf import settings
        from django.urls import reverse, NoReverseMatch

        ok = self.style.SUCCESS('[OK]')
        warn = self.style.WARNING('[!!]')
        fail = self.style.ERROR('[XX]')

        self.stdout.write('\nhtml_translator — Diagnóstico de configuración')
        self.stdout.write('=' * 50)

        warnings = 0
        errors = 0

        # 1. TRANSLATIONS_CONFIG existe
        cfg = getattr(settings, 'TRANSLATIONS_CONFIG', None)
        if cfg is None:
            self.stdout.write(f'{fail} TRANSLATIONS_CONFIG no definido en settings')
            errors += 1
            self.stdout.write('\nResumen: configura TRANSLATIONS_CONFIG para continuar.')
            return
        self.stdout.write(f'{ok} TRANSLATIONS_CONFIG encontrado')

        # 2. OPENAI_API_KEY
        api_key = cfg.get('OPENAI_API_KEY', '')
        resolved_key = api_key() if callable(api_key) else api_key
        if resolved_key:
            masked = resolved_key[:7] + '...' + resolved_key[-4:] if len(resolved_key) > 11 else '***'
            self.stdout.write(f'{ok} OPENAI_API_KEY configurado ({masked})')
        else:
            self.stdout.write(f'{warn} OPENAI_API_KEY no configurado — la traducción automática no funcionará')
            warnings += 1

        # 3. OPENAI_MODEL
        model_val = cfg.get('OPENAI_MODEL', 'gpt-4o-mini')
        model = model_val() if callable(model_val) else model_val
        self.stdout.write(f'{ok} OPENAI_MODEL: {model}')

        # 4. DEFAULT_LANGUAGE
        default = cfg.get('DEFAULT_LANGUAGE', 'es')
        self.stdout.write(f'{ok} DEFAULT_LANGUAGE: {default}')

        # 5. AVAILABLE_LANGUAGES
        available = cfg.get('AVAILABLE_LANGUAGES', [])
        if available:
            self.stdout.write(f'{ok} AVAILABLE_LANGUAGES: {", ".join(available)}')
        else:
            self.stdout.write(f'{warn} AVAILABLE_LANGUAGES no definido — cualquier idioma en cookie es aceptado')
            warnings += 1

        # 6. SECTIONS
        sections = cfg.get('SECTIONS', [])
        if sections:
            keys = [k for k, _ in sections]
            self.stdout.write(f'{ok} {len(sections)} sección(es): {", ".join(keys)}')
        else:
            self.stdout.write(f'{fail} SECTIONS está vacío — define al menos una sección')
            errors += 1

        # 7. PAGES
        pages = cfg.get('PAGES')
        if pages:
            self.stdout.write(f'{ok} {len(pages)} página(s) configurada(s): {", ".join(pages.keys())}')
        else:
            self.stdout.write(f'{warn} PAGES no definido — se usarán todas las secciones para cualquier página')
            warnings += 1

        # 8. CALLBACK_TOKEN
        token = cfg.get('CALLBACK_TOKEN', '')
        if token:
            self.stdout.write(f'{ok} CALLBACK_TOKEN configurado')
        else:
            self.stdout.write(f'{warn} CALLBACK_TOKEN no configurado — /translations/callback/ está abierto')
            warnings += 1

        # 9. Middleware en MIDDLEWARE
        middleware = getattr(settings, 'MIDDLEWARE', [])
        mw_name = 'html_translator.middleware.LanguageMiddleware'
        if mw_name in middleware:
            self.stdout.write(f'{ok} LanguageMiddleware activo (posición {middleware.index(mw_name)})')
        else:
            self.stdout.write(f'{fail} LanguageMiddleware no está en MIDDLEWARE')
            errors += 1

        # 10. URLs
        try:
            url = reverse('html_translator:request')
            self.stdout.write(f'{ok} URL /translations/request/ accesible ({url})')
        except NoReverseMatch:
            self.stdout.write(f'{fail} URL html_translator:request no encontrada — ¿añadiste include("html_translator.urls") a urls.py?')
            errors += 1

        # 11. SECTION_CONTEXT_PROVIDER
        provider = cfg.get('SECTION_CONTEXT_PROVIDER')
        if provider:
            try:
                from django.utils.module_loading import import_string
                import_string(provider)
                self.stdout.write(f'{ok} SECTION_CONTEXT_PROVIDER importable: {provider}')
            except ImportError as e:
                self.stdout.write(f'{fail} SECTION_CONTEXT_PROVIDER no importable ({provider}): {e}')
                errors += 1

        # 12. ON_TRANSLATION_UPDATED
        hook = cfg.get('ON_TRANSLATION_UPDATED')
        if hook:
            try:
                from django.utils.module_loading import import_string
                import_string(hook)
                self.stdout.write(f'{ok} ON_TRANSLATION_UPDATED importable: {hook}')
            except ImportError as e:
                self.stdout.write(f'{fail} ON_TRANSLATION_UPDATED no importable ({hook}): {e}')
                errors += 1

        # Resumen
        self.stdout.write('')
        if errors == 0 and warnings == 0:
            self.stdout.write(self.style.SUCCESS('Todo OK — configuracion lista para produccion.'))
        elif errors == 0:
            self.stdout.write(self.style.WARNING(f'Resumen: {warnings} advertencia(s), {errors} error(es).'))
        else:
            self.stdout.write(self.style.ERROR(f'Resumen: {warnings} advertencia(s), {errors} error(es). Corrige los errores antes de continuar.'))
