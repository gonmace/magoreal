# Proyecto 4 — Plataforma de gestión de jornadas y supervisión operativa de equipos

> **Sabé quién está conectado, cómo está su jornada y qué tiene entre manos — en tiempo real, con agente de escritorio, app móvil con GPS y dashboard ejecutivo. Desplegable en tu propia infraestructura.**

---

## 1. Lo que ofrece esta plataforma

Es una **solución full-stack de visibilidad operativa y control horario** que combina tres piezas que funcionan como una sola:

- Un **agente de escritorio** silencioso (Windows) que confirma la presencia del empleado, saca capturas de pantalla programadas y mantiene un canal en vivo con el servidor.
- Una **app móvil** pensada para empleados en calle, con GPS obligatorio al cerrar la jornada.
- Un **backoffice web** con vista ejecutiva en tiempo real y vista personal del empleado.

Todo corre **en infraestructura propia del cliente** (Docker Compose sobre VPS o nube privada), con **código propietario auditable**, autenticación vía SSO corporativo (Nextcloud OAuth2 u otro proveedor OIDC) y sin dependencia de SaaS de tracking con cobro por usuario.

### Rubros donde se implementa

- Empresas con equipos remotos o híbridos que necesitan evidencia de jornada
- Operaciones con personal de campo (técnicos, promotores, supervisores, distribuidores)
- Consultoras, agencias y centros de servicios que facturan por horas
- Empresas multirubro con oficinas + equipo de calle en simultáneo
- Organizaciones reguladas que necesitan auditoría de presencia y actividad

### Problemas que resuelve

- No saber quién está realmente trabajando en un momento dado
- Reportes de horas informales por WhatsApp o planilla, con errores y sin evidencia
- Jornadas que quedan abiertas toda la noche por olvido del empleado
- Personal de campo imposible de ubicar — no hay forma de saber si llegó al cliente
- Supervisores que deben llamar uno por uno para pedir estado
- Falta de calendario centralizado de vacaciones, licencias y feriados
- Plataformas SaaS que cobran por empleado y guardan datos sensibles en sus servidores

---

## 2. Capacidades de la plataforma

### 2.1 Agente de escritorio (Windows)

- **Instalador .exe** profesional (Inno Setup) con autostart al iniciar el sistema
- **Captura de pantalla por intervalo** configurable (global o por empleado)
- **Captura automática al cerrar jornada** — evidencia sin intervención del usuario
- **Auto-activación** mediante token + `config.json` distribuido con el instalador — onboarding de un clic
- **WebSocket persistente** al backend — el dashboard ve el estado en vivo
- **Respuesta a capturas inmediatas** solicitadas por el ejecutivo en menos de 1 segundo
- **Renovación automática de JWT** con refresh token (válido 30 días)
- **Reconexión con backoff exponencial** — resiste redes inestables
- **Auto-update de versión** con alerta en el dashboard si quedó desactualizado

### 2.2 App móvil (SPA)

- **Login usuario/contraseña** (sin SSO corporativo — pensado para personal externo o de calle)
- **Botones grandes** de inicio y fin de jornada con timer en vivo
- **GPS obligatorio al finalizar**: si el navegador niega la ubicación, el botón queda bloqueado — evidencia real de presencia en campo
- **Historial de actividad del día** editable por el empleado
- **Tokens JWT** persistidos en localStorage — la app sobrevive al refresco
- **Funciona en cualquier navegador móvil** — sin pasar por Play Store ni App Store

### 2.3 Dashboard ejecutivo (web)

- **Tabla de empleados en tiempo real**: online/offline, jornada activa, minutos de inactividad, GPS si es móvil, cantidad de capturas del día
- **Captura inmediata** por empleado (envía comando al agente por WebSocket)
- **Calendario mensual por empleado** — historial de jornadas con color por estado
- **Calendario del equipo** — feriados, eventos y notas compartidas
- **Registro de ausencias** con rango de fechas: vacación, licencia, permiso
- **Toggles por empleado**: activar/desactivar capturas, activar/desactivar acceso a la plataforma
- **Onboarding del agente**: generación de token + config.json + descarga del instalador
- **KPIs en cabecera**: empleados activos, jornadas en curso, sin agente, auto-cerradas

### 2.4 Dashboard del empleado (web)

