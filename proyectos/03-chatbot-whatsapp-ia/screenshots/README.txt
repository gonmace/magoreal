Mockups generados para el Proyecto 3 (Plataforma de chatbots WhatsApp con IA multi-agente y RAG).

Estos 4 PNG fueron creados programáticamente con PIL porque no había screenshots reales disponibles del producto en producción. Sirven como piezas visuales para la landing mientras se toman capturas del sistema real.

Archivos:

01-whatsapp-chat-bot.png  (460x900)
  Mockup del chat de WhatsApp mostrando al bot "Asistente con IA" atendiendo
  un caso de cotización de cisterna. Burbuja verde del cliente, burbuja blanca
  del bot, timestamps. Útil para la sección "así conversa el cliente".

02-dashboard-django.png  (1280x800)
  Dashboard web del backoffice Django con:
  - 4 tarjetas de KPIs (conversaciones activas, resueltas por IA, tiempo medio, derivaciones)
  - Lista de conversaciones en vivo con último mensaje
  - Barras de actividad por agente (cotizador, consultas, agenda, etc.)
  Útil para la sección "panel de control".

03-arquitectura-stack.png  (1400x820)
  Diagrama técnico del stack completo mostrando ~20 bloques agrupados
  en capas: canal (WhatsApp), orquestación (n8n), IA (OpenAI, Whisper),
  RAG (ChromaDB), backend (FastAPI + PostgreSQL), dashboard (Django) e
  infra (Docker, Nginx). Flechas indican flujo de datos.
  Útil para la sección "cómo funciona por dentro".

04-multi-agente.png  (1280x800)
  Vista del sistema multi-agente: Router central en el medio y 6 agentes
  especializados alrededor (Cotizador, Consultas, Agenda, Reclamos,
  Fallback, Cierre) con sus modelos y tools listados.
  Útil para la sección "equipo de agentes de IA".

Si en algún momento se obtienen capturas reales del producto en producción,
reemplazar los archivos manteniendo los mismos nombres para no romper la
landing.
