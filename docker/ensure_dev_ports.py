#!/usr/bin/env python3
"""
Asegura que los puertos publicados al host (dev Docker + Django) estén libres.
Si están ocupados, sube a los siguientes libres y actualiza .env.

Uso:
  python docker/ensure_dev_ports.py          # ajusta .env y muestra resumen
  python docker/ensure_dev_ports.py --check  # solo comprobar; exit 1 si hay conflicto
"""
from __future__ import annotations

import argparse
import re
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"

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


def port_free(p: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", p))
            return True
        except OSError:
            return False


def next_free(start: int) -> int:
    p = max(1, int(start))
    while p < 65535:
        if port_free(p):
            return p
        p += 1
    raise SystemExit("No se encontró puerto libre (127.0.0.1) por debajo de 65535.")


def update_env_file(path: Path, updates: dict[str, str]) -> None:
    if not updates:
        return
    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines(keepends=False)
    else:
        lines = []
    done = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            out.append(line)
            continue
        m = ENV_LINE_RE.match(stripped)
        if m and m.group(1) in updates:
            k = m.group(1)
            out.append(f"{k}={updates[k]}")
            done.add(k)
        else:
            m2 = re.match(r"^export\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", stripped)
            if m2 and m2.group(1) in updates:
                k = m2.group(1)
                out.append(f"{k}={updates[k]}")
                done.add(k)
            else:
                out.append(line)
    for k, v in updates.items():
        if k not in done:
            out.append(f"{k}={v}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def as_int(d: dict[str, str], key: str, default: int) -> int:
    v = d.get(key)
    if v is None or str(v).strip() == "":
        return default
    return int(str(v).strip())


def run_check_only(env: dict[str, str]) -> tuple[bool, list[str]]:
    """Devuelve (ok, mensajes de conflicto)."""
    messages: list[str] = []
    app = as_int(env, "APP_PORT", 8000)
    n8n_default_p = as_int(env, "N8N_PORT", app + 1)
    mcp_default_p = as_int(env, "N8N_MCP_PORT", app + 2)

    # Solo APP_PORT es relevante en producción — postgres y redis no exponen
    # puertos al host en docker-compose.yml (solo red interna app_network).
    specs: list[tuple[str, int]] = [
        ("APP_PORT", app),
    ]
    n8n_on = bool(env.get("N8N_DOMAIN", "").strip())
    if n8n_on:
        specs += [
            ("N8N_PORT", n8n_default_p),
            ("N8N_MCP_PORT", mcp_default_p),
        ]

    for name, p in specs:
        if not port_free(p):
            messages.append(f"  ✗ {name}={p} (ocupado en 127.0.0.1)")

    return (len(messages) == 0, messages)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Solo comprobar; no modificar .env")
    args = ap.parse_args()

    if not ENV_PATH.is_file():
        print("Error: .env no encontrado. Ejecuta 'make setup' primero.", file=sys.stderr)
        return 1

    env = load_env(ENV_PATH)
    if args.check:
        ok, bad = run_check_only(env)
        if ok:
            print("Puertos de desarrollo libres (127.0.0.1).")
            return 0
        print("Conflicto de puertos:\n" + "\n".join(bad), file=sys.stderr)
        return 1

    n8n_on = bool(env.get("N8N_DOMAIN", "").strip())
    work = dict(env)
    updates: dict[str, str] = {}

    # Puertos ya asignados en esta ejecución (para evitar que dos claves tomen el mismo).
    claimed: set[int] = set()

    def next_free_not_claimed(start: int) -> int:
        p = max(1, int(start))
        while p < 65535:
            if port_free(p) and p not in claimed:
                return p
            p += 1
        raise SystemExit("No se encontró puerto libre (127.0.0.1) por debajo de 65535.")

    def need_free(key: str, current: int) -> None:
        if port_free(current) and current not in claimed:
            claimed.add(current)
            return
        nxt = next_free_not_claimed(current)
        updates[key] = str(nxt)
        work[key] = str(nxt)
        claimed.add(nxt)
        print(f"  ▶ {key}: {current} ocupado → usando {nxt}", flush=True)

    need_free("POSTGRES_HOST_PORT", as_int(work, "POSTGRES_HOST_PORT", 5432))
    need_free("REDIS_HOST_PORT", as_int(work, "REDIS_HOST_PORT", 6379))
    need_free("APP_PORT", as_int(work, "APP_PORT", 8000))

    if n8n_on:
        app_b = as_int(work, "APP_PORT", 8000)
        need_free("N8N_PORT", as_int(work, "N8N_PORT", app_b + 1))
        need_free("N8N_MCP_PORT", as_int(work, "N8N_MCP_PORT", app_b + 2))

    if "REDIS_HOST_PORT" in updates:
        updates["REDIS_URL"] = f"redis://localhost:{updates['REDIS_HOST_PORT']}/0"
    if "APP_PORT" in updates:
        updates["CSRF_TRUSTED_ORIGINS"] = f"http://localhost:{updates['APP_PORT']}"
    if n8n_on and "N8N_PORT" in updates and work.get("N8N_DOMAIN", "").strip() == "localhost":
        np = updates["N8N_PORT"]
        updates["N8N_URL"] = f"http://localhost:{np}"
        updates["N8N_WEBHOOK_URL"] = f"http://localhost:{np}/webhook/"

    if not updates:
        return 0

    print("", flush=True)
    print("Ajustando .env para puertos libres…", flush=True)
    update_env_file(ENV_PATH, updates)
    print("  .env actualizado.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
