"""Tests para SiteConfig (singleton) y SitePage (multi-sitio)."""
import pytest
from django.db import IntegrityError

from .models import SiteConfig, SitePage


# ── SiteConfig (legacy) ───────────────────────────────────────────────────

@pytest.mark.django_db
def test_load_creates_singleton_if_missing():
    SiteConfig.objects.all().delete()
    obj = SiteConfig.load()
    assert obj.pk == 1
    assert SiteConfig.objects.count() == 1


@pytest.mark.django_db
def test_load_returns_existing_singleton():
    first = SiteConfig.load()
    first.site_name = 'Custom Name'
    first.save()
    second = SiteConfig.load()
    assert second.pk == first.pk == 1
    assert second.site_name == 'Custom Name'


@pytest.mark.django_db
def test_save_forces_pk_1_even_with_different_pk():
    # Intentar forzar pk=99 — el save() del modelo debe sobrescribir a 1
    obj = SiteConfig(pk=99, site_name='Intento pk=99')
    obj.save()
    assert obj.pk == 1
    assert SiteConfig.objects.count() == 1


@pytest.mark.django_db
def test_two_saves_do_not_duplicate():
    """Race condition básica: dos saves no crean dos rows."""
    a = SiteConfig(site_name='A')
    a.save()
    b = SiteConfig(site_name='B')
    b.save()
    assert SiteConfig.objects.count() == 1
    # El último gana (por pk=1 forced)
    assert SiteConfig.load().site_name == 'B'


@pytest.mark.django_db
def test_whatsapp_link_property():
    obj = SiteConfig.load()
    obj.whatsapp_number = ''
    assert obj.whatsapp_link is None
    obj.whatsapp_number = '59170000000'
    assert obj.whatsapp_link == 'https://wa.me/59170000000'


@pytest.mark.django_db
def test_languages_list_strips_and_splits():
    obj = SiteConfig.load()
    obj.available_languages = 'es, en ,pt'
    assert obj.languages_list == ['es', 'en', 'pt']
    obj.available_languages = 'es'
    assert obj.languages_list == ['es']


# ── SitePage (multi-sitio) ────────────────────────────────────────────────

@pytest.mark.django_db
def test_sitepage_creation():
    page = SitePage.objects.create(
        slug='cliente-a',
        domain='cliente-a.com',
        site_name='Cliente A',
        theme='ares',
    )
    assert page.slug == 'cliente-a'
    assert page.theme == 'ares'
    assert page.primary_rgb == '255,51,51'
    assert page.accent_rgb == '255,102,0'


@pytest.mark.django_db
def test_sitepage_resolution_by_domain():
    SitePage.objects.create(slug='tron-page', domain='tron.local', theme='tron')
    SitePage.objects.create(slug='ares-page', domain='ares.local', theme='ares')

    resolved = SitePage.objects.filter(domain__iexact='ares.local', is_active=True).first()
    assert resolved is not None
    assert resolved.theme == 'ares'


@pytest.mark.django_db
def test_sitepage_default_uniqueness():
    SitePage.objects.create(slug='default', is_default=True)
    # La constraint UNIQUE en is_default (condicional) previene duplicados a nivel DB
    with pytest.raises(IntegrityError):
        SitePage.objects.create(slug='another-default', is_default=True)


@pytest.mark.django_db
def test_sitepage_themes_rgb():
    themes = ['tron', 'ares', 'clu', 'athena', 'aphrodite', 'poseidon']
    for t in themes:
        page = SitePage.objects.create(slug=t, theme=t)
        assert len(page.primary_rgb.split(',')) == 3
        assert len(page.accent_rgb.split(',')) == 3


@pytest.mark.django_db
def test_sitepage_fallback_to_default():
    SitePage.objects.create(slug='fallback', is_default=True, theme='poseidon')
    # Simular que no hay match de dominio
    resolved = SitePage.objects.filter(domain__iexact='unknown.com', is_active=True).first()
    assert resolved is None
    fallback = SitePage.objects.filter(is_default=True, is_active=True).first()
    assert fallback is not None
    assert fallback.theme == 'poseidon'


@pytest.mark.django_db
def test_sitepage_languages_list():
    page = SitePage.objects.create(slug='multi', available_languages='es, en ,pt')
    assert page.languages_list == ['es', 'en', 'pt']


@pytest.mark.django_db
def test_sitepage_whatsapp_link():
    page = SitePage.objects.create(slug='wa', whatsapp_number='59170000000')
    assert page.whatsapp_link == 'https://wa.me/59170000000'
    page.whatsapp_number = ''
    assert page.whatsapp_link is None
