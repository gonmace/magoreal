"""Shift lowercase j keyhole vertically: align bottom (max Y) with descenders g,p,q,y."""
import os
import re
import sys

LANDING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(LANDING_DIR, "landing"))

from morph_banner.letter_paths import LETTER_PATHS  # noqa: E402

PATHS_FILE = os.path.join(LANDING_DIR, "landing", "morph_banner", "letter_paths.py")

# Bajos con descendiente comparten máx.Y ~31.3; umbraje evita pillar letras sólo altura x.
DESCENDER_MIN_MAXY = 30.5


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


def shift_path(path_str, dy):
    parts = []
    for cmd, x, y in parse_path_pts(path_str):
        if cmd == "Z":
            parts.append("Z")
        else:
            parts.append(f"{cmd} {x:.3f} {y + dy:.3f}")
    return " ".join(parts)


def y_bounds(path):
    ys = [y for c, _, y in parse_path_pts(path) if c in ("M", "L")]
    return min(ys), max(ys)


def is_keyhole(entry):
    o = entry["outer_path"]
    return (not entry["has_counter"]) and len(re.findall(r"[ML]", o)) > 75


def cohort_ref_maxy_descenders():
    mxs = []
    for char in LETTER_PATHS:
        if not char.islower():
            continue
        d = LETTER_PATHS[char]
        if is_keyhole(d):
            continue
        _, mx = y_bounds(d["outer_path"])
        if mx >= DESCENDER_MIN_MAXY:
            mxs.append(mx)
    return sum(mxs) / len(mxs)


def main():
    ref = cohort_ref_maxy_descenders()
    mn, mx = y_bounds(LETTER_PATHS["j"]["outer_path"])
    dy = ref - mx
    new_outer = shift_path(LETTER_PATHS["j"]["outer_path"], dy)
    print(f"cohort(descenders) baseline maxy={ref:.6f}  j_maxy_was={mx:.6f}  dy={dy:.6f}")

    with open(PATHS_FILE, encoding="utf-8") as f:
        src = f.read()

    pat = re.compile(
        r"('" + re.escape("j") + r"': \{\n"
        r"        'width': [^,]+,\n"
        r"        'outer_path': \")[^\"]+(\",\n)"
    )
    m = pat.search(src)
    if not m:
        sys.exit("outer_path pattern not found for 'j'")

    src = src[: m.start()] + m.group(1) + new_outer + m.group(2) + src[m.end() :]
    with open(PATHS_FILE, "w", encoding="utf-8") as f:
        f.write(src)

    nmn, nmx = y_bounds(new_outer)
    print(f"written. new bounds miny={nmn:.3f} maxy={nmx:.3f}")


if __name__ == "__main__":
    main()
