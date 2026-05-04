# django-html-translator

Django app reutilizable para traducción automática de páginas web via OpenAI.  
Extrae el texto visible de cada sección HTML, lo traduce con GPT y reconstruye
el markup original con las traducciones — preservando 100% de la estructura,
los scripts, los SVGs y los atributos no traducibles.

---

## Quickstart (5 minutos)

### 1. Instalar

```bash
# Desde git
pip install git+https://github.com/tu-usuario/django-html-translator.git

# Desde directorio local (para desarrollo activo)
pip install -e /ruta/a/django-html-translator
```

### 2. Configurar `settings.py`

```python
INSTALLED_APPS = [
    ...
    'html_translator',
]

MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',
    'html_translator.middleware.LanguageMiddleware',  # después de CSRF
    ...
]

TRANSLATIONS_CONFIG = {
    'OPENAI_API_KEY': 'sk-...',       # requerido
    'SECTIONS': [                      # requerido
        ('hero',      'app/_hero.html'),
        ('servicios', 'app/_servicios.html'),
        ('footer',    'app/_footer.html'),
    ],
    # Todo lo demás es opcional — tiene defaults razonables
}
```

### 3. Añadir URLs

```python
# proyecto/urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path('translations/', include('html_translator.urls')),
]
```

### 4. Migrar

```bash
python manage.py migrate html_translator
```

### 5. Usar en templates

```html
{% load translations %}

<!-- Renderiza sección con fallback automático al template original -->
{% section "hero" "app/_hero.html" %}
{% section "servicios" "app/_servicios.html" %}

<!-- Incluye el selector de idioma Alpine.js -->
{% html_translator_assets %}
```

### Verificar configuración

```bash
python manage.py html_translator_check
```

---

## Características

- **Traducción automática**: secciones HTML traducidas via OpenAI (GPT-4o-mini por defecto)
- **Extracción inteligente**: ignora `<script>`, `<svg>`, `aria-hidden`, `translate="no"`, emails
- **Reconstrucción 1:1**: el HTML original se reconstruye con los textos traducidos, sin perder estructura
- **Caché con detección de cambios**: SHA-256 sobre los textos extraídos — si el template cambia, se retraduce automáticamente
- **Asíncrono**: la traducción corre en background thread, no bloquea la request
- **Middleware de idioma**: resuelve el idioma desde prefijo URL (`/en/`), cookie, o default
- **Templatetags**: `{% section %}`, `{% tr %}`, `{% html_translator_assets %}`
- **Selector Alpine.js**: componente con polling automático y manejo de estado
- **Admin Django**: invalidación y regeneración de traducciones desde el panel
- **System checks**: errores claros en la consola si la configuración está incompleta
- **Rate limiting**: 10/h en producción, 200/h en dev (configurable)

---

## Requisitos

- Python 3.11+
- Django 4.2+
- Redis (opcional pero recomendado — para caché y estado de traducción en vuelo)
- Cuenta OpenAI con API key

---

## Configuración completa

### `TRANSLATIONS_CONFIG` — todas las opciones

