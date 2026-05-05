# Proyecto 5 — Acelerador de desarrollo web a medida

> **La base técnica que usamos para entregar aplicaciones Django a medida en días, no meses. Django 5 + PostgreSQL + Redis + n8n + n8n-MCP + Nginx, todo en Docker, desplegable en tu VPS con un comando y con seguridad enterprise de fábrica.**

---

## 1. Lo que es este producto

Es un **stack estandarizado de desarrollo y despliegue web** que reduce a horas lo que normalmente toma semanas en cada proyecto nuevo. No es un CMS, no es un framework, no es un SaaS — es un **backbone de infraestructura + buenas prácticas** que permite:

- Arrancar un proyecto nuevo con `git clone` + `make setup` y tener entorno listo en minutos
- Desplegar a producción en un VPS del cliente con **un solo comando** (`make deploy`)
- Tener **n8n integrado** desde el día 1 para automatizar procesos sin instalar nada más
- Integrar **IA desde el IDE** vía **n8n-MCP** — Claude Code o Cursor hablan directamente con los workflows
- Producir aplicaciones con **seguridad enterprise** de entrada: HSTS, CSP, rate limiting, brute-force blocker, SSL auto-renovable
- Todo el código y los datos corren **en la infraestructura del cliente** — sin vendor lock-in

Se entrega como parte de **cualquier proyecto Django a medida** que desarrollamos, y también puede **licenciarse al equipo interno de IT del cliente** para que lo adopten como su estándar.

### Para quién está pensado

- PyMEs y empresas que necesitan **una aplicación web a medida** rápido, sin depender de SaaS
- Equipos de IT internos que quieren un **estándar propio** de despliegue en Django
- Consultoras y agencias que cobran por resultados y necesitan **acortar el time-to-production**
- Empresas que quieren **automatizaciones internas** corriendo en su propia infraestructura (no en Zapier ni Make)
- Organizaciones que necesitan **integrar IA** con sus procesos internos y no quieren mandar datos a plataformas externas

### Problemas que resuelve

- Gastar 2 meses configurando Django, Postgres, Redis, Nginx, SSL, Docker y CSP antes de escribir la primera línea de valor
- Mantener media docena de proyectos con configuraciones distintas, cada uno con sus propios bugs de deploy
- Depender de plataformas SaaS de automatización (Zapier, Make) con cobro por operación y datos fuera del cliente
- Pagar servicios de hosting gestionado con costo recurrente alto
- Agregar IA a un proyecto existente y descubrir que el stack no la soporta
- Auditorías de seguridad que exigen headers, CSP, HSTS, rate limiting y hay que reimplementarlo en cada app

---

## 2. Capacidades del stack

### 2.1 Base Django lista para producción

- **Django 5.2+** con `core/settings.py` único que se adapta por variables de entorno
- **Gunicorn con 3 workers**, optimizado para VPS
- **DRF** preinstalado listo para APIs REST
- **Whitenoise** con `CompressedManifestStaticFilesStorage` — hashes en filenames, `.gz` pre-comprimidos
- **Nginx con `gzip_static`** sirve los estáticos directamente
- **Admin URL aleatorizada** generada por el wizard de setup
- **Zonas horarias y locales** configurables

### 2.2 Tailwind CSS v4 + DaisyUI v5

- Tailwind CSS 4.2 y DaisyUI 5.5 listos — sin configuración
- **Hot reload en desarrollo**: Tailwind recompila → Django recarga → browser se refresca
- **Build multistage en producción**: stage Node compila, stage Python solo se queda con el CSS final — imagen liviana
- Base para componentes UI modernos sin escribir CSS propio

### 2.3 PostgreSQL dual mode

- **Modo container**: PostgreSQL corre dentro de Docker Compose, simple y reproducible
- **Modo host**: los contenedores se conectan al PostgreSQL nativo del VPS — para casos donde el cliente ya tiene su propio cluster
- **Init script automático** crea las bases necesarias (una para Django, otra para n8n)
- Listo para backups programados

### 2.4 Redis 7 como capa de optimización

- **Cache compartido entre los 3 workers de Gunicorn** — cache real, no por-proceso
- **Sesiones en memoria** — sin golpes a PostgreSQL en cada request
- **Backend de django-axes** — las escrituras de intentos fallidos no martillean la DB
- **Channel layer disponible** para WebSockets cuando el proyecto lo necesite
- **Sin puerto expuesto** al exterior en ningún entorno

### 2.5 Automatización con n8n embebida

