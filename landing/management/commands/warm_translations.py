"""
python manage.py warm_translations [--langs en pt] [--clear] [--pages home portfolio-*]

Traduce todas las páginas del sitio a los idiomas indicados usando el sistema
html_translator. Limpia el caché previo y espera a que cada traducción complete
antes de pasar a la siguiente.

Uso típico post-deploy:
    python manage.py warm_translations
    python manage.py warm_translations --langs en pt fr
    python manage.py warm_translations --clear --langs en
"""
import sys
import time
import logging
import threading

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import RequestFactory

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Traduce todas las páginas del sitio a los idiomas indicados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--langs',
            nargs='+',
            default=['en', 'pt'],
            metavar='LANG',
            help='Idiomas a traducir (default: en pt). Skippea los ya traducidos.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            default=False,
            help='Limpiar caché y TranslationCache antes de traducir',
        )
        parser.add_argument(
            '--pages',
            nargs='+',
            default=None,
            metavar='PAGE_KEY',
            help='Páginas específicas a traducir (default: home + todos los proyectos)',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Segundos máximos por página/idioma (default: 300)',
        )

    def handle(self, *args, **options):
        from django.core.cache import cache
        from html_translator.models import TranslationCache
        from html_translator.views import _render_for_page
        from html_translator.translator import translate_page

        langs = options['langs']
        timeout = options['timeout']

        ok = self.style.SUCCESS
        warn = self.style.WARNING
        err = self.style.ERROR

        # ── 1. Limpiar caché ──────────────────────────────────────────────────
        if options['clear']:
            self.stdout.write('Limpiando caché...')
            try:
                # Redis keys de traducción
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern('tr_*')
                else:
                    for lang in langs:
                        cache.delete(f'tr_fresh:home:{lang}')
                        cache.delete(f'tr_pending:home:{lang}')
                # Resetear contenido de todas las traducciones
                deleted = TranslationCache.objects.all().update(content={})
                self.stdout.write(ok(f'  Cache limpiada — {deleted} entradas reseteadas'))
            except Exception as e:
                self.stdout.write(warn(f'  Advertencia al limpiar caché: {e}'))

        # ── 2. Descubrir páginas ──────────────────────────────────────────────
        if options['pages']:
            page_keys = options['pages']
        else:
            page_keys = ['home']
            try:
                from django.conf import settings as s
                from portfolio.loaders import load_proyectos
                from pathlib import Path
                proyectos_dir = Path(s.BASE_DIR) / 'proyectos'
                proyectos = load_proyectos(proyectos_dir)
                for p in proyectos:
                    page_keys.append(f"portfolio-{p['slug']}")
                self.stdout.write(f'Páginas encontradas: {len(page_keys)} ({len(proyectos)} proyectos)')
            except Exception as e:
                self.stdout.write(warn(f'  No se pudieron cargar proyectos: {e}'))

        self.stdout.write(f'Idiomas: {", ".join(langs)}')
        self.stdout.write('')

        # ── 3. Traducir cada página × idioma ─────────────────────────────────
        # Usar el dominio real para que request.get_host() pase ALLOWED_HOSTS
        import os
        domain = (
            os.environ.get('DOMAIN')
            or next((h for h in settings.ALLOWED_HOSTS
                     if h and not h.startswith('.') and h not in ('*', 'localhost', '127.0.0.1')),
                    None)
            or settings.ALLOWED_HOSTS[0]
            if settings.ALLOWED_HOSTS else 'localhost'
        )
        factory = RequestFactory(SERVER_NAME=domain, HTTP_HOST=domain)
        total = len(page_keys) * len(langs)
        done = 0
        failed = 0

        for page_key in page_keys:
            for lang in langs:
                done += 1
                prefix = f'[{done}/{total}] {page_key} → {lang.upper()}'
                self.stdout.write(f'{prefix}  ', ending='')
                self.stdout.flush()

                try:
                    # Construir request para renderizar secciones y calcular hash actual
                    lang_prefix = f'/{lang}/' if lang != 'es' else '/'
                    request = factory.get(lang_prefix)
                    request.LANGUAGE_CODE = lang
                    request.sitepage = None

                    # Renderizar secciones
                    sections_html, sections_texts, source_hash = _render_for_page(request, page_key)

                    if not sections_html:
                        self.stdout.write(warn('sin secciones — omitido'))
                        continue

                    # Verificar en DB si ya está traducido y el contenido no está desactualizado
                    try:
                        tc_existing = TranslationCache.objects.get(page_key=page_key, lang=lang)
                        if tc_existing.content and not tc_existing.is_stale(source_hash):
                            self.stdout.write(ok('ya traducido ✓'))
                            continue
                    except TranslationCache.DoesNotExist:
                        pass

                    # Guardar/actualizar TranslationCache
                    tc, _ = TranslationCache.objects.get_or_create(
                        page_key=page_key,
                        lang=lang,
                        defaults={
                            'source_html': sections_html,
                            'source_hash': source_hash,
                            'content': {},
                        },
                    )
                    tc.source_html = sections_html
                    tc.source_hash = source_hash
                    tc.save(update_fields=['source_html', 'source_hash', 'updated_at'])

                    # Traducir en este thread (síncrono — esperamos el resultado)
                    result = {'ok': False, 'error': None}

                    def _run():
                        try:
                            translate_page(page_key, lang, sections_html, sections_texts)
                            result['ok'] = True
                        except Exception as ex:
                            result['error'] = str(ex)

                    t = threading.Thread(target=_run, daemon=True)
                    t.start()

                    # Esperar con progress dots
                    elapsed = 0
                    interval = 5
                    while t.is_alive() and elapsed < timeout:
                        time.sleep(interval)
                        elapsed += interval
                        self.stdout.write('.', ending='')
                        self.stdout.flush()

                    if t.is_alive():
                        self.stdout.write(err(f' TIMEOUT ({timeout}s)'))
                        failed += 1
                        continue

                    # Verificar resultado
                    try:
                        tc.refresh_from_db()
                        if tc.content:
                            count = len(tc.content)
                            self.stdout.write(ok(f' OK ({count} secciones, {elapsed}s)'))
                        else:
                            self.stdout.write(warn(f' sin contenido tras {elapsed}s'))
                            failed += 1
                    except Exception:
                        if result['ok']:
                            self.stdout.write(ok(f' OK ({elapsed}s)'))
                        else:
                            self.stdout.write(err(f' FALLO: {result["error"]}'))
                            failed += 1

                except Exception as e:
                    self.stdout.write(err(f'ERROR: {e}'))
                    failed += 1
                    logger.exception('warm_translations: %s/%s', page_key, lang)

        # ── 4. Resumen ────────────────────────────────────────────────────────
        self.stdout.write('')
        succeeded = total - failed
        if failed == 0:
            self.stdout.write(ok(f'✓ Completado: {succeeded}/{total} páginas traducidas'))
        else:
            self.stdout.write(warn(f'Completado con errores: {succeeded}/{total} OK, {failed} fallidas'))
            sys.exit(1)
