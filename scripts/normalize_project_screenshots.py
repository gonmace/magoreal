#!/usr/bin/env python3
"""
Normaliza screenshots de un proyecto del portfolio.

Qué hace (en orden):
1) Lee `metadata.json` del proyecto.
2) Toma imágenes de `screenshots/` (png/jpg/jpeg/webp/avif), ignorando README.
3) Renombra secuencialmente a `01.webp`, `02.webp`, ... (conversión a WebP).
4) Reescribe `metadata.json` -> screenshots[i].archivo = "screenshots/NN.webp"
   preservando las descripciones existentes por posición.

Uso:
  python scripts/normalize_project_screenshots.py --slug 02-generador-documentos-ia --apply
  python scripts/normalize_project_screenshots.py --slug 02-generador-documentos-ia --quality 88 --delete-originals --apply
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
AUTOMATIONS_DIR = ROOT.parent / "landing-automatizaciones" / "proyectos"
VALID_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".avif"}


def sort_key(path: Path) -> tuple[int, str]:
    stem = path.stem
    if stem.isdigit():
        return (int(stem), path.name.lower())
    return (10_000, path.name.lower())


def load_metadata(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_metadata(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def collect_images(shots_dir: Path) -> list[Path]:
    candidates = [p for p in shots_dir.iterdir() if p.is_file() and p.suffix.lower() in VALID_EXTS]
    candidates = sorted(candidates, key=sort_key)

    # Deduplicar por stem numérico: si existen 1.png y 1.webp, preferir .webp.
    # También evita convertir doble cuando conviven formatos antiguos y nuevos.
    by_stem: dict[str, Path] = {}

    def rank(ext: str) -> int:
        order = {".webp": 0, ".avif": 1, ".png": 2, ".jpg": 3, ".jpeg": 4}
        return order.get(ext.lower(), 99)

    for p in candidates:
        key = p.stem
        prev = by_stem.get(key)
        if prev is None or rank(p.suffix) < rank(prev.suffix):
            by_stem[key] = p

    return sorted(by_stem.values(), key=sort_key)


def ensure_rgb(img: Image.Image) -> Image.Image:
    # WebP soporta alpha; RGB evita problemas con paletas en algunos PNG.
    if img.mode in {"RGB", "RGBA"}:
        return img
    if "A" in img.getbands():
        return img.convert("RGBA")
    return img.convert("RGB")


def convert_to_webp(src: Path, dst: Path, quality: int) -> None:
    with Image.open(src) as img:
        safe = ensure_rgb(img)
        safe.save(dst, format="WEBP", quality=quality, method=6)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="Carpeta del proyecto. Ej: 02-generador-documentos-ia")
    ap.add_argument("--quality", type=int, default=86, help="Calidad WebP (default: 86)")
    ap.add_argument(
        "--delete-originals",
        action="store_true",
        help="Eliminar archivos originales luego de convertir.",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Aplica cambios. Sin --apply solo muestra preview.",
    )
    args = ap.parse_args()

    project_dir = AUTOMATIONS_DIR / args.slug
    shots_dir = project_dir / "screenshots"
    metadata_path = project_dir / "metadata.json"

    if not project_dir.exists():
        raise SystemExit(f"Proyecto no encontrado: {project_dir}")
    if not shots_dir.exists():
        raise SystemExit(f"Carpeta screenshots no encontrada: {shots_dir}")
    if not metadata_path.exists():
        raise SystemExit(f"metadata.json no encontrado: {metadata_path}")

    metadata = load_metadata(metadata_path)
    old_screens = metadata.get("screenshots") or []
    descriptions = []
    for item in old_screens:
        if isinstance(item, dict):
            descriptions.append(item.get("descripcion", ""))

    images = collect_images(shots_dir)
    if not images:
        raise SystemExit("No hay imágenes para convertir en screenshots/.")

    print(f"Proyecto: {args.slug}")
    print(f"Imágenes detectadas: {len(images)}")
    print(f"metadata.screenshots actual: {len(old_screens)}")

    temp_dir = shots_dir / "_tmp_webp"
    if args.apply:
        temp_dir.mkdir(exist_ok=True)

    new_entries: list[dict[str, str]] = []
    planned_ops: list[tuple[Path, Path]] = []

    for idx, src in enumerate(images, start=1):
        new_name = f"{idx:02d}.webp"
        new_rel = f"screenshots/{new_name}"
        dst = shots_dir / new_name
        desc = descriptions[idx - 1] if idx - 1 < len(descriptions) else ""
        new_entries.append({"archivo": new_rel, "descripcion": desc})
        planned_ops.append((src, dst))
        print(f"- {src.name}  ->  {new_name}")

    if not args.apply:
        print("\nPreview listo. Ejecuta con --apply para aplicar cambios.")
        return 0

    # Convertir a temp para evitar pisar archivos si ya existen 01.webp, etc.
    temp_outputs: list[Path] = []
    for idx, (src, _dst) in enumerate(planned_ops, start=1):
        temp_dst = temp_dir / f"{idx:02d}.webp"
        convert_to_webp(src, temp_dst, args.quality)
        temp_outputs.append(temp_dst)

    # Limpiar antiguos webp destino + mover temporales.
    for _src, dst in planned_ops:
        if dst.exists():
            dst.unlink()
    for temp_file, (_src, dst) in zip(temp_outputs, planned_ops):
        shutil.move(str(temp_file), str(dst))
    shutil.rmtree(temp_dir, ignore_errors=True)

    # Opcional: borrar originales que no sean los nuevos webp.
    if args.delete_originals:
        keep = {dst.resolve() for _src, dst in planned_ops}
        for p in shots_dir.iterdir():
            if not p.is_file():
                continue
            if p.name.lower() == "readme.txt":
                continue
            if p.resolve() in keep:
                continue
            if p.suffix.lower() in VALID_EXTS:
                p.unlink()

    metadata["screenshots"] = new_entries
    save_metadata(metadata_path, metadata)

    print("\nOK: screenshots normalizados a WebP y metadata actualizado.")
    print(f"- quality={args.quality}")
    print(f"- delete_originals={args.delete_originals}")
    print(f"- metadata: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
