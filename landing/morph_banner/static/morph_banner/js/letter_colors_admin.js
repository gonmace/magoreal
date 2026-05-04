(function () {
  'use strict';

  const DEFAULT_COLOR = 'primary';

  /** Misma prioridad que get_letter_color (backend) sobre un objeto legacy. */
  function colorFromLegacyDict(char, dict) {
    if (!dict || typeof dict !== 'object') return DEFAULT_COLOR;
    if (/^[0-9]$/.test(char)) return dict[char] || DEFAULT_COLOR;
    return dict[char.toUpperCase()] || dict[char.toLowerCase()] || DEFAULT_COLOR;
  }

  function parseStoredValue(raw) {
    const val = (raw || '').trim();
    if (!val) return { kind: 'empty' };
    try {
      const j = JSON.parse(val);
      if (Array.isArray(j)) return { kind: 'list', data: j };
      if (j && typeof j === 'object') return { kind: 'legacy', data: j };
    } catch (e) {
      /* ignore */
    }
    return { kind: 'empty' };
  }

  function morphGlyphSequence(word, morphSet) {
    const out = [];
    for (const ch of word) {
      if (morphSet.has(ch)) out.push(ch);
    }
    return out;
  }

  function colorsForSequence(seq, parsed) {
    const n = seq.length;
    const out = [];
    if (parsed.kind === 'list') {
      const src = parsed.data || [];
      for (let i = 0; i < n; i++) {
        const v = src[i];
        out.push(v != null && v !== '' ? v : DEFAULT_COLOR);
      }
      return out;
    }
    if (parsed.kind === 'legacy') {
      for (const ch of seq) out.push(colorFromLegacyDict(ch, parsed.data));
      return out;
    }
    for (let i = 0; i < n; i++) out.push(DEFAULT_COLOR);
    return out;
  }

  function init() {
    const textarea = document.querySelector('[data-palette][data-morph-glyphs]');
    if (!textarea) return;

    const wordInput = document.getElementById('id_word');
    if (!wordInput) return;

    const palette = JSON.parse(textarea.dataset.palette || '[]');
    const morphGlyphs = JSON.parse(textarea.dataset.morphGlyphs || '[]');
    const morphSet = new Set(morphGlyphs);

    const container = document.createElement('div');
    container.id = 'letter-colors-ui';
    container.style.cssText = 'margin-bottom: 8px;';
    textarea.parentNode.insertBefore(container, textarea);

    textarea.style.display = 'none';

    function serializeColors() {
      const arr = [];
      container.querySelectorAll('.lc-row').forEach(row => {
        const select = row.querySelector('select');
        const hexInput = row.querySelector('input[type="color"]');
        if (!select) return;
        if (select.value === '_hex_') {
          arr.push(hexInput ? hexInput.value : '#000000');
        } else {
          arr.push(select.value);
        }
      });
      textarea.value = JSON.stringify(arr);
    }

    function buildRow(displayChar, currentColor) {
      const existing = currentColor || DEFAULT_COLOR;
      const isHex = typeof existing === 'string' && existing.startsWith('#');

      const row = document.createElement('div');
      row.className = 'lc-row';
      row.style.cssText =
        'display:flex; align-items:center; gap:8px; margin-bottom:6px;';

      const badge = document.createElement('span');
      badge.textContent = displayChar;
      badge.style.cssText =
        'display:inline-flex; width:28px; height:28px; align-items:center; justify-content:center; background:#444; color:#fff; border-radius:4px; font-weight:bold; font-size:13px; flex-shrink:0; font-family:ui-monospace,monospace;';
      row.appendChild(badge);

      const select = document.createElement('select');
      select.style.cssText =
        'padding:4px 6px; border:1px solid #666; background:#1a1a1a; color:#fff; border-radius:4px;';

      palette.forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name.charAt(0).toUpperCase() + name.slice(1);
        opt.selected = !isHex && existing === name;
        select.appendChild(opt);
      });

      const hexOpt = document.createElement('option');
      hexOpt.value = '_hex_';
      hexOpt.textContent = 'Color personalizado…';
      hexOpt.selected = isHex;
      select.appendChild(hexOpt);

      const hexInput = document.createElement('input');
      hexInput.type = 'color';
      hexInput.value = isHex ? existing.slice(0, 7) : '#3b82f6';
      hexInput.style.cssText =
        'display:' +
        (isHex ? 'inline' : 'none') +
        '; width:40px; height:28px; border:1px solid #666; border-radius:4px; cursor:pointer; padding:0;';

      select.addEventListener('change', function () {
        hexInput.style.display = this.value === '_hex_' ? 'inline' : 'none';
        serializeColors();
      });
      hexInput.addEventListener('input', serializeColors);

      row.appendChild(select);
      row.appendChild(hexInput);
      return row;
    }

    function rebuild() {
      const parsed = parseStoredValue(textarea.value);
      const seq = morphGlyphSequence(wordInput.value || '', morphSet);
      const posColors = colorsForSequence(seq, parsed);

      container.innerHTML = '';

      if (!seq.length) {
        container.innerHTML =
          '<p style="color:#888; font-size:13px;">Ingresá caracteres que tengan path morfable (el mismo subset que LETTER_PATHS en el backend).</p>';
        textarea.value = JSON.stringify([]);
        return;
      }

      const label = document.createElement('p');
      label.textContent =
        'Color por posición del glifo (índice 0 = primera letra morfable; repeticiones pueden diferir):';
      label.style.cssText = 'font-size:12px; color:#aaa; margin:0 0 6px;';
      container.appendChild(label);

      seq.forEach((ch, i) => {
        container.appendChild(buildRow(ch, posColors[i]));
      });

      serializeColors();
    }

    rebuild();
    wordInput.addEventListener('input', rebuild);
    wordInput.addEventListener('change', rebuild);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
