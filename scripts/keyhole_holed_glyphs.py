"""
Fusiona glifos con counter (hueco) en un único subpath tipo "keyhole" para que
tengan la misma topología que letras single-subpath (p, q, A, D, a, ...).

Idea: outer y counter se conectan por un slit invisible: el algoritmo busca el
par de puntos (uno del outer, uno del counter) más cercano y los usa como
"puente". El recorrido es:

    outer[0..bridge_outer]
    -> bridge a counter[bridge_counter]
    -> counter completo (vuelve a counter[bridge_counter])
    -> bridge de regreso a outer[bridge_outer]
    -> outer[bridge_outer..end]
    Z

Para múltiples counters (caso '8') se aplica iterativamente, insertando cada
counter en el segmento del outer más cercano. Los counters se ordenan por su
posición a lo largo del outer para que el recorrido sea monotónico.

Después de fusionar:
- has_counter = False
- counter_path = dummy degenerado (todos los puntos en el centro)
- total de puntos por letra ≈ 95 (igualando 'p', 'q', 'A', etc.)

Uso:
    python scripts/keyhole_holed_glyphs.py [--apply]

Sin --apply solo imprime resumen y guarda preview SVG en /tmp.
Con --apply reescribe las entradas de '0', 'O', 'o', 'B', '8' en
landing/morph_banner/letter_paths.py preservando el resto del archivo.
"""

import os
import re
import sys
import math

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LANDING_DIR = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(LANDING_DIR, 'landing'))

from morph_banner.letter_paths import LETTER_PATHS, LETTER_HEIGHT  # noqa: E402

LETTER_PATHS_FILE = os.path.join(
    LANDING_DIR, 'landing', 'morph_banner', 'letter_paths.py'
)
PREVIEW_FILE = os.path.join(LANDING_DIR, 'scripts', 'preview_keyhole.html')

TARGET_GLYPHS = ['0', 'O', 'o', 'B', '8', 'm']
TARGET_TOTAL_POINTS = 95  # paridad con 'p', 'q', 'A', etc.
DUMMY_COUNTER_POINTS = 20  # paridad con dummy counter de las otras letras


# ---------- Parsing helpers ----------

def parse_path(path_str):
    """Parse 'M x y L x y ... Z [M ... Z]' into list of subpaths.
    Each subpath is a list of (x, y) tuples (sin duplicar el primer punto al final)."""
    subpaths = []
    current = []
    pattern = re.compile(r'([MLZ])\s*(-?\d+(?:\.\d+)?)?\s*(-?\d+(?:\.\d+)?)?')
    for m in pattern.finditer(path_str):
        cmd = m.group(1)
        if cmd in ('M', 'L'):
            x = float(m.group(2))
            y = float(m.group(3))
            if cmd == 'M':
                if current:
                    subpaths.append(current)
                current = [(x, y)]
            else:
                current.append((x, y))
    if current:
        subpaths.append(current)
    return subpaths


def points_to_path(points):
    if not points:
        return ""
    parts = [f"M {points[0][0]:.3f} {points[0][1]:.3f}"]
    for x, y in points[1:]:
        parts.append(f"L {x:.3f} {y:.3f}")
    parts.append("Z")
    return " ".join(parts)


# ---------- Keyhole fusion ----------

def closest_pair_indices(outer, counter):
    """Return (i_outer, j_counter) with minimal squared distance."""
    best_d = math.inf
    bo, bc = 0, 0
    for i, op in enumerate(outer):
        for j, cp in enumerate(counter):
            dx = op[0] - cp[0]
            dy = op[1] - cp[1]
            d = dx * dx + dy * dy
            if d < best_d:
                best_d = d
                bo, bc = i, j
    return bo, bc, math.sqrt(best_d)