```python
TRANSLATIONS_CONFIG = {
    # ── OpenAI ───────────────────────────────────────────────────────────────
    # Puede ser string o callable — el callable se invoca en cada traducción.
    # Útil para leer desde una base de datos o panel de administración.
    'OPENAI_API_KEY': 'sk-...',
    # o: 'OPENAI_API_KEY': lambda: MiConfigModel.get_solo().api_key,
    
    'OPENAI_MODEL': 'gpt-4o-mini',       # default: 'gpt-4o-mini'

    # ── Seguridad ────────────────────────────────────────────────────────────
    'CALLBACK_TOKEN': 'tu-token-secreto', # para el endpoint /translations/callback/

    # ── Idiomas ──────────────────────────────────────────────────────────────
    'DEFAULT_LANGUAGE': 'es',             # idioma base, no se traduce (default: 'es')
    'AVAILABLE_LANGUAGES': ['es', 'en', 'pt-br', 'fr'],  # whitelist para cookie (opcional)

    # ── Secciones ────────────────────────────────────────────────────────────
    # Lista de (nombre_sección, ruta_template) disponibles para traducir
    'SECTIONS': [
        ('hero',      'app/_hero.html'),
        ('servicios', 'app/_servicios.html'),
        ('contacto',  'app/_contacto.html'),
        ('footer',    'app/_footer.html'),
        ('sidebar',   'app/_sidebar.html'),
    ],

    # ── Páginas ──────────────────────────────────────────────────────────────
    # Controla qué secciones se traducen en cada URL (ver sección "Gestión de secciones")
    'PAGES': {
        'home':       ['hero', 'servicios', 'contacto', 'footer'],
        'about':      {'exclude': ['sidebar']},
        'faq':        '__all__',
        'blog-*':     {'exclude': ['sidebar']},
    },

    # ── Hooks del proyecto consumidor ────────────────────────────────────────
    # Contexto extra al renderizar secciones (formularios, objetos, etc.)
    # Firma: (request, page_key) -> dict
    'SECTION_CONTEXT_PROVIDER': 'myapp.hooks.get_section_context',

    # Renderer personalizado para páginas especiales (detalles, etc.)
    # Firma: (request, page_key) -> (sections_html, sections_texts, source_hash)
    'PAGE_RENDERERS': {
        'blog-*': 'myapp.hooks.render_blog_detail',
    },

    # Hook post-traducción (para invalidar cachés del proyecto, etc.)
    # Firma: (page_key) -> None
    'ON_TRANSLATION_UPDATED': 'myapp.hooks.on_translation_updated',

    # ── Reescritura de URLs en HTML traducido ────────────────────────────────
    # Reescribe hrefs para añadir prefijo de idioma en el HTML servido.
    # {lang} es reemplazado por el idioma actual en cada request.
    'URL_REWRITE_PATTERNS': [
        (r'href="/(?:[a-z]{2}(?:-[a-z]{2})?/)?blog/', 'href="/{lang}/blog/'),
        (r'href="/(?:[a-z]{2}(?:-[a-z]{2})?/)?tienda/', 'href="/{lang}/tienda/'),
    ],

    # ── Rate limiting ────────────────────────────────────────────────────────
    'RATE_LIMIT_DEBUG': '200/h',          # default: '200/h'
    'RATE_LIMIT_PROD': '10/h',            # default: '10/h'
}
```

---

## Gestión de secciones

### Formatos soportados en `PAGES`

```python
'PAGES': {
    # Lista → include explícito (formato original, backward compatible)
    'home': ['hero', 'servicios', 'footer'],

    # Dict con include → equivalente a la lista
    'about': {'include': ['hero', 'body']},

    # Dict con exclude → todas las secciones EXCEPTO las listadas
    'blog': {'exclude': ['sidebar', 'footer']},

    # '__all__' → todas las secciones declaradas en SECTIONS
    'faq': '__all__',

    # Wildcard → aplica a blog-mi-post, blog-otro-post, etc.
    'blog-*': {'exclude': ['sidebar']},

    # Wildcard con include
    'proyecto-*': {'include': ['hero', 'detalle']},
}
```

Si `PAGES` no está definido (o no encuentra el page_key), usa todas las secciones.

### Añadir secciones dinámicamente

Útil para añadir secciones desde otro Django app sin modificar settings:

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'myapp'

    def ready(self):
        from html_translator.sections import register_section
        register_section('mi_banner', 'myapp/templates/_banner.html')
        register_section('newsletter', 'myapp/templates/_newsletter.html')
```

---

## Configuración avanzada

### OpenAI key dinámica (desde base de datos o panel admin)

Si el proyecto tiene un modelo de configuración administrable, usa un callable:

```python
# myapp/models.py
class SiteConfig(models.Model):
    openai_api_key = models.CharField(max_length=200)
    openai_model = models.CharField(default='gpt-4o-mini', max_length=50)

