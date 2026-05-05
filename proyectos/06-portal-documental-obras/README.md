# Portal documental de obras distribuidas con integración Nextcloud

**Un portal web donde toda la documentación de tus obras vive junto al mapa — sin cambiar las carpetas de Nextcloud.**

---

## Posicionamiento

Django + n8n + Nextcloud. Cada sitio geolocalizado, con su galería de fotos, sus subcarpetas, sus archivos y sus permisos — sin OAuth, sin migrar archivos, sin pagar por usuario.

La solución es un **portal documental georreferenciado**: unifica en un solo lugar el mapa de tus obras, el árbol de carpetas de cada sitio, las fotos del terreno y los documentos de entrega al cliente. La información sigue viviendo donde siempre estuvo — en Nextcloud (o cualquier nube privada que soporte WebDAV) — pero se consume a través de un portal web propio que respeta roles, filtra por estado de obra y visualiza todo sobre OpenStreetMap.

El cliente no tiene que migrar un solo archivo. El portal se adapta a la estructura de carpetas existente.

---

## Para qué industrias

Cualquier operación con **muchas obras distribuidas geográficamente** y documentación técnica por sitio:

- **Telecomunicaciones** — torres, antenas, tendido de fibra óptica, sitios de backhaul.
- **Energía** — líneas de transmisión, postes, subestaciones, parques solares / eólicos.
- **Agua y saneamiento** — redes, pozos, estaciones de bombeo, plantas satélite.
- **Minería** — accesos, campamentos, plantas satélite, obras civiles en faena.
- **Construcción civil** con decenas de obras simultáneas en distintas ubicaciones.
- **Mantenimiento de infraestructura** con brigadas dispersas (p. ej. rutas, puentes, oleoductos).

---

## Qué problemas resuelve

El punto de partida habitual: la empresa ya tiene Nextcloud (o Drive, o Dropbox Business) con una carpeta por contratista y, dentro, una carpeta por obra. Funciona para guardar archivos, pero no para **operar**. Problemas típicos:

- Decenas o centenas de obras, cada una con su carpeta, imposibles de encontrar sin saber el código exacto del sitio.
- La documentación técnica está separada del **sitio físico**: no se sabe qué obra corresponde a qué ubicación geográfica.
- Las **fotos que se mandan por WhatsApp** desde terreno nunca se integran con el resto de la documentación.
- **Permisos confusos**: administrador, visitante, ITO, cliente final — todos ven lo mismo o se arman shares a mano.
- Múltiples contratistas / empresas con sus propias carpetas y los mismos tipos de obra.
- Nadie sabe de un vistazo **qué sitios están al día y cuáles atrasados** sin abrir cada carpeta.
- Los **documentos finales de entrega al cliente** se mezclan con documentación de trabajo interno.

El portal resuelve todos esos problemas sin tocar la estructura de carpetas existente.

---

## Capacidades

### Portal multi-empresa

Cada contratista / empresa aparece en el sidebar con su número de sitios. Un click cambia todo el contexto (tabla de sitios, mapa, subcarpetas). La configuración de empresas se hace desde el admin de Django — no requiere redeploy.

### Vista de sitios

Tabla de sitios con código, nombre, coordenadas, contratista, ITO, estado y avance técnico. Búsqueda por código. Filtros por estado (asignado / en ejecución / completado) y por flags de avance configurables según la industria (hormigonado, montado, energizado, etc.).

### Mapa georreferenciado

Leaflet sobre OpenStreetMap — sin API keys ni costos por tile. Cada sitio es un pin coloreado por estado y por empresa. Clustering automático en zoom bajo. Popup con código, nombre, ITO, estado y link directo a la carpeta del sitio en el portal o en Nextcloud. Los filtros del mapa están sincronizados con la tabla: si filtro por "en ejecución", el mapa muestra solo esos sitios.

### Integración con Nextcloud vía n8n

Django **no habla WebDAV directamente**. Toda la comunicación con Nextcloud pasa por n8n mediante dos webhooks:

| Webhook | Uso |
|---|---|
| `nc-tekon` | Lista items (carpetas/archivos) de una ruta específica. |
| `nc-tekon-deep` | Devuelve conteo recursivo de archivos por subcarpeta en una sola petición. |

Internamente, n8n usa su nodo nativo de Nextcloud (WebDAV). Las credenciales quedan **dentro de n8n** — no en el settings de Django ni en variables de entorno del contenedor web. Los workflows se guardan como JSON versionado en el repo (`n8n-workflows/`), así que el deploy incluye la configuración del middleware.

### Caché en PostgreSQL

Llamar a Nextcloud por cada vista sería lento y cargaría el servidor. El portal cachea en Postgres:

- `EstructuraCache` — estructura de carpetas por empresa.
- `SitioCache` — árbol de subcarpetas por sitio con conteo de archivos y fecha real de última modificación.
- `ProyectoFinalCache` — árbol de docs. finales (entrega al cliente).

