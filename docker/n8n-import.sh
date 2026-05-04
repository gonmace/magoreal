#!/bin/bash
# Importa todos los workflows del repositorio a n8n dev.
# Uso: bash docker/n8n-import.sh

set -e

IMPORT_DIR="./n8n/workflows"

if [ ! -d "$IMPORT_DIR" ]; then
  echo "✗ Directorio $IMPORT_DIR no encontrado"
  exit 1
fi

echo "▶ Copiando workflows a n8n..."
docker compose -f docker-compose.dev.yml cp \
    "$IMPORT_DIR/." n8n:/home/node/.n8n/imports/

echo "▶ Importando workflows..."
docker compose -f docker-compose.dev.yml exec n8n \
    bash -c 'for f in /home/node/.n8n/imports/*.json; do echo "  → $f"; n8n import:workflow --input="$f"; done'

echo "✓ Workflows importados. Reinicia n8n si los cambios no se reflejan."
