import json
import logging
import re
from datetime import datetime

import urllib.request
import urllib.error

from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_GET
from django_ratelimit.decorators import ratelimit

from site_config.models import SiteConfig

from .forms import ContactForm, PliegoDemoForm

logger = logging.getLogger(__name__)


def index(request, lang=None):
    """Landing page principal."""
    from html_translator.conf import get_default_language
    if lang and lang == get_default_language():
        return redirect('/', permanent=True)
    return render(request, 'landing/index.html', {
        'contact_form': ContactForm(),
        'pliego_demo_form': PliegoDemoForm(),
    })


@require_POST
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def contacto_submit(request):
    """
    Recibe el formulario (AJAX desde la landing).
    Guarda en DB + opcionalmente reenvía a un webhook n8n con shared secret.
    Rate-limited: 5 POSTs/hora por IP.
    """
    form = ContactForm(request.POST)
    if not form.is_valid():
        return JsonResponse({
            'ok': False,
            'errors': {k: [str(e) for e in v] for k, v in form.errors.items()},
        }, status=400)

    msg = form.save(commit=False)
    msg.meta_origen = request.POST.get('origen', '')[:120]
    msg.sitepage = getattr(request, 'sitepage', None)
    msg.save()

    # Reenvío a n8n con shared secret (si está configurado)
    webhook = getattr(settings, 'CONTACTO_WEBHOOK_URL', '')
    if webhook:
        page = getattr(request, 'sitepage', None)
        secret = page.contacto_webhook_secret if page else SiteConfig.load().contacto_webhook_secret
        headers = {'Content-Type': 'application/json'}
        if secret:
            headers['X-Webhook-Secret'] = secret
        else:
            logger.warning(
                'CONTACTO_WEBHOOK_URL configurado pero sin shared secret — '
                'webhook n8n queda sin autenticar.'
            )

        payload = json.dumps({
            'id':       msg.id,
            'nombre':   msg.nombre,
            'email':    msg.email,
            'empresa':  msg.empresa,
            'interes':  msg.interes,
            'interes_label': msg.get_interes_display(),
            'mensaje':  msg.mensaje,
            'origen':   msg.meta_origen,
            'creado_en': msg.creado_en.isoformat(),
        }).encode('utf-8')
        req = urllib.request.Request(webhook, data=payload, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                msg.enviado_n8n = 200 <= resp.status < 300
                msg.save(update_fields=['enviado_n8n'])
        except (urllib.error.URLError, TimeoutError) as e:
            logger.warning('Contacto: error reenviando a n8n: %s', e)

    return JsonResponse({'ok': True, 'id': msg.id})


# ═══════════════════════════════════════════════════════════════════════
# Lead magnet de pliegos (licitaciones)
# ═══════════════════════════════════════════════════════════════════════

def _pliego_post_email(request):
    """Key de ratelimit por email (case-insensitive). Fallback al IP."""
    email = (request.POST.get('email') or '').strip().lower()
    return email or request.META.get('REMOTE_ADDR', '') or 'unknown'


@require_POST
@ratelimit(key='ip', rate='3/h', method='POST', block=True)
@ratelimit(key=_pliego_post_email, rate='1/d', method='POST', block=True)
def pliego_demo_submit(request):
    """
    Recibe el form del lead magnet de pliegos.
    Guarda en DB + notifica por email + opcionalmente reenvía a webhook n8n.
    Rate limits: 3/h por IP, 1/d por email.
    """
    form = PliegoDemoForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({
            'ok': False,
            'errors': {k: [str(e) for e in v] for k, v in form.errors.items()},
        }, status=400)

    lead = form.save(commit=False)
    pdf = form.cleaned_data['pdf_original']
    lead.pdf_filename_original = pdf.name[:255]
    lead.pdf_size_bytes = pdf.size
    lead.meta_origen = request.POST.get('origen', '')[:120]
    lead.sitepage = getattr(request, 'sitepage', None)
    lead.save()

    # Notificar a sales — nunca debe bloquear la respuesta al usuario
    _notify_pliego_lead(lead)

    # Reenvío opcional a webhook n8n (solo metadata; el PDF queda en Django)
    webhook = getattr(settings, 'PLIEGO_DEMO_WEBHOOK_URL', '')
    if webhook:
        _forward_pliego_to_n8n(lead, webhook)

    return JsonResponse({'ok': True, 'id': lead.id})


def _notify_pliego_lead(lead):
    """Email de notificación a sales. Fallbacks defensivos — nunca explota."""
    try:
        site = SiteConfig.load()
        page = lead.sitepage
        to_email = getattr(settings, 'LEADS_NOTIFY_EMAIL', '') or (page.email if page else '') or site.email
        if not to_email:
            logger.info('PliegoDemoLead #%s guardado sin destino de notificación', lead.id)
            return
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', to_email)
        subject = f'[Pliego-demo] {lead.empresa or lead.nombre} — nuevo lead'
        body = (
            f'Nuevo lead del magnet de licitaciones:\n\n'
            f'  Nombre:   {lead.nombre}\n'
            f'  Email:    {lead.email}\n'
            f'  Empresa:  {lead.empresa}\n'
            f'  Teléfono: {lead.telefono or "—"}\n'
            f'  Origen:   {lead.meta_origen or "—"}\n\n'
            f'  PDF:      {lead.pdf_filename_original} ({lead.pdf_size_bytes} bytes)\n'
            f'  Storage:  {lead.pdf_original.name}\n\n'
            f'Revisá en admin: /admin/landing/pliegodemolead/{lead.id}/change/\n'
        )
        send_mail(subject, body, from_email, [to_email], fail_silently=True)
    except Exception as e:  # nunca bloquear al usuario por un fallo de email
        logger.warning('PliegoDemoLead: error notificando a sales: %s', e)


def _forward_pliego_to_n8n(lead, webhook):
    """POST JSON con metadata del lead. n8n puede pedir el archivo aparte."""
    page = lead.sitepage
    secret = page.pliego_demo_webhook_secret if page else SiteConfig.load().pliego_demo_webhook_secret
    headers = {'Content-Type': 'application/json'}
    if secret:
        headers['X-Webhook-Secret'] = secret
    else:
        logger.warning(
            'PLIEGO_DEMO_WEBHOOK_URL configurado pero sin shared secret — '
            'webhook n8n queda sin autenticar.'
        )

    payload = json.dumps({
        'id': lead.id,
        'nombre': lead.nombre,
        'email': lead.email,
        'empresa': lead.empresa,
        'telefono': lead.telefono,
        'origen': lead.meta_origen,
        'creado_en': lead.creado_en.isoformat(),
        'pdf': {
            'filename_original': lead.pdf_filename_original,
            'size_bytes': lead.pdf_size_bytes,
            'storage_path': lead.pdf_original.name,
        },
    }).encode('utf-8')
    req = urllib.request.Request(webhook, data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            lead.enviado_n8n = 200 <= resp.status < 300
            lead.save(update_fields=['enviado_n8n'])
    except (urllib.error.URLError, TimeoutError) as e:
        logger.warning('PliegoDemoLead: error reenviando a n8n: %s', e)


# ═══════════════════════════════════════════════════════════════════════
# Health checks — split live/ready
# ═══════════════════════════════════════════════════════════════════════

@require_GET
def health_live(request):
    """
    Liveness probe: Django está up y responde.
    Usado por Docker restart policy. No toca DB ni disco.
    """
    return HttpResponse('OK\n', content_type='text/plain', status=200)


@require_GET
def health_ready(request):
    """
    Readiness probe: Django + DB + MEDIA + n8n reachable.
    Usado por UptimeRobot / load balancer / deploy canary.
    Retorna 200 solo si TODO responde.
    """
    import os
    import socket
    from urllib.parse import urlparse

    checks = {}
    failed = False

    # DB: SiteConfig.load() pega a la DB (singleton get_or_create)
    try:
        SiteConfig.load()
        checks['db'] = 'ok'
    except Exception as e:
        checks['db'] = f'fail: {type(e).__name__}'
        failed = True

    # MEDIA: directorio existe y es writable
    try:
        media_root = settings.MEDIA_ROOT
        if os.path.isdir(media_root) and os.access(media_root, os.R_OK):
            checks['media'] = 'ok'
        else:
            checks['media'] = 'fail: not readable'
            failed = True
    except Exception as e:
        checks['media'] = f'fail: {type(e).__name__}'
        failed = True

    # Webhook de contacto: si está configurado, DNS+TCP reachable
    try:
        webhook = getattr(settings, 'CONTACTO_WEBHOOK_URL', '')
        if webhook:
            parsed = urlparse(webhook)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            with socket.create_connection((host, port), timeout=2):
                checks['webhook'] = 'ok'
        else:
            checks['webhook'] = 'skipped (no webhook configured)'
    except (socket.gaierror, socket.timeout, OSError) as e:
        checks['webhook'] = f'fail: {type(e).__name__}'
        # No se marca como failed — el webhook es opcional

    return JsonResponse({
        'status': 'ready' if not failed else 'not_ready',
        'checks': checks,
    }, status=200 if not failed else 503)


@require_GET
def letter_preview(request):
    """Preview visual de todos los paths de letras/números desde letter_paths.py."""
    from .morph_banner.letter_paths import LETTER_PATHS, LETTER_HEIGHT

    def item_data(char):
        d = LETTER_PATHS[char]
        outer = d['outer_path']
        n_subs_outer = len(re.findall(r'M ', outer))
        outer_pts = len(re.findall(r'[ML]', outer))
        pts = outer_pts + len(re.findall(r'[ML]', d['counter_path']))
        w = d['width']
        vb = f"0 0 {w:.3f} {LETTER_HEIGHT:.5f}"
        is_keyhole = (not d['has_counter']) and n_subs_outer == 1 and outer_pts > 75
        return {
            'char': char,
            'outer_path': outer,
            'vb': vb,
            'pts': pts,
            'keyhole': is_keyhole,
            'two_sub': n_subs_outer > 1,
        }

    nums   = [c for c in '0123456789' if c in LETTER_PATHS]
    uppers = [c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if c in LETTER_PATHS]
    lowers = [c for c in 'abcdefghijklmnopqrstuvwxyz' if c in LETTER_PATHS]

    sections = [
        ('Números (0–9)',   [item_data(c) for c in nums]),
        ('Mayúsculas (A–Z)', [item_data(c) for c in uppers]),
        ('Minúsculas (a–z)', [item_data(c) for c in lowers]),
    ]

    return render(request, 'morph_banner/letter_preview.html', {
        'sections': sections,
        'total': len(nums) + len(uppers) + len(lowers),
        'now': datetime.now().strftime('%Y-%m-%d %H:%M'),
    })