- **Estado del agente** (online/offline) y versión instalada con alerta si hay nueva
- **Jornada en curso** con hora de inicio, tiempo trabajado y botón de finalizar
- **Calendario mensual** con horas trabajadas por día y totales semanales
- **Jornadas auto-cerradas** marcadas con alerta (el sistema cerró por vos a las 17:00)
- **Días con ausencia** coloreados según tipo (vacación / licencia / permiso)
- **Notas del equipo** visibles al pasar el mouse por cada día
- **Descarga del instalador del agente** desde la misma tarjeta de onboarding

### 2.5 Cierre automático de jornadas

- A las **17:00 (zona horaria configurable)** el sistema detecta jornadas sin cerrar del día anterior y las cierra con `auto_closed=True`
- **Se marcan en amarillo** en el calendario con tooltip de alerta para que el empleado lo vea al día siguiente
- Evita que una jornada olvidada quede corriendo 10 horas extra

### 2.6 Almacenamiento de capturas

- **Local** (`media/screenshots/<empleado>/<YYYY-mes>/<DD-HHhMMmSS>.jpg`) — simple, sin costos adicionales
- **Nextcloud vía WebDAV** — las capturas viajan encriptadas al NAS corporativo; las URLs se sirven por un **proxy interno seguro** que valida permisos
- **Limpieza programada** por retención configurable
- El empleado **nunca ve capturas de otros** — solo el ejecutivo autorizado

### 2.7 Tiempo real (Django Channels + Redis)

- **Dos canales WebSocket**: `ws/agent/` para los agentes, `ws/dashboard/` para los navegadores
- **Handshake con JWT** — nadie se conecta sin token válido
- **Channel layer en Redis** — escala a muchos agentes sin perder latencia
- Comandos remotos al agente (ej: "saca captura ahora") responden en menos de un segundo

### 2.8 Automatización con n8n

- Integración con **n8n** embebido en la infra para disparar flujos automáticos:
  - Email/WhatsApp al supervisor cuando alguien no inicia jornada a la hora esperada
  - Resumen diario automático del equipo
  - Export de reportes a planillas corporativas
  - Hooks con sistemas externos (RRHH, ERP, nómina)

### 2.9 IA operativa (roadmap incluido en la arquitectura)

- **Análisis de productividad por IA** sobre reportes diarios y capturas
- **Detección de anomalías** en jornadas (muy cortas, muchas auto-cerradas, inactividad excesiva)
- **Resumen inteligente** de la actividad del equipo por semana
- **Chat con asistente operativo** — "¿cuántas horas trabajó Juan en marzo?"
- Arquitectura preparada para enchufar modelos LLM con RAG sobre la base operativa

---

## 3. El motor: cómo se sincroniza todo en tiempo real

### 3.1 Flujo del empleado de escritorio

1. El empleado abre el dashboard, hace login con SSO corporativo
2. Descarga el instalador del agente desde la misma tarjeta de onboarding
3. El instalador detecta el `config.json` adjunto y activa el agente silenciosamente
4. El agente abre WebSocket al backend, queda **online**
5. El empleado presiona **"Iniciar jornada"** — empieza el timer en el dashboard y en el agente
6. El agente saca capturas según el intervalo configurado
7. Al presionar **"Finalizar jornada"**, el sistema pide el **reporte diario** (actividades hechas + planificadas) y dispara una captura automática de cierre
8. Si el empleado olvida cerrar, a las 17:00 el sistema lo hace por él (y lo marca como auto-cerrada)

### 3.2 Flujo del empleado de campo (móvil)

1. El empleado abre `/mobile/` en el navegador de su celular
2. Login con usuario/contraseña
3. Permite acceso al GPS
4. Presiona **"Iniciar jornada"** — queda registrada la ubicación
5. Durante el día agrega actividades a mano
6. Al cerrar, el sistema **exige GPS activo** y registra la ubicación de cierre

### 3.3 Flujo del ejecutivo

1. Abre el dashboard, SSO lo identifica como `executive`
2. Ve la tabla con todos los empleados en vivo
3. Si necesita ver qué está haciendo alguien, clic en **"Captura YA"** → el agente responde en menos de un segundo
4. Si alguien se va de vacaciones, registra la ausencia en el calendario
5. Si hay un feriado, lo carga como nota del equipo — todos los empleados lo ven
6. Ajusta toggles por empleado (capturas activas, acceso habilitado)

---

## 4. Stack técnico

