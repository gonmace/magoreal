Mockups generados para el Proyecto 4 (Plataforma de gestión de jornadas y supervisión operativa de equipos).

Los 4 PNG fueron creados programáticamente con PIL, porque el producto real está en producción bajo NDA y no podemos usar capturas identificables del cliente. En los mockups se usa "OperaLog" como nombre comercial neutro / placeholder — no es el nombre real del producto ni del cliente.

Archivos:

01-dashboard-ejecutivo.png  (1400x860)
  Dashboard ejecutivo con:
  - Sidebar de navegación
  - 4 KPIs en cabecera (empleados activos, jornadas en curso, sin agente, auto-cerradas)
  - Tabla de empleados en tiempo real con 10 filas de ejemplo:
    · Mezcla de empleados online (desktop) y móviles (mobile)
    · Columnas: Empleado, Agente, Jornada, Inicio, Inactividad, Ubicación, Capturas, Acciones
    · Botones "Captura YA" y "Ver GPS" según el tipo
  Útil para la sección "Así ve el supervisor a su equipo".

02-calendario-empleado.png  (1280x940)
  Dashboard personal del empleado con:
  - 3 tarjetas superiores: estado del agente, jornada en curso, total de la semana
  - Calendario mensual (abril 2026) con:
    · Días completos en verde con horas trabajadas
    · Día auto-cerrado en amarillo con alerta
    · Día en curso en celeste
    · Vacaciones en violeta
    · Feriado en amarillo con franja distintiva
  - Leyenda al pie
  Útil para la sección "Así ve el empleado su jornada".

03-app-movil-gps.png  (460x900)
  Vista mobile de la SPA con:
  - Header de la app
  - Card "Tu jornada" con estado "En curso" y timer
  - Card "Ubicación" con mini-mapa y pin GPS
  - Card "Actividad del día" con 4 items
  - Botón grande "Finalizar jornada" con aclaración "requiere GPS activo"
  - Nav inferior (Hoy / Historial / Perfil)
  Útil para la sección "Para el equipo de campo, el celular alcanza".

04-arquitectura.png  (1400x860)
  Diagrama técnico completo del producto en 3 filas:
  - Fila 1 (clientes): Agente desktop, App móvil, Dashboard ejecutivo, Dashboard empleado
  - Fila 2 (backend): Django + DRF, Django Channels, Servicios de IA (roadmap), Almacenamiento de capturas
  - Fila 3 (infra): PostgreSQL, Redis, n8n, Infra/seguridad
  Cada box tiene su lista de capacidades y tag de categoría.
  Útil para la sección "Cómo funciona por dentro".

Si en algún momento se obtienen screenshots reales usables (con datos anonimizados o
bajo autorización del cliente), reemplazar los archivos manteniendo los mismos nombres
para no romper la landing.
