from django.core.cache import cache

from .models import SiteConfig

# Nombres legibles para el selector
LANG_DISPLAY: dict[str, str] = {
    'es': 'ES', 'en': 'EN', 'pt': 'PT',
    'fr': 'FR', 'de': 'DE', 'it': 'IT',
    'nl': 'NL', 'pl': 'PL', 'tr': 'TR', 'sv': 'SV',
    'cs': 'CS', 'ro': 'RO', 'id': 'ID', 'hu': 'HU',
    'da': 'DA', 'fi': 'FI', 'ca': 'CA', 'no': 'NO',
    'sk': 'SK', 'hr': 'HR', 'vi': 'VI', 'ms': 'MS',
    'af': 'AF', 'eu': 'EU', 'gl': 'GL', 'sw': 'SW',
}

# Mapa lang-code → og:locale (formato Facebook/OGP: xx_XX)
_OG_LOCALE_MAP: dict[str, str] = {
    'es': 'es_ES', 'en': 'en_US', 'pt': 'pt_BR',
    'fr': 'fr_FR', 'de': 'de_DE', 'it': 'it_IT',
    'nl': 'nl_NL', 'pl': 'pl_PL', 'tr': 'tr_TR',
    'sv': 'sv_SE', 'cs': 'cs_CZ', 'ro': 'ro_RO',
    'id': 'id_ID', 'hu': 'hu_HU', 'da': 'da_DK',
    'fi': 'fi_FI', 'ca': 'ca_ES', 'no': 'nb_NO',
    'sk': 'sk_SK', 'hr': 'hr_HR', 'vi': 'vi_VN',
    'ms': 'ms_MY', 'af': 'af_ZA', 'eu': 'eu_ES',
    'gl': 'gl_ES', 'sw': 'sw_TZ',
}

# Idiomas con alfabeto latino disponibles para traducción adicional.
# No incluir los que ya están en siteconfig (fr, de, it, pt).
ADDITIONAL_LATIN_LANGS: list[tuple[str, str]] = [
    ('nl', 'Nederlands'),
    ('pl', 'Polski'),
    ('tr', 'Türkçe'),
    ('sv', 'Svenska'),
    ('cs', 'Čeština'),
    ('ro', 'Română'),
    ('id', 'Bahasa Indonesia'),
    ('hu', 'Magyar'),
    ('da', 'Dansk'),
    ('fi', 'Suomi'),
    ('ca', 'Català'),
    ('no', 'Norsk'),
    ('sk', 'Slovenčina'),
    ('hr', 'Hrvatski'),
    ('vi', 'Tiếng Việt'),
    ('ms', 'Bahasa Melayu'),
    ('af', 'Afrikaans'),
    ('eu', 'Euskara'),
    ('gl', 'Galego'),
    ('sw', 'Kiswahili'),
]

