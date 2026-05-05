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
import os
def substitute(content, replacements):
    for key, value in replacements.items():
        content = content.replace('{{' + key + '}}', value)
    return content

# Get bash variables
project_name = os.environ.get('PROJECT_NAME', '')
domain = os.environ.get('DOMAIN', '')
app_port = os.environ.get('APP_PORT', '8000')
project_dir = os.environ.get('PROJECT_DIR', '')
sitepage_domains_str = os.environ.get('SITEPAGE_DOMAINS', '')

# Generate main domain config
with open('nginx.conf') as f:
    main_config = substitute(f.read(), {
        'DOMAIN': domain,
        'APP_PORT': app_port,
        'PROJECT_DIR': project_dir,
    })
main_filename = f"{project_name}.conf"
with open(main_filename, 'w') as f:
    f.write(main_config)
print(f"  Generated {main_filename}")

# Generate SitePage configs
sitepage_domains = [d.strip() for d in sitepage_domains_str.split(',') if d.strip()]
for sp_domain in sitepage_domains:
    with open('nginx-sitepage.conf') as f:
        sp_config = substitute(f.read(), {
            'SITEPAGE_DOMAIN': sp_domain,
            'APP_PORT': app_port,
            'PROJECT_DIR': project_dir,
        })
    sp_filename = f"{project_name}-{sp_domain}.conf".replace('.', '-')
    with open(sp_filename, 'w') as f:
        f.write(sp_config)
    print(f"  Generated {sp_filename}")

PYEOF

echo "▶ Instalando en nginx..."
# Remove old symlinks
sudo rm -f /etc/nginx/sites-enabled/${PROJECT_NAME}.conf
sudo rm -f /etc/nginx/sites-enabled/${PROJECT_NAME}-*.conf

# Copy main config
sudo cp ${PROJECT_NAME}.conf /etc/nginx/sites-available/${PROJECT_NAME}.conf
sudo ln -s /etc/nginx/sites-available/${PROJECT_NAME}.conf /etc/nginx/sites-enabled/${PROJECT_NAME}.conf

# Copy SitePage configs
for sp_domain in $(echo ${SITEPAGE_DOMAINS} | tr ',' ' '); do
    sp_domain=$(echo $sp_domain | xargs)
    if [ -n "$sp_domain" ]; then
        sp_filename="${PROJECT_NAME}-${sp_domain}.conf"
        # Replace dots with dashes in filename
        sp_filename=$(echo $sp_filename | tr '.' '-')
        sudo cp $sp_filename /etc/nginx/sites-available/$sp_filename
        sudo ln -s /etc/nginx/sites-available/$sp_filename /etc/nginx/sites-enabled/$sp_filename
    fi
done

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
