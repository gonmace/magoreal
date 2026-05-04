#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

[ -f .env ] || { echo "Error: .env no encontrado. Ejecuta 'make setup' primero."; exit 1; }

# Comprobar 127.0.0.1: si un puerto del .env está ocupado, asigna el siguiente libre
# (PostgreSQL, Redis, app, n8n) y reescribe .env antes de levantar contenedores.
if command -v python3 &>/dev/null; then
  python3 docker/ensure_dev_ports.py
elif command -v python &>/dev/null; then
  python docker/ensure_dev_ports.py
else
  echo "Advertencia: no hay python en PATH; omite ajuste automático de puertos."
fi

set -a
# shellcheck disable=SC1091
. <(sed 's/\r//' .env)
set +a

PROFILES="--profile postgres"
if [ -n "${N8N_DOMAIN:-}" ]; then
    PROFILES="$PROFILES --profile n8n"
    mkdir -p volumes/n8n
fi
if [ "${N8N_MCP_ENABLED:-}" = "true" ] && [ -n "${N8N_DOMAIN:-}" ]; then
    PROFILES="$PROFILES --profile n8n-mcp"
fi

DOCKER_UID=$(id -u 2>/dev/null || echo 1000)
DOCKER_GID=$(id -g 2>/dev/null || echo 1000)

env UID=$DOCKER_UID GID=$DOCKER_GID docker compose -f docker-compose.dev.yml $PROFILES up -d
