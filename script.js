document.getElementById('year').textContent = new Date().getFullYear();
const btn = document.querySelector('.menu-btn'), menu = document.getElementById('menu');
btn.addEventListener('click', () => {
  const open = menu.classList.toggle('open');
  btn.setAttribute('aria-expanded', open);
});
menu.addEventListener('click', e => { if (e.target.tagName === 'A') { menu.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
document.getElementById('contact-form').addEventListener('submit', e => {
  e.preventDefault();
  document.getElementById('form-note').textContent = 'Thanks! We\'ll be in touch soon.';
  e.target.reset();
});
