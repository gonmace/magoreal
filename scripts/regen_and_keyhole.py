"""
Regenera los glifos huecos (0, O, o, B, 8, m) directamente desde la fuente OTF
y los convierte a keyhole path, reemplazando las entradas en letter_paths.py.

Usa los mismos parámetros que regenerate_all_paths.py (SCALE_K, TARGET_POINTS,
LETTER_HEIGHT global del módulo).

Uso: python scripts/regen_and_keyhole.py [--dry-run] [--font RUTA.otf]

La ruta debe ser la misma fuente OTF/TTF usada para generar letter_paths.py
(salida de regenerate_all_paths / font_pipeline).
"""
import argparse
import os
import re
import sys
import math

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LANDING_DIR = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(LANDING_DIR, 'landing'))
sys.path.insert(0, THIS_DIR)

from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
import numpy as np

from morph_banner.letter_paths import LETTER_HEIGHT, SCALE_K  # preservar escala global

DEFAULT_FONT_PATH = os.path.join(LANDING_DIR, 'landing', 'morph_banner', 'Quadrillion Sb.otf')
LETTER_PATHS_FILE = os.path.join(LANDING_DIR, 'landing', 'morph_banner', 'letter_paths.py')

TARGET_POINTS = 75          # igual que el módulo original
DUMMY_COUNTER_POINTS = 20   # igual que las otras letras

# Glifos a procesar.
#  - Con counter real (hueco interior):   '0', 'O', 'o', 'B', '8', 'm'
#  - Con dos subpaths disjuntos (cuerpo+punto, sin hueco real): 'i', 'j'
# La técnica de slit funciona en ambos casos: une los subpaths con un
# slit ida-y-vuelta que evenodd cancela. Visualmente queda 1 solo path.
TARGET_GLYPHS = ['0', 'O', 'o', 'B', '8', 'm', 'i', 'j']


# ──────────────────────────── Font extraction ────────────────────────────

class PointPen(BasePen):
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.commands = []
    def _moveTo(self, pt): self.commands.append(('M', pt))
    def _lineTo(self, pt): self.commands.append(('L', pt))
    def _curveToOne(self, pt1, pt2, pt3): self.commands.append(('C', pt1, pt2, pt3))
    def _closePath(self): self.commands.append(('Z',))
    def _endPath(self): pass


def interpolate_cubic(p0, p1, p2, p3, n):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        pts.append((
            u**3*p0[0] + 3*u**2*t*p1[0] + 3*u*t**2*p2[0] + t**3*p3[0],
            u**3*p0[1] + 3*u**2*t*p1[1] + 3*u*t**2*p2[1] + t**3*p3[1],
        ))
    return pts


def split_subpaths(commands):
    subs, cur = [], []
    for cmd in commands:
        if cmd[0] == 'M':
            if cur: subs.append(cur)
            cur = [cmd]
        else:
            cur.append(cmd)
    if cur: subs.append(cur)
    return subs


def resample_subpath(commands, target_n):
    pts, cur, start = [], (0, 0), None
    for cmd in commands:
        if cmd[0] == 'M':
            cur = cmd[1]; start = cur; pts.append(cur)
        elif cmd[0] == 'L':
            cur = cmd[1]; pts.append(cur)
        elif cmd[0] == 'C':
            p0 = cur; p1, p2, p3 = cmd[1], cmd[2], cmd[3]
            samp = max(10, target_n // max(len(commands), 1))
            pts.extend(interpolate_cubic(p0, p1, p2, p3, samp)[1:])
            cur = p3
        elif cmd[0] == 'Z':
            if start and pts and pts[-1] != start:
                pts.append(start)
    if len(pts) < 2: return pts
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + math.hypot(pts[i][0]-pts[i-1][0], pts[i][1]-pts[i-1][1]))
    total = cum[-1]
    if total == 0: return pts[:target_n]
    out = []
    for i in range(target_n):
        tgt = i / (target_n - 1) * total
        for j in range(1, len(cum)):
            if cum[j] >= tgt:
                if cum[j] == cum[j-1]: out.append(pts[j-1])
                else:
                    t2 = (tgt - cum[j-1]) / (cum[j] - cum[j-1])
                    out.append((pts[j-1][0] + t2*(pts[j][0]-pts[j-1][0]),
                                pts[j-1][1] + t2*(pts[j][1]-pts[j-1][1])))
                break
    return out


