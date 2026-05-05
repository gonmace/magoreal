# Proyecto 3 — Plataforma de Chatbots WhatsApp con IA Multi-Agente y RAG

> **Tu empresa atendiendo por WhatsApp 24/7, con agentes de IA especializados que cotizan, consultan base de conocimiento, agendan servicios y derivan a humanos cuando hace falta — todo orquestado con n8n y controlado desde un dashboard web.**

---

## 1. Lo que ofrece esta plataforma

Es una **solución full-stack conversacional** que convierte WhatsApp en el canal operativo principal de la empresa. A diferencia de los chatbots "de árbol de decisión" que se rompen cuando el cliente escribe algo inesperado, esta plataforma usa un **sistema multi-agente con IA** que razona, consulta documentación interna (RAG), accede a datos reales del negocio y responde con el tono de la marca.

Se entrega **desplegable en infraestructura propia del cliente** (Docker Compose sobre VPS o nube privada), con **código propietario auditable**, sin depender de plataformas SaaS de chatbots con cobro por conversación.

### Rubros donde se implementa

- Servicios con cotización y agenda (agua, gas, fletes, técnicos, limpieza, fumigación)
- E-commerce y retail con consultas de producto, stock y estado de pedido
- Clínicas, consultorios y centros de salud con turnos y triage
- Inmobiliarias y desarrolladoras con calificación de leads
- Instituciones educativas con atención a alumnos y padres
- Atención al cliente para PyMEs que reciben decenas o cientos de consultas diarias por WhatsApp

### Problemas que resuelve

- Respuestas lentas o fuera de horario — el negocio pierde ventas mientras nadie atiende WhatsApp
- Equipos saturados contestando lo mismo una y otra vez (precios, ubicación, horarios, stock)
- Información dispersa en documentos, PDFs y planillas que el operador humano no encuentra rápido
- Cotizaciones manuales que demoran, con errores y sin trazabilidad
- Falta de registro y análisis de las conversaciones (qué preguntan, qué no saben responder los bots, dónde se pierden los leads)
- Plataformas SaaS de chatbots que cobran por usuario/conversación y no permiten lógica real

---

## 2. Capacidades de la plataforma

### 2.1 Orquestación multi-agente con IA

- **Router inteligente** que analiza cada mensaje y lo deriva al agente especializado adecuado
- **Agentes especializados por dominio** (cotizaciones, consultas, reclamos, agenda, producto, etc.)
- **Memoria conversacional persistente** por usuario — el bot "se acuerda" del contexto
- **Handoff a humano** automático cuando detecta urgencia, tono negativo o consultas fuera de scope
- **Salidas estructuradas (JSON Schema)** para que cada respuesta sea parseable y accionable
- Modelos mixtos: **GPT-5.1 para razonamiento complejo, GPT-4.1-mini para tareas rápidas** — óptimo costo/calidad

### 2.2 RAG (Retrieval Augmented Generation) con base de conocimiento propia

- **ChromaDB** como base vectorial local — sin salir de la infraestructura del cliente
- Ingesta de **PDFs, manuales, listas de precios, FAQs, políticas comerciales** del negocio
- Búsqueda semántica con **MMR (Maximum Marginal Relevance)** — trae resultados diversos y relevantes
- El bot cita la fuente interna cuando responde — trazabilidad completa
- Base actualizable sin redeploy: subís un documento, re-indexa y ya está disponible

### 2.3 Integración WhatsApp Business

- Recepción y envío de mensajes por **WhatsApp Business API oficial**
- Soporte de **texto, imágenes, ubicación, audio, documentos** y mensajes interactivos
- **Multi-número** — un solo backend puede atender varias líneas (agua, técnicos, ventas)
- Transcripción automática de audios entrantes con Whisper
- Envío programado y campañas saliente controladas

### 2.4 Dashboard de control (Django admin)