Cada registro tiene TTL configurable y se puede forzar un refresh desde el admin. La lógica es: hit → render en <50 ms. Miss → webhook n8n → actualizar caché → render.

### Roles y permisos sin OAuth

Muchas soluciones complican esto con OAuth2 contra Nextcloud, usuarios espejo y sincronización. El portal lo resuelve de forma más simple:

- `UserProfile` con rol **administrador** o **visitante** (extensible).
- `EmpresaLink` por empresa contiene dos URLs: `link_admin` (share de edición) y `link_visitante` (share de solo lectura).
- Cuando un usuario abre la carpeta de una empresa, el portal le entrega la URL según su rol.
- Nextcloud emite shares públicos con o sin contraseña — sin OAuth, sin IdP, sin complejidad.

Se puede ampliar a más roles (ITO, cliente final, supervisor) agregando columnas al modelo `EmpresaLink`.

### Docs. Finales

Vista separada para la documentación de **entrega al cliente**. No se mezcla con la documentación de trabajo. El cliente final puede tener acceso solo a esta sección, sin ver el trabajo en curso de los contratistas.

### Galería de fotos de obra

Las fotos que los técnicos mandan por WhatsApp se sincronizan automáticamente a Nextcloud (hay workflows y apps gratuitas para esto). El portal las muestra como una galería agrupada por fecha dentro del sitio. El ITO y el cliente ven el avance **sin tener que pedir fotos**.

### Auditoría de frescura

Cada carpeta trae su `mtime` real de Nextcloud (no el de la caché). Badges visuales marcan si la carpeta se actualizó hoy, esta semana, este mes o está atrasada. Un panel de actividad reciente muestra los últimos cambios a nivel empresa.

### API REST interna

Los endpoints están documentados y disponibles para integrarlos con otros sistemas o reemplazar el frontend por uno propio:

| Endpoint | Método | Uso |
|---|---|---|
| `/docs/api/sitios/` | GET | Lista sitios por empresa |
| `/docs/api/carpetas/` | GET | Carpetas con estructura o con archivos |
| `/docs/api/carpetas/archivos/` | GET | Subcarpetas con conteo de archivos por sitio |
| `/docs/api/final/tree/` | GET | Árbol de docs. finales |

---

## Arquitectura (deep dive)

El portal se compone de cuatro capas bien delimitadas:

**1. Usuarios — navegador.** Administrador (edita y sube archivos vía Nextcloud), visitante (solo lectura), ITO / supervisor (valida en campo), cliente final (ve solo Docs. Finales).

**2. Django portal — app web + API.** Login multi-empresa con rol por `UserProfile`, vista de sitios con filtros y búsqueda, mapa Leaflet con OpenStreetMap, galería por obra, API REST interna, caché en PostgreSQL para no hacer PROPFIND por cada request.

**3. n8n self-hosted — middleware.** Webhook `nc-tekon` (listado), webhook `nc-tekon-deep` (conteo recursivo), node Nextcloud nativo (WebDAV), auth y reintentos encapsulados, workflows versionados en git.

**4. Nextcloud — fuente de verdad.** Una carpeta por empresa (p. ej. `/20 AJ`, `/20 MER`, `/20 GH3`), carpeta unificada de Docs. Finales (p. ej. `/20-PTI SP`), sincronización automática de fotos de WhatsApp a carpetas por sitio, share URLs diferentes por rol.

### Flujo de datos para cargar los archivos de un sitio

1. Usuario abre el sitio **CL-LI-1196** en el portal.
2. Django solicita las subcarpetas a la capa de caché.
3. Si la caché es válida → responde en <50 ms y termina.
4. Si está vencida → `GET /webhook/nc-tekon?path=/20 AJ/CL-LI-1196`.
5. n8n ejecuta PROPFIND recursivo vía WebDAV contra Nextcloud.
6. n8n devuelve JSON con carpetas, conteo de archivos y fecha de última modificación.
7. Django guarda la respuesta en `SitioCache` con TTL.
8. Tailwind + DaisyUI renderizan los badges de actualización y los links a las carpetas.

---

## Stack

| Capa | Tecnologías |
|---|---|
| Framework | Django 5.2, DRF (views ligeras) |
| Base de datos | PostgreSQL 17 (prod), MariaDB 10.2+ (opción), SQLite (dev) |
| Frontend | Tailwind CSS v4.2, DaisyUI v5.5, django-browser-reload |
| Mapas | Leaflet, OpenStreetMap tiles |
| Middleware de integración | n8n self-hosted (webhooks + node Nextcloud) |
| Storage de documentos | Nextcloud (vía WebDAV a través de n8n) |
| Caché | Tablas Postgres (EstructuraCache, SitioCache, ProyectoFinalCache) |
| Auth | Django auth + UserProfile con rol (sin OAuth externo) |
| Orquestación | Docker Compose (Dockerfile + Dockerfile.mariadb) |
| Web server | Gunicorn + Nginx reverse proxy + Let's Encrypt |

