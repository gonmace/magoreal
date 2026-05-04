"""Genera un preview con zoom 5x sobre la zona del slit del `0` y `O`."""
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LANDING_DIR = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(LANDING_DIR, 'landing'))
sys.path.insert(0, THIS_DIR)

from morph_banner.letter_paths import LETTER_HEIGHT, LETTER_PATHS  # noqa: E402
from keyhole_holed_glyphs import (  # noqa: E402
    build_keyhole_entry,
    closest_pair_indices,
    parse_path,
)

OUT = os.path.join(THIS_DIR, 'preview_slit_zoom.html')
GLYPHS = ['0', 'O', 'B']  # los que muestran slit

rows = []
for ch in GLYPHS:
    e = build_keyhole_entry(ch)
    outer = parse_path(LETTER_PATHS[ch]['outer_path'])[0]
    counters = parse_path(LETTER_PATHS[ch]['counter_path'])
    bo, bc, dist = closest_pair_indices(outer, counters[0])
    op = outer[bo]
    cp = counters[0][bc]
    # Centro del slit
    sx = (op[0] + cp[0]) / 2
    sy = (op[1] + cp[1]) / 2
    half = 4  # half size de la ventana de zoom (en unidades SVG)
    vb = f"{sx - half} {sy - half} {2 * half} {2 * half}"

    new_compound = e['outer_path'] + ' ' + e['counter_path']
    old_compound = LETTER_PATHS[ch]['outer_path'] + ' ' + LETTER_PATHS[ch]['counter_path']

    rows.append(f'''
<h3>'{ch}' — slit en ({sx:.2f}, {sy:.2f}), distancia {dist:.2f}</h3>
<div class="grid">
  <div>
    <div class="cap">Original (sin slit)</div>
    <svg viewBox="{vb}" width="400" height="400" xmlns="http://www.w3.org/2000/svg" style="background:#fff">
      <path d="{old_compound}" fill="black" fill-rule="evenodd"/>
    </svg>
  </div>
  <div>
    <div class="cap">Keyhole evenodd (no fill stroke)</div>
    <svg viewBox="{vb}" width="400" height="400" xmlns="http://www.w3.org/2000/svg" style="background:#fff">
      <path d="{new_compound}" fill="black" fill-rule="evenodd"/>
    </svg>
  </div>
  <div>
    <div class="cap">Keyhole + path debug (red border) muestra el camino</div>
    <svg viewBox="{vb}" width="400" height="400" xmlns="http://www.w3.org/2000/svg" style="background:#fff">
      <path d="{e['outer_path']}" fill="rgba(0,0,0,0.4)" fill-rule="evenodd"
            stroke="red" stroke-width="0.05"/>
      <circle cx="{op[0]}" cy="{op[1]}" r="0.15" fill="cyan"/>
      <circle cx="{cp[0]}" cy="{cp[1]}" r="0.15" fill="magenta"/>
    </svg>
  </div>
</div>
''')

html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Zoom slit</title>
<style>
body{{padding:20px;font-family:system-ui;background:#f0f0f0;}}
.grid{{display:flex;gap:14px;margin-bottom:24px;}}
.cap{{font-size:11px;color:#666;margin-bottom:4px;}}
svg{{border:1px solid #999;}}
</style></head><body>
<h1>Zoom 5x sobre el slit (cyan=outer bridge, magenta=counter bridge)</h1>
{"".join(rows)}
</body></html>
'''
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Preview zoom escrito en: {OUT}")
