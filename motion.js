(() => {
  const root = document.documentElement;
  root.classList.add('js');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, c = document) => [...c.querySelectorAll(s)];
  if (reduced) { root.classList.add('ready'); return; }

  // ---- curtain: intro + page transitions
  const cur = document.createElement('div');
  cur.className = 'curtain';
  const word = 'Brewtiful';
  cur.innerHTML = '<b aria-hidden="true">' + [...word].map((c, i) => `<i class="${i >= 4 ? 'a' : ''}" style="--i:${i}">${c}</i>`).join('') + '</b><div class="cup-mini"></div>';
  document.body.appendChild(cur);
  const reveal = () => { requestAnimationFrame(() => { cur.classList.add('out'); root.classList.add('ready'); }); };
  const first = !sessionStorage.getItem('bt-seen');
  try { sessionStorage.setItem('bt-seen', '1'); } catch (e) {}
  if (first) setTimeout(reveal, 1100); else { cur.querySelector('b').style.display = 'none'; setTimeout(reveal, 80); }
  addEventListener('pageshow', e => { if (e.persisted) { cur.classList.add('out'); root.classList.add('ready'); } });
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href]');
    if (!a || a.target === '_blank' || e.metaKey || e.ctrlKey || e.shiftKey) return;
    const u = new URL(a.href, location.href);
    if (u.origin !== location.origin || u.pathname === location.pathname) return;
    e.preventDefault();
    cur.querySelector('b').style.display = 'none';
    cur.classList.remove('out'); cur.classList.add('in-from-bottom');
    void cur.offsetWidth;
    cur.classList.remove('in-from-bottom'); cur.classList.add('cover');
    setTimeout(() => { location.href = a.href; }, 650);
  });

  // ---- inner page headline: split into words
  const ph = document.querySelector('.page-hero h1');
  if (ph) ph.innerHTML = ph.textContent.trim().split(/\s+/).map((w, i) => `<span class="w"><span style="--i:${i}">${w}</span></span>`).join(' ');

  // ---- falling beans in hero
  const hero = document.querySelector('.hero');
  if (hero) {
    const rain = document.createElement('div'); rain.className = 'rain'; rain.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < 14; i++) {
      const b = document.createElement('i');
      b.style.cssText = `left:${Math.random() * 100}%;--s:${8 + Math.random() * 10}px;--t:${9 + Math.random() * 9}s;--dl:${-Math.random() * 14}s;--dx:${(Math.random() - .5) * 160}px;--r:${(Math.random() < .5 ? -1 : 1) * (180 + Math.random() * 360)}deg`;
      rain.appendChild(b);
    }
    hero.prepend(rain);
    const art = hero.querySelector('.hero-art');
    hero.addEventListener('mousemove', e => {
      const r = hero.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
      hero.style.setProperty('--mx', x.toFixed(3)); hero.style.setProperty('--my', y.toFixed(3));
      art.style.setProperty('--mx', x.toFixed(3)); art.style.setProperty('--my', y.toFixed(3));
    });
  }

  // ---- scroll scrub words
  const sc = document.querySelector('.scrub');
  let words = [];
  if (sc) {
    const hl = ['coffee', 'dream.'];
    sc.innerHTML = sc.textContent.trim().split(/\s+/).map(w => `<span class="sw${hl.includes(w) ? ' hl' : ''}">${w}</span>`).join(' ');
    words = $('.sw', sc);
  }

  // ---- nav hide/show, marquee velocity
  const nav = document.querySelector('.nav');
  const track = document.querySelector('.track');
  let lastY = scrollY, vel = 0, x = 0, half = 0;
  const measure = () => { if (track) half = track.scrollWidth / 2; };
  measure(); addEventListener('load', measure); addEventListener('resize', measure);
  const loop = () => {
    const y = scrollY, d = y - lastY; lastY = y;
    vel += (d - vel) * .1;
    if (track && half) {
      x -= .8 + Math.abs(vel) * .6;
      if (x <= -half) x += half;
      track.style.transform = `translate3d(${x}px,0,0) skewX(${Math.max(-12, Math.min(12, -vel * .5))}deg)`;
    }
    if (nav) {
      nav.classList.toggle('solid', y > 20);
      if (y > 200 && d > 4 && !document.getElementById('menu').classList.contains('open')) nav.classList.add('hide');
      else if (d < -4 || y < 200) nav.classList.remove('hide');
    }
    if (words.length) {
      const r = sc.getBoundingClientRect(), vh = innerHeight;
      const p = Math.min(1, Math.max(0, (vh * .85 - r.top) / (r.height + vh * .35)));
      const n = Math.round(p * words.length);
      words.forEach((w, i) => w.classList.toggle('on', i < n));
    }
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);

  // ---- ripple on buttons
  document.addEventListener('pointerdown', e => {
    const b = e.target.closest('.btn'); if (!b) return;
    const r = b.getBoundingClientRect(), s = Math.max(r.width, r.height) * 2;
    const rp = document.createElement('span'); rp.className = 'ripple';
    rp.style.cssText = `width:${s}px;height:${s}px;left:${e.clientX - r.left - s / 2}px;top:${e.clientY - r.top - s / 2}px`;
    b.appendChild(rp); setTimeout(() => rp.remove(), 700);
  });

  // ---- custom cursor
  if (matchMedia('(hover:hover) and (pointer:fine)').matches) {
    const dot = document.createElement('div'), ring = document.createElement('div');
    dot.className = 'cur-dot'; ring.className = 'cur-ring';
    document.body.append(dot, ring);
    let mx = innerWidth / 2, my = innerHeight / 2, rx = mx, ry = my;
    addEventListener('mousemove', e => {
      mx = e.clientX; my = e.clientY; root.classList.add('cursor-on');
      dot.style.transform = `translate(${mx}px,${my}px)`;
      ring.classList.toggle('hot', !!e.target.closest('a,button,summary,.card,select,input,textarea'));
    });
    document.addEventListener('mouseleave', () => root.classList.remove('cursor-on'));
    (function f() { rx += (mx - rx) * .18; ry += (my - ry) * .18; ring.style.transform = `translate(${rx}px,${ry}px)`; requestAnimationFrame(f); })();
  }
})();
