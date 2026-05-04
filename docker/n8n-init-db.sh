#!/bin/sh
# Crea la base "n8n" si no existe. Necesario cuando el volumen de Postgres se creó
# antes de añadir init-db.sql. Fallos habituales: CRLF en .env (Windows) o
# credenciales del .env que no coinciden con el usuario ya creado en el volumen.
set -e

# Quitar \r (CRLF) — típico con .env creado en Windows
POSTGRES_USER=$(printf %s "$POSTGRES_USER" | tr -d '\r')
export POSTGRES_USER
# psql usa PGPASSWORD; el .env define POSTGRES_PASSWORD (no expandir en compose.yml)
PW=$(printf %s "${POSTGRES_PASSWORD:-}" | tr -d '\r')
export PGPASSWORD="$PW"

if [ -z "$POSTGRES_USER" ] || [ -z "$PGPASSWORD" ]; then
  echo "n8n-db-init: POSTGRES_USER o POSTGRES_PASSWORD vacío (revisa .env)" >&2
  exit 1
fi

if ! psql -h postgres -U "$POSTGRES_USER" -d postgres -c "SELECT 1" >/dev/null 2>&1; then
  psql -h postgres -U "$POSTGRES_USER" -d postgres -c "SELECT 1" 2>&1 || true
  echo "n8n-db-init: conexión a postgres falló (p. ej. FATAL: password authentication failed)." >&2
  echo "En Docker, POSTGRES_PASSWORD del .env solo se aplica el PRIMER arranque con volumen" >&2
  echo "nuevo. Si luego cambiaste el .env, la clave dentro del volumen es la antigua." >&2
  echo "Solución:  make dev-db-reset   luego  make dev-up" >&2
  echo "  (borra el volumen de datos de dev; asegúrate de tener copia de lo que importe)" >&2
  exit 2
fi

n=$(psql -h postgres -U "$POSTGRES_USER" -d postgres -tAc "SELECT count(*)::text FROM pg_database WHERE datname = 'n8n'")
n=$(printf %s "$n" | tr -d ' \n\r')

if [ "$n" = "1" ]; then
  echo "n8n: base de datos ya existe"
  exit 0
fi

psql -h postgres -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE n8n"
echo "n8n: base de datos creada"
