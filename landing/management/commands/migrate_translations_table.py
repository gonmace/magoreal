"""
python manage.py migrate_translations_table

Migración única: mueve los datos de translations_translationcache
a html_translator_translationcache tras cambiar al app html_translator.

Ejecutar UNA sola vez, después de instalar django-html-translator
y antes (o después) de correr 'python manage.py migrate html_translator'.

Opciones:
  --drop-old   Elimina la tabla antigua después de copiar los datos.
               Por defecto solo copia, no borra.
"""
from django.core.management.base import BaseCommand
from django.db import connection


OLD_TABLE = 'translations_translationcache'
NEW_TABLE = 'html_translator_translationcache'


def table_exists(cursor, name: str) -> bool:
    vendor = connection.vendor
    if vendor == 'postgresql':
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
            [name],
        )
        return cursor.fetchone()[0]
    else:  # sqlite
        cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            [name],
        )
        return cursor.fetchone()[0] > 0


class Command(BaseCommand):
    help = 'Migra datos de translations_translationcache a html_translator_translationcache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--drop-old',
            action='store_true',
            help='Elimina la tabla antigua tras copiar los datos',
        )

    def handle(self, *args, **options):
        ok = self.style.SUCCESS
        warn = self.style.WARNING
        fail = self.style.ERROR

        with connection.cursor() as cursor:
            old_exists = table_exists(cursor, OLD_TABLE)
            new_exists = table_exists(cursor, NEW_TABLE)

            if not old_exists:
                self.stdout.write(warn(f'La tabla {OLD_TABLE} no existe — nada que migrar.'))
                return

            if not new_exists:
                self.stdout.write(fail(
                    f'La tabla {NEW_TABLE} no existe todavía.\n'
                    'Ejecuta primero: python manage.py migrate html_translator'
                ))
                return

            # Contar registros en tabla antigua
            cursor.execute(f'SELECT COUNT(*) FROM {OLD_TABLE}')
            old_count = cursor.fetchone()[0]

            if old_count == 0:
                self.stdout.write(warn(f'{OLD_TABLE} está vacía — nada que copiar.'))
            else:
                # Copiar datos (INSERT OR IGNORE para no duplicar si ya se copió antes)
                if connection.vendor == 'postgresql':
                    cursor.execute(f"""
                        INSERT INTO {NEW_TABLE}
                            (page_key, lang, content, source_html, source_hash, updated_at)
                        SELECT page_key, lang, content, source_html, source_hash, updated_at
                        FROM {OLD_TABLE}
                        ON CONFLICT (page_key, lang) DO NOTHING
                    """)
                else:  # sqlite
                    cursor.execute(f"""
                        INSERT OR IGNORE INTO {NEW_TABLE}
                            (page_key, lang, content, source_html, source_hash, updated_at)
                        SELECT page_key, lang, content, source_html, source_hash, updated_at
                        FROM {OLD_TABLE}
                    """)

                cursor.execute(f'SELECT COUNT(*) FROM {NEW_TABLE}')
                new_count = cursor.fetchone()[0]
                self.stdout.write(ok(
                    f'Copiados {old_count} registro(s) de {OLD_TABLE} a {NEW_TABLE} '
                    f'(total en nueva: {new_count})'
                ))

            if options['drop_old']:
                cursor.execute(f'DROP TABLE {OLD_TABLE}')
                self.stdout.write(ok(f'Tabla {OLD_TABLE} eliminada.'))
            else:
                self.stdout.write(self.style.NOTICE(
                    f'La tabla {OLD_TABLE} aún existe. '
                    'Usa --drop-old para eliminarla cuando confirmes que todo funciona.'
                ))

        self.stdout.write(ok('Migración completada.'))
