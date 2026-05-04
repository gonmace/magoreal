/* Magoreal · Capa de modernización
   - Reveal on scroll (IntersectionObserver)
   - Progress bar scroll-linked
   - Custom cursor con easing
   - Canvas network animado en #hero-net
   Respeta prefers-reduced-motion y touch devices. */
(function () {
  'use strict';

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isTouch = window.matchMedia('(hover: none)').matches;

  /* ─── Reveal on scroll ─────────────────────────────────────────────── */
  (function initReveal() {
    const targets = document.querySelectorAll('.reveal');
    if (!targets.length) return;
    if (prefersReduced) {
      targets.forEach(el => el.classList.add('visible'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -50px 0px' });
    targets.forEach(el => io.observe(el));
  })();

  /* ─── Progress bar ─────────────────────────────────────────────────── */
  (function initProgress() {
    const bar = document.querySelector('.scroll-progress');
    if (!bar) return;
    let ticking = false;
    const update = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
      bar.style.width = pct.toFixed(2) + '%';
      ticking = false;
    };
    window.addEventListener('scroll', () => {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
    update();
  })();

  /* ─── Auto carousel (slow, bidirectional) ───────────────────────────── */
  (function initAutoCarousel() {
    const tracks = document.querySelectorAll('.js-auto-carousel');
    if (!tracks.length) return;
    if (prefersReduced) return;

    tracks.forEach((track) => {
      const maxScroll = () => Math.max(0, track.scrollWidth - track.clientWidth);

      const speedAttr = parseFloat(track.dataset.carouselSpeed || '18'); // px/s
      const speed = Number.isFinite(speedAttr) ? Math.max(6, Math.min(40, speedAttr)) : 18;
      let dir = 1;
      let pausedUntil = 0;
      let raf = null;
      let lastTs = 0;

      const pauseFor = (ms = 2500) => {
        pausedUntil = performance.now() + ms;
      };

      const onFrame = (ts) => {
        if (!lastTs) lastTs = ts;
        const dt = (ts - lastTs) / 1000;
        lastTs = ts;

        if (ts < pausedUntil) {
          raf = requestAnimationFrame(onFrame);
          return;
        }

        const max = maxScroll();
        if (max <= 0) {
          raf = requestAnimationFrame(onFrame);
          return;
        }

        const next = track.scrollLeft + (speed * dt * dir);
        track.scrollLeft = next;

        // Rebote en bordes para evitar "salto" visual.
        if (track.scrollLeft <= 0) {
          dir = 1;
          pauseFor(1200);
        } else if (track.scrollLeft >= max - 1) {
          dir = -1;
          pauseFor(1200);
        }

        raf = requestAnimationFrame(onFrame);
      };

      track.addEventListener('mouseenter', () => pauseFor(10_000), { passive: true });
      track.addEventListener('mouseleave', () => pauseFor(600), { passive: true });
      track.addEventListener('pointerdown', () => pauseFor(6000), { passive: true });
      track.addEventListener('touchstart', () => pauseFor(6000), { passive: true });
      track.addEventListener('wheel', () => pauseFor(3000), { passive: true });

      const start = () => {
        if (raf) return;
        lastTs = 0;
        pauseFor(900);
        raf = requestAnimationFrame(onFrame);
      };
      const stop = () => {
        if (!raf) return;
        cancelAnimationFrame(raf);
        raf = null;
      };

      document.addEventListener('visibilitychange', () => {
        if (document.hidden) stop();
        else start();
      });
      window.addEventListener('resize', () => pauseFor(900), { passive: true });
      window.addEventListener('load', () => pauseFor(900), { passive: true });
      start();
    });
  })();

  /* ─── Canvas network hero (#hero-net) ──────────────────────────────── */
  (function initHeroNet() {
    if (prefersReduced) return;
    const canvas = document.getElementById('hero-net');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const root = document.documentElement;
    const primaryRGB = root.dataset.primaryRgb || '0,212,255';
    const accentRGB  = root.dataset.accentRgb  || '0,255,136';
    const PALETTE = {
      primary: primaryRGB.split(',').map(Number),
      accent:  accentRGB.split(',').map(Number),
    };

    let W = 0, H = 0, DPR = Math.min(window.devicePixelRatio || 1, 2);
    let nodes = [];
    let packets = [];
    let raf = null;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      W = rect.width;
      H = rect.height;
      canvas.width = W * DPR;
      canvas.height = H * DPR;
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      const density = Math.max(20, Math.min(60, Math.floor((W * H) / 22000)));
      nodes = Array.from({ length: density }, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
        pulse: Math.random() * Math.PI * 2,
      }));
      packets = [];
    };

    const maybeSpawnPacket = () => {
      if (packets.length > 4) return;
      if (Math.random() > 0.02) return;
      const a = nodes[Math.floor(Math.random() * nodes.length)];
      const b = nodes[Math.floor(Math.random() * nodes.length)];
      if (!a || !b || a === b) return;
      const palette = Math.random() < 0.65 ? PALETTE.primary : PALETTE.accent;
      packets.push({ a, b, t: 0, color: palette });
    };

    const draw = () => {
      ctx.clearRect(0, 0, W, H);

      const MAX_DIST = Math.min(180, W * 0.18);

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < MAX_DIST) {
            const alpha = (1 - d / MAX_DIST) * 0.18;
            ctx.strokeStyle = `rgba(${PALETTE.primary.join(',')},${alpha.toFixed(3)})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      nodes.forEach(n => {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;
        n.pulse += 0.018;
        const glow = 0.5 + Math.sin(n.pulse) * 0.5;
        const r = 1.6 + glow * 1.2;
        ctx.fillStyle = `rgba(${PALETTE.primary.join(',')},${(0.35 + glow * 0.4).toFixed(3)})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fill();
      });

      maybeSpawnPacket();
      packets = packets.filter(p => p.t < 1);
      packets.forEach(p => {
        p.t += 0.012;
        const x = p.a.x + (p.b.x - p.a.x) * p.t;
        const y = p.a.y + (p.b.y - p.a.y) * p.t;
        const [r, g, b] = p.color;
        const grad = ctx.createRadialGradient(x, y, 0, x, y, 16);
        grad.addColorStop(0, `rgba(${r},${g},${b},0.7)`);
        grad.addColorStop(1, `rgba(${r},${g},${b},0)`);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, 16, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = `rgba(${r},${g},${b},0.95)`;
        ctx.beginPath();
        ctx.arc(x, y, 2.2, 0, Math.PI * 2);
        ctx.fill();
      });

      raf = requestAnimationFrame(draw);
    };

    const start = () => {
      resize();
      if (!raf) raf = requestAnimationFrame(draw);
    };
    const stop = () => {
      if (raf) cancelAnimationFrame(raf);
      raf = null;
    };

    window.addEventListener('resize', () => { stop(); start(); }, { passive: true });
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stop(); else start();
    });

    start();
  })();

})();
