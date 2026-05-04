import json
from django import forms

from .constants import COLOR_PALETTE
from .letter_paths import LETTER_PATHS


class LetterColorsWidget(forms.Textarea):
    class Media:
        js = ['morph_banner/js/letter_colors_admin.js']

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['data-palette'] = json.dumps(list(COLOR_PALETTE.keys()))
        attrs['data-morph-glyphs'] = json.dumps(list(LETTER_PATHS.keys()))
        return attrs