# Traducciones estáticas del nav — se aplican de inmediato sin necesidad de n8n.
# Las claves coinciden con los identificadores usados en _nav.html ({{ nav_t.clave }}).
_NAV_TRANSLATIONS: dict[str, dict[str, str]] = {
    'en': {
        'proyectos': 'Projects', 'servicios': 'Services',
        'tecnologia': 'Technology', 'contacto': 'Contact',
        'agendar': 'Book a call',
        'otro_idioma': '+ other language', 'seleccionar': '— select —',
        'idioma': 'Language', 'otro': '+ other',
        'traduciendo': 'Translating…', 'primer_vez': '~60-90s first time',
        'fallo': 'Translation failed.', 'reintentar': 'Retry',
        'saltar': 'Skip to main content', 'abrir_menu': 'Open menu',
        'site_name': 'Magoreal | Automation and Artificial Intelligence Agency',
        'tagline': 'We automate your processes with AI. In your own system.',
    },
    'fr': {
        'proyectos': 'Projets', 'servicios': 'Services',
        'tecnologia': 'Technologie', 'contacto': 'Contact',
        'agendar': 'Prendre RDV',
        'otro_idioma': '+ autre langue', 'seleccionar': '— sélectionner —',
        'idioma': 'Langue', 'otro': '+ autre',
        'traduciendo': 'Traduction…', 'primer_vez': '~60-90s première fois',
        'fallo': 'Échec de la traduction.', 'reintentar': 'Réessayer',
        'saltar': 'Aller au contenu principal', 'abrir_menu': 'Ouvrir le menu',
        'site_name': 'Magoreal | Agence d\'Automatisation et d\'Intelligence Artificielle',
        'tagline': 'Nous automatisons vos processus avec l\'IA. Dans votre propre système.',
    },
    'de': {
        'proyectos': 'Projekte', 'servicios': 'Leistungen',
        'tecnologia': 'Technologie', 'contacto': 'Kontakt',
        'agendar': 'Termin buchen',
        'otro_idioma': '+ andere Sprache', 'seleccionar': '— auswählen —',
        'idioma': 'Sprache', 'otro': '+ andere',
        'traduciendo': 'Übersetzung…', 'primer_vez': '~60-90s erstes Mal',
        'fallo': 'Übersetzung fehlgeschlagen.', 'reintentar': 'Erneut versuchen',
        'saltar': 'Zum Hauptinhalt springen', 'abrir_menu': 'Menü öffnen',
        'site_name': 'Magoreal | Automatisierung und Künstliche Intelligenz Agentur',
        'tagline': 'Wir automatisieren Ihre Prozesse mit KI. In Ihrem eigenen System.',
    },
    'it': {
        'proyectos': 'Progetti', 'servicios': 'Servizi',
        'tecnologia': 'Tecnologia', 'contacto': 'Contatto',
        'agendar': 'Prenota una chiamata',
        'otro_idioma': '+ altra lingua', 'seleccionar': '— selezionare —',
        'idioma': 'Lingua', 'otro': '+ altra',
        'traduciendo': 'Traduzione…', 'primer_vez': '~60-90s prima volta',
        'fallo': 'Traduzione non riuscita.', 'reintentar': 'Riprova',
        'saltar': 'Vai al contenuto principale', 'abrir_menu': 'Apri il menu',
        'site_name': 'Magoreal | Agenzia di Automazione e Intelligenza Artificiale',
        'tagline': 'Automatizziamo i tuoi processi con l\'IA. Nel tuo stesso sistema.',
    },
    'pt': {
        'proyectos': 'Projetos', 'servicios': 'Serviços',
        'tecnologia': 'Tecnologia', 'contacto': 'Contato',
        'agendar': 'Agendar chamada',
        'otro_idioma': '+ outro idioma', 'seleccionar': '— selecionar —',
        'idioma': 'Idioma', 'otro': '+ outro',
        'traduciendo': 'Traduzindo…', 'primer_vez': '~60-90s primeira vez',
        'fallo': 'Falha na tradução.', 'reintentar': 'Tentar novamente',
        'saltar': 'Ir para o conteúdo principal', 'abrir_menu': 'Abrir menu',
        'site_name': 'Magoreal | Agência de Automação e Inteligência Artificial',
        'tagline': 'Automatizamos seus processos com IA. No seu próprio sistema.',
    },
    'nl': {
        'proyectos': 'Projecten', 'servicios': 'Diensten',
        'tecnologia': 'Technologie', 'contacto': 'Contact',
        'agendar': 'Afspraak plannen',
        'otro_idioma': '+ andere taal', 'seleccionar': '— selecteren —',
        'idioma': 'Taal', 'otro': '+ andere',
        'traduciendo': 'Vertalen…', 'primer_vez': '~60-90s eerste keer',
        'fallo': 'Vertaling mislukt.', 'reintentar': 'Opnieuw proberen',
        'saltar': 'Ga naar hoofdinhoud', 'abrir_menu': 'Menu openen',
    },
    'pl': {
        'proyectos': 'Projekty', 'servicios': 'Usługi',
        'tecnologia': 'Technologia', 'contacto': 'Kontakt',
        'agendar': 'Umów rozmowę',
        'otro_idioma': '+ inny język', 'seleccionar': '— wybierz —',
        'idioma': 'Język', 'otro': '+ inne',
        'traduciendo': 'Tłumaczenie…', 'primer_vez': '~60-90s za pierwszym razem',
        'fallo': 'Tłumaczenie nie powiodło się.', 'reintentar': 'Spróbuj ponownie',
        'saltar': 'Przejdź do głównej treści', 'abrir_menu': 'Otwórz menu',
    },
    'tr': {
        'proyectos': 'Projeler', 'servicios': 'Hizmetler',
        'tecnologia': 'Teknoloji', 'contacto': 'İletişim',
        'agendar': 'Görüşme planla',
        'otro_idioma': '+ diğer dil', 'seleccionar': '— seçin —',
        'idioma': 'Dil', 'otro': '+ diğer',
        'traduciendo': 'Çeviriliyor…', 'primer_vez': '~60-90s ilk kez',
        'fallo': 'Çeviri başarısız.', 'reintentar': 'Yeniden dene',
        'saltar': 'Ana içeriğe geç', 'abrir_menu': 'Menüyü aç',
    },
    'sv': {
        'proyectos': 'Projekt', 'servicios': 'Tjänster',
        'tecnologia': 'Teknologi', 'contacto': 'Kontakt',
        'agendar': 'Boka samtal',
        'otro_idioma': '+ annat språk', 'seleccionar': '— välj —',
        'idioma': 'Språk', 'otro': '+ annat',
        'traduciendo': 'Översätter…', 'primer_vez': '~60-90s första gången',
        'fallo': 'Översättning misslyckades.', 'reintentar': 'Försök igen',
        'saltar': 'Hoppa till huvudinnehåll', 'abrir_menu': 'Öppna menyn',
    },
}

