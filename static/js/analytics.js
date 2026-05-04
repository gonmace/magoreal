/* Magoreal · Analytics shim
 *
 * Capa delgada sobre Plausible/Umami (configurables desde admin via
 * siteconfig.scripts_body_end). Expone window.magAnalytics.track() y
 * además auto-dispara eventos desde atributos data-analytics + data-
 * analytics-prop-*. También trackea scroll depth en 25/50/75/90%.
 *
 * Si no hay analytics instalado, los eventos se quedan en memoria —
 * nunca explota ni loggea nada en producción.
 */
(function () {
  'use strict';

  if (typeof window === 'undefined') return;

  const pending = [];      // eventos que llegaron antes de que cargue el script
  const fired = new Set(); // para scroll depth y otros "una sola vez"
  let flushTimer = null;

  function dispatch(event, props) {
    try {
      if (typeof window.plausible === 'function') {
        if (props) window.plausible(event, { props: props });
        else       window.plausible(event);
        return true;
      }
      if (window.umami && typeof window.umami.track === 'function') {
        if (props) window.umami.track(event, props);
        else       window.umami.track(event);
        return true;
      }
    } catch (e) { /* no-op */ }
    return false;
  }

  function scheduleFlush() {
    if (flushTimer) return;
    let tries = 0;
    flushTimer = setInterval(function () {
      tries++;
      if (pending.length === 0 || tries >= 20) {
        clearInterval(flushTimer);
        flushTimer = null;
        return;
      }
      const keep = [];
      for (let i = 0; i < pending.length; i++) {
        const [e, p] = pending[i];
        if (!dispatch(e, p)) keep.push([e, p]);
      }
      pending.length = 0;
      for (let i = 0; i < keep.length; i++) pending.push(keep[i]);
    }, 500);
  }

  function track(event, props) {
    if (!event) return;
    if (!dispatch(event, props)) {
      pending.push([event, props]);
      scheduleFlush();
    }
  }

  window.magAnalytics = {
    track: track,
    // Fire an event once per page load. Útil para slides/views que pueden
    // re-activarse muchas veces pero solo se reportan la primera.
    trackOnce: function (key, event, props) {
      if (fired.has(key)) return;
      fired.add(key);
      track(event, props);
    },
  };

  // ─── Auto-wire clicks en [data-analytics] ──────────────────────────
  // Lee además cualquier data-analytics-prop-<key> como prop adicional.
  document.addEventListener('click', function (ev) {
    const el = ev.target && ev.target.closest && ev.target.closest('[data-analytics]');
    if (!el) return;
    const name = el.getAttribute('data-analytics');
    if (!name) return;
    const props = {};
    const attrs = el.attributes;
    for (let i = 0; i < attrs.length; i++) {
      const a = attrs[i];
      if (a.name.indexOf('data-analytics-prop-') === 0) {
        props[a.name.slice('data-analytics-prop-'.length)] = a.value;
      }
    }
    track(name, Object.keys(props).length ? props : undefined);
  }, true);

  // ─── Scroll depth: 25/50/75/90% ────────────────────────────────────
  const MARKS = [25, 50, 75, 90];
  let scrollTicking = false;

  function currentPct() {
    const h = document.documentElement;
    const scroll = window.scrollY || h.scrollTop || 0;
    const total = (h.scrollHeight - h.clientHeight) || 1;
    return Math.min(100, Math.round((scroll / total) * 100));
  }

  function onScroll() {
    if (scrollTicking) return;
    scrollTicking = true;
    requestAnimationFrame(function () {
      scrollTicking = false;
      const pct = currentPct();
      for (let i = 0; i < MARKS.length; i++) {
        const m = MARKS[i];
        if (pct >= m && !fired.has('scroll_' + m)) {
          fired.add('scroll_' + m);
          track('scroll_depth', { pct: String(m) });
        }
      }
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
})();