def fuse_keyhole_single(outer, counter):
    """Fusiona outer (n pts) + counter (m pts) → keyhole (n + m + 2 pts).

    Topología:
        outer[0..bo] → counter[bc..bc] (recorre counter completo, vuelve a bc)
                    → outer[bo] (slit OUT) → outer[bo..n-1] → cierre Z

    Los segmentos del slit son colineales y opuestos:
      - slit IN:  outer[bo] → counter[bc]
      - slit OUT: counter[bc] → outer[bo]

    Con `fill-rule=evenodd` se cancelan topológicamente (área 0).
    """
    bo, bc, _dist = closest_pair_indices(outer, counter)
    counter_ring = counter[bc:] + counter[:bc] + [counter[bc]]  # vuelve al bridge
    fused = (
        outer[:bo + 1]
        + counter_ring
        + [outer[bo]]
        + outer[bo + 1:]
    )
    return fused


def fuse_keyhole_multi(outer, counters):
    """Para 8: outer + N counters. Inserta cada counter en su punto más cercano.
    Los counters se ordenan por índice de bridge en el outer para mantener
    monotonicidad y evitar que los slits se crucen."""
    bridges = []
    for cnt in counters:
        bo, bc, _ = closest_pair_indices(outer, cnt)
        bridges.append({'outer_idx': bo, 'counter_idx': bc, 'counter': cnt})
    bridges.sort(key=lambda b: b['outer_idx'])

    fused = []
    last = 0
    for b in bridges:
        bo = b['outer_idx']
        bc = b['counter_idx']
        cnt = b['counter']
        fused.extend(outer[last:bo + 1])
        counter_ring = cnt[bc:] + cnt[:bc] + [cnt[bc]]
        fused.extend(counter_ring)
        fused.append(outer[bo])
        last = bo + 1
    fused.extend(outer[last:])
    return fused


# ---------- Dummy counter ----------

def dummy_counter_path(width, num_points=DUMMY_COUNTER_POINTS, y_center=None):
    """Dummy con todos los puntos colapsados en el centro del glifo."""
    cx = width / 2.0
    cy = LETTER_HEIGHT / 2.0 if y_center is None else y_center
    pts = [(cx, cy)] * num_points
    return points_to_path(pts)


# ---------- Resampling (uniforme por longitud) ----------

def path_length(points):
    total = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        dy = points[i][1] - points[i - 1][1]
        total += math.hypot(dx, dy)
    # cierre
    dx = points[0][0] - points[-1][0]
    dy = points[0][1] - points[-1][1]
    total += math.hypot(dx, dy)
    return total


def resample_uniform(points, target_n, preserve_indices=()):
    """Resamplea por longitud uniforme. Preserva los puntos en `preserve_indices`
    (índices del array original) — útil para conservar los puntos del slit."""
    if target_n <= len(preserve_indices):
        return [points[i] for i in preserve_indices]

    # Construir lista cerrada con sus longitudes acumuladas
    n = len(points)
    cum = [0.0]
    for i in range(1, n + 1):
        a = points[i - 1]
        b = points[i % n]
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = cum[-1]
    if total <= 1e-9:
        return list(points)

    # Distancias arc-length de los puntos a preservar
    preserve_arcs = sorted(cum[i] for i in preserve_indices)
    # Distribuir el resto uniformemente entre cada par consecutivo de preservados
    free = target_n - len(preserve_indices)
    arcs = list(preserve_arcs)
    if preserve_arcs:
        # tratar como ciclo: [p0, p1, ..., pk-1, p0+total]
        wrapped = preserve_arcs + [preserve_arcs[0] + total]
        gaps = [(wrapped[i + 1] - wrapped[i]) for i in range(len(preserve_arcs))]
        gap_total = sum(gaps)
        # asignar puntos a cada gap proporcionalmente
        per_gap = [max(0, round(free * g / gap_total)) for g in gaps]
        # ajuste por redondeo
        diff = free - sum(per_gap)
        for i in sorted(range(len(per_gap)), key=lambda x: -gaps[x]):
            if diff == 0:
                break
            if diff > 0:
                per_gap[i] += 1
                diff -= 1
            else:
                if per_gap[i] > 0:
                    per_gap[i] -= 1
                    diff += 1
        for i, pg in enumerate(per_gap):
            a0 = wrapped[i]
            a1 = wrapped[i + 1]
            for k in range(1, pg + 1):
                arcs.append(a0 + (a1 - a0) * k / (pg + 1))
    else:
        for k in range(target_n):
            arcs.append(total * k / target_n)

    arcs = sorted(a % total for a in arcs)

    # Sample at each arc length
    out = []
    j = 0
    for a in arcs:
        while j < n and cum[j + 1] < a:
            j += 1
        if j >= n:
            j = n - 1
        seg_len = cum[j + 1] - cum[j]
        if seg_len <= 1e-9:
            out.append(points[j % n])
        else:
            t = (a - cum[j]) / seg_len
            p0 = points[j % n]
            p1 = points[(j + 1) % n]
            out.append((p0[0] + t * (p1[0] - p0[0]),
                        p0[1] + t * (p1[1] - p0[1])))
    return out


