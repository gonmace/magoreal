/* Magoreal · Section counter — giro de dígitos
   Cuando cada section header entra al viewport, los dígitos de [ NNN ]
   ciclan caracteres aleatorios y se estabilizan uno a uno (izq→der). */
(function () {
  'use strict';

  if (typeof window === 'undefined') return;

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const RAIN_CHARS = '0123456789abcdef';

  function init() {
    const headers = Array.from(document.querySelectorAll('.section-header[data-num]'));
    if (!headers.length) return;

    if (prefersReduced) return;

    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        io.unobserve(entry.target);
        rainHeader(entry.target);
      });
    }, { threshold: 0.4, rootMargin: '0px 0px -60px 0px' });

    headers.forEach(h => io.observe(h));
  }

  function rainHeader(header) {
    const slots = Array.from(header.querySelectorAll('.digit-slot'));
    if (!slots.length) return;

    // Duración total más larga para que se sienta la lluvia (~2s)
    // Cada slot se estabiliza en un momento distinto (stagger izq→der)
    const TICK_MS = 55;           // velocidad de cambio por frame
    const SETTLE_START = 700;     // el primer slot empieza a settle
    const SETTLE_STEP = 500;      // gap entre settles

    slots.forEach((slot, i) => {
      const target = slot.getAttribute('data-target');
      const settleAt = SETTLE_START + i * SETTLE_STEP;
      rollSlot(slot, target, settleAt, TICK_MS);
    });
  }

  function rollSlot(slot, finalChar, settleMs, tickMs) {
    const start = performance.now();
    let timerId = null;
    let settled = false;

    const tick = () => {
      if (settled) return;
      const elapsed = performance.now() - start;
      if (elapsed >= settleMs) {
        settled = true;
        setText(slot, finalChar, true);
        slot.classList.remove('rolling');
        slot.classList.add('settled');
        return;
      }
      // Char aleatorio con animación de caída
      const c = RAIN_CHARS[(Math.random() * RAIN_CHARS.length) | 0];
      setText(slot, c.toUpperCase(), false);
      // Re-disparar la animación de caída (remove+reflow+add)
      slot.classList.remove('rolling');
      // eslint-disable-next-line no-unused-expressions
      slot.offsetHeight;
      slot.classList.add('rolling');
      timerId = setTimeout(tick, tickMs);
    };

    // Quitar clase settled si venía (re-run)
    slot.classList.remove('settled');
    tick();
  }

  function setText(el, text, isFinal) {
    el.textContent = text;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(init, 80));
  } else {
    setTimeout(init, 80);
  }
})();
