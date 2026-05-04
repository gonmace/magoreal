# Morph banner: incorporar o cambiar la fuente

Este documento describe el flujo oficial para regenerar los paths SVG del banner morfológico (`morph_banner`) a partir de un archivo `.otf` / `.ttf`.

## Qué problema resuelve

- El frontend usa **KUTE.js** para interpolar cada letra contra la siguiente (misma topología).
- Por eso **cada glifo lleva exactamente `TARGET_POINTS` (75) vértices** en `outer_path` y otro tanto en `counter_path` (`letter_paths.py`).
- Ciertos caracteres llevan forma de **contrahuella (keyhole)**: hueco real o fusión slit según configuración (`has_counter`).
- Ya existen ajustes de **métrica visual**: baseline de la **i**, descender + centrado horizontal de la **j**, alineación vertical de los keyholes de **0 O o B 8 m** respecto al centro de masa.

Sin el pipeline posterior, cambiar sólo los paths suele dar morphs deformes o centrados incorrectos.

## Artefactos clave

| Ruta | Rol |
|------|-----|
| `landing/landing/morph_banner/letter_paths.py` | Fuente de verdad Python: anchos y paths escalados (`LETTER_HEIGHT`, `SCALE_K`, etc.). La regeneración lo **sobrescribe**. |
| `landing/scripts/regenerate_all_paths.py` | Extrae contornos de la fuente (fonttools), remuestrea y escribe la constante `LETTER_PATHS`. |
| `landing/scripts/regen_and_keyhole.py` | Aplica slit/keyhole usando la fuente como referencia; normaliza puntos donde hace falta. |
| `landing/scripts/align_keyhole_y.py` | Corrige alineación Y de keyholes; reglas especiales **i** (altura-x) / **j** (descender). |
| `landing/scripts/center_glyph_x.py` | Centra horizontalmente un glifo dado (`j` por defecto en pipeline). |
| `landing/scripts/font_pipeline.py` | Orquestador: ejecuta todos los pasos en orden. |

Carpeta sugerida para archivos nuevos:

- `landing/landing/morph_banner/fonts/` (ver `README.md` en esa carpeta).

## Requisitos de la fuente

1. Licencia permite incrustación o uso Web según necesites en producción (legal, no técnico).
2. Tabla **`cmap`** con entradas ASCII para **`A`-`Z`, `a`-`z`, `0`-`9`** (los scripts esperan estos codepoints Unicode).
3. Contornos razonables: si algún dígito o letra no tiene geometría asignada, ese glifo puede fallar o quedar degenerado — conviene revisar en preview antes de dar por cerrado el cambio.

## Dependencias

```bash
pip install fonttools numpy
```

(El proyecto suele tener `numpy`; `fonttools` puede faltar si nunca ejecutaste estos scripts.)

## Procedimiento recomendado (un solo comando)

Trabajar siempre desde el directorio que contiene `manage.py` y la carpeta `scripts/` (**`landing/`** en este repo):

```bash
python scripts/font_pipeline.py --font "landing/morph_banner/fonts/MiFuente.otf"
```

Opcional:

```bash
python scripts/font_pipeline.py --font "ruta/a/fuente.ttf" --skip-center-j
```

### Modo sólo post-proceso (`--post-only`)

Úsalo **sólo** si ya tienes un `letter_paths.py` válido para la **misma** fuente (por ejemplo, lo extrajiste tú mismo con `regenerate_all_paths.py` y no quieres repetir ese paso) y solo necesitas re-aplicar keyhole/alineaciones:

```bash
python scripts/font_pipeline.py --post-only --font "landing/morph_banner/fonts/MiFuente.otf"
```

La fuente sigue siendo necesaria porque `regen_and_keyhole.py` usa el archivo como referencia de geometría.

## Equivalente Makefile

Si usás Git Bash desde `landing/`:

