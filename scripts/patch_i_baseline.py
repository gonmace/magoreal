"""One-off / reusable: shift lowercase i vertically so baseline (max Y) matches x-height cohort."""
import os
import re
import sys

LANDING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Repo layout: landing/landing/morph_banner/ — first parent of this file is Django project root.
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


def cohort_ref_maxy():
    mxs = []
    for char in LETTER_PATHS:
        if not char.islower():
            continue
        d = LETTER_PATHS[char]
        if is_keyhole(d):
            continue
        mn, mx = y_bounds(d["outer_path"])
        h = mx - mn
        if 14.5 <= h <= 16.0:
            mxs.append(mx)
    return sum(mxs) / len(mxs)


def main():
    ref = cohort_ref_maxy()
    mn, mx = y_bounds(LETTER_PATHS["i"]["outer_path"])
    dy = ref - mx
    new_outer = shift_path(LETTER_PATHS["i"]["outer_path"], dy)
    print(f"cohort baseline maxy={ref:.6f}  i_maxy_was={mx:.6f}  dy={dy:.6f}")

    with open(PATHS_FILE, encoding="utf-8") as f:
        src = f.read()

    pat = re.compile(
        r"('" + re.escape("i") + r"': \{\n"
        r"        'width': [^,]+,\n"
        r"        'outer_path': \")[^\"]+(\",\n)"
    )
    m = pat.search(src)
    if not m:
        sys.exit("outer_path pattern not found for 'i'")

    src = src[: m.start()] + m.group(1) + new_outer + m.group(2) + src[m.end() :]
    with open(PATHS_FILE, "w", encoding="utf-8") as f:
        f.write(src)

    nmn, nmx = y_bounds(new_outer)
    print(f"written. new bounds miny={nmn:.3f} maxy={nmx:.3f}")


if __name__ == "__main__":
    main()