- **Subdominio propio** con SSL (`n8n.tudominio.com`) generado automáticamente
- **Imagen custom** con Python 3.12 integrado — el nodo "Code" puede correr Python además de JavaScript
- **Comparte PostgreSQL** con Django en una DB separada (sin sumar más servicios)
- **Workflows versionados en git** en `n8n/workflows/` — importados automáticamente al arrancar
- **Exportable** con `make n8n-export` para commitear cambios del dev
- **Actualización con un comando**: `make n8n-update` rebuild + restart preservando todos los datos
- **Encryption key estable** — las credenciales sobreviven a upgrades

### 2.6 n8n-MCP: canal IA nativo

- **Servidor MCP sobre HTTP/SSE** expuesto en `/mcp`
- **Token JWT** de autenticación
- **Integrable con Claude Code, Cursor, Claude Desktop** y cualquier cliente MCP
- Permite al desarrollador **crear, modificar, desplegar y ejecutar workflows de n8n hablando con un LLM desde su IDE**
- **Tools MCP expuestas**: `list_workflows`, `get_workflow`, `create_workflow`, `update_workflow`, `deploy_workflow`, `execute_workflow`, `validate_node`, `search_nodes`, `n8n_executions`, y varias más
- Roadmap: agentes de IA autónomos construyendo automatizaciones sin intervención humana

### 2.7 Nginx + Let's Encrypt automático

- **Reverse proxy** con HTTPS desde el día 1
- **Configuración generada dinámicamente** según el `.env` (multi-dominio si n8n está activo)
- **Headers de seguridad duros**: HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **Certificados Let's Encrypt** auto-renovables
- **`gzip_static on`** sirve los `.gz` pre-comprimidos sin trabajo extra

### 2.8 Seguridad enterprise out of the box

- **HSTS de 1 año** con subdominios y preload (en producción)
- **CSP estricto** vía django-csp, con modo relajado en DEBUG para el browser-reload
- **django-axes** — bloqueo por brute-force tras 5 intentos fallidos, 1h de cooldown, backend en Redis
- **Admin URL aleatorizada** desindexada por `robots.txt`
- **Throttling DRF** configurable
- **SECRET_KEY + tokens + passwords** generados por el wizard — no hay valores por defecto publicables
- **JWT con blacklist y rotación** si el proyecto usa autenticación stateless

### 2.9 Docker Compose con profiles

- **PostgreSQL** condicional (container vs host)
- **n8n** condicional (se activa si hay `N8N_DOMAIN` en el `.env`)
- **n8n-MCP** condicional (se activa si `N8N_MCP_ENABLED=true`)
- **Redis + Django** siempre activos
- **Healthchecks + restart policies** configurados
- **Volúmenes persistentes** para que los datos sobrevivan a rebuilds

### 2.10 Wizard de setup interactivo

- `make setup` ejecuta un script interactivo que:
  - Pide dominio principal, dominio n8n, email de admin, modo Postgres
  - Genera `SECRET_KEY`, `N8N_ENCRYPTION_KEY`, `N8N_MCP_AUTH_TOKEN`
  - Genera una **URL de admin aleatoria** (ej: `/panel-k9x4m2/`)
  - Crea el `.env` completo listo para `make deploy`

---

## 3. De cero a producción en 4 pasos

```
1) make setup
   → Wizard interactivo genera el .env (SECRET_KEY, dominios, tokens)

2) make nginx
   → Instala configuración de reverse proxy en el VPS

3) sudo certbot --nginx -d app.cliente.com -d n8n.cliente.com
   → Obtiene SSL automático para todos los subdominios

4) make deploy
   → git pull + verifica puertos + docker compose build + migrate + gunicorn up
```

Tiempo real: **bajo 10 minutos** para una VPS nueva. Los deploys posteriores solo necesitan `make deploy`.

---

## 4. Stack técnico resumido

| Capa | Tecnologías |
|---|---|
| **Framework** | Django 5.2+, Django REST Framework |
| **Servidor WSGI** | Gunicorn (3 workers) |
| **Base de datos** | PostgreSQL 17 (contenedor o host) |
| **Cache / sesiones** | Redis 7 |
| **CSS** | Tailwind CSS 4.2, DaisyUI 5.5 |
| **Static files** | Whitenoise + nginx `gzip_static` |
| **Automatización** | n8n (self-hosted, imagen custom con Python) |
| **Canal IA** | n8n-MCP server sobre HTTP/SSE |
| **Seguridad** | django-axes (Redis), django-csp, HSTS, throttling DRF |
| **Reverse proxy** | Nginx + Let's Encrypt auto-renovable |
| **Orquestación** | Docker Compose con profiles condicionales |
| **Hot reload dev** | django-browser-reload |

