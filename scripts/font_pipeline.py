#!/usr/bin/env python3
"""
Orquestador para incorporar una fuente nueva al banner morfología (letter_paths.py).

Ejecutar desde el directorio `landing/` (donde están `manage.py` y `scripts/`).

Pasos (por defecto: extracción + post):
  1) regenerate_all_paths  -> sobrescribe letter_paths.py completo
  2) regen_and_keyhole     -> fusion slit + normalizacion puntos huecos/i/j
  3) align_keyhole_y       -> alineacion vertical keyholes (+ i baseline + j descender)
  4) center_glyph_x j      -> centro horizontal tipico de la j

Uso:
  python scripts/font_pipeline.py --font landing/morph_banner/fonts/MiFont.otf
  python scripts/font_pipeline.py --post-only --font ruta.otf

Requiere: fonttools (`pip install fonttools`), numpy.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def repo_root():
    """Directorio Django `landing/` (parent de `scripts/`)."""
    return Path(__file__).resolve().parents[1]


def scripts_dir():
    return repo_root() / "scripts"


def letter_paths_py():
    return repo_root() / "landing" / "morph_banner" / "letter_paths.py"


def default_font_path():
    return repo_root() / "landing" / "morph_banner" / "Quadrillion Sb.otf"


def run(py_script: Path, argv: list[str], title: str) -> None:
    sep = "-" * 60
    print(f"\n{sep}\n>> {title}\n{sep}")
    cmd = [sys.executable, str(py_script)] + argv
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=str(repo_root()))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Pipeline morfologia: nueva fuente -> letter_paths.py + post-procesado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument(
        "--font",
        "-f",
        type=Path,
        default=default_font_path(),
        help="Fuente .otf / .ttf (debe tener cmap para A-Z a-z y 0-9)",
    )
    ap.add_argument(
        "--post-only",
        action="store_true",
        help=(
            "Solo pasos después de extracción (keyhole, Y, centro j); "
            "usar si ya generaste letter_paths.py manualmente desde la misma fuente"
        ),
    )
    ap.add_argument(
        "--skip-center-j",
        action="store_true",
        help="No ejecutar centrado horizontal de la j",
    )
    args = ap.parse_args()

    font_path = args.font.resolve()
    if not font_path.is_file():
        print(f"ERROR: no existe fuente: {font_path}", file=sys.stderr)
        sys.exit(1)

    font_s = str(font_path)
    sdir = scripts_dir()
    outp = letter_paths_py()

    if not args.post_only:
        run(
            sdir / "regenerate_all_paths.py",
            ["--font", font_s, "--out", str(outp)],
            "Extracción completa (A-Za-z0-9) -> letter_paths.py",
        )

    run(
        sdir / "regen_and_keyhole.py",
        ["--font", font_s],
        "Fusión keyhole desde fuente (0 O o B 8 m i j)",
    )
    run(
        sdir / "align_keyhole_y.py",
        [],
        "Alineación vertical de keyholes (incluye i baseline y j descender)",
    )
    if not args.skip_center_j:
        run(
            sdir / "center_glyph_x.py",
            ["j"],
            "Centrar horizontalmente la j en el ancho metrico",
        )

    print("\nOK Pipeline terminado.")
    print("  Preview: iniciá el servidor y abrí /dev/letter-preview/")
    print("  Revisión morfología: panel admin MorphBanner / home con la palabra de prueba.")


if __name__ == "__main__":
    main()
