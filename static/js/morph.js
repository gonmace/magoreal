/* Magoreal · Morphosis SVG scroll-triggered
   Usa KUTE.js UMD `kute.min.js` (CDN en base.html; incluye plugins SVG) + IntersectionObserver.
   Dispara un morph de path SVG cuando el elemento [data-morph] entra al viewport.
   Pausa automáticamente cuando sale del viewport o la pestaña queda oculta.
   Respeta prefers-reduced-motion aplicando el path final sin animar.
   `data-effect="always"`: con data-morph-leave los fantasmas se van sumando (.is-visible) en cada paso del morph
   sin borrar los anteriores; el loop debe ser único al frente (no yoyo desde el markup). */
(function () {
  'use strict';

  if (typeof window === 'undefined') return;

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Per-root alive flag: false = kill the loop at next onComplete
  const rootAlive = new WeakMap();

  function parseTargets(raw) {
    return (raw || '').split(',').map(s => s.trim()).filter(Boolean);
  }

  function revealAllLetterGhosts(rootEl) {
    rootEl.querySelectorAll('.letter-ghost').forEach((g) => g.classList.add('is-visible'));
  }

  function hideActiveMorphShape(rootEl) {
    const shape = rootEl.querySelector('.morph-shape.letter-active');
    if (shape) shape.style.opacity = '0';
  }

  function applyFinalPath(rootEl) {
    // Fallback reduced-motion: setea cada shape al ÚLTIMO path destino sin animar
    rootEl.querySelectorAll('[data-morph-to]').forEach(shape => {
      const targets = parseTargets(shape.getAttribute('data-morph-to'));
      if (!targets.length) return;
      const target = rootEl.querySelector(targets[targets.length - 1]);
      if (target) {
        const d = target.getAttribute('d');
        if (d) shape.setAttribute('d', d);
        const fill = target.getAttribute('data-fill') || target.getAttribute('fill');
        if (fill && fill !== 'none') shape.setAttribute('fill', fill);
      }
    });
  }

  function runMorph(rootEl) {
    rootEl.classList.add('morph-in-view');

    const effectAttr = rootEl.getAttribute('data-effect') || '';
    const accumulateGhostsForward = effectAttr === 'always';

    if (!window.KUTE) {
      applyFinalPath(rootEl);
      if (accumulateGhostsForward) {
        revealAllLetterGhosts(rootEl);
        hideActiveMorphShape(rootEl);
        rootEl.classList.add('morph-in-view', 'morph-revealed');
      }
      return;
    }
    const duration = parseInt(rootEl.getAttribute('data-morph-duration') || '1400', 10);
    const easing = rootEl.getAttribute('data-morph-easing') || 'easingCubicOut';
    const holdMs = parseInt(rootEl.getAttribute('data-morph-hold') || '350', 10);

    const shapes = Array.from(rootEl.querySelectorAll('[data-morph-to]'));
    if (!shapes.length) return;

    // Configuración por shape (overrides per-shape opcionales)
    const cfgs = shapes.map((shape) => ({
      shape,
      targetSels: parseTargets(shape.getAttribute('data-morph-to')),
      leaveSels: parseTargets(shape.getAttribute('data-morph-leave')),
      homeSel: shape.getAttribute('data-morph-home'),
      initialDelay: parseInt(shape.getAttribute('data-morph-delay') || '0', 10),
      easing: shape.getAttribute('data-morph-easing') || easing,
      duration: parseInt(shape.getAttribute('data-morph-duration-shape') || duration, 10),
      precision: parseInt(shape.getAttribute('data-morph-precision') || '15', 10),
      morphIndex: parseInt(shape.getAttribute('data-morph-index') || '0', 10),
    }));

    // Loop / longitud comunes (toman del primer shape o del root)
    const loopMode = rootEl.getAttribute('data-morph-loop')
                  || shapes[0].getAttribute('data-morph-loop');
    const len = cfgs[0].targetSels.length;
    if (!len) return;

    // Mark root as active for this run
    rootAlive.set(rootEl, true);

    let direction = 1;   // 1 forward, -1 backward
    let stepIdx = 0;

    const resolveStep = (cfg) => {
      let targetSel, fromPos;
      if (direction === 1) {
        targetSel = cfg.targetSels[stepIdx];
        fromPos = stepIdx;
      } else {
        const k = stepIdx;
        if (k < len - 1) {
          targetSel = cfg.targetSels[len - 2 - k];
        } else {
          targetSel = cfg.homeSel || cfg.targetSels[0];
        }
        fromPos = len - k;
      }
      return { targetSel, fromPos };
    };

    const runStep = () => {
      let pending = cfgs.length;

      const oneDone = () => {
        pending--;
        if (pending > 0) return;
        // Stop the loop if this root was killed (scrolled out / tab hidden)
        if (!rootAlive.get(rootEl)) return;
        stepIdx++;
        if (stepIdx >= len) {
          if (loopMode === 'yoyo') {
            direction *= -1;
            stepIdx = 0;
            runStep();
          } else {
            rootEl.dispatchEvent(new CustomEvent('morph:complete', { bubbles: true }));
          }
          return;
        }
        runStep();
      };

      cfgs.forEach((cfg) => {
        const { targetSel, fromPos } = resolveStep(cfg);
        if (!targetSel) { oneDone(); return; }
        const target = rootEl.querySelector(targetSel);
        if (!target) { oneDone(); return; }

        const activeGhostSel = (fromPos >= 0 && fromPos < cfg.leaveSels.length)
                             ? cfg.leaveSels[fromPos] : null;

        // Capture delay now (stepIdx/direction may change by the time onStart fires)
        const stepDelay = (stepIdx === 0 && direction === 1) ? cfg.initialDelay : holdMs;

        const tween = window.KUTE.to(
          cfg.shape,
          { path: target, ...(target.getAttribute('data-fill') ? { attr: { fill: target.getAttribute('data-fill') } } : {}) },
          {
            duration: cfg.duration,
            delay: stepDelay,
            easing: cfg.easing,
            morphPrecision: cfg.precision,
            morphIndex: cfg.morphIndex,
            onStart: () => {
              // Sync active shape color to target — delay matches KUTE's own delay
              // so the CSS transition starts exactly when path morphing begins.
              const targetFill = target.style.fill;
              if (targetFill) {
                cfg.shape.style.transitionDelay = stepDelay + 'ms';
                cfg.shape.style.fill = targetFill;
                if (cfg.shape.style.stroke) cfg.shape.style.stroke = targetFill;
              }
              // Ghost visibility (only when data-morph-leave is used)
              if (!cfg.leaveSels.length) return;
              const acc = accumulateGhostsForward && direction === 1;
              if (!acc) {
                cfg.leaveSels.forEach((sel) => {
                  const g = rootEl.querySelector(sel);
                  if (g) g.classList.remove('is-visible');
                });
              }
              if (activeGhostSel) {
                const ag = rootEl.querySelector(activeGhostSel);
                if (ag) ag.classList.add('is-visible');
              }
            },
            onComplete: oneDone,
          }
        );
        tween.start();
      });
    };

    runStep();
  }

  function initMorphs() {
    const roots = Array.from(document.querySelectorAll('[data-morph]'));
    if (!roots.length) return;

    if (prefersReduced) {
      roots.forEach((rootEl) => {
        if (rootEl.getAttribute('data-effect') === 'always') {
          applyFinalPath(rootEl);
          revealAllLetterGhosts(rootEl);
          hideActiveMorphShape(rootEl);
          rootEl.classList.add('morph-in-view', 'morph-revealed');
          return;
        }
        applyFinalPath(rootEl);
      });
      return;
    }

    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          // (Re-)start the morph loop when element enters the viewport
          runMorph(entry.target);
        } else {
          // Kill the loop — the current in-flight tween finishes naturally
          // (≤ duration ms) but won't chain a new one
          rootAlive.set(entry.target, false);
          entry.target.classList.remove('morph-in-view');
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    roots.forEach(el => {
      io.observe(el);
      el.addEventListener('morph:complete', () => el.classList.add('morph-revealed'));
    });

    // Pause all morphs when the tab is hidden; restart via IO bounce when visible again
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        roots.forEach(el => rootAlive.set(el, false));
      } else {
        // Force IO to re-check intersections so in-viewport roots restart
        roots.forEach(el => { io.unobserve(el); io.observe(el); });
      }
    });
  }

  // KUTE carga vía CDN defer; esperamos DOMContentLoaded + un tick más
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(initMorphs, 0));
  } else {
    setTimeout(initMorphs, 0);
  }
})();
