from django.apps import AppConfig


class HtmlTranslatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'html_translator'
    verbose_name = 'HTML Translator'

    def ready(self):
        from . import checks  # noqa: F401 — registra los system checks