# ---------- Build keyhole entries ----------

def build_keyhole_entry(char):
    data = LETTER_PATHS[char]
    outer_subs = parse_path(data['outer_path'])
    counter_subs = parse_path(data['counter_path'])

    if len(outer_subs) != 1:
        raise ValueError(f"{char}: outer_path tiene {len(outer_subs)} subpaths, esperaba 1")
    outer = outer_subs[0]

    if len(counter_subs) == 1:
        fused = fuse_keyhole_single(outer, counter_subs[0])
    elif len(counter_subs) == 2:
        fused = fuse_keyhole_multi(outer, counter_subs)
    else:
        raise ValueError(f"{char}: counter_path tiene {len(counter_subs)} subpaths, soporto 1 o 2")

    new_outer_path = points_to_path(fused)
    new_counter_path = dummy_counter_path(data['width'], DUMMY_COUNTER_POINTS)

    return {
        'width': data['width'],
        'outer_path': new_outer_path,
        'counter_path': new_counter_path,
        'has_counter': False,
        'fused_count': len(fused),
        'dummy_count': DUMMY_COUNTER_POINTS,
        'old_outer_count': len(outer),
        'old_counter_count': sum(len(s) for s in counter_subs),
    }


# ---------- Preview ----------

def render_preview_html(entries):
    """Genera un HTML que muestra glifo viejo vs glifo keyhole lado a lado."""
    rows = []
    for char, new in entries.items():
        old = LETTER_PATHS[char]
        old_compound = old['outer_path'] + ' ' + old['counter_path']
        new_compound = new['outer_path'] + ' ' + new['counter_path']
        w = max(old['width'], new['width']) + 4
        h = LETTER_HEIGHT + 4
        rows.append(f'''
<div class="row">
  <div class="label">{char}</div>
  <div class="cell">
    <div class="caption">Original evenodd ({new["old_outer_count"]}+{new["old_counter_count"]}={new["old_outer_count"]+new["old_counter_count"]} pts)</div>
    <svg viewBox="-2 -2 {w} {h}" width="200" height="300" xmlns="http://www.w3.org/2000/svg">
      <path d="{old_compound}" fill="black" fill-rule="evenodd"/>
    </svg>
  </div>
  <div class="cell">
    <div class="caption">Keyhole evenodd ({new["fused_count"]}+{new["dummy_count"]}={new["fused_count"]+new["dummy_count"]} pts)</div>
    <svg viewBox="-2 -2 {w} {h}" width="200" height="300" xmlns="http://www.w3.org/2000/svg">
      <path d="{new_compound}" fill="black" fill-rule="evenodd"/>
    </svg>
  </div>
  <div class="cell">
    <div class="caption">Keyhole nonzero (debug)</div>
    <svg viewBox="-2 -2 {w} {h}" width="200" height="300" xmlns="http://www.w3.org/2000/svg">
      <path d="{new["outer_path"]}" fill="black" fill-rule="nonzero"/>
    </svg>
  </div>
  <div class="cell">
    <div class="caption">Keyhole + stroke 1 (simula morph activo)</div>
    <svg viewBox="-2 -2 {w} {h}" width="200" height="300" xmlns="http://www.w3.org/2000/svg">
      <path d="{new["outer_path"]}" fill="black" fill-rule="evenodd"
            stroke="black" stroke-width="1" stroke-linejoin="round" stroke-linecap="round"/>
    </svg>
  </div>
  <div class="cell">
    <div class="caption">Keyhole + stroke 0.1</div>
    <svg viewBox="-2 -2 {w} {h}" width="200" height="300" xmlns="http://www.w3.org/2000/svg">
      <path d="{new["outer_path"]}" fill="black" fill-rule="evenodd"
            stroke="black" stroke-width="0.1" stroke-linejoin="round" stroke-linecap="round"/>
    </svg>
  </div>
</div>''')

    html = f'''<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Keyhole preview</title>
<style>
body{{background:#f4f4f4;font-family:system-ui;padding:20px;}}
.row{{display:flex;gap:14px;align-items:center;margin-bottom:24px;background:#fff;padding:14px;border-radius:8px;}}
.label{{font-size:48px;font-weight:bold;width:60px;text-align:center;}}
.cell{{display:flex;flex-direction:column;align-items:center;}}
.caption{{font-size:12px;color:#666;margin-bottom:4px;}}
svg{{background:#fff;border:1px solid #ddd;}}
</style></head><body>
<h1>Keyhole conversion preview</h1>
{"".join(rows)}
</body></html>
'''
    with open(PREVIEW_FILE, 'w', encoding='utf-8') as f:
        f.write(html)


