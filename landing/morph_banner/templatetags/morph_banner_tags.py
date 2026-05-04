from django import template

from ..models import MorphBanner
from ..constants import resolve_banner_color
from ..letter_paths import get_letter_data_for_word, build_morph_attributes, get_absolute_path

register = template.Library()


@register.inclusion_tag('morph_banner/morph_banner.html', takes_context=True)
def morph_banner(context):
    """
    Template tag to render the morph banner.
    Gets the appropriate MorphBanner based on the current sitepage.
    """
    request = context.get('request')
    sitepage = getattr(request, 'sitepage', None) if request else None

    config = MorphBanner.get_for_sitepage(sitepage)

    if not config:
        return {'word': '', 'letters': [], 'neon': False, 'neon_filter_id': ''}

    word = config.word
    raw_colors = config.letter_colors

    letter_data = get_letter_data_for_word(word)
    if not letter_data:
        letter_data = get_letter_data_for_word('MAGOREAL')
        raw_colors = None

    letters = letter_data['letters']

    padding = letter_data['total_width'] * 0.05
    for position_index, letter in enumerate(letters):
        letter['abs_path'] = get_absolute_path(letter['compound_path'], letter['x'] + padding)
        letter['color'] = resolve_banner_color(position_index, letter['char'], raw_colors)

    morph_attrs = build_morph_attributes(letters)

    viewbox_width = int(letter_data['total_width'] * 1.1)
    viewbox_height_str = f"{letter_data['viewbox_height']:.1f}"

    neon = getattr(config, 'neon_style', False)

    return {
        'word': letter_data['word'],
        'letters': letters,
        'viewbox_width': viewbox_width,
        'viewbox_height': viewbox_height_str,
        'effect': config.effect,
        'neon': neon,
        'neon_filter_id': f'morph-neon-{config.pk}' if neon else '',
        **morph_attrs,
    }
