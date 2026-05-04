#!/usr/bin/env python3
"""
Verificación del entorno de desarrollo (portable Windows/macOS/Linux).
Evita sintaxis bash ([, command -v) en el Makefile: GNU Make en Windows
suele ejecutar recetas con cmd.exe.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
COMPOSE = ROOT / "docker-compose.dev.yml"
ENV_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")


def load_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        m = ENV_LINE_RE.match(line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            out[k] = v
    return out


def main() -> int:
    print("Verificando entorno de desarrollo...")
    bad = 0

    if ENV_PATH.is_file():
        print("  [OK] .env existe")
    else:
        print("  [NO] .env no encontrado — ejecuta: make setup")
        bad += 1

    py = shutil.which("python") or shutil.which("python3")
    if py:
        print(f"  [OK] Python disponible ({py})")
    else:
        print("  [NO] Python no encontrado en PATH")
        bad += 1

    if shutil.which("docker"):
        print("  [OK] Docker disponible")
    else:
        print("  [NO] Docker no encontrado en PATH")
        bad += 1

    if not COMPOSE.is_file():
        print("  [NO] docker-compose.dev.yml no encontrado")
        bad += 1
    elif shutil.which("docker"):
        try:
            r = subprocess.run(
                ["docker", "compose", "-f", str(COMPOSE), "ps"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="replace",
            )
            out = (r.stdout or "") + (r.stderr or "")
            if r.returncode == 0 and "Up" in out:
                print("  [OK] Contenedores activos (docker compose ps)")
            else:
                print("  [!!] Contenedores detenidos o sin servicio Up — ejecuta: make dev-up")
        except (OSError, subprocess.TimeoutExpired) as e:
            print(f"  [!!] No se pudo ejecutar docker compose ps: {e}")

    env = load_env(ENV_PATH)
    port = 6379
    try:
        port = int(str(env.get("REDIS_HOST_PORT", "6379")).strip() or "6379")
    except ValueError:
        pass
    url = f"redis://127.0.0.1:{port}/0"
    try:
        import redis  # noqa: PLC0415

        redis.from_url(url).ping()
        print(f"  [OK] Redis accesible en 127.0.0.1:{port}")
    except ImportError:
        print("  [!!] Paquete 'redis' no instalado (pip install -r requirements-dev.txt)")
    except Exception:
        print(f"  [!!] Redis no accesible en 127.0.0.1:{port} — ¿make dev-up corriendo?")

    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
