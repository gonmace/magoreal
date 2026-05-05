# AGENTS.md - Magoreal Tecnologia / Landing Django

## Working directory

All commands run inside `landing/`. The `proyectos/` directory contains project data (screenshots, metadata JSONs) within the Django project.

## Developer commands

```bash
make setup      # genera .env interactivo (primera vez)
make install    # pip install -r requirements-dev.txt + tailwind install
make dev-up     # levanta Redis + PostgreSQL + n8n (segun .env)
make dev        # migrate + tailwind watch + runserver (hot reload completo)
make dev-check  # verifica estado del entorno
```

On Windows: the project uses PowerShell-compatible scripts. `run_dev_serve.py` wraps the tailwind/dev server startup because `tailwind &` backgrounding does not work in cmd.exe.

Django management commands use a dynamic MANAGE variable that routes to `docker compose exec django python manage.py` when DEBUG=False in .env.

## Django project structure

- `core/settings.py` -- unico, comportamiento driven por variables de entorno
- Apps: `landing/`, `portfolio/`, `translations/`, `site_config/`
- Plantillas: `templates/` (base + includes), `landing/templates/landing/`, `portfolio/templates/portfolio/`
- PROYECTOS_DIR en settings = `proyectos/` -- los proyectos se cargan desde JSON en runtime

## Tailwind / CSS

- Tailwind v4.2 + DaisyUI v5.5
- Dev: `python manage.py tailwind start` (compila en watch)
- Prod: Dockerfile compila en stage Node, copia solo CSS al stage Python
- Agregar una app Django: anadir a INSTALLED_APPS + `@source "../../../<app>"` en `theme/static_src/src/styles.css`

## n8n workflows

- Workflows JSON en `n8n/workflows/` -- exportados de n8n, NO editar a mano
- Actualizar n8n: `make n8n-update` (preserva workflows en volumen Docker)
- Traduccion: `n8n/workflows/traduccion.json` -- webhook Django en `/translations/request/`, callback en `/translations/callback/`

## Sistema de traduccion (secciones traducibles)

- `translations/sections.py` -- mapa de `section_key -> template_path`
- `translations/views.py` -- `_render_sections()` para landing, `_render_detail_sections()` para portfolio
- `translations/utils.py` -- `HtmlTextExtractor` (BeautifulSoup) extrae textos del HTML y reconstruye con traducciones
- CRITICO al crear partials de seccion traducibles: siempre cargar `{% load static portfolio_tags %}` -- `get_media_prefix` viene de `static`, `{% picture %}` de `portfolio_tags`
- `translations/templatetags/translations.py` -- `{% section %}` tag: sirve HTML cacheado en TranslationCache o fallback al template original
- Portfolio detail page keys: `proyecto-<slug>` (ej: `proyecto-01-pozos-scz`)

## Morph banner (fuentes y paths SVG)

- Datos Python: `landing/morph_banner/letter_paths.py` (en el paquete Django `landing/`; paths pre-muestreados para KUTE.js).
- Para **cambiar o añadir una fuente nueva**: ver procedimiento paso a paso en `docs/MORPH_BANNER_FONT.md`.
- Desde este directorio:

  ```bash
  python scripts/font_pipeline.py --font "landing/morph_banner/fonts/MiFuente.otf"
  # o
  make morph-banner-font FONT="landing/morph_banner/fonts/MiFuente.otf"
  ```

- Archivos recomendados: `landing/morph_banner/fonts/` (OTF/TTF nuevos).

## Portfolio project data

- Metadatos: `proyectos/<slug>/metadata.json`
- Screenshots: `proyectos/<slug>/screenshots/`
- Loader: `portfolio/loaders.py` -> `portfolio/context_processors.py:get_proyectos()`
- No son modelos Django -- se recargan en cache de modulo al restart o cuando cambia el JSON (dev mode)

## Testing

```bash
python -m pytest translations/tests.py -v  # tests de traducciones
python -m pytest -v                       # todos los tests
```

Pytest usa DJANGO_SETTINGS_MODULE = core.test_settings (pytest.ini). No necesita DB ni servicios.

## Conventions

- Rutas URL portfolio: `proyectos/<slug>/` (sin prefijo idioma) y `<lang>/proyectos/<slug>/` (con prefijo para SEO)
- Selector de idioma en `_nav.html`: JavaScript Alpine `langSelector()` -- detecta si estas en detail page y usa `page_key=proyecto-<slug>`
- Siempre usar `{% url 'namespace:name' args %}` para links internos -- nunca hardcodear paths
- `{% section "key" "template/path.html" %}` para secciones que se traducen via n8n
- Traducir contenido no-DB: el sistema envia HTML a n8n, OpenAI traduce textos, el callback reconstruye el HTML preserving spans y clases de color (`text-whatsapp`, `text-ia`, `text-accent`, etc.)
