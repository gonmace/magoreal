# Plataforma de gestión operativa para servicios con logística de campo

> Sistema full-stack (backoffice web + app móvil) con **inteligencia geográfica** y **motor de precio multivariable** que convierte operaciones manuales en una operación medible, automática y escalable. Cotiza, programa, rutea y controla operadores en tiempo real — adaptado al rubro de cada cliente.

**Caso de referencia en producción:** *Pozos SCZ* — empresa de distribución de agua con cisternas en Santa Cruz de la Sierra (Bolivia). 500+ servicios históricos, 50+ clientes activos, múltiples bases de carga y flota gestionada.

---

## 🎯 A qué tipo de negocio le sirve

Cualquier empresa que **presta un servicio que implica moverse hasta el cliente** y que hoy gestiona con cuadernos, Excel y WhatsApp:

- **Distribución a domicilio** — agua, gas, combustible, alimentos, gastronomía, productos frescos.
- **Servicios técnicos en campo** — electricistas, plomeros, aire acondicionado, internet, cerrajería.
- **Fumigación, limpieza, jardinería, control de plagas**.
- **Fletes, mudanzas, courier, mensajería, last-mile**.
- **Construcción y obras** — asignación de cuadrillas por zona.
- **Servicios de salud a domicilio** — enfermería, kinesiología, laboratorio, extracciones.
- **Mantenimiento y posventa** — reparación de equipos con técnicos móviles.
- **Servicios municipales y públicos** — recolección, inspección, intervención en terreno.

Si tu empresa cotiza según distancia, tiene operadores en la calle y querés dejar de perder dinero y clientes por falta de control, esta plataforma se adapta a tu operación.

---

## 🚩 Problemas que resuelve

- **Cotizaciones inconsistentes** — el precio depende del ánimo de quien atiende, no de los costos reales ni de la zona.
- **Pérdida de clientes y oportunidades** — sin historial no se sabe quién quedó cotizado, quién reincide o quién hace cuánto que no compra.
- **Operación ciega** — el dueño no sabe dónde está cada operador, qué hizo en el día ni cuánto facturó.
- **Ruteo ineficiente y costos descontrolados** — combustible, horas y kilómetros que nadie mide.
- **Cero trazabilidad** — imposible tomar decisiones (qué zona es rentable, qué operador rinde, qué horario conviene).
- **Dependencia de personas clave** — si el dueño o el despachador no está, la empresa se frena.
- **Imposibilidad de escalar** — agregar un camión / técnico / zona nueva es una pesadilla porque todo vive en la cabeza de alguien.

---

## ✅ Capacidades de la plataforma

Solución **modular**: cada capacidad se activa o ajusta según el rubro del cliente.

### 1. Backoffice web (centro de operaciones)
Dashboard con mapa interactivo y panel de gestión.

- **Cartera de clientes georreferenciada** con clusters inteligentes (agrupa puntos cercanos con conteo).
- **Gestión de zonas con polígonos dibujables** y **factor de precio por zona** configurable.
- **Cotización instantánea** pegando un link de Google Maps o coordenadas.
- **Slider temporal** para analizar comportamiento histórico (años de data consultables).
- **Filtros por estado** del servicio: Cotizado, Programado, Ejecutado, Cancelado.
- **Visualización por precio / categoría** con leyenda de colores configurable.
- **Gestión multi-base** (depósitos, sucursales, puntos de partida).
- **Búsqueda de clientes** por nombre/teléfono con historial completo.
- **Asignación de servicios** a operadores con estado en tiempo real.
- **Solicitud de ubicación en vivo** al operador (sin llamarlo).
- **Capas base intercambiables** (mapa estándar o imagen satelital).

### 2. App móvil para operadores
Aplicación que reemplaza al WhatsApp de coordinación y al papel.

- **Tareas/servicios del día** ordenados con distancia y valor.
- **Acciones rápidas por servicio**: marcar terminado, abrir navegación, enviar WhatsApp pre-cargado al cliente.
- **Indicadores de estado** del operador: activo/inactivo, recursos (stock, combustible, tanque, batería del equipo).
- **Alertas por compromiso horario** (destaca servicios cuando se acerca la hora pactada).
- **Sincronización en tiempo real** con el backoffice: lo que marca el operador se ve al instante en el panel.
- **Modo offline tolerante** — sigue operando aunque el operador pierda señal, sincroniza cuando vuelve.