# settings.py
TRANSLATIONS_CONFIG = {
    'OPENAI_API_KEY': lambda: SiteConfig.objects.first().openai_api_key,
    'OPENAI_MODEL':   lambda: SiteConfig.objects.first().openai_model,
    ...
}
```

### Contexto extra para secciones (formularios, datos dinámicos)

```python
# myapp/hooks.py
def get_section_context(request, page_key):
    from myapp.forms import ContactForm, NewsletterForm
    ctx = {
        'contact_form': ContactForm(),
        'lang_prefix': '/',
    }
    if page_key == 'home':
        ctx['newsletter_form'] = NewsletterForm()
    return ctx
```

### Renderer personalizado para páginas de detalle

```python
# myapp/hooks.py
def render_blog_detail(request, page_key):
    from html_translator.models import TranslationCache
    from html_translator.utils import HtmlTextExtractor
    from html_translator.sections import get_sections
    from django.template.loader import render_to_string
    from myapp.models import Post

    slug = page_key[len('blog-'):]
    post = Post.objects.get(slug=slug)
    context = {'post': post, 'request': request}

    sections_html, sections_texts = {}, {}
    for section_key, template_path in get_sections(page_key):
        html = render_to_string(template_path, context, request=request)
        if html.strip():
            sections_html[section_key] = html
            sections_texts[section_key] = HtmlTextExtractor(html).get_texts()

    source_hash = TranslationCache.compute_hash(sections_texts)
    return sections_html, sections_texts, source_hash
```

### Hook post-traducción

```python
# myapp/hooks.py
from django.core.cache import cache

def on_translation_updated(page_key):
    # Invalida cualquier caché adicional del proyecto
    cache.delete(f'available_langs:{page_key}')
    cache.delete('sidebar_langs')
```

---

## Uso en templates

```html
{% load translations %}

<!-- Sección traducida con fallback automático al template original -->
{% section "hero" "app/_hero.html" %}
{% section "servicios" "app/_servicios.html" %}

<!-- Campo individual (legado — pre-secciones) -->
{% tr "titulo_pagina" "Bienvenido" %}

<!-- Assets del selector de idioma -->
{% html_translator_assets %}
<!-- Con defer -->
{% html_translator_assets defer=True %}
```

### Selector de idioma Alpine.js

```html
<!-- Ejemplo de selector con Alpine.js -->
<div x-data="langSelector()">
  <button @click="choose('en')" :disabled="loading">EN</button>
  <button @click="choose('es')" :disabled="loading">ES</button>
  <button @click="choose('pt-br')" :disabled="loading">PT·BR</button>
  
  <span x-show="loading">Traduciendo...</span>
  <span x-show="error">Error — <button @click="retry()">reintentar</button></span>
</div>

{% html_translator_assets %}
```

### Excluir elementos del HTML de la traducción

En el template, usa los atributos HTML estándar:

```html
<!-- Excluir elemento y todos sus hijos -->
<span translate="no">WhatsApp</span>
<code translate="no">var x = 1;</code>

<!-- Excluir de la accesibilidad (también excluido de la traducción) -->
<span aria-hidden="true">decorativo</span>
```

---

## API HTTP

### `POST /translations/request/`

Solicita traducción para una página. El cliente hace polling hasta recibir `cached`.

**Request:**
```json
{ "page_key": "home", "lang": "en" }
```

**Respuestas:**
| status | Significado |
|--------|-------------|
| `cached` | Traducción lista — navegar a `/{lang}/` |
| `generating` | En proceso — sondear de nuevo en 5s |
| `base_language` | Es el idioma base, no se traduce |
| `unavailable` | OPENAI_API_KEY no configurado |
| `error` | Sin secciones para renderizar |

### `POST /translations/callback/`

Recibe traducciones de sistemas externos (n8n, webhooks propios).  
Requiere: `Authorization: Bearer {CALLBACK_TOKEN}`

**Request:**
```json
{
  "page_key": "home",
  "lang": "en",
  "content": {
    "hero": ["Welcome", "Automate your business...", ...],
    "servicios": ["Our services", ...]
  }
}
```

---

## Estructura de datos

### `TranslationCache`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `page_key` | CharField | `"home"`, `"blog-intro"`, etc. |
| `lang` | CharField | `"en"`, `"pt-br"`, `"fr"`, etc. |
| `content` | JSONField | `{section_key: html_traducido}` |
| `source_html` | JSONField | `{section_key: html_idioma_base}` |
| `source_hash` | CharField | SHA-256 de los textos fuente |
| `updated_at` | DateTime | Última actualización |

Constraint único: `(page_key, lang)` — una fila por página por idioma.

---

## Cómo funciona internamente

```
1. Usuario selecciona idioma
      ↓ POST /translations/request/ {page_key, lang}