- **KPIs en vivo**: conversaciones activas, tasa de resolución automática, tiempo medio de respuesta
- **Vista de conversaciones** en tiempo real con filtros y buscador
- **Panel de auditoría** — cada mensaje queda registrado con el agente que respondió, el modelo usado, el tiempo y el costo
- **Métricas por agente** — cuál contesta más, cuál deriva más a humano, cuál falla más
- **Gestión de base de conocimiento** — subir y tagear documentos desde la web
- Exportación de conversaciones y métricas a CSV/Excel

### 2.5 Sistema de auditoría y mejora continua

- Workflow de auditoría independiente que **revisa conversaciones ya cerradas**
- Detecta patrones de fallo: preguntas sin responder, respuestas inconsistentes, loops
- Sugiere **nuevos documentos para RAG** o **nuevos agentes** para cubrir gaps
- Alimenta un proceso de mejora continua sin intervención manual

### 2.6 Integración con IDEs de IA vía MCP (Model Context Protocol)

- Servidor **n8n-MCP** incluido — permite que herramientas como **Cursor, Claude Code o Claude Desktop** conversen directamente con n8n
- El propio programador puede pedirle a una IA que **cree, modifique o deploye un workflow nuevo** hablándole en lenguaje natural
- Diferenciador técnico único: la plataforma **se extiende sola** con ayuda de IA

---

## 3. El motor: arquitectura multi-agente en detalle

El cerebro del sistema son **3 workflows de n8n interconectados** que suman **más de 217 nodos** orquestados:

### 01_Main — Punto de entrada y router

Recibe el webhook de WhatsApp, normaliza el mensaje, recupera el contexto del usuario, consulta si hay conversación activa y **deriva al router central**. El router usa un modelo LLM para clasificar la intención del mensaje (cotización, consulta, reclamo, agenda, saludo, etc.) y lanza el agente correspondiente.

### 02_Agentes — Los especialistas

Cada agente es una **subrutina independiente con su propio prompt, sus propias herramientas y su propio modelo**. Ejemplos típicos implementados:

| Agente | Función | Modelo | Herramientas |
|---|---|---|---|
| **Agente Cotizador** | Calcula precios consultando el sistema operativo (Proyecto 1) | GPT-5.1 | API backend, RAG precios, calculadora |
| **Agente Consultas** | Responde preguntas sobre productos/servicios/horarios | GPT-4.1-mini | RAG de base de conocimiento |
| **Agente Agenda** | Programa y reprograma servicios en calendario | GPT-5.1 | API calendario, RAG políticas |
| **Agente Reclamos** | Recibe, clasifica y escala reclamos a humano | GPT-4.1-mini | Creación de ticket, handoff |
| **Agente Fallback** | Maneja cualquier mensaje no clasificado y decide si derivar | GPT-4.1-mini | RAG general |
| **Agente Cierre** | Cierra la conversación con encuesta de satisfacción | GPT-4.1-mini | — |

Cada agente devuelve **JSON estructurado** que el workflow sabe procesar y convertir en respuesta de WhatsApp (texto, botones, ubicación, imagen).

### 03_Auditoria — El observador

Workflow que corre en segundo plano, **lee conversaciones cerradas** y las evalúa con un agente revisor. Genera reportes y marca casos donde el bot "no supo" — material directo para mejorar la base RAG y los prompts.

### Flujo completo de un mensaje

1. Cliente manda mensaje por WhatsApp
2. Webhook → 01_Main recibe y normaliza
3. Router clasifica intención con LLM
4. Se invoca al agente especializado (02_Agentes)
5. El agente consulta RAG, APIs internas, calculadoras
6. Devuelve respuesta estructurada
7. Se envía a WhatsApp y se guarda en base de datos
8. 03_Auditoria lo revisa después para mejora continua
9. Todo queda visible en el dashboard Django

---

## 4. Stack técnico

