"""
Alinea verticalmente los paths keyhole de letter_paths.py con sus pares
no-keyhole, modificando las coordenadas Y in-place.

Para cada keyhole (outer_pts > 75) se calcula el delta Y comparándolo con
el promedio de miny de las letras NO-keyhole del mismo grupo (nums / uppers /
lowers) que tienen altura similar (delta_height < 2.0). Luego se reescribe
el outer_path con cada Y desplazada por ese delta.

El counter_path es dummy y no se toca.

Casos especiales: 'i' por baseline de altura-x; 'j' por baseline de descendientes (g/p/q/y).

Uso: python scripts/align_keyhole_y.py [--dry-run]
"""
import os
import re
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LANDING_DIR = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(LANDING_DIR, 'landing'))

from morph_banner.letter_paths import LETTER_PATHS

LETTER_PATHS_FILE = os.path.join(LANDING_DIR, 'landing', 'morph_banner', 'letter_paths.py')


def parse_path_pts(path_str):
    """Devuelve [(cmd, x, y), ...] preservando el orden."""
    tokens = re.findall(r'[MLZ]|[-\d.]+', path_str)
    out = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ('M', 'L'):
            x = float(tokens[i+1]); y = float(tokens[i+2])
            out.append((t, x, y))
            i += 3
        elif t == 'Z':
            out.append(('Z', None, None))
            i += 1
        else:
            i += 1
    return out


def shift_path_y(path_str, dy):
    """Reconstruye el path con cada Y desplazada por dy."""
    parts = []
    for cmd, x, y in parse_path_pts(path_str):
        if cmd == 'Z':
            parts.append('Z')
        else:
            parts.append(f'{cmd} {x:.3f} {y + dy:.3f}')
    return ' '.join(parts)


def y_bounds(path_str):
    pts = [(x, y) for cmd, x, y in parse_path_pts(path_str) if cmd in ('M', 'L')]
    ys = [y for _, y in pts]
    return min(ys), max(ys)


def is_keyhole(entry):
    outer_pts = len(re.findall(r'[ML]', entry['outer_path']))
    return (not entry['has_counter']) and outer_pts > 75


def dy_lowercase_i_baseline(paths):
    """
    La 'i' keyhole fusiona punto + bastón; el heuristico por min-y la emparenta mal
    con ascendientes (l/h/...) porque comparten alto de bbox parecido. Alineamos
    por línea inferior (max Y) contra minúsculas de altura x sin descendentes fuertes.
    """
    mxs = []
    for char in paths:
        if char == 'i' or not char.islower():
            continue
        e = paths[char]
        if is_keyhole(e):
            continue
        miny, maxy = y_bounds(e['outer_path'])
        height = maxy - miny
        if 14.5 <= height <= 16.0:
            mxs.append(maxy)
    if not mxs:
        return 0.0
    ref_max = sum(mxs) / len(mxs)
    _, imx = y_bounds(paths['i']['outer_path'])
    return ref_max - imx


def dy_lowercase_j_baseline(paths):
    """
    La 'j' keyhole fusiona punto + bastón + descendiente; el heuristico por min-y puede
    desalinear. Alineamos el fondo del bbox con g/p/q/y (max Y >= DESCENDER_MIN_MAXY).
    """
    desc_floor = 30.5
    mxs = []
    for char in paths:
        if char == 'j' or not char.islower():
            continue
        e = paths[char]
        if is_keyhole(e):
            continue
        _, maxy = y_bounds(e['outer_path'])
        if maxy >= desc_floor:
            mxs.append(maxy)
    if not mxs:
        return 0.0
    ref_max = sum(mxs) / len(mxs)
    _, jmx = y_bounds(paths['j']['outer_path'])
    return ref_max - jmx


def compute_dy_for_groups(items_by_group):
    """
    Para cada keyhole en cada grupo, calcula el dy necesario para alinearlo
    con el promedio de miny de las letras no-keyhole de altura similar.
    """
    dys = {}
    for group_name, chars in items_by_group.items():
        group = []
        for c in chars:
            if c not in LETTER_PATHS:
                continue
            e = LETTER_PATHS[c]
            miny, maxy = y_bounds(e['outer_path'])
            group.append({
                'char': c,
                'miny': miny,
                'maxy': maxy,
                'height': maxy - miny,
                'kh': is_keyhole(e),
            })
        non_kh = [g for g in group if not g['kh']]
        for g in group:
            if not g['kh']:
                continue
            # Ver dy_lowercase_i_baseline().
            if group_name == 'lowers' and g['char'] == 'i':
                dys['i'] = dy_lowercase_i_baseline(LETTER_PATHS)
                continue
            if group_name == 'lowers' and g['char'] == 'j':
                dys['j'] = dy_lowercase_j_baseline(LETTER_PATHS)
                continue
            similar = [n for n in non_kh if abs(n['height'] - g['height']) < 2.0]
            if not similar:
                similar = non_kh
            ref_miny = sum(s['miny'] for s in similar) / len(similar)
            dys[g['char']] = ref_miny - g['miny']
    return dys


def patch_letter_paths(dys, dry_run=False):
    with open(LETTER_PATHS_FILE, 'r', encoding='utf-8') as f:
        src = f.read()

    for char, dy in dys.items():
        if abs(dy) < 1e-3:
            continue
        new_outer = shift_path_y(LETTER_PATHS[char]['outer_path'], dy)
        # Patch SOLO el outer_path de este char.
        char_esc = re.escape(char)
        # Patron robusto: busca la entrada del char y captura su outer_path.
        pat = re.compile(
            r"('" + char_esc + r"': \{\n"
            r"        'width': [^,]+,\n"
            r"        'outer_path': \")[^\"]+(\",\n)"
        )
        m = pat.search(src)
        if not m:
            print(f"  WARN: no se encontro outer_path de '{char}'")
            continue
        new_src = src[:m.start()] + m.group(1) + new_outer + m.group(2) + src[m.end():]
        src = new_src
        print(f"  {char}: dy={dy:+.3f}  outer_path desplazado")

    if dry_run:
        print("\n[dry-run] Sin cambios.")
        return
    with open(LETTER_PATHS_FILE, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f"\nOK: letter_paths.py actualizado.")


def main():
    dry = '--dry-run' in sys.argv
    items_by_group = {
        'nums':   list('0123456789'),
        'uppers': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
        'lowers': list('abcdefghijklmnopqrstuvwxyz'),
    }
    dys = compute_dy_for_groups(items_by_group)

    if not dys:
        print("No hay keyhole que ajustar.")
        return

    print("Deltas Y para keyhole (negativo = subir el glifo):\n")
    for char, dy in sorted(dys.items()):
        print(f"  {char}: dy = {dy:+.3f}")
    print()

    patch_letter_paths(dys, dry_run=dry)


if __name__ == '__main__':
    main()
