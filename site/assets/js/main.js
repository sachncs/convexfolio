(() => {
  'use strict';

  // Mark JS as available so the reveal CSS can hide initial state.
  document.documentElement.classList.add('js');

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ───────────────────────────────────────────── nav scrolled state
  const nav = document.getElementById('topnav');
  if (nav) {
    const setScrolled = () => {
      nav.classList.toggle('is-scrolled', window.scrollY > 12);
    };
    setScrolled();
    window.addEventListener('scroll', setScrolled, { passive: true });
  }

  // ───────────────────────────────────────────── mobile menu
  const burger = document.querySelector('.nav-burger');
  const mobile = document.getElementById('mobile-menu');
  if (burger && mobile) {
    burger.addEventListener('click', () => {
      const open = !mobile.hasAttribute('hidden');
      if (open) {
        mobile.setAttribute('hidden', '');
        burger.setAttribute('aria-expanded', 'false');
      } else {
        mobile.removeAttribute('hidden');
        burger.setAttribute('aria-expanded', 'true');
      }
    });
    mobile.addEventListener('click', (e) => {
      if (e.target.tagName === 'A') {
        mobile.setAttribute('hidden', '');
        burger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ───────────────────────────────────────────── reveal on scroll
  const reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
      reveals.forEach((el) => el.classList.add('is-in'));
    } else {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const delay = parseInt(entry.target.dataset.delay || '0', 10);
              setTimeout(() => entry.target.classList.add('is-in'), delay * 80);
              io.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.12, rootMargin: '0px 0px -8% 0px' }
      );
      reveals.forEach((el) => io.observe(el));
    }
  }

  // ───────────────────────────────────────────── typewriter for hero CLI
  const typer = document.querySelector('[data-typer]');
  if (typer && !prefersReducedMotion) {
    const text = typer.textContent;
    typer.textContent = '';
    let i = 0;
    const step = () => {
      i += 1;
      typer.textContent = text.slice(0, i);
      if (i < text.length) {
        setTimeout(step, 22 + Math.random() * 28);
      }
    };
    setTimeout(step, 380);
  }

  // ───────────────────────────────────────────── counter-up
  const counters = document.querySelectorAll('.counter');
  if (counters.length) {
    const animate = (el) => {
      const to = parseFloat(el.dataset.to);
      const suffix = el.dataset.suffix || '';
      const dur = 1100;
      if (prefersReducedMotion) {
        el.textContent = (Number.isInteger(to) ? to : to.toFixed(0)) + suffix;
        return;
      }
      const start = performance.now();
      const tick = (now) => {
        const t = Math.min(1, (now - start) / dur);
        const eased = 1 - Math.pow(1 - t, 3);
        const value = to * eased;
        const display = Number.isInteger(to) ? Math.round(value) : value.toFixed(0);
        el.textContent = display + suffix;
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    if ('IntersectionObserver' in window) {
      const cio = new IntersectionObserver(
        (entries) => {
          entries.forEach((e) => {
            if (e.isIntersecting) {
              animate(e.target);
              cio.unobserve(e.target);
            }
          });
        },
        { threshold: 0.5 }
      );
      counters.forEach((el) => cio.observe(el));
    } else {
      counters.forEach(animate);
    }
  }

  // ───────────────────────────────────────────── copy buttons
  document.querySelectorAll('[data-copy]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const text = btn.dataset.copy;
      try {
        await navigator.clipboard.writeText(text);
        const original = btn.querySelector('span').textContent;
        btn.querySelector('span').textContent = 'Copied';
        btn.classList.add('is-copied');
        setTimeout(() => {
          btn.querySelector('span').textContent = original;
          btn.classList.remove('is-copied');
        }, 1500);
      } catch (_) {
        // ignore; clipboard unavailable
      }
    });
  });

  // ───────────────────────────────────────────── install tabs
  const installTabs = document.querySelectorAll('.install-tab');
  const installPanels = document.querySelectorAll('.install-panel');
  if (installTabs.length) {
    installTabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        installTabs.forEach((t) => {
          const active = t === tab;
          t.classList.toggle('is-active', active);
          t.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        installPanels.forEach((p) => {
          const active = p.dataset.panel === target;
          p.classList.toggle('is-active', active);
          if (active) p.removeAttribute('hidden');
          else p.setAttribute('hidden', '');
        });
      });
    });
  }

  // ───────────────────────────────────────────── sparkline draw
  const sparkLine = document.querySelector('.spark-line');
  if (sparkLine && !prefersReducedMotion) {
    const len = sparkLine.getTotalLength();
    sparkLine.style.strokeDasharray = len;
    sparkLine.style.strokeDashoffset = len;
    requestAnimationFrame(() => {
      sparkLine.style.transition = 'stroke-dashoffset 1.6s cubic-bezier(.2,.8,.2,1) .25s';
      sparkLine.style.strokeDashoffset = '0';
    });
  }
})();
