"""
Inspect the structure of the '0', 'p', 'q' glyphs directly in
Quadrillion Sb.otf to count subpaths/contours and dump raw pen
commands. This tells us whether the dual-subpath structure of '0'
in letter_paths.py is inherent to the font or introduced by the
extraction script.
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen


FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'landing', 'morph_banner', 'Quadrillion Sb.otf',
)


class CommandPen(BasePen):
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.commands = []

    def _moveTo(self, pt):
        self.commands.append(('M', pt))

    def _lineTo(self, pt):
        self.commands.append(('L', pt))

    def _curveToOne(self, pt1, pt2, pt3):
        self.commands.append(('C', pt1, pt2, pt3))

    def _qCurveToOne(self, pt1, pt2):
        self.commands.append(('Q', pt1, pt2))

    def _closePath(self):
        self.commands.append(('Z',))


def count_subpaths(commands):
    return sum(1 for c in commands if c[0] == 'M')


def summarise(char, commands):
    n_sub = count_subpaths(commands)
    print(f"\n=== Glyph '{char}' ===")
    print(f"  total commands: {len(commands)}")
    print(f"  subpaths (contours): {n_sub}")
    sub_idx = -1
    sub_lens = []
    cur_len = 0
    sub_bounds = []
    cur_bounds = None
    for cmd in commands:
        if cmd[0] == 'M':
            if cur_len:
                sub_lens.append(cur_len)
                sub_bounds.append(cur_bounds)
            sub_idx += 1
            cur_len = 1
            cur_bounds = {'min_x': cmd[1][0], 'max_x': cmd[1][0],
                          'min_y': cmd[1][1], 'max_y': cmd[1][1]}
        elif cmd[0] == 'Z':
            cur_len += 1
        else:
            cur_len += 1
            pts = cmd[1:]
            for p in pts:
                cur_bounds['min_x'] = min(cur_bounds['min_x'], p[0])
                cur_bounds['max_x'] = max(cur_bounds['max_x'], p[0])
                cur_bounds['min_y'] = min(cur_bounds['min_y'], p[1])
                cur_bounds['max_y'] = max(cur_bounds['max_y'], p[1])
    if cur_len:
        sub_lens.append(cur_len)
        sub_bounds.append(cur_bounds)

    for i, (length, b) in enumerate(zip(sub_lens, sub_bounds)):
        w = b['max_x'] - b['min_x']
        h = b['max_y'] - b['min_y']
        print(f"  subpath #{i}: {length} commands, bbox "
              f"x=[{b['min_x']:.1f},{b['max_x']:.1f}] "
              f"y=[{b['min_y']:.1f},{b['max_y']:.1f}] "
              f"w={w:.1f} h={h:.1f}")


def main():
    print(f"Inspecting font: {FONT_PATH}")
    font = TTFont(FONT_PATH)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()

    targets = ['0', 'p', 'q', 'O', 'o', 'B', '8']
    for ch in targets:
        if ord(ch) not in cmap:
            print(f"\n'{ch}' not in cmap")
            continue
        glyph_name = cmap[ord(ch)]
        if glyph_name not in glyph_set:
            print(f"\nglyph '{glyph_name}' for '{ch}' missing")
            continue
        pen = CommandPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        summarise(ch, pen.commands)


if __name__ == '__main__':
    main()
