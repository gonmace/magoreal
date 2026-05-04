"""Django Admin configuration for MorphBanner."""

from django import forms
from django.contrib import admin

from landing.morph_banner.constants import COLOR_PALETTE, HEX_COLOR_PATTERN
from landing.morph_banner.letter_paths import LETTER_PATHS
from landing.morph_banner.models import MorphBanner
from landing.morph_banner.widgets import LetterColorsWidget

_PALETTE_LIST = ", ".join(sorted(COLOR_PALETTE))


class MorphBannerAdminForm(forms.ModelForm):
    """Validación para letter_colors como lista ordenada por glifo o objeto legacy."""

    class Meta:
        model = MorphBanner
        fields = "__all__"
        widgets = {
            "letter_colors": LetterColorsWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        word = cleaned_data.get("word")
        letter_colors = cleaned_data.get("letter_colors")
        if word is None or letter_colors is None:
            return cleaned_data
        if not isinstance(letter_colors, list):
            return cleaned_data

        glyphs = [c for c in word if c in LETTER_PATHS]
        expected = len(glyphs)
        actual = len(letter_colors)
        if actual != expected:
            raise forms.ValidationError(
                {
                    "letter_colors": forms.ValidationError(
                        f'La lista debe tener exactamente {expected} entrada(s), una por cada glifo morph '
                        f'en la palabra ({actual} recibida(s)). Solo cuentan caracteres con path definido.',
                        code="letter_colors_bad_length",
                    )
                }
            )

        return cleaned_data

    def clean_letter_colors(self):
        value = self.cleaned_data.get("letter_colors")

        palette_names = set(COLOR_PALETTE)

        if value is None:
            raise forms.ValidationError(
                "letter_colors debe ser lista o objeto.", code="letter_colors_bad_type"
            )

        if isinstance(value, list):
            for i, item in enumerate(value):
                pos = i + 1
                if item is None or item == "":
                    continue
                if not isinstance(item, str):
                    raise forms.ValidationError(
                        f"Posición {pos}: debe ser string (nombre paleta o #RRGGBB).",
                        code="letter_colors_bad_item_type",
                    )
                if item in palette_names:
                    continue
                if HEX_COLOR_PATTERN.match(item):
                    continue
                raise forms.ValidationError(
                    (
                        f"Posición {pos}: valor inválido {item!r}. "
                        f"Use un nombre de paleta ({_PALETTE_LIST}) o un hex #RRGGBB."
                    ),
                    code="letter_colors_bad_item",
                )
            return value

        if isinstance(value, dict):
            for char, color in value.items():
                if not isinstance(char, str) or len(char) != 1:
                    raise forms.ValidationError(
                        (
                            'Formato objeto legacy: cada clave debe ser un único carácter (clave inválida: '
                            f"{char!r})."
                        ),
                        code="legacy_key_invalid",
                    )
                if len(char.encode("utf-8")) != 1:
                    raise forms.ValidationError(
                        "Formato objeto legacy: use un solo carácter ASCII como clave.",
                        code="legacy_key_non_ascii",
                    )
                if color in palette_names:
                    continue
                if isinstance(color, str) and HEX_COLOR_PATTERN.match(color):
                    continue
                raise forms.ValidationError(
                    (f'{char!r}: color inválido {color!r}. Use nombre de paleta o #RRGGBB.'),
                    code="legacy_bad_color",
                )
            return value

        raise forms.ValidationError(
            "letter_colors debe ser una lista ordenada de colores o un objeto por letra.",
            code="letter_colors_bad_type",
        )


@admin.register(MorphBanner)
class MorphBannerAdmin(admin.ModelAdmin):
    form = MorphBannerAdminForm
    list_display = ("word", "sitepage", "effect", "neon_style", "is_active", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": ("sitepage", "word", "effect", "neon_style", "letter_colors", "is_active"),
                "description": (
                    "Colores por posición: el widget genera una lista en el mismo orden que los glifos "
                    "del banner (omitidos espacios y caracteres sin path morfable). Una misma letra puede "
                    "tener otro color en otra posición. El formato objeto tipo {\"M\":\"accent\"} se acepta "
                    "solo como migración hasta que guardes desde el admin (se convierte a lista). "
                    "Estilo neón añade halo luminoso usando el color de cada letra."
                ),
            },
        ),
    )

