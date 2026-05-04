#!/usr/bin/env python3
"""
migrate + tailwind (subproceso) + runserver — portable Windows/macOS/Linux.

El Makefile usaba `tailwind start &` + `runserver`; en Windows GNU Make suele
invocar cmd.exe, donde `&` no hace background como en bash, y runserver no llega a arrancar.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_ensure() -> tuple:
    spec = importlib.util.spec_from_file_location(
        "ensure_dev_ports",
        ROOT / "docker" / "ensure_dev_ports.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar ensure_dev_ports.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_env, mod.ENV_PATH


def main() -> int:
    os.chdir(ROOT)
    load_env, env_path = _load_ensure()
    env = load_env(env_path)
    raw = str(env.get("APP_PORT", "8000")).strip() or "8000"
    try:
        port = max(1, min(65535, int(raw)))
    except ValueError:
        port = 8000

    if not env_path.is_file():
        print("Aviso: no hay .env; runserver usará valores por defecto de Django.", file=sys.stderr)

    r = subprocess.run(
        [sys.executable, "manage.py", "migrate"],
        cwd=str(ROOT),
    )
    if r.returncode != 0:
        return r.returncode

    tailwind = subprocess.Popen(
        [sys.executable, "manage.py", "tailwind", "start"],
        cwd=str(ROOT),
    )

    def stop_tailwind() -> None:
        if tailwind.poll() is not None:
            return
        tailwind.terminate()
        try:
            tailwind.wait(timeout=10)
        except subprocess.TimeoutExpired:
            tailwind.kill()
            tailwind.wait(timeout=5)

    # Dar un instante a Tailwind por si el CLI tarda en enlazar pipes.
    time.sleep(0.3)
    if tailwind.poll() is not None:
        print(
            "Error: `tailwind start` terminó al instante (revisa la salida de Tailwind arriba).",
            file=sys.stderr,
        )
        return 1

    addr = f"127.0.0.1:{port}"
    print(f">> Django runserver en http://{addr}/ (APP_PORT desde .env)\n", flush=True)
    try:
        r2 = subprocess.run(
            [sys.executable, "manage.py", "runserver", addr],
            cwd=str(ROOT),
        )
        return r2.returncode or 0
    except KeyboardInterrupt:
        return 0
    finally:
        stop_tailwind()


if __name__ == "__main__":
    raise SystemExit(main())
