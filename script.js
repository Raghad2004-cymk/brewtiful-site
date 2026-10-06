const STORE = 'https://brewtiful.club';
const PRODUCTS = [
  {t:'Ethiopia Sidamo Bombe Decaf', h:'ethiopia-sidamo-bombe', p:110, s:5, i:'4E73B99E-55CD-4941-AD7D-3CF5A7800D33.png?v=1789062616'},
  {t:'Ethiopia Sidamo Decaf', h:'ethiopia-sidamo-decaf-beans', p:110, s:8, i:'ADCBDCC2-72CA-48DC-8DC3-268A27D1B86C.png?v=1789062616'},
  {t:'Colombia Huila Decaf', h:'colombia-huila-decaf', p:125, s:9, i:'IMG-0141.png?v=1790080307'},
  {t:'Sunday Drive Decaf', h:'sunday-drive-decaf-beans', p:120, s:9, i:'84450374-EAEC-4FED-BE38-24EFF4BC5CFD.png?v=1789062616'},
  {t:'Honduras Decaf', h:'honduras-decaf-beans', p:135, s:9, i:'1E5FCD8D-7CCC-431A-A21C-6D00C72309D9.png?v=1789062617'},
  {t:'Mississippi Grogg Decaf', h:'mississippi-grogg-decaf-beans', p:135, s:10, i:'D6BDBDBC-97F8-4FE6-9992-1DA3A57A54AB.png?v=1789062617'},
  {t:'True Love Decaf', h:'true-love-decaf', p:150, s:0, i:'D109E80D-520E-41C6-A3A2-4CE905DD2965.png?v=1789062617', tag:'LIMITED TIME'}
];
const IMG = 'https://cdn.shopify.com/s/files/1/1023/2581/3527/files/';
const esc = s => s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

const FAQS = [
  ['Is Brewtiful really 100% decaf?', 'Yes. Every roast we sell is decaffeinated coffee. Like all decaf coffee, trace amounts of caffeine can remain, so ask your doctor if you have specific limits.'],
  ['What comes in a box?', 'Each box has 5 pouches of ground coffee and 5 paper cups, so you can brew a cup anywhere with just hot water.'],
  ['How do I brew it?', 'Tear open a pouch, pour hot water into your cup, and sip. It is that simple.'],
  ['Is it safe during pregnancy?', 'Many people choose decaf during pregnancy, but recommendations vary. Please check with your doctor about what is right for you.'],
  ['How do I order?', 'Pick a roast on our shop page and press Buy now. You will check out securely on brewtiful.club.'],
  ['Do you offer gifting or wholesale?', 'Yes, we would love to help. Send us a message on the contact page and we will get back to you.'],
  ['Why is a roast sold out?', 'We roast in small batches, so some roasts sell out. Message us and we will let you know when it is back.']
];
const faqHTML = list => list.map(([q, a]) => `<details><summary>${esc(q)}</summary><p>${esc(a)}</p></details>`).join('');
const fh = document.getElementById('faq-home'), fa = document.getElementById('faq-all');
if (fh) fh.innerHTML = faqHTML(FAQS.slice(0, 4));
if (fa) fa.innerHTML = faqHTML(FAQS);