_AVAIL_CACHE_TTL = 60  # segundos — se refresca tras cada callback


def _available_langs_cache_key(page_key: str) -> str:
    return f'available_langs:{page_key}'


def invalidate_available_langs(page_key: str = 'home') -> None:
    """Llamar desde translations.views.callback cuando llega una traducción nueva."""
    cache.delete(_available_langs_cache_key(page_key))


def site_context(request):
    """
    Expone la configuración del sitio a todos los templates.

    Variables adicionales:
      all_available_langs   — lista de códigos con contenido traducido disponible
                              (siteconfig.languages_list + los recién traducidos)
      additional_latin_langs — lista de (code, name) para el selector 'otro idioma',
                               filtrada para excluir los ya disponibles
    """
    page = getattr(request, 'sitepage', None)
    config = SiteConfig.load()
    lang = getattr(request, 'LANGUAGE_CODE', 'es')
    ctx = {
        'siteconfig': config,
        'nav_t': _NAV_TRANSLATIONS.get(lang, {}),
        'lang_prefix': f'/{lang}/' if lang != 'es' else '/',
        'og_locale': _OG_LOCALE_MAP.get(lang, 'es_ES'),
    }
    if page:
        ctx['sitepage'] = page

    multilingual = page.multilingual if page else config.multilingual
    ctx['multilingual'] = multilingual

    base_langs: list[str] = page.languages_list if page else config.languages_list

    # Idiomas con traducción en DB (cache corta para refrescar tras callback)
    page_key = 'home'
    cache_key = _available_langs_cache_key(page_key)
    all_langs: list[str] | None = cache.get(cache_key)
    if all_langs is None:
        try:
            from html_translator.models import TranslationCache
            translated_langs = list(
                TranslationCache.objects
                .filter(page_key=page_key)
                .exclude(content={})
                .values_list('lang', flat=True)
            )
            seen: set[str] = set()
            merged: list[str] = []
            for lc in base_langs + translated_langs:
                if lc not in seen:
                    seen.add(lc)
                    merged.append(lc)
            all_langs = merged
        except Exception:
            all_langs = base_langs
        cache.set(cache_key, all_langs, _AVAIL_CACHE_TTL)

    ctx['all_available_langs'] = all_langs
    # Lista de (code, label) para el selector principal
    ctx['all_available_langs_labeled'] = [
        (lc, LANG_DISPLAY.get(lc, lc.upper()))
        for lc in all_langs
    ]
    # og:locale:alternate — todos los idiomas disponibles excepto el actual
    ctx['og_locale_alternates'] = [
        _OG_LOCALE_MAP[lc]
        for lc in all_langs
        if lc != lang and lc in _OG_LOCALE_MAP
    ]

    # Dropdown "otro idioma": solo latinas no disponibles aún
    available_set = set(all_langs)
    ctx['additional_latin_langs'] = [
        (code, name)
        for code, name in ADDITIONAL_LATIN_LANGS
        if code not in available_set
    ]

    return ctx