### 3. Motor de cálculo de precio (el diferencial)
*Equivalente al "motor de IA" de otros productos, pero aplicado a la economía real del servicio.*

El sistema no "adivina" un precio: lo calcula con una **hoja de costos real** y **compara todas las opciones disponibles** antes de sugerir el precio óptimo.

### 4. Inteligencia operativa (reportes y trazabilidad)
Todo lo que pasa queda registrado y se puede analizar.

- Historial completo de clientes, servicios, cotizaciones y ejecuciones.
- Pipeline comercial visible en el mapa (Cotizado → Programado → Ejecutado).
- Análisis por zona, por operador, por base, por rango de fecha.
- Base para dashboards gerenciales y reportes automáticos.

---

## 🧠 Motor de cálculo de precio — el corazón del sistema

Lo que hace potente a esta solución **no es tener un mapa bonito**: es la arquitectura de cálculo que convierte datos geográficos, costos variables y factores de negocio en un precio justificable frente al cliente final.

### Arquitectura del motor

Para cada pedido, el motor evalúa por separado **cada origen** (base / depósito / punto de partida) y **cada recurso** (operador, camión, técnico) disponible, y presenta una comparativa:

| Variable calculada | Qué hace |
|--------------------|----------|
| **Distancia real (km)** | Cálculo geoespacial desde cada base/recurso al cliente |
| **Tiempo estimado (min)** | Tiempo de viaje con factor de carga configurable (ej. ×1.05 cargado) |
| **Costo variable** | Combustible / insumos ida y retorno |
| **Utilidad** | Margen esperado por operación (editable por rubro) |
| **Mantenimiento** | Prorrateo de amortización de equipos |
| **Mano de obra** | Costo del operador/técnico asignado |
| **Precio final sugerido** | Por cada combinación base-recurso, con comparativa visible |

### Factores aplicados
- **Factor por zona** (ej. 1.00, 1.10, 1.20…) configurable por polígono dibujado en el mapa.
- **Factor de carga / dificultad** (cargado, horario pico, acceso complejo).
- **Utilidad de retorno** — aprovecha viajes de vuelta si aplica al rubro.
- **Costos fijos de operación** — arranque, tiempo muerto, tarifa mínima.

### Tres niveles de precio
El sistema distingue **Precio Sin Factor / Precio Cotizado / Precio Facturado** para analizar el margen real vs. teórico y detectar dónde se "pierde plata".

### Técnicas aplicadas
- **PostGIS** para cálculo geoespacial nativo (zonas con polígonos, distancias reales).
- **Clusters dinámicos** en el mapa para no saturar la UI con cientos de marcadores.
- **Motor de reglas** configurable por el propio dueño del negocio (no requiere programador para ajustar precios o factores).
- **Comparador de alternativas** — recomienda la opción más rentable para cada servicio, no solo "la más cercana".
- **Histórico auditable** — cada cotización y cada factura queda registrada con los valores que tenían los parámetros en ese momento.

**Por qué esto vende:**
- Cotizaciones **justificables con números** frente al cliente.
- Decisiones de asignación basadas en **rentabilidad real**, no en intuición.
- **Ajuste instantáneo** cuando cambia un costo (combustible, sueldos, insumos).
- Elimina **errores humanos** en el precio.
- El dueño deja de depender de un despachador experto: el sistema sabe más que cualquier empleado.

---

## 🧱 Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python + Django (full-stack) |
| Base de datos | PostgreSQL + **PostGIS** (geolocalización nativa) |
| Mapas web | Leaflet + OpenStreetMap + Esri World Imagery |
| Frontend admin | Django Templates + JavaScript + CSS moderno (modo oscuro) |
| App móvil | **Flutter** (Android / iOS multiplataforma, un solo código) |
| Geocodificación | Parsing de links de Google Maps y coordenadas |
| Mensajería | Integración **WhatsApp** (deep links) |
| Hosting | VPS propio (Ubuntu) o nube a elección del cliente |

