Mockups generados para el Proyecto 7 (Servicios de infraestructura y
plataformas self-hosted).

Los 4 PNG fueron creados programáticamente con PIL porque este proyecto es un
servicio profesional (no un producto con UI propia). Los mockups ilustran el
catálogo de servicios, el stack técnico que queda instalado, el proceso de
entrega y la propuesta económica frente a SaaS equivalentes.

Archivos:

01-catalogo-servicios.png  (1400x880)
  Catálogo de los 4 módulos en un grid 2x2:
    · VPS con Linux (azul)        — desde 1 día    — 8 items incluidos
    · Nextcloud / ownCloud (morado) — 2-4 días      — 8 items incluidos
    · n8n Automatización (verde)   — 1-3 días      — 8 items incluidos
    · Nginx · Certbot · Docker (rosa) — 0,5-2 días  — 8 items incluidos
  Cada módulo muestra su tag, su duración estimada, los 8 items que incluye
  y el entregable final al cliente.
  Útil para la sección "Qué ofrecemos".

02-stack-instalado.png  (1400x860)
  Diagrama técnico del stack completo corriendo en un VPS:
    · Header con specs del VPS (Ubuntu 22.04, 4 vCPU, 8 GB RAM, 80 GB SSD)
    · Capa Nginx: 4 subdominios con sus targets
    · Capa Docker Compose: 8 servicios en grid (Nextcloud, n8n, Django,
      Postgres, MariaDB, Redis, n8n-MCP, Gunicorn) con versión y status OK
    · Capa transversal: Seguridad, Backup, Monitoring, Accesos con 6 items
      cada una
    · Footer con los 5 entregables finales al cliente
  Útil para la sección "Qué queda instalado" / "Arquitectura".

03-proceso-entrega.png  (1400x820)
  Timeline horizontal de 6 fases con nodos circulares numerados:
    01 Kickoff (½ día)  —  02 VPS base  —  03 Docker + Nginx  —
    04 Plataformas  —  05 Backup + monitor  —  06 Handoff
  Cada tarjeta muestra los pasos de la fase y su entregable concreto.
  Al pie: "Total típico 3,5 – 6 días" + "Incluye 30 días de soporte".
  Útil para la sección "Cómo trabajamos" / "Proceso".

04-casos-uso.png  (1400x860)
  Grid 2x2 con 4 casos de uso + comparativa económica:
    · PyME 20 empleados:   −86% vs Google Workspace / M365
    · Consultora con 50+ automatizaciones: −87% vs Zapier / Make
    · Equipo de IT interno: −70% a −90% vs Heroku / Render
    · Empresa con datos sensibles: riesgo reducido
  Cada caso muestra badges del stack, bullets del valor, y box de
  comparación (SaaS en rojo / Self en verde) con el ahorro en grande.
  Al pie: "Lo que no se ve en la factura del SaaS" con 6 costos ocultos.
  Útil para la sección "Ahorro y comparativa" / "Por qué self-hosted".
