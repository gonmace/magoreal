"""Tests para portfolio.loaders."""
import json
import pytest
from pathlib import Path

from .loaders import (
    load_proyectos,
    _derive_categoria_principal,
    _build_gallery,
)


@pytest.fixture
def tmp_proyectos_dir(tmp_path):
    """Estructura básica con 1 proyecto válido y 1 inválido."""
    proyectos = tmp_path / 'proyectos'
    proyectos.mkdir()

    # Proyecto válido
    p1 = proyectos / '01-valido'
    (p1 / 'screenshots').mkdir(parents=True)
    (p1 / 'screenshots' / '1.jpg').write_bytes(b'\xFF\xD8\xFF\xE0' + b'\x00' * 100)
    (p1 / 'metadata.json').write_text(json.dumps({
        'id': 'valido',
        'titulo': 'Proyecto válido',
        'tipo_solucion': 'Plataforma full-stack a medida',
    }), encoding='utf-8')

    # Proyecto JSON corrupto
    p2 = proyectos / '02-corrupto'
    p2.mkdir()
    (p2 / 'metadata.json').write_text('{ "titulo": broken json }', encoding='utf-8')

    # Directorio sin metadata
    p3 = proyectos / '03-sin-metadata'
    p3.mkdir()

    return proyectos


def test_load_proyectos_skips_corrupt_and_missing_metadata(tmp_proyectos_dir):
    projs = load_proyectos(tmp_proyectos_dir)
    assert len(projs) == 1
    assert projs[0]['slug'] == '01-valido'


def test_load_proyectos_handles_missing_directory(tmp_path):
    projs = load_proyectos(tmp_path / 'does-not-exist')
    assert projs == []


def test_load_proyectos_enriches_fields(tmp_proyectos_dir):
    projs = load_proyectos(tmp_proyectos_dir)
    p = projs[0]
    assert p['num'] == 1
    assert p['slug'] == '01-valido'
    assert p['categoria_principal'] == 'A medida'
    assert len(p['gallery']) == 1
    assert p['screenshot_main'] == 'proyectos/01-valido/screenshots/1.jpg'


def test_derive_categoria_servicio():
    data = {'tipo_solucion': 'Servicio profesional de implementación', 'modalidad': 'llave en mano'}
    assert _derive_categoria_principal(data) == 'Servicio'


def test_derive_categoria_con_ia():
    data = {
        'tipo_solucion': 'Plataforma con IA',
        'categorias': ['Chatbots conversacionales con IA', 'Multi-agente LLM'],
    }
    assert _derive_categoria_principal(data) == 'Con IA'


def test_derive_categoria_infraestructura_acelerador():
    data = {
        'id': 'acelerador-desarrollo-web',
        'tipo_solucion': 'Stack de desarrollo y despliegue',
    }
    assert _derive_categoria_principal(data) == 'Infraestructura'


def test_derive_categoria_a_medida_default():
    data = {'tipo_solucion': 'Plataforma full-stack', 'categorias': ['Sistemas a medida']}
    assert _derive_categoria_principal(data) == 'A medida'


def test_build_gallery_pairs_metadata_with_disk(tmp_path):
    """Gallery debe emparejar descriptiones del metadata con archivos del disco."""
    folder = tmp_path / '01-test'
    (folder / 'screenshots').mkdir(parents=True)
    (folder / 'screenshots' / '01-uno.png').write_bytes(b'fake png')
    (folder / 'screenshots' / '02-dos.png').write_bytes(b'fake png')

    meta = [
        {'archivo': 'screenshots/01-uno.png', 'descripcion': 'Primero'},
        {'archivo': 'screenshots/02-dos.png', 'descripcion': 'Segundo'},
    ]
    gallery = _build_gallery(folder, '01-test', meta)
    assert len(gallery) == 2
    assert gallery[0]['descripcion'] == 'Primero'
    assert gallery[1]['descripcion'] == 'Segundo'


def test_build_gallery_handles_extra_disk_files(tmp_path):
    """Archivos en disco NO listados en metadata se agregan al final sin descripción."""
    folder = tmp_path / '01-test'
    (folder / 'screenshots').mkdir(parents=True)
    (folder / 'screenshots' / '01-uno.png').write_bytes(b'fake')
    (folder / 'screenshots' / '02-extra.png').write_bytes(b'fake')

    meta = [{'archivo': 'screenshots/01-uno.png', 'descripcion': 'Uno'}]
    gallery = _build_gallery(folder, '01-test', meta)
    assert len(gallery) == 2
    assert gallery[0]['descripcion'] == 'Uno'
    assert gallery[1]['descripcion'] == ''  # archivo extra sin desc


def test_load_proyectos_partial_metadata_degrades_gracefully(tmp_path):
    """Metadata con fields faltantes no crashea — retorna con defaults."""
    proyectos = tmp_path / 'proyectos'
    p = proyectos / '01-minimo'
    p.mkdir(parents=True)
    (p / 'metadata.json').write_text('{"id": "minimo"}', encoding='utf-8')

    projs = load_proyectos(proyectos)
    assert len(projs) == 1
    assert projs[0]['slug'] == '01-minimo'
    assert projs[0]['gallery'] == []
    assert projs[0]['screenshot_main'] is None
    assert projs[0]['has_workflows'] is False