El backbone técnico completo (Docker, Nginx, Let's Encrypt, seguridad enterprise, n8n embebido, wizard de setup) es el **[Proyecto 5 — Acelerador de desarrollo web a medida](../05-acelerador-desarrollo-web/README.md)**.

---

## Beneficios

- **Tiempo de búsqueda de un documento de obra**: de minutos a segundos.
- **Visión de conjunto**: qué sitios están al día y cuáles atrasados, en un mapa.
- **Cero migración**: Nextcloud sigue siendo la fuente de verdad, los archivos no se mueven.
- **Multi-empresa**: agregar nuevos contratistas desde admin sin tocar código.
- **Auditoría real**: fecha de última modificación desde Nextcloud, no inventada.
- **Permisos sin complejidad**: admin y visitante con URLs distintas, sin OAuth.
- **Cliente final segmentado**: accede solo a Docs. Finales, no ve trabajo en curso.

---

## Diferenciales

**Vs. obligar al usuario a navegar Nextcloud directo.** Nextcloud es excelente para guardar archivos; no es un panel de operaciones. El portal agrega contexto: mapa, estado de obra, permisos por rol, filtros, búsqueda — cosas que no vas a conseguir en la UI nativa de Nextcloud.

**Vs. SharePoint / SaaS documental.** Sin costo por usuario, sin encierro de datos. La nube privada del cliente sigue siendo la nube privada del cliente.

**Vs. Google Drive con permisos a mano.** El portal genera automáticamente la URL correcta según el rol del usuario — sin configurar permisos archivo por archivo.

**Vs. construir con WebDAV directo desde Django.** Tener n8n como middleware aísla credenciales (no viven en el contenedor web), permite agregar reintentos, caché y transformaciones sin tocar el código Django, y deja los workflows como código versionado. Además, n8n ya resuelve casos raros del protocolo WebDAV que en Python toman días de debugging.

**Vs. apps genéricas de GIS (ArcGIS, QGIS web).** Esas herramientas apuntan al análisis espacial; acá el foco es la documentación técnica operativa. Cada pin muestra qué falta, qué se entregó y quién lo hizo, no polígonos de análisis.

**Vs. no tener nada.** El ITO ya no manda por WhatsApp la carpeta del sitio — manda el link del sitio en el portal.

---

## Caso de referencia

Implementado en producción para un **contratista regional de telecomunicaciones** con operaciones multi-país (Chile) que subcontrata la ejecución de obras de torres, antenas y energización a varias empresas especializadas.

**Escala aproximada:** 87 sitios activos, 3 empresas contratistas, 4 roles diferenciados (administrador de la contratista principal, administradores de cada subcontratista, ITOs, cliente final).

**Valor aportado:** antes cada subcontratista miraba su propia carpeta de Nextcloud y la contratista principal tenía que abrir las tres para auditar. Ahora hay un mapa y un portal único por arriba, con permisos por rol, que además integra las fotos de WhatsApp de terreno y separa la documentación final de entrega al cliente.

**Publicable:** sí, con cliente anonimizado como "contratista regional de telecomunicaciones".

---

## Roadmap

- **Edición desde el portal** — subir / renombrar / mover archivos vía n8n (hoy es solo lectura).
- **Comentarios y tareas por carpeta** — un issue tracker ligero contextualizado por sitio.
- **Notificaciones** — WhatsApp o mail cuando un sitio cambia de estado o pasa cierto tiempo sin actividad.
- **App móvil PWA para ITO** — geolocalización del reporte en campo, upload directo de fotos.
- **OCR automático** de planos y documentos para búsqueda por contenido.
- **Panel de cumplimiento SLA** por sitio y contratista, con métricas de tiempo por etapa.

---

## Capturas

Las 4 imágenes en `screenshots/` son mockups (sin datos reales del cliente) que ilustran las vistas principales del portal:

1. `01-portal-sitios.png` — Portal principal con sidebar de empresas, subcarpetas de un sitio con conteo de archivos, panel de actividad reciente y Docs. Finales.
2. `02-mapa-sitios.png` — Mapa con pins coloreados por estado y empresa, filtros laterales, popup con detalle de obra.
3. `03-galeria-nextcloud.png` — Galería de fotos de obra agrupadas por fecha + árbol Nextcloud en vivo.
4. `04-arquitectura.png` — Diagrama de las 4 capas (usuarios, Django, n8n, Nextcloud) con el flujo de datos en 7 pasos.

Los workflows de n8n están versionados en `n8n-workflows/` y son importables directamente a cualquier instalación de n8n.

---

## Modelos de contratación

- **Proyecto llave en mano** — portal + workflows n8n + despliegue en VPS del cliente.
- **Licenciamiento** a equipos internos de IT con capacitación.
- **Adaptación a otra industria** — energía, agua, minería, construcción civil.
- **Soporte mensual** con actualizaciones de capacidades (nuevos filtros, nuevos roles, integraciones adicionales).

---

## Propuesta de valor, en una línea

> Toda tu obra en un mapa. Toda tu documentación, donde ya estaba.
