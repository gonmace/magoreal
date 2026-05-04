"""Horizontally center a glyph's outer_path ink between 0 and width."""
import os
import re
import sys

LANDING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(LANDING_DIR, "landing"))

from morph_banner.letter_paths import LETTER_PATHS  # noqa: E402

PATHS_FILE = os.path.join(LANDING_DIR, "landing", "morph_banner", "letter_paths.py")


def parse_path_pts(path_str):
    tokens = re.findall(r"[MLZ]|[-\d.]+", path_str)
    out = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("M", "L"):
            out.append((t, float(tokens[i + 1]), float(tokens[i + 2])))
            i += 3
        elif t == "Z":
            out.append(("Z", None, None))
            i += 1
        else:
            i += 1
    return out


def rebuild_path(dx, dy, path_str):
    parts = []
    for cmd, x, y in parse_path_pts(path_str):
        if cmd == "Z":
            parts.append("Z")
        else:
            parts.append(f"{cmd} {x + dx:.3f} {y + dy:.3f}")
    return " ".join(parts)


def x_bbox(path_str):
    xs = [x for c, x, _ in parse_path_pts(path_str) if c in ("M", "L")]
    return min(xs), max(xs)


def main():
    char = sys.argv[1] if len(sys.argv) > 1 else "j"
    dy = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    if char not in LETTER_PATHS:
        sys.exit(f"unknown char {char!r}")

    d = LETTER_PATHS[char]
    w = d["width"]
    outer = d["outer_path"]
    mn, mx = x_bbox(outer)
    ink_cx = (mn + mx) / 2
    dx = w / 2 - ink_cx
    new_outer = rebuild_path(dx, dy, outer)
    mn2, mx2 = x_bbox(new_outer)
    print(f"{char}: width={w}  ink_x[{mn:.3f},{mx:.3f}]  dx={dx:+.3f} dy={dy:+.3f}")
    print(f"  -> ink_x[{mn2:.3f},{mx2:.3f}]  center={(mn2+mx2)/2:.3f} (target {w/2:.3f})")

    with open(PATHS_FILE, encoding="utf-8") as f:
        src = f.read()
    pat = re.compile(
        r"('"
        + re.escape(char)
        + r"': \{\n"
        r"        'width': [^,]+,\n"
        r"        'outer_path': \")[^\"]+(\",\n)"
    )
    m = pat.search(src)
    if not m:
        sys.exit(f"outer_path pattern not found for {char!r}")
    src = src[: m.start()] + m.group(1) + new_outer + m.group(2) + src[m.end() :]
    with open(PATHS_FILE, "w", encoding="utf-8") as f:
        f.write(src)


if __name__ == "__main__":
    main()