# ---------- Patch letter_paths.py ----------

def _build_entry_pattern(char):
    """Construye la regex que matchea una entrada completa de LETTER_PATHS por carácter."""
    char_re = re.escape(char)
    return re.compile(
        r"(    '" + char_re + r"': \{\n"
        r"        'width': )[^,]+(,\n"
        r"        'outer_path': \")[^\"]+(\",\n"
        r"        'counter_path': \")[^\"]+(\",\n"
        r"        'has_counter': )(?:True|False)(,\n"
        r"    \},\n)"
    )


def patch_letter_paths(entries):
    with open(LETTER_PATHS_FILE, 'r', encoding='utf-8') as f:
        src = f.read()

    for char, e in entries.items():
        pattern = _build_entry_pattern(char)
        repl = (
            r"\g<1>" + f"{e['width']}"
            + r"\g<2>" + e['outer_path']
            + r"\g<3>" + e['counter_path']
            + r"\g<4>" + "False"
            + r"\g<5>"
        )
        new_src, n = pattern.subn(repl, src, count=1)
        if n != 1:
            raise RuntimeError(f"No se pudo localizar la entrada '{char}' en letter_paths.py")
        src = new_src

    with open(LETTER_PATHS_FILE, 'w', encoding='utf-8') as f:
        f.write(src)


# ---------- Main ----------

def main():
    apply = '--apply' in sys.argv
    entries = {}
    print("Computing keyhole fusion for: " + ", ".join(TARGET_GLYPHS))
    print()
    for ch in TARGET_GLYPHS:
        e = build_keyhole_entry(ch)
        entries[ch] = e
        old_total = e['old_outer_count'] + e['old_counter_count']
        new_total = e['fused_count'] + e['dummy_count']
        print(f"  {ch}: old={old_total} pts (outer={e['old_outer_count']}, counter={e['old_counter_count']}) "
              f"-> new={new_total} pts (fused={e['fused_count']}, dummy={e['dummy_count']})")

    print()
    render_preview_html(entries)
    print(f"Preview generado en: {PREVIEW_FILE}")
    print(f"  ábrelo en el navegador para validar visualmente.")

    if apply:
        patch_letter_paths(entries)
        print()
        print(f"OK: letter_paths.py actualizado con {len(entries)} entradas keyhole.")
    else:
        print()
        print("Sin --apply: no se modificó letter_paths.py.")
        print("Revisa el preview y vuelve a ejecutar con --apply para confirmar.")


if __name__ == '__main__':
    main()