```bash
make morph-banner-font FONT="landing/morph_banner/fonts/MiFuente.otf"
make morph-banner-font-post FONT="landing/morph_banner/fonts/MiFuente.otf"
```

## Qué hace cada paso (orden)

1. **`regenerate_all_paths.py`**  
   Sobrescribe `letter_paths.py` con extracción de **todos** los sets A-Z, a-z, 0-9. Ajustables en el propio script: escala inicial, alto de letterbox, número de puntos.

2. **`regen_and_keyhole.py`**  
   Para glifos con contrahuella o estrategias especiales (**0**, **O**, **o**, **B**, **8**, **m**, **i**, **j** como conjunto habitual), fusiona borde exterior + contrahuella en paths compatibles con el morph sin self-intersection absurdas. Si agregás glifos con contrahuella “real” nueva, puede ser necesario ampliar la lista/objetivos en ese script tras entender cómo marca `has_counter` en `LETTER_PATHS`.

3. **`align_keyhole_y.py`**  
   Ajusta centrado vertical de los keyholes y aplica overrides de métricas para **i** y **j** que equilibran la animación sobre la línea base.

4. **`center_glyph_x.py j`**  
   Recoloca horizontalmente la **j** usando el avance típico como caja métrica. Si en otra fuente otro glifo necesita igual trato, ejecutá ese script pasando el caracter (`python scripts/center_glyph_x.py X`) e incorporalo al pipeline si debe ser estable.

## Verificación

1. Levantá el servidor de desarrollo (`make dev`).
2. Abrir la página de desarrollo **`/dev/letter-preview/`** (si está habilitada en `urls`; es la prevista para inspeccionar letras aisladas).
3. Mirar la home / bloque Morph banner con tu palabra de prueba configurada en el admin (**MorphBanner** u opción correspondiente).

Revisión visual: interpolaciones que “explotan”, cruces espurios o huecos invertidos (`fill-rule`), descender inconsistente ⇒ volver sobre el paso keyhole/alineaciones o aumentar muestras de puntos en extracción.

## Scripts opcionales (depuración, no rutina diaria)

En `landing/scripts/` pueden ser útiles de forma puntual:

- `inspect_ij.py`, `inspect_zero_glyph.py`, `count_points.py` — inspeccionar vértices o subpaths.
- `debug_bridges.py`, `zoom_slit.py` — trabajo fino slit/puentes antes de automatizar algo nuevo.
- `keyhole_holed_glyphs.py` — lógica reutilizada para algunos merges.
- `regenerate_letter_paths.py` — variante/antigua extracción; el flujo unificado debe preferir **`regenerate_all_paths.py` + pipeline**.

Si un script nuevo queda estable, documentalo aquí enlazándolo desde una PR.

## Troubleshooting rápido

| Síntoma | Qué revisar |
|--------|--------------|
| `UnicodeEncodeError` al imprimir en consola Windows | Usar UTF-8 en la terminal (`chcp 65001`) o ejecutar Makefile con `PYTHONIOENCODING=utf-8`; `font_pipeline.py` evita flechas Unicode en texto crítico. |
| Letra falta saliendo plana/degenerada | cmap / nombre de glyph / que no sea variable font sin tabla estática esperada por fonttools para ese subset. |
| Morph raro sólo entre dos letras puntual | Probable orden de vértices o topología slit; comparar punto a punto (`count_points`). |
| Nueva contrahuella (ej.: @) | Probable trabajo manual de diseño slit + aumentar objetivos del step keyhole antes de producir rutas estables para KUTE.

## Mantenimiento

Tras cualquier fusión importante de `letter_paths.py`, ejecutar siempre revisión preview + página real. Mantener **`TARGET_POINTS`** y factores (`SCALE_K`, `LETTER_HEIGHT`) coherentes entre regeneraciones para no desalinear el layout previo CSS que asume tamaños relacionados.

---

**Índice del repo:** comandos día a día siguen descritos en `AGENTS.md` (sección morph banner fonts).
