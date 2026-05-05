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

sitepage_domains = [d.strip() for d in '${SITEPAGE_DOMAINS}'.split(',') if d.strip()]
for sp_domain in sitepage_domains:
    with open('nginx-sitepage.conf') as f:
        output += substitute(f.read(), {
            'SITEPAGE_DOMAIN': sp_domain,
            'APP_PORT': '${APP_PORT}',
            'PROJECT_DIR': '${PROJECT_DIR}',
        })

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
