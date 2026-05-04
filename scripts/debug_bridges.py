"""Debug: muestra los puntos puente elegidos por el algoritmo de fusión keyhole."""
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LANDING_DIR = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(LANDING_DIR, 'landing'))
sys.path.insert(0, THIS_DIR)

from morph_banner.letter_paths import LETTER_PATHS  # noqa: E402
from keyhole_holed_glyphs import parse_path, closest_pair_indices  # noqa: E402

for ch in ['0', 'O', 'o', 'B', '8']:
    d = LETTER_PATHS[ch]
    outer = parse_path(d['outer_path'])[0]
    counters = parse_path(d['counter_path'])
    print(f"\n=== '{ch}' ===")
    print(f"  outer: {len(outer)} pts")
    for idx, c in enumerate(counters):
        bo, bc, dist = closest_pair_indices(outer, c)
        op = outer[bo]
        cp = c[bc]
        print(f"  counter#{idx}: {len(c)} pts")
        print(f"    bridge: outer[{bo}]={op} <-> counter[{bc}]={cp}")
        print(f"    distance = {dist:.4f} units")