2. Django renderiza cada sección del template en el idioma base
      ↓ HtmlTextExtractor extrae textos visibles (skip: scripts, SVGs, emails)

3. Persiste source_html + source_hash en TranslationCache
      ↓ Lanza background thread (no bloquea)

4. Thread: para cada sección
      ↓ Llama OpenAI con lista de textos
      ↓ Valida que el conteo sea exactamente N items
      ↓ HtmlTextExtractor.rebuild() reconstruye el HTML
      ↓ Guarda en TranslationCache.content

5. Cliente (polling 5s) recibe status="cached"
      ↓ Navega a /{lang}/

6. GET /{lang}/ — LanguageMiddleware fija LANGUAGE_CODE='en'
      ↓ {% section %} carga TranslationCache.content['hero']
      ↓ Aplica URL_REWRITE_PATTERNS
      ↓ Sirve HTML traducido marcado como safe
```

### Detección de cambios de template

Cuando el template HTML cambia:
- Se calcula SHA-256 sobre los **textos extraídos** (no el HTML crudo — evita falsos positivos por CSRF tokens)
- Si el hash actual ≠ hash guardado → se retraduce automáticamente
- El contenido anterior sigue visible durante la regeneración

---

## Admin Django

Accede en `/admin/html_translator/translationcache/`

Acciones disponibles:
- **Invalidar caché**: fuerza recarga desde DB en el próximo request (sin borrar datos)
- **Borrar y forzar regeneración**: elimina las traducciones; la próxima visita en ese idioma dispara nueva traducción

---

## Migración desde `translations` (módulo interno)

Si tenías el módulo `translations/` directamente en tu proyecto:

### 1. Renombra o elimina el directorio

```bash
mv landing/translations landing/_translations_backup
```

### 2. Instala la librería

```bash
pip install -e /ruta/a/django-html-translator
```

### 3. Actualiza `INSTALLED_APPS`

```python
# Antes:
'translations',
# Después:
'html_translator',
```

### 4. Actualiza URLs

```python
# Antes:
path('translations/', include('translations.urls')),
# Después:
path('translations/', include('html_translator.urls')),
```

### 5. Migra la tabla existente

Si tienes datos en `translations_translationcache`:

```sql
-- PostgreSQL / SQLite
ALTER TABLE translations_translationcache 
  RENAME TO html_translator_translationcache;

-- Actualiza django_migrations
UPDATE django_migrations SET app = 'html_translator' 
  WHERE app = 'translations';
```

O borra los datos y vuelve a generar traducciones (más simple si el volumen es bajo).

### 6. Crea `translations_hooks.py` en tu proyecto

Mueve la lógica específica del proyecto (formularios, portfolio, etc.) a un archivo de hooks:

```python
# myapp/translations_hooks.py

def get_section_context(request, page_key):
    from myapp.forms import ContactForm
    return {'contact_form': ContactForm(), 'lang_prefix': '/'}

def on_translation_updated(page_key):
    from myapp.context_processors import invalidate_available_langs
    invalidate_available_langs(page_key)
```

### 7. Añade `TRANSLATIONS_CONFIG` a settings

Ver sección "Configuración completa" arriba.

---

## Publicar en PyPI

```bash
pip install hatch

# Build
hatch build

# Test en TestPyPI primero
hatch publish --repo test

# Publicar en PyPI real
hatch publish
```

---

## Contribuir

```bash
git clone https://github.com/tu-usuario/django-html-translator
cd django-html-translator
pip install -e ".[dev]"
```

---

## Licencia

MIT