| Capa | Tecnologías |
|---|---|
| **Orquestación** | n8n (self-hosted) |
| **IA** | OpenAI GPT-5.1, GPT-4.1-mini, Whisper, embeddings text-embedding-3 |
| **RAG / Vectores** | ChromaDB |
| **Backend API** | FastAPI (Python) |
| **Dashboard** | Django + Django Admin |
| **Base de datos** | PostgreSQL |
| **Integración** | WhatsApp Business API oficial |
| **Infra** | Docker Compose, Nginx (reverse proxy), VPS Ubuntu o nube del cliente |
| **Frontend dashboard** | Tailwind CSS, daisyUI |
| **Extensibilidad IA** | Servidor n8n-MCP para conectar Cursor / Claude Code |

---

## 5. Beneficios concretos para el negocio

- **Reducción drástica en tiempo de respuesta**: de horas a segundos, 24/7
- **Descarga al equipo humano**: el bot resuelve el 60–80% de las consultas repetitivas
- **Más conversiones**: el cliente que pregunta y recibe respuesta al instante compra más
- **Trazabilidad total**: cada conversación queda registrada, auditable, exportable
- **Sin costos por usuario**: plataforma propia, no se paga por conversación ni por operador
- **Escalable**: el mismo backend atiende 10 o 10.000 conversaciones diarias
- **Aprende sola**: el sistema de auditoría marca lo que falta y permite mejorar sin desarrollo

---

## 6. Diferenciales frente a soluciones genéricas

- **Multi-agente real**, no bot de un solo prompt — cada especialista hace lo suyo mejor
- **RAG con base propia auditable** — no envía los documentos del cliente a terceros
- **100% on-premise / nube privada** — los datos de WhatsApp no salen de la infraestructura del cliente
- **Código propietario sin vendor lock-in** — si mañana cambia OpenAI por otro modelo, se hace; si cambia n8n por otro orquestador, también
- **Auditoría automática** — el sistema se mejora a sí mismo detectando sus huecos
- **Integración con IDEs de IA (MCP)** — extensión del sistema con ayuda de IA en segundos
- **Arquitectura modular** — cada agente se enchufa o desenchufa sin romper los demás
- **Adaptable a cualquier rubro** — el core es el mismo, cambian los prompts y la base RAG

---

## 7. Caso de referencia

**Pozos SCZ** — Santa Cruz de la Sierra, Bolivia.

La misma empresa del Proyecto 1 (plataforma de gestión operativa) incorporó este chatbot como **canal comercial y de atención** sobre WhatsApp. El bot cotiza servicios de cisterna consultando el motor de precios de la plataforma operativa, responde preguntas frecuentes sobre zonas de cobertura, agenda servicios y deriva a humano cuando el cliente pide algo fuera del standard. La integración entre ambos proyectos muestra la **capacidad de componer soluciones**: un mismo cliente, dos productos que se hablan entre sí.

---

## 8. Próximas capacidades en el roadmap

- Agente de **upsell** proactivo basado en histórico del cliente
- **Dashboards predictivos** — proyección de demanda por zona y día basados en conversaciones
- **Voicebot** — misma arquitectura, canal telefónico
- Integración con **CRMs populares** (HubSpot, Pipedrive) vía MCP
- Módulo de **campañas saliente** con personalización por IA

---

## 9. Material visual

En `/screenshots/` están los mockups del producto:

1. `01-whatsapp-chat-bot.png` — Vista del chat de WhatsApp con el bot atendiendo un caso real
2. `02-dashboard-django.png` — Dashboard de control con KPIs y conversaciones en vivo
3. `03-arquitectura-stack.png` — Diagrama técnico del stack completo
4. `04-multi-agente.png` — Vista del sistema multi-agente con el router y los especialistas

En `/n8n-workflows/` están los 3 workflows reales del sistema (exportables/importables a cualquier instancia de n8n):

- `01_Main.json` — Entrada y router
- `02_Agentes.json` — Agentes especializados
- `03_Auditoria.json` — Auditoría y mejora continua

---

## 10. Propuesta de valor en una línea

> **Deja de perder ventas por WhatsApp. Poné un equipo de agentes de IA especializados trabajando 24/7 sobre tu propio conocimiento, con código propio y sin mensualidades por conversación.**
