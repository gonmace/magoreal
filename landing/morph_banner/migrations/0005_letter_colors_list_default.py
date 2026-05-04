# Generated manually: letter_colors lista por glifo morph + datos legacy dict -> list

from django.db import migrations, models


def letter_colors_default_empty():
    return []


def forwards_dict_to_list(apps, schema_editor):
    MorphBanner = apps.get_model('morph_banner', 'MorphBanner')
    try:
        from landing.morph_banner.letter_paths import LETTER_PATHS
    except ImportError:
        LETTER_PATHS = {}

    for row in MorphBanner.objects.all():
        lc = row.letter_colors

        if isinstance(lc, list):
            continue

        word = row.word or ''
        glyph_chars = [c for c in word if c in LETTER_PATHS]

        if not isinstance(lc, dict):
            row.letter_colors = []
            row.save(update_fields=['letter_colors'])
            continue

        if not lc:
            row.letter_colors = []
            row.save(update_fields=['letter_colors'])
            continue

        new_list = []
        for ch in glyph_chars:
            if ch.isdigit():
                cv = lc.get(ch)
            else:
                cv = lc.get(ch.upper())
                if cv is None:
                    cv = lc.get(ch.lower())
            if isinstance(cv, str) and cv:
                new_list.append(cv)
            else:
                new_list.append('primary')
        row.letter_colors = new_list
        row.save(update_fields=['letter_colors'])


def backwards_nop(apps, schema_editor):
    """Revertir sólo AlterField no es lossless; datos list se conservan en DB."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('morph_banner', '0004_letter_colors_verbose_character'),
    ]

    operations = [
        migrations.RunPython(forwards_dict_to_list, backwards_nop),
        migrations.AlterField(
            model_name='morphbanner',
            name='letter_colors',
            field=models.JSONField(
                blank=True,
                default=letter_colors_default_empty,
                verbose_name='Colores por posición',
                help_text='Lista JSON ordenada por cada glifo renderizado en la palabra (espacios y símbolos sin '
                          'fuente morph se omiten): ["primary","accent","#3366CC", …]. Índice 0 = primera letra '
                          'visible, etc.; dos letras repetidas pueden tener dos colores distintos. Formatos legacy '
                          'tipo {"M":"accent"} pueden migrarse desde admin. '
                          'Valores: paleta (primary…) o hex #RRGGBB.',
            ),
        ),
    ]
