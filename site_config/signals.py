from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='site_config.SiteConfig')
def invalidate_home_translations(sender, **kwargs):
    """Borra TranslationCache de 'home' cuando cambia SiteConfig."""
    from html_translator.models import TranslationCache
    from html_translator.templatetags.translations import _invalidate_cache
    TranslationCache.objects.filter(page_key='home').delete()
    _invalidate_cache('home')