| Capa | Tecnologías |
|---|---|
| **Backend** | Django 5.1, Django REST Framework, SimpleJWT con blacklist |
| **Real-time** | Django Channels 4, Daphne (ASGI), Redis |
| **Base de datos** | PostgreSQL 17 (SQLite en dev) |
| **Frontend web** | Django Templates, Tailwind CSS v4, DaisyUI v5, Whitenoise |
| **App móvil** | SPA autónoma (HTML/JS) con JWT en localStorage y Geolocation API |
| **Agente Windows** | Python 3.11, Pillow, WebSockets, PyInstaller (.exe), Inno Setup |
| **Autenticación** | OAuth2 corporativo (Nextcloud / OIDC genérico), JWT con refresh y blacklist |
| **Almacenamiento** | Local (`media/`) o Nextcloud WebDAV con proxy interno |
| **Orquestación** | n8n (self-hosted) para flujos de negocio |
| **Infra** | Docker Compose, Nginx, HTTPS Let's Encrypt, VPS Ubuntu o nube del cliente |
| **Seguridad** | django-axes (brute-force), CSP, HSTS, throttling DRF, admin URL aleatorizada |

---

## 5. Beneficios concretos para el negocio

- **Visibilidad total del equipo en un solo pantallazo** — online, jornada, inactividad, GPS
- **Evidencia irrefutable de horas trabajadas** — agente, capturas, GPS
- **Cero fricción para el empleado** — agente silencioso, app móvil simple
- **Cero abandono de jornadas** — cierre automático al final del día
- **Reportes de jornada automáticos** — sin que nadie tipee nada extra
- **Control horario sin espiar** — las capturas son visibles solo al ejecutivo autorizado y el empleado sabe que existen
- **Datos dentro de casa** — nada se va a un SaaS externo
- **Escalable a decenas o cientos de empleados** sin cambiar la arquitectura
- **Integrable con RRHH, nómina y ERP** vía n8n

---

## 6. Diferenciales frente a soluciones genéricas

- **Desktop + Mobile + Web integrados en un solo producto** — no hay que pegar tres herramientas distintas
- **Agente propio** con auto-activación de un clic (token + config.json embebido) — onboarding real sin soporte técnico
- **GPS obligatorio solo para quien debe** (empleados móviles) — no invade al empleado de oficina
- **Cierre automático de jornadas** — funcionalidad que ninguna planilla tiene
- **100% on-premise / nube privada** — capturas y ubicaciones nunca salen del cliente
- **SSO corporativo** para los empleados internos, **usuario/pass** para los externos — sin mezclar modelos de identidad
- **Sin mensualidad por empleado** — licencia única, escalable
- **Seguridad enterprise**: JWT blacklist, CSP, HSTS, rate limiting, admin URL aleatorizada, brute-force blocker
- **Código propio, sin vendor lock-in** — mañana cambia el SSO o el storage y se reconfigura
- **Arquitectura lista para IA** — se puede enchufar un analizador de productividad o un asistente sin rehacer nada

---

## 7. Caso de referencia

**Operación corporativa** (confidencial — datos del cliente protegidos por NDA).

Empresa con equipo mixto de empleados de oficina + personal técnico de campo. La plataforma está en producción dando:

- Tabla ejecutiva con el equipo en vivo
- Captura inmediata bajo demanda
- Cierre automático de jornadas olvidadas a las 17:00
- Calendario de ausencias y feriados centralizado
- App móvil con GPS para los técnicos en calle
- Integración con el Nextcloud corporativo como proveedor de identidad y como almacén de capturas

Se puede compartir **demo funcional en entorno controlado** y **casos de uso detallados** bajo firma de NDA recíproco.

---

## 8. Roadmap corto

- Analizador de productividad por IA sobre reportes diarios
- Detección de anomalías en jornadas (muy cortas, inactividad larga)
- Chat con asistente operativo para consultar la base
- App móvil nativa (Flutter) con modo offline
- Integración directa con sistemas de nómina populares
- Webhooks públicos para que terceros escuchen eventos de jornada

---

## 9. Material visual

En `/screenshots/` están los mockups del producto:

1. `01-dashboard-ejecutivo.png` — Vista ejecutiva con la tabla del equipo en vivo y KPIs
2. `02-calendario-empleado.png` — Dashboard personal del empleado con calendario mensual
3. `03-app-movil-gps.png` — App móvil SPA con GPS y estado de jornada
4. `04-arquitectura.png` — Arquitectura completa del producto en una sola imagen

---

## 10. Propuesta de valor en una línea

> **Control horario real, con evidencia y sin espiar, desplegado en tu infraestructura. Agente de escritorio, app móvil con GPS y dashboard ejecutivo en vivo — todo desde un solo producto, con código propio.**
