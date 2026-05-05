# Generador de documentos técnicos con IA + validación humana

> Plataforma web que genera documentación técnica, normativa y contractual en minutos — no en días. Usa modelos de lenguaje de última generación (GPT-5.1) orquestados con validación humana en cada paso, para entregar documentos completos, coherentes y alineados al estándar de la empresa.

**Caso de referencia en producción:** Módulo **GDAR** para **EMBOL S.A.** — embotelladora de Coca-Cola en Bolivia. Genera especificaciones técnicas para licitaciones y procesos de compra de obras civiles, infraestructura y servicios.

---

## 🎯 A qué tipo de negocio le sirve

Cualquier empresa u organización que **produce documentos técnicos, normativos o contractuales de forma repetitiva**, con requisitos de calidad y trazabilidad:

- **Áreas de compras / procurement** — especificaciones técnicas para licitaciones, TDR, pliegos.
- **Constructoras e ingenierías** — especificaciones de obras, memorias de cálculo, protocolos.
- **Estudios jurídicos y legales** — contratos, acuerdos, cláusulas estandarizadas.
- **Industria farmacéutica y salud** — protocolos, POE (procedimientos operativos estándar), fichas técnicas.
- **Consultoras y auditoras** — informes, reportes de cumplimiento, papeles de trabajo.
- **Educación y formación** — materiales didácticos estructurados por norma curricular.
- **Gobierno y compliance** — actas, resoluciones, documentación regulatoria.
- **Industria y mantenimiento** — fichas de equipo, procedimientos de seguridad, manuales.

Si tu equipo redacta los mismos tipos de documento una y otra vez, con estructura similar pero contenido técnico distinto, esta plataforma multiplica su capacidad sin perder calidad.

---

## 🚩 Problemas que resuelve

- **Tiempo improductivo** — un especialista invierte horas o días escribiendo lo que un modelo puede redactar en minutos.
- **Inconsistencia entre documentos** — cada redactor usa su propio criterio, no hay estándar.
- **Conocimiento disperso** — normas, tolerancias, valores recomendados viven en la cabeza de pocos expertos.
- **Errores y omisiones** — se olvida una norma aplicable, un parámetro crítico o una actividad complementaria.
- **Cuello de botella en áreas clave** — compras, legales, técnica no dan abasto y frenan licitaciones, contratos y proyectos.
- **Documentación pobre en PyMEs** — no pueden contratar redactores técnicos dedicados y pierden oportunidades por no tener pliegos profesionales.

---

## ✅ Capacidades de la plataforma

### 1. Wizard guiado paso a paso (human-in-the-loop)
La IA propone, el humano valida. El usuario nunca parte de una hoja en blanco, pero siempre tiene el control final.

Estructura típica (7 pasos, configurable por tipo de documento):

1. **Datos iniciales** — título, unidad, categoría, descripción breve.
2. **Validación de coherencia** — un agente de IA verifica que el título y la descripción sean consistentes antes de continuar (evita documentos incoherentes).
3. **Parámetros técnicos** — la IA propone valores recomendados con su unidad y justificación; el usuario elige cuáles incluir.
4. **Normativa aplicable** — el sistema sugiere estándares relevantes (ej. normas locales, ACI, ASTM, ISO) y explica por qué aplican.
5. **Criterios de calidad / aceptación** — tolerancias y métricas con descripción del método de verificación.
6. **Ajuste de título por IA** — propone un nombre técnico/formal final, editable.
7. **Actividades o elementos complementarios** — la IA identifica lo que suele acompañar al ítem principal (ej. base granular, geotextil, juntas en un pavimento).

### 2. Generación del documento final
Con los parámetros seleccionados, la plataforma redacta el documento completo con estructura profesional:

- **Descripción** del alcance y contexto.
- **Materiales, equipos, herramientas y EPP**.
- **Procedimiento** paso a paso.
- **Medición y forma de pago** (para licitaciones).
- **Normativa aplicable** y **criterios de calidad** embebidos en el texto.

Todo en un lenguaje técnico profesional, listo para ser parte de un pliego, contrato o manual oficial.

### 3. Personalización por organización
La misma plataforma se adapta a la realidad de cada cliente:

- **Branding propio** (logo, colores, encabezados).
- **Catálogo de normas y estándares** específicos del rubro / país.
- **Vocabulario y estilo** propio de la empresa.
- **Plantillas** de documento final exportables a Word / PDF.
- **Aprobaciones y flujos** (borrador → revisado → aprobado) si se requiere.

### 4. Trazabilidad y gobernanza
- Historial de documentos generados, con versiones.
- Registro de qué usuario validó qué parámetro.
- Auditoría de cambios sobre las sugerencias de la IA.
- Base para analítica (qué parámetros se aceptan/rechazan, qué normas se usan más).

---

## 🧠 Inteligencia Artificial — el corazón del sistema

Lo que hace potente a esta solución **no es "meterle ChatGPT"**: es diseñar una **orquestación** donde cada paso tiene un agente especializado, con su propio prompt, su esquema de salida estructurado y sus validaciones.

### Arquitectura de agentes IA

| Paso | Agente / Modelo | Rol |
|------|-----------------|-----|
| Coherencia | GPT-5-mini | Verifica consistencia entre título y descripción antes de gastar más tokens |
| Clasificación técnica | GPT-5.1 | Identifica sistema constructivo / tipo de elemento / material / proceso |
| Parámetros | GPT-4.1-mini / GPT-5.1 | Genera parámetros con valores recomendados y justificaciones |
| Normas | GPT-5.1 | Selecciona normas aplicables según la clasificación técnica |
| Calidad | GPT-5.1 | Define tolerancias y métodos de verificación |
| Título final | GPT-5.1 | Reformula el nombre con estándar técnico |
| Actividades adicionales | GPT-5.1 | Descubre complementos relacionados con el ítem |
| Documento final | GPT-5.1 | Redacta el documento completo en prosa profesional |

