"""
Carga los proyectos del portfolio desde los metadata.json ubicados en
la carpeta proyectos/ dentro del proyecto Django.

Los datos se leen en frío una sola vez y se cachean en memoria del proceso.
En Gunicorn con múltiples workers cada worker mantiene su propia caché, lo
cual es aceptable porque los archivos solo cambian al hacer redeploy.
"""
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_FOLDER_NUMBER_RE = re.compile(r'^(\d+)')
_SCREENSHOT_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.avif'}


def _derive_categoria_principal(data):
    """
    Clasifica el proyecto en una de las categorías de los filtros del grid:
    'Con IA', 'A medida', 'Infraestructura', 'Servicio'.
    Orden de prioridad: Servicio > Infraestructura > Con IA > A medida.
    """
    tipo = (data.get('tipo_solucion') or '').lower()
    cats_list = [c.lower() for c in (data.get('categorias') or [])]
    modalidad = (data.get('modalidad') or '').lower()
    id_ = (data.get('id') or '').lower()

    # 1. Servicio profesional / llave en mano / consultoría
    if 'servicio profesional' in tipo or 'llave en mano' in tipo \
            or 'implementación e instalación' in tipo \
            or 'servicio profesional' in modalidad:
        return 'Servicio'

    # 2. Infraestructura / Stack / Acelerador (antes de IA para que el
    #    Acelerador no caiga en 'Con IA' por mencionar MCP)
    if 'acelerador' in id_ or 'self-hosted' in id_ \
            or 'stack de desarrollo' in tipo or 'infraestructura' in tipo \
            or any('infraestructura en' in c or 'administración de sistemas' in c
                   or 'self-hosted' in c for c in cats_list):
        return 'Infraestructura'

    # 3. Usa IA como componente central
    if 'con ia' in tipo or 'ia aplicada' in tipo \
            or any('ia' in c.split() or 'chatbots' in c or 'rag' in c
                   or 'multi-agente' in c or 'llm' in c for c in cats_list):
        return 'Con IA'

    # 4. Por defecto: producto a medida
    return 'A medida'


def _build_gallery(folder, slug, metadata_screenshots):
    """
    Une los archivos físicos del disco con las descripciones del metadata.
    Devuelve lista de dicts {url, descripcion} en el orden del metadata
    (si está presente) o alfabético del disco (fallback).
    """
    screenshots_dir = folder / 'screenshots'
    if not screenshots_dir.exists():
        return []

    # Index filesystem por nombre de archivo (basename)
    disk_files = {
        f.name: f'proyectos/{slug}/screenshots/{f.name}'
        for f in sorted(screenshots_dir.iterdir())
        if f.is_file() and f.suffix.lower() in _SCREENSHOT_EXTS
    }

    gallery = []

    # Si el metadata lista screenshots con descripciones, usar ese orden
    if isinstance(metadata_screenshots, list) and metadata_screenshots:
        for item in metadata_screenshots:
            if not isinstance(item, dict):
                continue
            archivo = item.get('archivo', '')
            # "screenshots/01-foo.png" → "01-foo.png"
            basename = archivo.split('/')[-1]
            if basename in disk_files:
                gallery.append({
                    'url': disk_files.pop(basename),
                    'descripcion': item.get('descripcion', ''),
                })

    # Agregar archivos en disco no listados en metadata, evitando duplicados
    # por stem (ej. "1.png" si "1.webp" ya fue agregado desde metadata).
    added_stems = {Path(g['url']).stem for g in gallery}
    for basename, url in disk_files.items():
        if Path(basename).stem not in added_stems:
            gallery.append({'url': url, 'descripcion': ''})

    return gallery


def load_proyectos(proyectos_dir):
    """
    Lee todos los metadata.json dentro de ``proyectos_dir`` y retorna una
    lista de dicts enriquecidos con campos derivados:

    - ``slug``:               nombre de la carpeta (ej. "01-pozos-scz")
    - ``num``:                prefijo numérico (ej. 1)
    - ``gallery``:            lista [{url, descripcion}] emparejada con metadata
    - ``screenshot_urls``:    solo las URLs, sin descripciones
    - ``screenshot_main``:    primer screenshot o None si no hay
    - ``categoria_principal``: 'Con IA' / 'A medida' / 'Infraestructura' / 'Servicio' / 'Stack'
    - ``has_workflows``:      True si existe carpeta n8n-workflows/ con JSONs

    Se preserva el campo ``screenshots`` original del metadata.
    """
    proyectos_dir = Path(proyectos_dir)
    if not proyectos_dir.exists():
        logger.warning("PROYECTOS_DIR no existe: %s", proyectos_dir)
        return []

    proyectos = []

    for folder in sorted(proyectos_dir.iterdir()):
        if not folder.is_dir():
            continue

        metadata_path = folder / 'metadata.json'
        if not metadata_path.exists():
            continue

        try:
            with metadata_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Error leyendo %s: %s", metadata_path, e)
            continue

        slug = folder.name
        num_match = _FOLDER_NUMBER_RE.match(slug)
        num = int(num_match.group(1)) if num_match else 999

        gallery = _build_gallery(folder, slug, data.get('screenshots'))

        # Enriquecer sin pisar claves originales
        data['slug'] = slug
        data['num'] = num
        data['gallery'] = gallery
        data['screenshot_urls'] = [g['url'] for g in gallery]
        data['screenshot_main'] = gallery[0]['url'] if gallery else None
        data['categoria_principal'] = _derive_categoria_principal(data)
        data['has_workflows'] = (folder / 'n8n-workflows').exists()

        proyectos.append(data)

    proyectos.sort(key=lambda p: p['num'])
    logger.info("Cargados %d proyectos desde %s", len(proyectos), proyectos_dir)
    return proyectos
