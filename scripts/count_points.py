"""Cuenta puntos M/L de cada glifo en letter_paths.py."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'landing'))

from morph_banner.letter_paths import LETTER_PATHS

chars = ['0', 'O', 'o', 'B', '8', 'p', 'q', 'A', 'D', 'a']
for c in chars:
    d = LETTER_PATHS[c]
    outer = len(re.findall(r'[ML]', d['outer_path']))
    counter = len(re.findall(r'[ML]', d['counter_path']))
    n_sub_outer = len(re.findall(r'M', d['outer_path']))
    n_sub_counter = len(re.findall(r'M', d['counter_path']))
    print(f"{c}: outer={outer}pts/{n_sub_outer}sub  counter={counter}pts/{n_sub_counter}sub  has_counter={d['has_counter']}  total={outer + counter}")