### Técnicas aplicadas
- **Output estructurado (JSON Schema)** — cada agente devuelve datos tipados, no texto libre.
- **Prompt engineering por rol** — cada agente tiene su propio system prompt y su conjunto de ejemplos.
- **Validación en cadena (pipeline)** — si un paso falla la validación, no avanza al siguiente.
- **Human-in-the-loop** — el usuario valida cada paso antes de gastar tokens del siguiente.
- **Retries con backoff** — tolerancia a fallos transitorios de la API de modelos.
- **Modelos mixtos** — se usan modelos más livianos (mini) para tareas simples y modelos top para razonamiento complejo. Esto optimiza costo sin perder calidad.

---

## 🧱 Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | Framework web moderno (wizard paso a paso, modo oscuro configurable, branding del cliente) |
| Orquestación IA | **n8n** (workflows de agentes, webhooks, retries) |
| Modelos LLM | **OpenAI GPT-5.1** (razonamiento complejo) + **GPT-4.1-mini / GPT-5-mini** (tareas livianas) |
| Output estructurado | JSON Schema + Structured Output Parsers |
| Backend de datos | API + base relacional para historial, usuarios, plantillas |
| Exportación | Word / PDF con formato corporativo |
| Hosting | Nube o on-premise (el cliente elige) |

**Ventajas del stack:**
- **n8n** permite modificar flujos de IA sin redeploy — el equipo del cliente puede ajustar prompts.
- **Mezcla de modelos** según complejidad → costo optimizado.
- **Output tipado** → integración limpia con el frontend y bases de datos.
- **Webhooks** → cada paso es un endpoint REST auditable.

---

## 💡 Beneficios que vende (copy para la landing)

- ✅ **De días a minutos.** Un documento técnico completo generado y validado en una sola sesión.
- ✅ **El conocimiento queda en el sistema.** No se pierde cuando un especialista se va.
- ✅ **Estándar único en toda la empresa.** Mismo formato, mismo nivel de detalle, siempre.
- ✅ **IA que propone, humano que decide.** Nunca entregás algo sin que un experto lo revise.
- ✅ **Adaptado a tu rubro y tu normativa.** No es un ChatGPT genérico, es tu plantilla de negocio.
- ✅ **Auditable y trazable.** Historial completo para compliance e ISO.
- ✅ **Costo controlado.** Modelos livianos para tareas simples, top para las críticas.
- ✅ **Exporta lo que necesites.** Word, PDF, plantilla corporativa lista para firmar.

---

## 📊 Caso en producción — EMBOL S.A. (GDAR)

Módulo implementado para la **embotelladora de Coca-Cola en Bolivia**, específicamente para el área que gestiona licitaciones y compras de obras civiles e infraestructura.

- **Sector:** Industria / Compras y contrataciones.
- **Uso:** Redacción de especificaciones técnicas para licitaciones de obras (pavimentos, edificaciones, instalaciones, etc.).
- **Ejemplo de documento generado:** Especificación completa para "Pavimento hormigón armado doble parrilla e=10 cm" — con descripción, materiales, equipos, procedimiento, normas (NB 623, NB 611, NB 688, ACI 360R, ASTM C39) y medición/pago.
- **Resultado:** el área de OOCC deja de redactar desde cero y pasa a validar/ajustar documentos generados. El tiempo de elaboración cae drásticamente y el estándar queda unificado.

---

## 🖼️ Capturas incluidas (carpeta `screenshots/`)

1. `01-datos-iniciales.png` — Paso 1: captura de datos iniciales (actividad, unidad, tipo de servicio, descripción).
2. `02-parametros-materiales.png` — Paso 2: parámetros de materiales sugeridos por IA con valores y unidades.
3. `03-parametros-ejecucion.png` — Paso 3: parámetros de ejecución (tolerancias, tiempos, dimensiones).
4. `04-normas-aplicables.png` — Paso 4: normas sugeridas (NB, ACI, ASTM) con justificación.
5. `05-criterios-calidad.png` — Paso 5: criterios de calidad con tolerancias.
6. `06-ajustar-titulo.png` — Paso 6: ajuste de título con sugerencia de IA.
7. `07-actividades-adicionales.png` — Paso 7: actividades complementarias propuestas.
8. `08-documento-final.png` — Documento técnico completo generado.

## 📂 Workflows n8n incluidos (carpeta `n8n-workflows/`)

- `EspTec_01coherencia.json` — validación de coherencia + clasificación técnica.
- `EspTec_02-04parametros.json` — generación de parámetros (materiales, ejecución, normas, calidad).
- `EspTec_05ajustar_titulo.json` — sugerencia de título final.
- `EspTec_06adicionales.json` — actividades adicionales.
- `EspTec_07final.json` — redacción del documento final.

---

## 📝 Pendientes para cerrar el caso

- [ ] Confirmar si EMBOL autoriza citar el nombre o va como "embotelladora líder en Bolivia".
- [ ] Fecha de puesta en producción y tiempo de uso.
- [ ] Métricas de antes/después (tiempo de redacción, cantidad de especificaciones generadas, ahorro en horas-persona).
- [ ] Testimonio del responsable del área de OOCC o compras.
- [ ] ¿Cuántos tipos de documento distintos se pueden generar hoy con la plataforma?
