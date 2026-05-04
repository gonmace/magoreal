#!/usr/bin/env bash
# Comprueba que los puertos de desarrollo estén libres (127.0.0.1).
# Misma lógica que al inicio de `make dev-up`; ver docker/ensure_dev_ports.py
set -e
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f .env ]; then
    echo "Error: no se encontró el archivo .env"
    exit 1
fi
if command -v python3 &>/dev/null; then
  python3 docker/ensure_dev_ports.py --check
else
  python docker/ensure_dev_ports.py --check
fi
