Mockups generados para el Proyecto 6 (Portal documental de obras distribuidas
con integración Nextcloud).

Los 4 PNG fueron creados programáticamente con PIL para no exponer datos reales
del cliente (códigos de sitios, ubicaciones exactas, nombres de ITOs). Los
mockups reflejan la UI real del portal con datos ilustrativos.

Archivos:

01-portal-sitios.png  (1400x860)
  Vista principal del portal:
  - Sidebar con empresas (AJ / MER / GH3), buscador y filtros por estado.
  - Card de sitio seleccionado (CL-LI-1196 BLANCO ENCALADA) con coordenadas,
    altura de torre, ITO y flags de avance (hormigonado / montado / empalme E.).
  - Lista de 9 subcarpetas con conteo de archivos y fecha de última
    actualización.
  - Panel derecho con actividad reciente + Docs. Finales (entrega al cliente)
    como sección separada.
  - Indicador de última sincronización con Nextcloud vía n8n.
  Útil para la sección "Todo en un solo portal".

02-mapa-sitios.png  (1400x820)
  Vista de mapa:
  - Filtros laterales por empresa (checkbox con color), estado de obra
    (asignado / en ejecución / completado) y avance técnico con barras de
    progreso (hormigonado 68%, montado 52%, empalme E. 34%).
  - Mapa simulado (OpenStreetMap) con 30 pins coloreados por estado,
    3 clusters y un popup abierto sobre el sitio CL-AT-2174 con detalle.
  - Leyenda + botones de exportar CSV y abrir en Nextcloud.
  Útil para la sección "Tus obras, sobre el mapa".

03-galeria-nextcloud.png  (1400x820)
  Galería de obra y árbol Nextcloud:
  - Panel izquierdo con 12 fotos ordenadas por fecha (18 / 17 / 15 abr),
    agrupadas por día, cada una con su filename visible.
  - Panel derecho con el árbol en vivo de Nextcloud mostrando la estructura
    (20 AJ → CL-LI-1196 → 9 subcarpetas con conteo de archivos).
  - Tarjetas de integración: Nextcloud vía WebDAV, webhooks n8n
    (nc-tekon, nc-tekon-deep), sync de WhatsApp, role-based share URLs.
  Útil para la sección "Las fotos del terreno y tu carpeta, juntas".

04-arquitectura.png  (1400x820)
  Diagrama de arquitectura en 4 columnas:
  - Usuarios (administrador, visitante, ITO, cliente final).
  - Django portal (login multi-empresa, vista de sitios, mapa Leaflet,
    galería, API REST, caché Postgres).
  - n8n self-hosted (webhooks nc-tekon / nc-tekon-deep, node Nextcloud,
    auth, versionado en git).
  - Nextcloud (carpetas por empresa, Docs. Finales, sync WhatsApp, share
    URLs por rol).
  Abajo: flujo de datos en 7 pasos para cargar los archivos de un sitio,
  más badges con el stack tecnológico completo.
  Útil para la sección "Arquitectura" / "Cómo está armado".
