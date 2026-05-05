#!/bin/bash
# nginx-deploy.sh — instala la config de nginx
# IMPORTANTE: ejecutar solo una vez (primer deploy).
#             NO ejecutar tras certbot — sobreescribirlo eliminaría los certificados.

set -e

if [ ! -f .env ]; then
    echo "Error: no se encontró .env. Ejecuta: bash setup.sh"
    exit 1
fi
set -a
source .env
set +a

PROJECT_NAME=${PROJECT_NAME:?PROJECT_NAME no está definida en .env}
APP_PORT=${APP_PORT:-8000}
DOMAIN=${DOMAIN:?DOMAIN no está definida en .env}
PROJECT_DIR=$(pwd)
SITEPAGE_DOMAINS=${SITEPAGE_DOMAINS:-}

NGINX_OUT="${PROJECT_NAME}.conf"
NGINX_AVAILABLE="/etc/nginx/sites-available/${PROJECT_NAME}.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/${PROJECT_NAME}.conf"

echo "▶ Generando ${NGINX_OUT}..."

python3 - << PYEOF
def substitute(content, replacements):
    for key, value in replacements.items():
        content = content.replace('{{' + key + '}}', value)
    return content

with open('nginx.conf') as f:
    output = substitute(f.read(), {
        'DOMAIN': '${DOMAIN}',
        'APP_PORT': '${APP_PORT}',
        'PROJECT_DIR': '${PROJECT_DIR}',
    })

sitepage_template = """
# --- SitePage: {{SITEPAGE_DOMAIN}} ---
server {
    listen 80;
    server_name {{SITEPAGE_DOMAIN}};

    client_max_body_size 20M;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss image/svg+xml;

    location /static/ {
        alias {{PROJECT_DIR}}/staticfiles/;
        expires 365d;
        add_header Cache-Control "public, immutable";
        gzip_static on;
    }

    location /media/proyectos/ {
        alias {{PROJECT_DIR}}/proyectos/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias {{PROJECT_DIR}}/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:{{APP_PORT}};
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
"""

sitepage_blocks = ''
sitepage_domains = [d.strip() for d in '${SITEPAGE_DOMAINS}'.split(',') if d.strip()]
for sp_domain in sitepage_domains:
    sitepage_blocks += substitute(sitepage_template, {
        'SITEPAGE_DOMAIN': sp_domain,
        'APP_PORT': '${APP_PORT}',
        'PROJECT_DIR': '${PROJECT_DIR}',
    })

# Replace placeholder with generated blocks (or empty)
output = output.replace('{{SITEPAGE_BLOCKS}}', sitepage_blocks)

with open('${NGINX_OUT}', 'w') as f:
    f.write(output)

print("  Config generada correctamente.")
PYEOF

echo "▶ Instalando en nginx..."
sudo cp "${NGINX_OUT}" "${NGINX_AVAILABLE}"

if [ ! -L "${NGINX_ENABLED}" ]; then
    sudo ln -s "${NGINX_AVAILABLE}" "${NGINX_ENABLED}"
    echo "  Symlink creado: ${NGINX_ENABLED}"
fi

sudo nginx -t
sudo systemctl reload nginx
echo "✓ nginx recargado."
echo ""
echo "Próximo paso — certificado SSL:"
CERTBOT_CMD="sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
IFS=',' read -ra _SP_ARRAY <<< "${SITEPAGE_DOMAINS}"
for _sp in "${_SP_ARRAY[@]}"; do
    _sp="${_sp// /}"
    [ -n "${_sp}" ] && CERTBOT_CMD="${CERTBOT_CMD} -d ${_sp}"
done
echo "  ${CERTBOT_CMD}"
