from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='site_config.SiteConfig')
def invalidate_home_translations(sender, **kwargs):
    """Invalida el cache en memoria cuando cambia SiteConfig.
    
    No borra las traducciones de la BD, solo invalida el cache de memoria.
    Las traducciones se marcarán como obsoletas y se regenerarán automáticamente.
    """
    from html_translator.templatetags.translations import _invalidate_cache
    # Solo invalidar el cache de memoria, no borrar las traducciones de la BD
    # Las traducciones se marcarán como obsoletas y se regenerarán cuando sea necesario
    _invalidate_cache('home')