const grid = document.getElementById('products');
const card = (x, n) => {
  const out = x.s === 0;
  const badge = out ? '<span class="badge out">SOLD OUT</span>' : x.tag ? `<span class="badge">${esc(x.tag)}</span>` : (x.s <= 5 ? '<span class="badge">LOW STOCK</span>' : '');
  return `<article class="card reveal in" style="--d:${(n % 4) * .08}s">${badge}
    <div class="img"><img src="${IMG}${x.i}&width=600" alt="${esc(x.t)}" loading="lazy" onerror="this.remove()"></div>
    <div class="body"><h3>${esc(x.t)}</h3><p>5 pouches of ground coffee + 5 paper cups</p>
    <span class="price">${x.p} QAR</span>
    <a class="btn${out ? ' soldout' : ''}" href="${STORE}/products/${x.h}" target="_blank" rel="noopener">${out ? 'Sold out' : 'Buy now'}</a></div></article>`;
};
let filter = 'all', sort = 'default';
const tilt = c => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  c.addEventListener('mousemove', e => {
    const r = c.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
    c.style.transform = `perspective(800px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg) translateY(-6px)`;
  });
  c.addEventListener('mouseleave', () => c.style.transform = '');
};
const renderProducts = () => {
  if (!grid) return;
  let list = PRODUCTS.filter(x => filter === 'all' || x.s > 0);
  if (sort === 'low') list = [...list].sort((a, b) => a.p - b.p);
  if (sort === 'high') list = [...list].sort((a, b) => b.p - a.p);
  if (sort === 'az') list = [...list].sort((a, b) => a.t.localeCompare(b.t));
  const limit = +grid.dataset.limit;
  if (limit) list = list.filter(x => x.s > 0).slice(0, limit);
  grid.innerHTML = list.map(card).join('');
  grid.querySelectorAll('.card').forEach(tilt);
};
renderProducts();
document.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => {
  document.querySelectorAll('.chip').forEach(o => o.classList.toggle('on', o === c));
  filter = c.dataset.filter; renderProducts();
}));
const sel = document.getElementById('sort');
if (sel) sel.addEventListener('change', () => { sort = sel.value; renderProducts(); });

// contact form -> opens mail client
const form = document.getElementById('contact-form');
if (form) form.addEventListener('submit', e => {
  e.preventDefault();
  const f = form.elements;
  if (!f.name.value.trim() || !/\S+@\S+\.\S+/.test(f.email.value) || !f.msg.value.trim()) {
    document.getElementById('form-note').textContent = 'Please fill in your name, a valid email and a message.';
    return;
  }
  const body = `${f.msg.value}\n\n— ${f.name.value} (${f.email.value})`;
  location.href = `mailto:brewtiful.qa@gmail.com?subject=${encodeURIComponent('Brewtiful: ' + f.topic.value)}&body=${encodeURIComponent(body)}`;
});

document.getElementById('year').textContent = new Date().getFullYear();

// mobile menu
const btn = document.querySelector('.menu-btn'), menu = document.getElementById('menu');
const setMenu = o => { menu.classList.toggle('open', o); btn.setAttribute('aria-expanded', o); };
btn.addEventListener('click', () => setMenu(!menu.classList.contains('open')));
menu.addEventListener('click', e => { if (e.target.tagName === 'A') setMenu(false); });

// scroll progress
const bar = document.querySelector('.progress');
const onScroll = () => {
  const h = document.documentElement;
  bar.style.transform = `scaleX(${h.scrollTop / (h.scrollHeight - h.clientHeight || 1)})`;
};
addEventListener('scroll', onScroll, {passive: true}); onScroll();

// reveal on scroll + count-up
const count = el => {
  const end = +el.dataset.count, suf = el.dataset.suffix || '', t0 = performance.now();
  const tick = t => {
    const k = Math.min((t - t0) / 1400, 1);
    el.textContent = Math.round(end * (1 - Math.pow(1 - k, 3))) + suf;
    if (k < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
};
const io = new IntersectionObserver(es => es.forEach(e => {
  if (!e.isIntersecting) return;
  e.target.classList.add('in');
  e.target.querySelectorAll('[data-count]').forEach(count);
  io.unobserve(e.target);
}), {threshold: .15});
document.querySelectorAll('.reveal:not(.hero .reveal)').forEach(el => io.observe(el));

const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (still) document.querySelectorAll('[data-count]').forEach(el => el.textContent = el.dataset.count + (el.dataset.suffix || ''));
else {
  // magnetic buttons
  document.querySelectorAll('.magnetic').forEach(b => {
    b.addEventListener('mousemove', e => {
      const r = b.getBoundingClientRect();
      b.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * .25}px,${(e.clientY - r.top - r.height / 2) * .35}px)`;
    });
    b.addEventListener('mouseleave', () => b.style.transform = '');
  });
  // hero parallax
  const art = document.querySelector('.hero-art');
  if (art) addEventListener('scroll', () => { art.style.transform = `translateY(${scrollY * .12}px)`; }, {passive: true});
}
