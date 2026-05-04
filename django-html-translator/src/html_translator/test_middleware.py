"""
Test para LanguageMiddleware con Accept-Language detection.
"""
import os
from unittest.mock import MagicMock

import django
from django.conf import settings

# Configurar Django para tests
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        DEFAULT_CHARSET='utf-8',
    )
    django.setup()

from django.http import HttpResponseRedirect

from html_translator.middleware import (
    _find_best_language,
    _parse_accept_language,
    LanguageMiddleware,
)


def test_parse_accept_language_simple():
    """Parsea un header simple."""
    result = _parse_accept_language('en')
    assert result == ['en']


def test_parse_accept_language_with_q():
    """Parsea un header con q-values."""
    result = _parse_accept_language('fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7')
    assert result == ['fr-fr', 'fr', 'en-us', 'en']


def test_find_best_language_exact_match():
    """Encuentra un idioma exacto en la lista disponible."""
    result = _find_best_language(['fr', 'en'], ['fr', 'es'], 'es')
    assert result == 'fr'


def test_find_best_language_fallback_to_base():
    """Hace fallback de fr-FR a fr."""
    result = _find_best_language(['fr-FR', 'en'], ['fr', 'en'], 'es')
    assert result == 'fr'


def test_find_best_language_no_match():
    """Retorna None si ningún idioma está disponible."""
    result = _find_best_language(['de', 'it'], ['fr', 'en'], 'es')
    assert result is None


def test_find_best_language_empty_available():
    """Retorna None si la lista de idiomas disponibles está vacía."""
    result = _find_best_language(['fr', 'en'], [], 'es')
    assert result is None


def test_find_best_language_skips_default():
    """El idioma por defecto no fuerza redirect."""
    result = _find_best_language(['es', 'en'], ['es', 'en'], 'es')
    # Debería retornar 'es', pero el middleware lo ignorará porque es el default
    assert result == 'es'


def test_middleware_with_accept_language_redirect():
    """Middleware hace redirect cuando Accept-Language tiene idioma disponible."""
    # Mock request
    request = MagicMock()
    request.path_info = '/'
    request.COOKIES = {}
    request.META = {'HTTP_ACCEPT_LANGUAGE': 'fr-FR,fr;q=0.9,en;q=0.8'}

    # Mock get_response
    def mock_get_response(req):
        return MagicMock()

    # Mock conf
    import html_translator.middleware as middleware_module
    original_get_default = middleware_module.conf.get_default_language
    original_get_available = middleware_module.conf.get_available_languages

    middleware_module.conf.get_default_language = lambda: 'es'
    middleware_module.conf.get_available_languages = lambda: ['fr', 'en', 'es']

    try:
        mw = LanguageMiddleware(mock_get_response)
        response = mw(request)

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == '/fr/'
    finally:
        middleware_module.conf.get_default_language = original_get_default
        middleware_module.conf.get_available_languages = original_get_available


def test_middleware_no_redirect_when_no_accept_language():
    """Middleware no hace redirect cuando no hay header Accept-Language."""
    request = MagicMock()
    request.path_info = '/'
    request.COOKIES = {}
    request.META = {}  # No Accept-Language header

    def mock_get_response(req):
        return MagicMock()

    import html_translator.middleware as middleware_module
    original_get_default = middleware_module.conf.get_default_language
    original_get_available = middleware_module.conf.get_available_languages

    middleware_module.conf.get_default_language = lambda: 'es'
    middleware_module.conf.get_available_languages = lambda: ['fr', 'en', 'es']

    try:
        mw = LanguageMiddleware(mock_get_response)
        response = mw(request)

        assert not isinstance(response, HttpResponseRedirect)
    finally:
        middleware_module.conf.get_default_language = original_get_default
        middleware_module.conf.get_available_languages = original_get_available


def test_middleware_cookie_overrides_accept_language():
    """Cookie tiene prioridad sobre Accept-Language."""
    request = MagicMock()
    request.path_info = '/'
    request.COOKIES = {'lang': 'en'}
    request.META = {'HTTP_ACCEPT_LANGUAGE': 'fr'}

    def mock_get_response(req):
        return MagicMock()

    import html_translator.middleware as middleware_module
    original_get_default = middleware_module.conf.get_default_language
    original_get_available = middleware_module.conf.get_available_languages

    middleware_module.conf.get_default_language = lambda: 'es'
    middleware_module.conf.get_available_languages = lambda: ['fr', 'en', 'es']

    try:
        mw = LanguageMiddleware(mock_get_response)
        response = mw(request)

        # No debe hacer redirect porque la cookie tiene prioridad
        assert not isinstance(response, HttpResponseRedirect)
    finally:
        middleware_module.conf.get_default_language = original_get_default
        middleware_module.conf.get_available_languages = original_get_available


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
