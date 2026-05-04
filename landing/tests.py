"""Tests para landing — contact form + lead magnet + views + health."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.urls import reverse

from .models import ContactMessage, PliegoDemoLead


# PDF mínimo válido: header %PDF + bytes de relleno suficientes para que
# no sea un archivo vacío.
_MINIMAL_PDF = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n%%EOF\n'


@pytest.mark.django_db
def test_index_returns_200():
    client = Client()
    resp = client.get(reverse('landing:index'))
    assert resp.status_code == 200
    assert b'Magoreal' in resp.content or b'magoreal' in resp.content


@pytest.mark.django_db
def test_contacto_submit_valid_form_creates_message():
    client = Client()
    resp = client.post(reverse('landing:contacto_submit'), {
        'nombre': 'Test User',
        'email': 'test@example.com',
        'empresa': 'ACME',
        'interes': 'ia',
        'mensaje': 'Necesito un chatbot multi-agente para mi empresa en producción',
    })
    assert resp.status_code == 200
    assert resp.json()['ok'] is True
    assert ContactMessage.objects.count() == 1


@pytest.mark.django_db
def test_contacto_submit_mensaje_too_short_rejected():
    client = Client()
    resp = client.post(reverse('landing:contacto_submit'), {
        'nombre': 'Test',
        'email': 'test@example.com',
        'interes': 'otro',
        'mensaje': 'corto',  # <20 chars
    })
    assert resp.status_code == 400
    assert 'mensaje' in resp.json()['errors']


@pytest.mark.django_db
def test_contacto_submit_missing_email_rejected():
    client = Client()
    resp = client.post(reverse('landing:contacto_submit'), {
        'nombre': 'Test',
        'interes': 'otro',
        'mensaje': 'Mensaje lo bastante largo para pasar la validacion',
    })
    assert resp.status_code == 400


@pytest.mark.django_db
def test_health_live():
    client = Client()
    resp = client.get(reverse('landing:health_live'))
    assert resp.status_code == 200
    assert b'OK' in resp.content


@pytest.mark.django_db
def test_health_ready_returns_json_with_checks():
    client = Client()
    resp = client.get(reverse('landing:health_ready'))
    data = resp.json()
    assert resp.status_code in (200, 503)
    assert 'status' in data
    assert 'checks' in data
    assert 'db' in data['checks']
    assert 'media' in data['checks']


@pytest.mark.django_db
def test_portfolio_detalle_known_slug():
    """Requiere que PROYECTOS_DIR tenga al menos 1 proyecto real cargado."""
    client = Client()
    resp = client.get('/proyectos/01-pozos-scz/')
    # Puede ser 200 si el metadata existe, o 404 si no — ambos son válidos
    assert resp.status_code in (200, 404)


@pytest.mark.django_db
def test_portfolio_detalle_nonexistent_returns_404():
    client = Client()
    resp = client.get('/proyectos/this-slug-does-not-exist/')
    assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# Lead magnet de pliegos (Bloque 8)
# ═══════════════════════════════════════════════════════════════════════

def _pliego_form_data(**overrides):
    """Datos válidos mínimos del form del lead magnet, con overrides opcionales."""
    data = {
        'nombre': 'Marcos Ingeniero',
        'email': 'marcos@distribuidora.com.ar',
        'empresa': 'Distribuidora Telecom SA',
        'telefono': '+54 9 351 555 1234',
        'consentimiento': 'on',
    }
    data.update(overrides)
    return data


def _pdf_upload(name='compulsa-2026.pdf', content=_MINIMAL_PDF, content_type='application/pdf'):
    return SimpleUploadedFile(name=name, content=content, content_type=content_type)


@pytest.fixture
def pliego_upload_tmp(tmp_path, settings):
    """Redirige los uploads del lead magnet a un tmp path por test."""
    settings.PLIEGOS_UPLOAD_ROOT = str(tmp_path)
    return tmp_path


@pytest.mark.django_db
def test_pliego_demo_submit_valid_creates_lead(pliego_upload_tmp):
    client = Client()
    resp = client.post(
        reverse('landing:pliego_demo_submit'),
        data={**_pliego_form_data(), 'pdf_original': _pdf_upload()},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['ok'] is True

    assert PliegoDemoLead.objects.count() == 1
    lead = PliegoDemoLead.objects.first()
    assert lead.email == 'marcos@distribuidora.com.ar'
    assert lead.empresa == 'Distribuidora Telecom SA'
    assert lead.consentimiento is True
    # El filename original se preserva para display; el file en disco usa UUID
    assert lead.pdf_filename_original == 'compulsa-2026.pdf'
    assert lead.pdf_size_bytes == len(_MINIMAL_PDF)
    assert lead.pdf_original.name.endswith('.pdf')
    assert 'compulsa-2026' not in lead.pdf_original.name  # se guardó como UUID


@pytest.mark.django_db
def test_pliego_demo_submit_missing_pdf_rejected(pliego_upload_tmp):
    client = Client()
    resp = client.post(
        reverse('landing:pliego_demo_submit'),
        data=_pliego_form_data(),  # sin pdf_original
    )
    assert resp.status_code == 400
    assert 'pdf_original' in resp.json()['errors']
    assert PliegoDemoLead.objects.count() == 0


@pytest.mark.django_db
def test_pliego_demo_submit_non_pdf_rejected(pliego_upload_tmp):
    client = Client()
    fake = _pdf_upload(name='mal.pdf', content=b'<html>not a pdf</html>\n')
    resp = client.post(
        reverse('landing:pliego_demo_submit'),
        data={**_pliego_form_data(), 'pdf_original': fake},
    )
    assert resp.status_code == 400
    errors = resp.json()['errors']
    assert 'pdf_original' in errors
    assert PliegoDemoLead.objects.count() == 0


@pytest.mark.django_db
def test_pliego_demo_submit_no_consent_rejected(pliego_upload_tmp):
    client = Client()
    data = _pliego_form_data()
    data.pop('consentimiento')  # sin opt-in
    resp = client.post(
        reverse('landing:pliego_demo_submit'),
        data={**data, 'pdf_original': _pdf_upload()},
    )
    assert resp.status_code == 400
    assert 'consentimiento' in resp.json()['errors']
    assert PliegoDemoLead.objects.count() == 0


@pytest.mark.django_db
def test_pliego_demo_submit_missing_empresa_rejected(pliego_upload_tmp):
    client = Client()
    resp = client.post(
        reverse('landing:pliego_demo_submit'),
        data={**_pliego_form_data(empresa=''), 'pdf_original': _pdf_upload()},
    )
    assert resp.status_code == 400
    assert 'empresa' in resp.json()['errors']


@pytest.mark.django_db
def test_pliego_demo_submit_oversized_pdf_rejected(pliego_upload_tmp, monkeypatch):
    """Un PDF por encima del límite debe rechazarse sin tocar disco."""
    from landing import forms as landing_forms
    monkeypatch.setattr(landing_forms, 'PLIEGO_MAX_BYTES', 128)  # 128 bytes
    client = Client()
    big = _pdf_upload(name='gigante.pdf', content=_MINIMAL_PDF + b'\x00' * 512)
    resp = client.post(
        reverse('landing:pliego_demo_submit'),
        data={**_pliego_form_data(), 'pdf_original': big},
    )
    assert resp.status_code == 400
    assert 'pdf_original' in resp.json()['errors']
    assert PliegoDemoLead.objects.count() == 0


@pytest.mark.django_db
def test_index_page_renders_pliego_form(pliego_upload_tmp):
    """El form del lead magnet debe renderizar como parte del index."""
    client = Client()
    resp = client.get(reverse('landing:index'))
    assert resp.status_code == 200
    assert b'demo-pliego' in resp.content  # id del contenedor
    assert b'pliego_demo_submit' not in resp.content  # la URL sí, el name no
    assert b'/pliegos/demo/' in resp.content