def extract_glyph_subpaths(glyph_set, cmap, char, target_n):
    """Returns list of subpath point-lists (scaled) for given char."""
    gname = cmap[ord(char)]
    pen = PointPen(glyph_set)
    glyph_set[gname].draw(pen)
    subs = split_subpaths(pen.commands)
    # Proporcional al arco
    sub_lens = []
    for s in subs:
        raw = resample_subpath(s, 20)
        l = sum(math.hypot(raw[i][0]-raw[i-1][0], raw[i][1]-raw[i-1][1]) for i in range(1, len(raw)))
        sub_lens.append(max(l, 1.0))
    total_l = sum(sub_lens)
    pts_per = [max(10, round(target_n * l / total_l)) for l in sub_lens]
    # ajuste
    diff = target_n - sum(pts_per)
    for idx in sorted(range(len(pts_per)), key=lambda x: -sub_lens[x]):
        if diff == 0: break
        pts_per[idx] += diff; diff = 0
    result = []
    for sub, n in zip(subs, pts_per):
        raw = resample_subpath(sub, n)
        scaled = [(x * SCALE_K, y * SCALE_K) for x, y in raw]
        result.append(scaled)
    return result


# ──────────────────────────── Glyph → outer/counter identification ────────────────────────────

def bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def area_approx(pts):
    xmin, xmax, ymin, ymax = bbox(pts)
    return (xmax - xmin) * (ymax - ymin)


def identify_subpaths(subpaths):
    """Returns (outer_idx, counter_indices) sorted by area descending."""
    areas = [(i, area_approx(s)) for i, s in enumerate(subpaths)]
    areas.sort(key=lambda x: -x[1])
    outer_idx = areas[0][0]
    counter_idxs = [i for i, _ in areas[1:]]
    return outer_idx, counter_idxs


# ──────────────────────────── Keyhole fusion ────────────────────────────

def closest_pair(outer, counter):
    best, bo, bc = math.inf, 0, 0
    for i, op in enumerate(outer):
        for j, cp in enumerate(counter):
            d = (op[0]-cp[0])**2 + (op[1]-cp[1])**2
            if d < best: best, bo, bc = d, i, j
    return bo, bc


def fuse_keyhole(outer, counter):
    bo, bc = closest_pair(outer, counter)
    ring = counter[bc:] + counter[:bc] + [counter[bc]]
    return outer[:bo+1] + ring + [outer[bo]] + outer[bo+1:]


def fuse_multi_keyhole(outer, counters):
    bridges = []
    for cnt in counters:
        bo, bc = closest_pair(outer, cnt)
        bridges.append({'bo': bo, 'bc': bc, 'cnt': cnt})
    bridges.sort(key=lambda b: b['bo'])
    fused, last = [], 0
    for b in bridges:
        fused.extend(outer[last:b['bo']+1])
        ring = b['cnt'][b['bc']:] + b['cnt'][:b['bc']] + [b['cnt'][b['bc']]]
        fused.extend(ring)
        fused.append(outer[b['bo']])
        last = b['bo'] + 1
    fused.extend(outer[last:])
    return fused


# ──────────────────────────── Path string helpers ────────────────────────────

def pts_to_path(pts, y_flip=True):
    def y(p): return LETTER_HEIGHT - p[1] if y_flip else p[1]
    parts = [f"M {pts[0][0]:.3f} {y(pts[0]):.3f}"]
    for p in pts[1:]:
        parts.append(f"L {p[0]:.3f} {y(p):.3f}")
    parts.append("Z")
    return " ".join(parts)


