# Servicios de infraestructura y plataformas self-hosted

**Tu infraestructura corriendo en tu VPS — sin mensualidades por usuario, sin datos afuera.**

---

## Posicionamiento

Setup llave en mano de la infraestructura que tu empresa necesita para dejar de pagar mensualidades por feature y por usuario. Te instalamos, configuramos y documentamos:

- **VPS con Linux** endurecido y listo para producción.
- **Nubes privadas** (Nextcloud / ownCloud) con todas sus apps (calendar, chat, office online).
- **Automatización self-hosted** con n8n — integraciones ilimitadas, con IA opcional vía MCP.
- **Web stack** completo (Nginx + Let's Encrypt + Docker) para correr lo que hoy pagás en Heroku, Render o Vercel.

A diferencia de los Proyectos 1-6, esto **no es un producto propietario**: es un **servicio profesional**. El entregable es tu infraestructura funcionando, documentada y en tus manos — más 30 días de soporte post-entrega y capacitación al equipo.

---

## Para quién

- **PyMEs** que quieren bajar costos de Google Workspace / Microsoft 365 / Dropbox Business.
- **Consultoras** que hoy pagan Zapier / Make por operación y ya no les alcanza el plan.
- **Equipos de IT internos** que necesitan estandarizar su stack de deploy.
- **Empresas con datos sensibles** (legal, salud, financiero, gobierno) que necesitan soberanía de datos.
- Organizaciones que quieren **sumar automatización y/o IA** sin subir datos a servicios externos.
- Clientes con **compliance estricto** que exigen infraestructura en jurisdicción conocida.

---

## Qué problemas resuelve

- Factura de SaaS que **crece cada mes** con el equipo.
- **Datos de la empresa en servidores de terceros** sin control real.
- **Vendor lock-in** — migrar en 3 años es caro y doloroso.
- Dependencia de features que el SaaS puede **quitar, mover de plan o cobrar aparte**.
- Ausencia de un **estándar de deploy** en el equipo de IT.
- Miedo a tocar Linux puro — falta de conocimiento para montar todo bien.
- Cumplimiento regulatorio complicado cuando los datos viven en otra jurisdicción.

---

## Los 4 módulos

### ◆ VPS con Linux — desde ½ día

Instalación base endurecida sobre Ubuntu 22.04 LTS o Debian 12 LTS: usuario administrador con SSH por clave (root deshabilitado), firewall UFW / nftables con solo los puertos necesarios, fail2ban contra brute-force, unattended security upgrades, swap, timezone, locale, logrotate y hardening CIS básico. Se entrega el VPS endurecido y una doc. de accesos.

### ◈ Nextcloud / ownCloud — 2-4 días

Nube privada con todas las apps relevantes para la empresa: Calendar, Talk (chat + videollamadas), Office online (Collabora u OnlyOffice). Postgres o MariaDB gestionada, Redis como cache, SSL con subdominio propio. Storage externo S3 / B2 / local según necesidad. LDAP / SAML / OIDC opcional para SSO con el directorio de la empresa. Backup rutinado y restore probado.

### ▸ n8n — 1-3 días

Automatización self-hosted última versión en imagen oficial o custom (con Python 3.12 incluido). Docker + Postgres + Redis queue para escalabilidad horizontal. HTTPS con auth básica o OIDC. Opcionalmente, **n8n-MCP** para conectar Claude Code / Cursor a n8n y que la IA escriba workflows hablando con el servidor. Se entregan 3 workflows base de ejemplo (mail, Slack/WhatsApp, API), credenciales cifradas con encryption key estable, workflows versionados en git.

### ◉ Nginx · Certbot · Docker — ½ - 2 días

Stack web completo: Nginx reverse proxy multi-dominio, Let's Encrypt con renovación automática, Docker + Docker Compose. Redirección HTTP → HTTPS forzada con HSTS, gzip / brotli + cache de estáticos, rate limiting y headers de seguridad (CSP, X-Frame, XSS). Docker-compose.yml de ejemplo (app web + DB), healthchecks y restart policies.

---

## Qué queda instalado

Todo corre en un **único VPS** (Ubuntu 22.04, 4 vCPU, 8 GB RAM típico) endurecido con UFW + fail2ban + SSH por clave.

**Capa de entrada:** Nginx como reverse proxy con HTTPS de Let's Encrypt. Subdominios apuntando a cada servicio (`cloud.cliente.com` → Nextcloud, `n8n.cliente.com` → n8n, `app.cliente.com` → app web, etc.).

**Capa de servicios (Docker Compose):** Nextcloud (cloud privado), n8n (automatización), Django o la app web que corresponda (opcional), Postgres 17 (DB principal — puede hospedar 2 DBs en el mismo cluster), MariaDB 10.11 (opción para Nextcloud), Redis 7 (cache y sesiones), n8n-MCP (IA ↔ n8n, opcional), Gunicorn 3 workers (si hay Django).

**Capa transversal — seguridad, backup, monitoring:**

- **Seguridad:** SSH por clave (root off), UFW con puertos 22 / 80 / 443, fail2ban (SSH, Nginx, n8n), unattended security upgrades, headers HSTS / CSP / X-Frame / XSS, rate limiting en Nginx.
- **Backup:** dump Postgres diario, dump MariaDB diario, snapshot de volúmenes Docker, retención 7d / 30d / 365d, copia offsite S3 / B2 opcional, restore probado al final del proyecto.
- **Monitoring:** uptime check externo, alertas por mail o Telegram, journalctl + logrotate, métricas Docker, cron-healthcheck.io opcional, Grafana + Prometheus opcional.
- **Accesos:** doc. de credenciales cifrada, recomendación de Vault / pass, admin user Django aleatorizado (si aplica), tokens rotados post-entrega, sudo con contraseña, acceso SSH restringido a admin.

---

## Proceso de entrega

El trabajo se divide en 6 fases con entregable concreto en cada una:

**01 — Kickoff (½ día).** Call inicial, relevamiento de dominios, elección del proveedor VPS, acceso compartido (SSH o panel del proveedor), confirmación de entregables. *Entregable: plan de trabajo + accesos compartidos.*

**02 — VPS base (½ - 1 día).** Instalación del sistema operativo, usuario admin con SSH por clave, hardening (UFW, fail2ban, updates), timezone / swap / logrotate, healthcheck inicial. *Entregable: VPS endurecido.*

**03 — Docker + Nginx (½ día).** Docker + Compose, Nginx como reverse proxy, DNS apuntando a la IP, Let's Encrypt (certbot), HSTS + redirección HTTPS. *Entregable: stack web con SSL.*

**04 — Plataformas (1-3 días).** Instalación de Nextcloud / ownCloud, n8n + Postgres + Redis, app Django si corresponde. Configuración inicial, usuarios y permisos. *Entregable: servicios listos para usar.*

**05 — Backup + monitor (½ día).** Rutina de backup, retención configurada, restore probado, uptime check externo, alertas por mail / Telegram. *Entregable: operación cubierta.*

**06 — Handoff (½ día).** Documentación completa, runbook de operación, transferencia de accesos, capacitación al equipo, sesión de dudas. *Entregable: cliente en control.*

**Duración total típica: 3,5 a 6 días**, según los módulos elegidos. Solo Nextcloud: 1-2 días. Todo el paquete (los 4 módulos): 5-6 días. Incluye 30 días de soporte post-entrega.

---

## Casos de uso con números concretos

### PyME con 20 empleados — nube propia, mail, archivos

Comparación: Google Workspace / Microsoft 365 a ~$12/usuario/mes → **USD 2.880 / año**. Alternativa self-hosted: VPS $15-30/mes + setup único → **USD ~400 / año**. **Ahorro estimado: −86%.**

### Consultora con 50+ automatizaciones

Comparación: Make Pro $29/mes + Zapier Team $103/mes → **USD ~1.600 / año**. Alternativa self-hosted con n8n: VPS $15/mes + setup único → **USD ~200 / año**. **Ahorro estimado: −87%.**

### Equipo de IT interno estandarizando su deploy

Comparación: Heroku / Render $25-100/app/mes → **USD 300-1.200 por app por año**. Alternativa self-hosted: 1 VPS compartido para varias apps → **USD ~400 total / año**. **Ahorro estimado: −70% a −90%.**

### Empresa con datos sensibles (legal / salud / financiero / público)

SaaS multi-tenant implica riesgo legal y auditoría compleja. Alternativa self-hosted: VPS en jurisdicción elegida, auditable punto por punto. **Valor principal: riesgo reducido**, no ahorro directo.

---

## Lo que no se ve en la factura del SaaS

- **Datos fuera** — en jurisdicción ajena, sin control real.
- **Vendor lock-in** — migrar en 3 años es caro.
- **Cobro por feature** — cada addon es una línea más en la factura.
- **Cobro por usuario** — el equipo crece y la factura también.
- **Límite de ejecuciones / API** — techo oculto hasta que se llega.
- **Integraciones limitadas** — solo con lo que el proveedor permite.

---

## Diferenciales

**Vs. instalar desde cero con tutoriales de internet.** Te entrego en días lo que te tomaría semanas de ensayo-error. Incluye configuraciones de seguridad que rara vez aparecen en tutoriales públicos.

**Vs. contratar a un freelance genérico.** Base probada en los 6 proyectos reales que ya están en producción en la landing — no es experimentación.

**Vs. managed hosting (Cloudways, GridPane).** Control total, sin cobros por feature, sin tope de escalamiento, sin vendor lock-in.

**Vs. SaaS.** Costo plano, datos donde el cliente elija, migrable a otro proveedor con un `git clone` + `docker compose up`.

**Vs. instalación "a mano" sin código.** Todo queda versionado como código — reproducible, auditable, portable. Si hay que migrar el VPS de proveedor, es una tarde de trabajo, no un proyecto nuevo.

**Vs. solo entregar scripts.** Queda corriendo en tu VPS, con documentación, capacitación y 30 días de soporte.

---

## Stack técnico

| Capa | Tecnologías |
|---|---|
| Sistema base | Ubuntu 22.04 LTS o Debian 12 LTS |
| Hardening | UFW / nftables, fail2ban, SSH por clave, unattended upgrades |
| Orquestación | Docker, Docker Compose |
| Reverse proxy | Nginx + Let's Encrypt (certbot) |
| Bases de datos | PostgreSQL 17, MariaDB 10.11 (opción), Redis 7 |
| Plataformas | Nextcloud AIO / ownCloud, n8n, n8n-MCP (opc.) |
| App web opcional | Django + Gunicorn |
| Seguridad transversal | HSTS, CSP, X-Frame, rate limiting |
| Backup | pg_dump / mysqldump, snapshot volúmenes, offsite S3/B2 |
| Monitoring | uptime externo, alertas mail/Telegram, Grafana + Prometheus (opc.) |

---

## Beneficios

- Ahorro sostenido del **70-90%** frente a SaaS equivalentes (según caso).
- **Datos en tu jurisdicción**, auditables punto por punto.
- **Todo como código** — reproducible y portable a otro proveedor.
- Stack consistente con los Proyectos 1-6 de esta misma landing (si ya tenés Django + n8n funcionando, este servicio es natural).
- **30 días de soporte** post-entrega incluidos.
- **Capacitación al equipo** para que pueda operarlo solo.
- **Upgrade path claro** — se pueden sumar módulos sobre la marcha.

---

## Qué se incluye siempre

- VPS endurecido y documentado.
- Docker Compose completo del stack.
- Documento de accesos (credenciales cifradas).
- Runbook de operación (backup, restore, upgrade).
- 30 días de soporte post-entrega.
- Capacitación básica al equipo (1 sesión).

## Qué NO se incluye

- El **costo del VPS** (se contrata a nombre del cliente — Hetzner, DigitalOcean, Contabo, etc.).
- **Dominio y DNS** (el cliente los tiene o los compra).
- **Licencias de software de terceros** si no son open source.
- **Soporte ilimitado post 30 días** (hay plan mensual separado).

---

## Modelos de contratación

- **Por módulo** — solo VPS, solo Nextcloud, solo n8n, solo web stack.
- **Paquete completo** — los 4 módulos juntos con descuento.
- **Servicio continuo mensual** — operación, actualizaciones, nuevas plataformas a pedido.
- **Consultoría de migración** — de un SaaS actual al equivalente self-hosted, con plan y ejecución.

---

## Referencia cruzada

Este servicio es la **base técnica** sobre la que corren los Proyectos 1-6 de esta misma landing. Cada uno de esos proyectos incluye la infraestructura descripta acá.

- [Proyecto 1 — Plataforma de gestión operativa](../01-pozos-scz/README.md)
- [Proyecto 2 — Generador de documentos con IA](../02-generador-documentos-ia/README.md)
- [Proyecto 3 — Chatbot WhatsApp multi-agente](../03-chatbot-whatsapp-ia/README.md)
- [Proyecto 4 — Gestión de jornadas de equipos](../04-gestion-jornadas-equipos/README.md)
- [Proyecto 5 — Acelerador de desarrollo web a medida](../05-acelerador-desarrollo-web/README.md)
- [Proyecto 6 — Portal documental de obras distribuidas](../06-portal-documental-obras/README.md)

---

## Roadmap

- Paquete "Soberanía de datos" orientado a sector público y salud.
- Addon **Mail server** (Mailcow) como módulo opcional.
- Addon **Monitoring avanzado** (Grafana + Prometheus + Loki).
- Addon **GitLab / Gitea** self-hosted para equipos de desarrollo.
- Plan **multi-VPS** con replicación y failover.
- Migración asistida desde Google Drive / Dropbox a Nextcloud.

---

## Capturas

1. `01-catalogo-servicios.png` — catálogo de los 4 módulos con lo incluido, duración y entregable de cada uno.
2. `02-stack-instalado.png` — diagrama del stack completo que queda corriendo en el VPS.
3. `03-proceso-entrega.png` — timeline de 6 fases con entregable concreto en cada una.
4. `04-casos-uso.png` — 4 casos de uso con números concretos + comparativa self-hosted vs SaaS.

---

## Propuesta de valor, en una línea

> Tu infra corriendo en tu VPS. Sin mensualidades por usuario. Sin datos afuera.
