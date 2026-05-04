"""
Constants for Morph Banner module.
"""

import re

# Color palette mapping to CSS variables (DaisyUI/Tailwind)
COLOR_PALETTE = {
    'primary':   'var(--color-primary)',
    'secondary': 'var(--color-secondary)',
    'accent':    'var(--color-accent)',
    'info':      'var(--color-info)',
    'success':   'var(--color-success)',
    'warning':   'var(--color-warning)',
    'error':     'var(--color-error)',
    'neutral':   'var(--color-neutral)',
}

# Regex pattern to validate hex colors (#RRGGBB)
HEX_COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')

# Default color for letters when not specified
DEFAULT_LETTER_COLOR = 'primary'


def get_color_css(color_value):
    """
    Convert a color value to CSS value.
    
    Args:
        color_value: Either a palette name (e.g., 'primary') or hex color (e.g., '#FF0000')
    
    Returns:
        CSS value string (e.g., 'var(--p)' or '#FF0000')
    """
    if not color_value:
        color_value = DEFAULT_LETTER_COLOR
    
    # Check if it's a palette name
    if color_value in COLOR_PALETTE:
        return COLOR_PALETTE[color_value]
    
    # Check if it's a valid hex color
    if HEX_COLOR_PATTERN.match(color_value):
        return color_value
    
    # Fallback to default
    return COLOR_PALETTE[DEFAULT_LETTER_COLOR]


def get_letter_color(char, letter_colors_dict):
    """
    CSS color para un carácter (solo formato legacy dict en letter_colors).

    Claves típicas: mayúscula para letras, dígito para números; también minúscula opcional.
    """
    if not char or not isinstance(letter_colors_dict, dict):
        return get_color_css(DEFAULT_LETTER_COLOR)
    if char.isdigit():
        color_value = letter_colors_dict.get(char, DEFAULT_LETTER_COLOR)
    else:
        color_value = letter_colors_dict.get(
            char.upper(),
            letter_colors_dict.get(char.lower(), DEFAULT_LETTER_COLOR),
        )
    return get_color_css(color_value)


def resolve_banner_color(position_index, char, letter_colors):
    """
    Determina el fill CSS por posición (0-indexed) dentro de los glifos que renderiza el morph.

    ``letter_colors`` puede ser:

    - list: ``[palette|hex per position]``. Posiciones omitidas / None / '' -> primary.
    - dict (legacy): igual que antes, por grafema repetido vale el mismo valor en cada aparición.
    """
    if letter_colors is None:
        return get_color_css(DEFAULT_LETTER_COLOR)
    if isinstance(letter_colors, list):
        if position_index >= len(letter_colors):
            return get_color_css(DEFAULT_LETTER_COLOR)
        cv = letter_colors[position_index]
        if cv is None or cv == '':
            return get_color_css(DEFAULT_LETTER_COLOR)
        if isinstance(cv, str):
            return get_color_css(cv)
        return get_color_css(DEFAULT_LETTER_COLOR)
    if isinstance(letter_colors, dict):
        return get_letter_color(char, letter_colors)
    return get_color_css(DEFAULT_LETTER_COLOR)
