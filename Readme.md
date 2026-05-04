# Magoreal Tecnología — Landing

Sitio web de [Magoreal Tecnología](https://magoreal.com), empresa de desarrollo web, automatización con IA e infraestructura self-hosted con base en Santa Cruz de la Sierra, Bolivia.

## Qué hace este proyecto

- **Landing page** con hero, servicios, comparativa, FAQ y formulario de contacto
- **Portfolio** de proyectos con páginas de detalle SEO-optimizadas
- **Lead magnet de licitaciones** — el prospecto sube un TDR/compulsa en PDF y recibe un borrador de pliego técnico generado con IA vía n8n
- **Páginas white-label** — un mismo Django sirve dominios de clientes distintos con identidad visual propia (tema, logo, idioma, webhooks) vía el modelo `SitePage`
- **Multilenguaje** (ES/EN) con `django-html-translator` y OpenAI como motor de traducción
- **MorphBanner** — componente SVG de letras animadas con morphing

## Stack

| Componente | Tecnología |
|---|---|
| Framework | Django 5.2+ |
| Servidor WSGI | Gunicorn (3 workers) |
| Base de datos | PostgreSQL 17 |
| Cache / Sesiones | Redis 7 |
| CSS | Tailwind CSS v4.2 + DaisyUI v5.5 |
| Archivos estáticos | Whitenoise (`CompressedManifestStaticFilesStorage`) + nginx |
| Traducciones | django-html-translator + OpenAI API |
| Seguridad | django-axes, django-csp, HSTS |
| Hot reload (dev) | django-browser-reload |
| Automatización | n8n (opcional) |
| MCP Server | n8n-MCP (opcional) |
| Reverse proxy | Nginx (host) + Let's Encrypt |

---

## Quick Start (VPS)

```bash
# 1. Clonar
git clone https://github.com/gonmace/magoreal miproyecto && cd miproyecto

# 2. Configurar — genera .env de forma interactiva
make setup

# 3. Configurar nginx (SOLO la primera vez — certbot modifica este archivo)
make nginx

# 4. Obtener certificado SSL
sudo certbot --nginx -d tudominio.com
# Si n8n está habilitado, agregar también: -d n8n.tudominio.com

# 5. Desplegar
make deploy
```

Para deploys posteriores solo se necesita `make deploy`. **Nunca volver a ejecutar `make nginx`** después de que certbot configuró el SSL.

---

## Desarrollo local

### Opción A — Mínimo (SQLite, sin Docker)

```bash
make install    # pip install + tailwind install
make setup      # genera .env (borrar POSTGRES_* para quedar en SQLite)
make dev        # migrate + tailwind watcher + runserver
```

### Opción B — Completo (PostgreSQL + Redis en Docker)

```bash
make install
make setup
make dev-up       # levanta Redis + PostgreSQL (+ n8n/MCP si están en .env)
make dev-check    # verifica estado
make dev-serve    # migrate + tailwind watcher + runserver
```

Django siempre corre nativo en el host (no en Docker).

### Hot reload

`make dev` / `make dev-serve` ejecutan `docker/run_dev_serve.py`: migraciones, Tailwind en subproceso y `runserver` en `127.0.0.1:APP_PORT`. `django-browser-reload` recarga el browser al cambiar Python o templates. Cambios CSS requieren refrescar manualmente (Tailwind recompila primero).

**Windows:** `NPM_BIN_PATH = r'C:\Program Files\nodejs\npm.cmd'` en `core/settings.py` dentro del bloque `if DEBUG:`.

---

## Arquitectura de apps

| App | Responsabilidad |
|---|---|
| `core/` | Settings, URLs globales |
| `landing/` | Hero, servicios, contacto, lead magnet de licitaciones |
| `portfolio/` | Proyectos — carga desde YAML/JSON en disco, SEO por slug |
| `site_config/` | Singleton `SiteConfig` + páginas white-label `SitePage` |
| `home/` | Vista raíz + sitemaps |
| `django-html-translator/` | Middleware de traducción HTML con caché y OpenAI |
| `theme/` | Tailwind CSS — `npm build` en Node stage del Dockerfile |

### SiteConfig vs SitePage

`SiteConfig` (singleton pk=1) es la identidad principal de Magoreal. `SitePage` activa una identidad alternativa cuando `request.get_host()` coincide con su campo `domain` — permite servir páginas de clientes con su propio logo, tema, idioma y webhooks desde el mismo Django.

### Lead magnet de licitaciones

El prospecto sube un PDF (TDR/compulsa) en la landing. Django lo guarda fuera del `MEDIA_ROOT` público, registra el lead en `PliegoDemoLead` y dispara un webhook n8n con el archivo. n8n procesa el PDF con IA y devuelve un borrador de pliego técnico al email del prospecto.

---

## Configuración por variables de entorno

`core/settings.py` único — el comportamiento cambia según `.env`:

| Variable | Ausente | Presente |
|---|---|---|
| `POSTGRES_DB` | SQLite | PostgreSQL |
| `N8N_DOMAIN` | n8n deshabilitado | n8n en contenedor |
| `EMAIL_HOST` | Backend consola | SMTP real |
| `DEBUG` | Producción (HSTS, CSP estricto) | Dev (browser-reload, Tailwind activo) |

Variables principales:

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Clave secreta Django |
| `DOMAIN` | Dominio principal |
| `ALLOWED_HOSTS` | Dominios permitidos (CSV) |
| `POSTGRES_DB/USER/PASSWORD` | Credenciales PostgreSQL |
| `REDIS_URL` | URL de Redis (default: `redis://redis:6379/0`) |
| `N8N_DOMAIN` | Subdominio n8n (activa el servicio) |
| `N8N_ENCRYPTION_KEY` | Clave n8n — **no cambiar nunca** |
| `PLIEGO_DEMO_WEBHOOK_URL` | Webhook n8n que procesa los PDFs de licitaciones |
| `APP_PORT` | Puerto Django (default: `8000`) |

---

## Servicios opcionales (Docker Compose profiles)

`deploy.sh` activa los profiles automáticamente según el `.env`.

### n8n

```env
N8N_DOMAIN=n8n.tudominio.com
N8N_ENCRYPTION_KEY=clave-generada-por-setup
```

Imagen custom con Python 3.12 para Code nodes. Comparte PostgreSQL (base `n8n`). Workflows versionados en `n8n/workflows/` — se importan al arrancar y se exportan con `make n8n-export`.

### n8n-MCP

```env
N8N_MCP_ENABLED=true
N8N_API_KEY=<generar en n8n: Settings > API>
N8N_MCP_AUTH_TOKEN=token-generado-por-setup
```

Expone un servidor MCP sobre HTTP en `https://n8n.tudominio.com/mcp` para integración con Claude Code u otros clientes MCP.

---

## Comandos

| Comando | Descripción |
|---|---|
| `make setup` | Wizard interactivo — genera `.env` |
| `make install` | Instala dependencias Python y Tailwind |
| `make dev-up` | Levanta servicios Docker de desarrollo |
| `make dev-check` | Verifica estado del entorno |
| `make dev` | Opción A: migrate + tailwind + runserver |
| `make dev-serve` | Opción B: mismo que `dev`, usar tras `make dev-up` |
| `make migrate` | Ejecuta migraciones |
| `make migrations` | Crea migraciones |
| `make superuser` | Crea superusuario |
| `make shell` | Django shell |
| `make collect` | collectstatic |
| `make n8n-export` | Exporta workflows de n8n a `n8n/workflows/` |
| `make n8n-update` | Actualiza n8n en producción (rebuild + restart) |
| `make nginx` | Instala config nginx (**solo primera vez**) |
| `make deploy` | Despliega en VPS (git pull + verifica puertos + rebuild) |
| `make logs` | Logs de Django en producción |

---

## Estructura

```
├── core/                    # Settings, URLs, WSGI
├── landing/                 # Landing principal + lead magnet licitaciones
│   └── morph_banner/        # Componente SVG de letras animadas
├── portfolio/               # Proyectos con páginas de detalle SEO
├── site_config/             # SiteConfig (singleton) + SitePage (white-label)
├── home/                    # Vista raíz + sitemaps
├── django-html-translator/  # Middleware de traducción HTML + OpenAI
├── theme/                   # Tailwind CSS (npm build)
├── templates/               # base.html, 404, 500, robots.txt
├── static/                  # Fuentes, imágenes, JS, OG images
├── n8n/workflows/           # Workflows n8n versionados en git
├── docker/
│   ├── n8n.Dockerfile       # n8n con Python 3.12
│   └── init-db.sql          # Crea la base de datos n8n
├── Dockerfile               # Multi-stage: Node (CSS) → Python (prod)
├── docker-compose.yml       # Producción
├── docker-compose.dev.yml   # Desarrollo
├── nginx.conf               # Template nginx Django
├── nginx-n8n.conf           # Template nginx n8n
├── deploy.sh                # Script de despliegue VPS
└── setup.sh                 # Wizard de configuración inicial
```
