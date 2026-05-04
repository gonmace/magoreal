"""Inspeccionar los glifos i, j, m en la fuente."""
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)

# Parchear inspect_zero_glyph para inspeccionar i, j, m
FONT_PATH = os.path.join(
    os.path.dirname(THIS_DIR),
    'landing', 'morph_banner', 'Quadrillion Sb.otf',
)

from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen


class CommandPen(BasePen):
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.commands = []
    def _moveTo(self, pt): self.commands.append(('M', pt))
    def _lineTo(self, pt): self.commands.append(('L', pt))
    def _curveToOne(self, pt1, pt2, pt3): self.commands.append(('C', pt1, pt2, pt3))
    def _qCurveToOne(self, pt1, pt2): self.commands.append(('Q', pt1, pt2))
    def _closePath(self): self.commands.append(('Z',))


def summarise(char, commands):
    n_sub = sum(1 for c in commands if c[0] == 'M')
    print(f"\n=== Glyph '{char}' ===")
    print(f"  total commands: {len(commands)}")
    print(f"  subpaths (contours): {n_sub}")
    sub_lens = []
    cur_len = 0
    cur_bounds = None
    for cmd in commands:
        if cmd[0] == 'M':
            if cur_len:
                sub_lens.append((cur_len, cur_bounds))
            cur_len = 1
            cur_bounds = {'min_x': cmd[1][0], 'max_x': cmd[1][0], 'min_y': cmd[1][1], 'max_y': cmd[1][1]}
        elif cmd[0] == 'Z':
            cur_len += 1
        else:
            cur_len += 1
            for p in cmd[1:]:
                cur_bounds['min_x'] = min(cur_bounds['min_x'], p[0])
                cur_bounds['max_x'] = max(cur_bounds['max_x'], p[0])
                cur_bounds['min_y'] = min(cur_bounds['min_y'], p[1])
                cur_bounds['max_y'] = max(cur_bounds['max_y'], p[1])
    if cur_len:
        sub_lens.append((cur_len, cur_bounds))
    for i, (length, b) in enumerate(sub_lens):
        print(f"  subpath #{i}: {length} cmds  bbox x=[{b['min_x']:.1f},{b['max_x']:.1f}] y=[{b['min_y']:.1f},{b['max_y']:.1f}]")


font = TTFont(FONT_PATH)
glyph_set = font.getGlyphSet()
cmap = font.getBestCmap()

for ch in ['i', 'j', 'm', 'n']:
    if ord(ch) not in cmap:
        print(f"'{ch}' not in cmap")
        continue
    gname = cmap[ord(ch)]
    pen = CommandPen(glyph_set)
    glyph_set[gname].draw(pen)
    summarise(ch, pen.commands)