---

## 5. Beneficios concretos para el negocio

- **Reducción de 60+ días a horas** en el tiempo hasta el primer deploy
- **Costos operativos controlados**: un solo VPS, Docker Compose, Let's Encrypt gratuito
- **Sin mensualidades por automatización**: n8n self-hosted reemplaza a Zapier/Make para casos internos
- **IA conectada desde el día 1**: el desarrollo se acelera porque el propio desarrollador habla con la app vía LLM
- **Cumplimiento de seguridad fuera del día 1**: HSTS, CSP, rate limiting — no hay que explicarle al auditor
- **Datos y workflows dentro de casa** — cero lock-in con plataformas externas
- **Estándar reusable**: cada proyecto nuevo arranca de la misma base, el equipo se especializa más rápido
- **Actualizaciones controladas**: cambiar n8n o Django se hace con un comando y conserva los datos

---

## 6. Diferenciales frente a alternativas

- **vs. empezar de cero**: ahorrás 1-2 meses de configuración de infraestructura en cada proyecto
- **vs. SaaS (Heroku, Render, Vercel)**: tus datos y código viven en tu VPS — sin costos por usuario ni bloqueos de tier
- **vs. plataformas no-code (Bubble, Retool)**: tenés el código, podés extender sin límites, y la IA puede leerlo
- **vs. Zapier / Make**: n8n embebido, sin costos por operación, con Python nativo en los nodos Code
- **vs. Django "solo"**: n8n-MCP te permite que IA escriba workflows en tu infraestructura — diferenciador único
- **vs. boilerplates genéricos**: este está afinado en proyectos reales en producción (los Proyectos 1–4 corren sobre él)

---

## 7. Caso de referencia

**Este acelerador es el backbone de los Proyectos 1–4 de esta misma página.**

- **Proyecto 1** (Plataforma de gestión operativa con mapas) — Django + Postgres + Nginx heredados de este stack
- **Proyecto 2** (Generador de documentos con IA) — n8n para orquestar los 8 agentes + Django + Postgres
- **Proyecto 3** (Chatbot WhatsApp multi-agente) — n8n-MCP como diferenciador técnico + Django dashboard
- **Proyecto 4** (Gestión de jornadas y supervisión operativa) — Django Channels + Postgres + Redis + n8n

Esto significa que **todo lo que ves funcionando en los otros 4 proyectos corre sobre esta base**. No es una propuesta teórica — es un estándar probado en producción con clientes reales.

---

## 8. Modelos de contratación

- **Incluido** en cualquier proyecto Django a medida que desarrollemos — el cliente recibe la app + el stack
- **Licenciamiento** para equipos internos de IT que quieran adoptarlo como su estándar, con soporte y capacitación
- **Consultoría de migración** para llevar aplicaciones Django existentes a este stack (deploy, seguridad, integración n8n/MCP)
- **Soporte continuo** con actualizaciones de versiones y nuevos módulos

---

## 9. Roadmap corto

- Plantilla de **agentes de IA autónomos** que se auto-despliegan con `n8n-MCP`
- Módulo opcional de **observabilidad**: Grafana + Prometheus sobre los mismos containers
- Módulo opcional de **CI/CD con GitHub Actions** preconfigurado
- Plantilla de **multi-tenant** para entregar SaaS a partir del mismo stack
- Integración directa con **WhatsApp Business API** como módulo plug-and-play

---

## 10. Material visual

En `/screenshots/` están los mockups:

1. `01-stack-completo.png` — Diagrama completo del stack con las 9 piezas y los 4 pasos de deploy
2. `02-deploy-flow.png` — Terminal mostrando un deploy real de cero a producción en 4 min 12 s
3. `03-mcp-integracion.png` — Flujo de IA ↔ n8n-MCP ↔ n8n ↔ Django
4. `04-timeline-comparacion.png` — Comparación visual: desarrollo tradicional vs. con este acelerador

En `/n8n-workflows/` están workflows de ejemplo listos para importar:

- `chat_webhook.json` — Webhook base para recibir mensajes y redirigir a agentes
- `zHV5dYAqduSEfSiR.json` — Workflow de ejemplo de n8n

---

## 11. Propuesta de valor en una línea

> **Bajá a horas lo que te lleva meses. Stack Django + n8n + IA listo, en tu propia infraestructura, seguro de fábrica y con un solo comando para deployar.**
