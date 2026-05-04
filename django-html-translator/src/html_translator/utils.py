"""
HtmlTextExtractor — extrae textos visibles de HTML y reconstruye el markup
con textos traducidos preservando 100% de tags, atributos, scripts y SVGs.

Soporta también extracción de valores string en bloques
<script type="application/ld+json" data-translate="true">.
"""
import copy
import json as _json
import re

from bs4 import BeautifulSoup, NavigableString, Tag

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_SKIP_TAGS = {"script", "style", "svg", "code", "pre", "noscript", "template"}
_TRANSLATABLE_ATTRS = ("placeholder",)

# Claves JSON-LD que nunca se traducen: identificadores, URLs, códigos ISO,
# nombres de marca (@type, @id) y campos geográficos con nombres propios.
_JSONLD_SKIP_KEYS = frozenset({
    '@context', '@id', '@type',
    'inLanguage', 'url', 'email', 'sameAs',
    'name',                                   # nombres de marca y propios
    'addressCountry', 'addressRegion', 'addressLocality',
})

# Longitud mínima para considerar un valor JSON-LD como traducible.
# Evita traducir códigos cortos ("BO", "es", "Article", etc.).
_JSONLD_MIN_LEN = 12


def _is_inside_skip_tag(node) -> bool:
    """True si el nodo está anidado dentro de algún tag de _SKIP_TAGS (en cualquier nivel)."""
    parent = node.parent
    while parent and getattr(parent, 'name', None):
        if parent.name in _SKIP_TAGS:
            return True
        parent = parent.parent
    return False


def _is_aria_hidden(node) -> bool:
    if isinstance(node, Tag) and node.get('aria-hidden') == 'true':
        return True
    parent = node.parent
    while parent and getattr(parent, 'name', None):
        if parent.get('aria-hidden') == 'true':
            return True
        parent = parent.parent
    return False


def _is_notranslate(node) -> bool:
    """True si el nodo o cualquier ancestro tiene translate='no'."""
    if isinstance(node, Tag) and node.get('translate') == 'no':
        return True
    parent = node.parent
    while parent and getattr(parent, 'name', None):
        if parent.get('translate') == 'no':
            return True
        parent = parent.parent
    return False


def _jsonld_extract_values(data, path=()):
    """
    Recorre recursivamente un objeto JSON-LD y devuelve lista de
    (path_tuple, valor_string) para todos los strings traducibles.
    """
    results = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k in _JSONLD_SKIP_KEYS:
                continue
            results.extend(_jsonld_extract_values(v, path + (k,)))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            results.extend(_jsonld_extract_values(v, path + (i,)))
    elif isinstance(data, str):
        val = data.strip()
        if (val
                and len(val) >= _JSONLD_MIN_LEN
                and not val.startswith(('http://', 'https://', '@'))
                and not _EMAIL_RE.match(val)):
            results.append((path, val))
    return results


def _jsonld_set_value(data, path, value):
    """Navega data por path y actualiza el valor en la última clave."""
    obj = data
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


class HtmlTextExtractor:
    """
    Extrae textos visibles de un fragmento HTML y permite reconstruirlo
    sustituyendo esos textos por sus traducciones.

    Reglas de extracción:
    - Ignora <script>, <style>, <svg>, <code>, <pre>, <noscript>, <template>
    - Ignora nodos con aria-hidden="true" o translate="no"
    - Ignora direcciones de email
    - Extrae atributos placeholder de inputs/textareas
    - Extrae strings de <script type="application/ld+json" data-translate="true">

    Uso:
        extractor = HtmlTextExtractor(html)
        texts = extractor.get_texts()
        translated = translate(texts)
        new_html = extractor.rebuild(translated)
    """

    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "html.parser")
        self._text_nodes: list[NavigableString] = []
        self._attr_slots: list[tuple[Tag, str]] = []
        # Lista de (script_tag, parsed_data, [(path, original_value), ...])
        self._jsonld_slots: list[tuple[Tag, dict, list]] = []
        self._extract()

    def _extract(self) -> None:
        for element in self.soup.descendants:
            if isinstance(element, NavigableString):
                if _is_inside_skip_tag(element):
                    continue
                if _is_aria_hidden(element) or _is_notranslate(element):
                    continue
                text = str(element).strip()
                if _EMAIL_RE.match(text):
                    continue
                if text:
                    self._text_nodes.append(element)
            elif isinstance(element, Tag):
                if element.name in _SKIP_TAGS or _is_inside_skip_tag(element):
                    continue
                if _is_aria_hidden(element) or _is_notranslate(element):
                    continue
                for attr in _TRANSLATABLE_ATTRS:
                    val = element.get(attr, '')
                    if val and str(val).strip():
                        self._attr_slots.append((element, attr))

        # Extracción de JSON-LD: solo scripts marcados con data-translate="true"
        for script in self.soup.find_all('script', type='application/ld+json'):
            if not script.get('data-translate'):
                continue
            try:
                data = _json.loads(script.string or '')
            except (_json.JSONDecodeError, TypeError):
                continue
            extracted = _jsonld_extract_values(data)
            if extracted:
                self._jsonld_slots.append((script, data, extracted))

    def get_texts(self) -> list[str]:
        """Textos visibles en orden: nodos de texto, placeholders, strings JSON-LD."""
        texts = [str(node).strip() for node in self._text_nodes]
        texts += [str(tag[attr]).strip() for tag, attr in self._attr_slots]
        for _, _, extracted in self._jsonld_slots:
            texts += [val for _, val in extracted]
        return texts

    def rebuild(self, translated: list[str]) -> str:
        """
        Reconstruye el HTML sustituyendo cada texto por su traducción.
        translated debe tener la misma longitud que get_texts().
        Lanza ValueError si el conteo difiere en más de 2.
        """
        import logging
        logger = logging.getLogger(__name__)

        n_nodes = len(self._text_nodes)
        n_attrs = len(self._attr_slots)
        n_jsonld = sum(len(e) for _, _, e in self._jsonld_slots)
        expected = n_nodes + n_attrs + n_jsonld

        if len(translated) != expected:
            diff = abs(len(translated) - expected)
            if diff > 2:
                logger.error(
                    'rebuild: mismatch grave %d traducidos vs %d esperados '
                    '(%d nodos + %d attrs + %d jsonld)',
                    len(translated), expected, n_nodes, n_attrs, n_jsonld,
                )
                raise ValueError(f'Text count mismatch: {len(translated)} vs {expected}')
            logger.warning(
                'rebuild: mismatch %d traducidos vs %d esperados — reconstrucción parcial',
                len(translated), expected,
            )

        # Nodos de texto
        for node, new_text in zip(self._text_nodes, translated[:n_nodes]):
            if not new_text.strip():
                continue
            original = str(node)
            prefix = original[: len(original) - len(original.lstrip())]
            suffix = original[len(original.rstrip()):]
            node.replace_with(NavigableString(prefix + new_text + suffix))

        # Atributos (placeholder, etc.)
        for (tag, attr), new_text in zip(self._attr_slots, translated[n_nodes:n_nodes + n_attrs]):
            if new_text.strip():
                tag[attr] = new_text

        # Strings JSON-LD
        offset = n_nodes + n_attrs
        for script, original_data, extracted in self._jsonld_slots:
            new_data = copy.deepcopy(original_data)
            for (path, _), new_text in zip(extracted, translated[offset:offset + len(extracted)]):
                if new_text.strip():
                    _jsonld_set_value(new_data, path, new_text)
            offset += len(extracted)
            script.string = _json.dumps(new_data, ensure_ascii=False, indent=2)

        return str(self.soup)