def dummy_counter(width, n=DUMMY_COUNTER_POINTS):
    cx = width / 2.0
    cy = LETTER_HEIGHT / 2.0
    parts = [f"M {cx:.3f} {cy:.3f}"]
    for _ in range(n - 1):
        parts.append(f"L {cx:.3f} {cy:.3f}")
    parts.append("Z")
    return " ".join(parts)


# ──────────────────────────── Patch letter_paths.py ────────────────────────────

def build_entry_pattern(char):
    return re.compile(
        r"(    '" + re.escape(char) + r"': \{\n"
        r"        'width': )[^,]+(,\n"
        r"        'outer_path': \")[^\"]+(\",\n"
        r"        'counter_path': \")[^\"]+(\",\n"
        r"        'has_counter': )(?:True|False)(,\n"
        r"    \},\n)"
    )


def patch(entries):
    with open(LETTER_PATHS_FILE, 'r', encoding='utf-8') as f:
        src = f.read()
    for char, e in entries.items():
        pat = build_entry_pattern(char)
        repl = (r"\g<1>" + str(e['width']) + r"\g<2>" + e['outer_path']
                + r"\g<3>" + e['counter_path'] + r"\g<4>False\g<5>")
        new_src, n = pat.subn(repl, src, count=1)
        if n != 1:
            raise RuntimeError(f"No se encontro entrada para '{char}'")
        src = new_src
    with open(LETTER_PATHS_FILE, 'w', encoding='utf-8') as f:
        f.write(src)


# ──────────────────────────── Main ────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='Keyhole desde fuente sobre letter_paths.py')
    ap.add_argument('--dry-run', action='store_true', help='solo imprimir, no escribir')
    ap.add_argument(
        '--font', '-f',
        default=DEFAULT_FONT_PATH,
        help='OTF/TTF (misma que la extracción completa)',
    )
    args = ap.parse_args()
    dry = args.dry_run

    font_path = os.path.abspath(args.font)
    if not os.path.isfile(font_path):
        print(f'ERROR: no existe fuente: {font_path}', file=sys.stderr)
        sys.exit(1)

    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()

    entries = {}
    print(f"Regenerando desde fuente: {font_path}")
    print(f"SCALE_K={SCALE_K}  LETTER_HEIGHT={LETTER_HEIGHT:.3f}  TARGET_POINTS={TARGET_POINTS}\n")

    for char in TARGET_GLYPHS:
        subpaths = extract_glyph_subpaths(glyph_set, cmap, char, TARGET_POINTS)
        outer_idx, counter_idxs = identify_subpaths(subpaths)
        outer = subpaths[outer_idx]
        counters = [subpaths[i] for i in counter_idxs]

        if len(counters) == 0:
            print(f"  {char}: no counters found in font, skipping")
            continue
        elif len(counters) == 1:
            fused = fuse_keyhole(outer, counters[0])
        else:
            fused = fuse_multi_keyhole(outer, counters)

        # Width from all pts
        all_pts = [p for s in subpaths for p in s]
        xs = [p[0] for p in all_pts]
        width = round(max(xs) - min(xs), 1)

        outer_path = pts_to_path(fused)
        counter_path = dummy_counter(width)

        entries[char] = {
            'width': width,
            'outer_path': outer_path,
            'counter_path': counter_path,
        }
        print(f"  {char}: outer_src={len(outer)} cntr_src={sum(len(c) for c in counters)} "
              f"-> fused={len(fused)} dummy={DUMMY_COUNTER_POINTS}  total={len(fused)+DUMMY_COUNTER_POINTS}")

    if not dry:
        patch(entries)
        print(f"\nOK: letter_paths.py actualizado ({len(entries)} entradas).")
    else:
        print("\n[dry-run] Sin cambios.")


if __name__ == '__main__':
    main()
