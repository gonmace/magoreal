# Forzar bash como shell (necesario en Windows con Git Bash)
SHELL := bash
.SHELLFLAGS := -c

# ── Configuración inicial ──────────────────────────────────────────────────────
setup:
	bash setup.sh

# ── Docker de desarrollo (Redis + PostgreSQL + n8n opcionales) ─────────────────
ifeq ($(OS),Windows_NT)
    CURRENT_UID := 1000
    CURRENT_GID := 1000
else
    CURRENT_UID := $(shell id -u)
    CURRENT_GID := $(shell id -g)
endif

dev-up:
	bash docker/dev-up.sh

dev-down:
	docker compose -f docker-compose.dev.yml down

# Borra el volumen de datos de PostgreSQL de dev. Úsalo si POSTGRES_PASSWORD
# del .env no coincide con la clave creada la primera vez (el contenedor ignora
# POSTGRES_PASSWORD si el directorio de datos ya existía).
dev-db-reset:
	@echo "Parando contenedores y eliminando volumen de Postgres de dev (pierde datos de esa BD)…"
	docker compose -f docker-compose.dev.yml down -v
	@echo "Listo. Ejecuta: make dev-up"

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

dev-check:
	@python docker/dev_check.py

# ── n8n ───────────────────────────────────────────────────────────────────────
n8n-export:
	bash docker/n8n-export.sh

# Actualizar n8n: pull nueva imagen + restart del contenedor
# Los datos (workflows, credenciales) se preservan en el volumen ./volumes/n8n
n8n-update:
	@[ -f .env ] || { echo "Error: .env no encontrado."; exit 1; }
	@set -a && . <(sed 's/\r//' .env) && set +a; \
	[ -n "$${N8N_DOMAIN}" ] || { echo "Error: N8N_DOMAIN no definido en .env"; exit 1; }; \
	echo "▶ Descargando nueva imagen de n8n..."; \
	docker build -t $${PROJECT_NAME}_n8n:latest -f docker/n8n.Dockerfile .; \
	echo "▶ Reiniciando contenedor n8n..."; \
	docker compose --profile n8n up -d --no-deps n8n; \
	echo "✓ n8n actualizado."

# ── Django local ──────────────────────────────────────────────────────────────
install:
	pip install -r requirements-dev.txt
	python manage.py tailwind install
	@echo ""
	@python -c "import os; (not os.path.isfile('.env')) and print('  Siguiente paso: ejecuta make setup para generar el .env')"

# Desarrollo en el host (Django + Tailwind + browser-reload).
#   Opción A (Readme): solo SQLite, sin Docker →  make dev
#   Opción B (Readme): tras make dev-up      →  make dev-serve
# Implementación en Python (docker/run_dev_serve.py): en Windows, `tailwind &` en el Makefile
# no hace background con cmd.exe y runserver no arrancaba.
dev dev-serve:
	python docker/run_dev_serve.py

tailwind:
	python manage.py tailwind start

# ── Comandos Django (dev: directo | prod: dentro del container) ───────────────
MANAGE := $(shell bash -c '[ -f .env ] && . ./.env && [ "$${DEBUG}" = "False" ] && echo "docker compose exec django python manage.py" || echo "python manage.py"')

migrate:
	$(MANAGE) migrate

migrations:
	$(MANAGE) makemigrations

shell:
	$(MANAGE) shell

superuser:
	$(MANAGE) createsuperuser

collect:
	$(MANAGE) collectstatic --noinput

# ── Base de datos (dev) ────────────────────────────────────────────────────────
db-shell:
	@[ -f .env ] && . ./.env; \
	if [ -n "$${POSTGRES_DB}" ]; then \
		docker compose -f docker-compose.dev.yml exec postgres psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}; \
	else \
		echo "Modo SQLite — usa: sqlite3 db.sqlite3"; \
	fi

db-reset:
	@[ -f db.sqlite3 ] && rm db.sqlite3 && echo "SQLite eliminado." || true
	python manage.py migrate

# ── Producción ────────────────────────────────────────────────────────────────
deploy:
	bash deploy.sh

nginx:
	bash nginx-deploy.sh

check-ports:
	python docker/ensure_dev_ports.py --check

screenshots-normalize:
	python scripts/normalize_project_screenshots.py --slug 02-generador-documentos-ia --apply

# Morph banner: regenerar letter_paths desde una fuente (ejecutar en landing/)
# FONT default: Quadrillion junto al morph_banner (nombre con espacio escapado)
FONT ?= landing/morph_banner/Quadrillion\ Sb.otf

morph-banner-font:
	@PYTHONIOENCODING=utf-8 python scripts/font_pipeline.py --font "$(FONT)"

morph-banner-font-post:
	@PYTHONIOENCODING=utf-8 python scripts/font_pipeline.py --post-only --font "$(FONT)"

logs:
	docker compose logs -f django

down:
	docker compose down

.PHONY: setup dev-up dev-down dev-db-reset dev-logs dev-check n8n-export n8n-update install dev dev-serve tailwind \
        migrate migrations shell superuser collect db-shell db-reset \
        deploy nginx check-ports screenshots-normalize morph-banner-font morph-banner-font-post logs down