**Ventajas del stack:**
- **Código propio** — no dependés de SaaS ajenos con mensualidades por usuario.
- **Mapas gratuitos** — OpenStreetMap sin costo por API (a diferencia de Google Maps).
- **Flutter** — una sola app sirve para Android y iOS.
- **PostGIS** — todo el cálculo geográfico a nivel de base de datos, veloz y estándar.
- **Escalable** — la misma arquitectura sirve para 10 clientes o para 10.000.

---

## 💡 Beneficios que vende (copy para la landing)

- ✅ **Cotizá en segundos, no en minutos.** Pegás un link y el sistema saca distancia, tiempo y costo real.
- ✅ **Nunca más pierdas un cotizado.** Pipeline visible en un mapa con todos los estados.
- ✅ **Que el precio lo decida tu hoja de costos, no tu estado de ánimo.** Motor configurable con variables reales.
- ✅ **Tus operadores en una app, no en un grupo de WhatsApp.** Tareas, navegación, estado y mensajes en un solo lugar.
- ✅ **Sabé siempre qué zona te rinde más.** Analizá por zona, operador, base y rango de fecha.
- ✅ **Dejá de depender de una sola persona.** El conocimiento queda en el sistema, no en la cabeza del despachador.
- ✅ **Crecé sin que explote la operación.** La misma plataforma escala a más clientes, operadores y bases.
- ✅ **Sin mensualidades por usuario.** Código propio, licencia única y adaptable.

---

## 🏆 Diferenciales

- **Código propio, sin SaaS de por medio** — no pagás mensualidades por usuario ni quedás atado a un proveedor.
- **100% adaptable al rubro** — el mismo core se reconfigura para agua, gas, técnicos, fletes o fumigación.
- **Motor de precio transparente y justificable** — cada Bs. del precio está explicado con números.
- **Funciona con mapas gratuitos (OpenStreetMap)** — cero costo de API.
- **Pensado para PyMEs de países en desarrollo** — datos limitados, equipos modestos, operadores con conectividad variable.
- **Modo oscuro y UX cuidada** — no es un sistema "de empresa aburrida", se siente moderno.
- **Extensible con IA** — la arquitectura está lista para sumar ruteo óptimo, predicción de demanda o sugerencia de zonas nuevas cuando el cliente lo pida.

---

## 📊 Caso en producción — Pozos SCZ

Aplicación real del sistema en una empresa de distribución de agua con cisternas en Santa Cruz de la Sierra.

- **Sector:** Distribución / servicios a domicilio.
- **Operación gestionada:** múltiples camiones, múltiples bases de carga, flota propia + tercerizada.
- **Volumen visible:** 50+ clientes activos, 500+ servicios históricos, 5+ años de data acumulada (2020 en adelante).
- **Rango de precio operado:** Bs. 300 a Bs. 1.000+, autocalculado por el motor para cada combinación camión/base.
- **Resultado:** pasaron de gestionar con WhatsApp y cuaderno a una operación con trazabilidad total, cotización automática y app para cada operador.

---

## 🖼️ Capturas incluidas (carpeta `screenshots/`)

1. `01-mapa-mobile-clientes-activos.png` — Vista mobile del mapa con panel de clientes activos.
2. `02-panel-clientes-activos.png` — Panel expandido de clientes con estados del pipeline.
3. `03-lista-clientes-historico.png` — Lista paginada con cientos de registros históricos y filtros.
4. `04-buscar-cliente.png` — Buscador avanzado con historial e importe del último servicio.
5. `05-mapa-admin-desktop.png` — Vista desktop del admin con bases, zonas y solicitud de ubicación.
6. `06-mapa-leyenda-precios.png` — Mapa con leyenda visual por rango de precio / categoría.
7. `07-app-operador-flutter.png` — App Flutter del operador con tareas del día, estado y recursos.
8. `08-motor-calculo-precio.png` — Motor de cálculo de precio con desglose completo por recurso y base.

---

## 📝 Pendientes para cerrar el caso

- [ ] Confirmar si el cliente (Pozos SCZ) autoriza publicar el nombre, o va como *"empresa de distribución"*.
- [ ] Fecha de puesta en producción y tiempo operando.
- [ ] Métricas duras del antes/después (tiempo de cotización, servicios/mes, margen).
- [ ] Testimonio corto del dueño (1-2 frases).
- [ ] Definir 2-3 rubros prioritarios para segmentar en la landing (ej. distribución, servicios técnicos, fletes).
