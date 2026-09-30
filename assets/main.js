/* JRS real — interakce (bez knihoven, nativní scroll) */
(() => {
  const d = document, root = d.documentElement;
  root.classList.remove('no-js');
  const $ = (s, c = d) => c.querySelector(s), $$ = (s, c = d) => [...c.querySelectorAll(s)];
  const fmt = n => n.toLocaleString('cs-CZ').replace(/ /g, ' ');

  /* header */
  const hdr = $('.hdr');
  if (hdr) {
    const over = hdr.classList.contains('hdr--over');
    let last = scrollY, ticking = false;
    const upd = () => {
      const y = scrollY;
      hdr.classList.toggle('is-solid', !over || y > 40);
      const hide = y > 400 && y > last + 4 && !d.body.classList.contains('menu-open');
      const show = y < last - 4 || y < 400;
      if (hide) hdr.classList.add('is-hidden');
      else if (show) hdr.classList.remove('is-hidden');
      d.body.classList.toggle('hdr-shown', !hdr.classList.contains('is-hidden'));
      last = y; ticking = false;
    };
    addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(upd); } }, { passive: true });
    upd();
  }
  const burger = $('.burger'), mnav = $('.mnav');
  if (burger && mnav) {
    burger.addEventListener('click', () => {
      const open = burger.getAttribute('aria-expanded') !== 'true';
      burger.setAttribute('aria-expanded', open);
      mnav.classList.toggle('open', open);
      d.body.classList.toggle('menu-open', open);
      d.body.style.overflow = open ? 'hidden' : '';
    });
    $$('a', mnav).forEach(a => a.addEventListener('click', () => burger.click()));
  }

  /* reveal + counters */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.classList.add('in'); io.unobserve(e.target);
    if (e.target.dataset.to) count(e.target);
  }), { rootMargin: '0px 0px -8% 0px', threshold: .08 });
  $$('.rv, .clip, [data-to]').forEach(el => io.observe(el));
  function count(el) {
    const to = parseFloat(el.dataset.to.replace(',', '.')), dec = (el.dataset.to.split(',')[1] || '').length;
    const t0 = performance.now(), dur = 1600;
    const step = t => {
      const p = Math.min(1, (t - t0) / dur), v = to * (1 - Math.pow(1 - p, 4));
      el.textContent = dec ? v.toFixed(dec).replace('.', ',') : fmt(Math.round(v));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  /* service hover preview */
  const pv = $('.svc-preview');
  if (pv && matchMedia('(hover: hover) and (min-width: 900px)').matches) {
    const img = $('img', pv); let x = 0, y = 0, cx = 0, cy = 0, raf = 0, on = false;
    const loop = () => { cx += (x - cx) * .16; cy += (y - cy) * .16; pv.style.left = cx + 'px'; pv.style.top = cy + 'px'; raf = on || Math.abs(x - cx) > .5 ? requestAnimationFrame(loop) : 0; };
    $$('.svc[data-img]').forEach(r => {
      r.addEventListener('mouseenter', e => { img.src = r.dataset.img; on = true; x = cx = e.clientX + 170; y = cy = e.clientY; pv.classList.add('on'); if (!raf) raf = requestAnimationFrame(loop); });
      r.addEventListener('mousemove', e => { x = e.clientX + 170; y = e.clientY; });
      r.addEventListener('mouseleave', () => { on = false; pv.classList.remove('on'); });
    });
  }

  /* horizontal strip */
  $$('[data-strip]').forEach(w => {
    const s = $('.strip', w);
    $$('[data-dir]', w).forEach(b => b.addEventListener('click', () => s.scrollBy({ left: +b.dataset.dir * s.clientWidth * .8, behavior: 'smooth' })));
  });

  /* demo forms */
  $$('form[data-demo]').forEach(f => f.addEventListener('submit', e => {
    e.preventDefault(); f.classList.add('sent');
    const ok = $('.form__ok', f); if (ok) ok.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }));
  const tema = new URLSearchParams(location.search).get('tema');
  if (tema) $$(`input[name="tema"][value="${tema}"]`).forEach(i => i.checked = true);

  /* lightbox */
  const lb = $('.lb');
  if (lb) {
    const im = $('img', lb), cnt = $('.lb__count', lb); let list = [], i = 0, lastFocus;
    const show = () => { im.src = list[i]; cnt.textContent = `${i + 1} / ${list.length}`; };
    const open = (g, k) => { list = JSON.parse(g); i = k; show(); lb.classList.add('open'); d.body.style.overflow = 'hidden'; lastFocus = d.activeElement; $('.lb__close', lb).focus(); };
    const close = () => { lb.classList.remove('open'); d.body.style.overflow = ''; lastFocus && lastFocus.focus(); };
    const go = n => { i = (i + n + list.length) % list.length; show(); };
    $$('[data-lb]').forEach(b => b.addEventListener('click', () => open(b.closest('[data-gal]').dataset.gal, +b.dataset.lb)));
    $('.lb__prev', lb).onclick = () => go(-1); $('.lb__next', lb).onclick = () => go(1); $('.lb__close', lb).onclick = close;
    lb.addEventListener('click', e => { if (e.target === lb) close(); });
    addEventListener('keydown', e => { if (!lb.classList.contains('open')) return; if (e.key === 'Escape') close(); if (e.key === 'ArrowLeft') go(-1); if (e.key === 'ArrowRight') go(1); });
    let sx = 0; lb.addEventListener('touchstart', e => sx = e.touches[0].clientX, { passive: true });
    lb.addEventListener('touchend', e => { const dx = e.changedTouches[0].clientX - sx; if (Math.abs(dx) > 50) go(dx < 0 ? 1 : -1); });
  }
  const gm = $('.gal-m');
  if (gm) {
    const c = $('.gal-m-count'), n = gm.children.length;
    gm.addEventListener('scroll', () => { c.textContent = `${Math.round(gm.scrollLeft / gm.clientWidth) + 1} / ${n}`; }, { passive: true });
  }

  /* detail extras */
  const txt = $('.det__text');
  if (txt && txt.scrollHeight > 330) {
    txt.classList.add('clamped');
    const b = $('.more-btn'); b.hidden = false;
    b.onclick = () => { txt.classList.remove('clamped'); b.remove(); };
  }
  $$('.video[data-yt]').forEach(v => v.addEventListener('click', () => {
    v.innerHTML = `<iframe src="https://www.youtube-nocookie.com/embed/${v.dataset.yt}?autoplay=1&rel=0" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen title="Videoprohlídka"></iframe>`;
  }, { once: true }));
  const mbar = $('.mbar');
  if (mbar) addEventListener('scroll', () => mbar.classList.toggle('on', scrollY > 500), { passive: true });
  const calc = $('.calc');
  if (calc) {
    const f = n => $(`[name=${n}]`, calc), out = $('.calc__out b', calc);
    const run = () => {
      const price = +f('c_price').value.replace(/\D/g, ''), own = +f('c_own').value, r = +f('c_rate').value.replace(',', '.') / 1200, y = +f('c_years').value;
      const P = price * (1 - own / 100), n = y * 12;
      const m = r ? P * r / (1 - Math.pow(1 + r, -n)) : P / n;
      out.textContent = isFinite(m) && m > 0 ? fmt(Math.round(m / 10) * 10) + ' Kč' : '—';
    };
    $$('input, select', calc).forEach(i => i.addEventListener('input', run)); run();
  }

  /* data for finder + listing page */
  const dataEl = $('#ldata');
  const L = dataEl ? JSON.parse(dataEl.textContent) : [];

  /* home finder */
  const fd = $('#finder');
  if (fd) {
    const btnN = $('[data-n]', fd);
    const upd = () => {
      const deal = $('input[name=deal]:checked', fd).value, cat = fd.cat.value, dist = fd.district.value;
      const n = L.filter(x => x.deal === deal && (!cat || x.cat === cat) && (!dist || x.district === dist)).length;
      btnN.textContent = n;
    };
    fd.addEventListener('change', upd); upd();
    fd.addEventListener('submit', e => {
      e.preventDefault();
      const p = new URLSearchParams();
      p.set('deal', $('input[name=deal]:checked', fd).value);
      if (fd.cat.value) p.set('cat', fd.cat.value);
      if (fd.district.value) p.set('district', fd.district.value);
      location.href = fd.action.split('?')[0] + '?' + p;
    });
  }

  /* listing page filter */
  const app = $('#listing-app');
  if (app) {
    const grid = $('#grid', app), cntEl = $('#count', app), empty = $('.empty', app), moreBtn = $('#more', app);
    const panel = $('.fpanel', app), tgl = $('.fmore', app);
    const CAT = { byty: 'Byty', domy: 'Domy', pozemky: 'Pozemky', komercni: 'Komerční', ostatni: 'Ostatní' };
    const S = { deal: '', cat: '', district: '', disp: '', pmin: '', pmax: '', q: '', sort: 'new', broker: '' };
    const qs = new URLSearchParams(location.search);
    Object.keys(S).forEach(k => { if (qs.get(k)) S[k] = qs.get(k); });
    let shown = 24;
    const norm = s => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    const ctl = n => $(`[name=${n}]`, app);
    ['district', 'disp', 'pmin', 'pmax', 'q', 'sort', 'broker'].forEach(k => { const c = ctl(k); if (c) c.value = S[k]; });
    if (['district', 'disp', 'pmin', 'pmax', 'q', 'broker'].some(k => S[k])) { panel.classList.add('open'); tgl.setAttribute('aria-expanded', 'true'); }
    tgl.addEventListener('click', () => { const o = panel.classList.toggle('open'); tgl.setAttribute('aria-expanded', o); });
    const match = (x, skip) => (skip === 'deal' || !S.deal || x.deal === S.deal) && (skip === 'cat' || !S.cat || x.cat === S.cat)
      && (!S.district || x.district === S.district) && (!S.disp || x.disp === S.disp) && (!S.broker || x.broker === S.broker)
      && (!S.pmin || (x.ps && x.ps >= +S.pmin)) && (!S.pmax || (x.ps && x.ps <= +S.pmax))
      && (!S.q || norm(x.t + ' ' + x.loc + ' ' + x.sub).includes(norm(S.q)));
    const priceHtml = x => x.price ? `${fmt(x.price)} Kč${x.unit ? ` <small>${x.unit}</small>` : ''}` : `<small style="font-size:1rem">${x.pt || 'Cena na vyžádání'}</small>`;
    const facts = x => [x.disp, x.area ? fmt(x.area) + ' m²' : '', !x.area && x.land ? 'pozemek ' + fmt(x.land) + ' m²' : ''].filter(Boolean).join(' · ');
    const card = (x, k) => `<a class="card rv in" href="${x.url}">
      <div class="card__img"><span class="card__tag${x.deal === 'pronajem' ? ' card__tag--rent' : ''}">${x.deal === 'pronajem' ? 'Pronájem' : 'Prodej'}</span>
      ${x.img ? `<img src="${x.img}" alt="" loading="${k < 6 ? 'eager' : 'lazy'}" width="640" height="480">` : ''}
      ${x.n > 1 ? `<span class="card__n"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="m21 16-5-5-9 8"/></svg>${x.n}</span>` : ''}</div>
      <div class="card__body"><span class="card__loc">${x.loc}</span><h3 class="card__title">${x.t}</h3>
      <div class="card__meta"><span class="card__price">${priceHtml(x)}</span><span class="card__facts">${facts(x)}</span></div></div></a>`;
    const render = () => {
      let r = L.filter(x => match(x));
      if (S.sort === 'cheap') r.sort((a, b) => (a.ps || 9e12) - (b.ps || 9e12));
      else if (S.sort === 'dear') r.sort((a, b) => (b.ps || -1) - (a.ps || -1));
      else r.sort((a, b) => b.id - a.id);
      cntEl.textContent = r.length;
      grid.innerHTML = r.slice(0, shown).map(card).join('');
      empty.classList.toggle('on', !r.length);
      moreBtn.parentElement.hidden = r.length <= shown;
      moreBtn.querySelector('span').textContent = `Načíst další (${r.length - shown})`;
      $$('[data-deal]', app).forEach(b => {
        b.setAttribute('aria-pressed', b.dataset.deal === S.deal);
        const n = L.filter(x => match(x, 'deal') && (!b.dataset.deal || x.deal === b.dataset.deal)).length;
        $('small', b).textContent = n;
      });
      $$('[data-cat]', app).forEach(b => {
        b.setAttribute('aria-pressed', b.dataset.cat === S.cat);
        const n = L.filter(x => match(x, 'cat') && (!b.dataset.cat || x.cat === b.dataset.cat)).length;
        $('small', b).textContent = n; b.disabled = !n && b.dataset.cat !== S.cat;
      });
      $('.fdisp', app).hidden = !(S.cat === 'byty' || S.cat === 'domy' || S.cat === '');
      const p = new URLSearchParams(); Object.entries(S).forEach(([k, v]) => { if (v && !(k === 'sort' && v === 'new')) p.set(k, v); });
      history.replaceState(null, '', location.pathname + (p.toString() ? '?' + p : ''));
      const act = ['district', 'disp', 'pmin', 'pmax', 'q', 'broker'].filter(k => S[k]).length;
      $('small', tgl).textContent = act ? act : '';
      $('.reset', app).hidden = !Object.entries(S).some(([k, v]) => v && k !== 'sort');
    };
    $$('[data-deal]', app).forEach(b => b.addEventListener('click', () => { S.deal = b.dataset.deal; shown = 24; render(); }));
    $$('[data-cat]', app).forEach(b => b.addEventListener('click', () => { S.cat = b.dataset.cat; if (S.cat !== 'byty' && S.cat !== 'domy') S.disp = S.disp; shown = 24; render(); }));
    $$('.fpanel select, .fpanel input, #sortsel', app).forEach(c => c.addEventListener(c.tagName === 'INPUT' ? 'input' : 'change', () => { S[c.name] = c.value.trim(); shown = 24; render(); }));
    moreBtn.addEventListener('click', () => { shown += 24; render(); });
    $('.reset', app).addEventListener('click', () => { Object.keys(S).forEach(k => S[k] = k === 'sort' ? 'new' : ''); $$('.fpanel select, .fpanel input, #sortsel', app).forEach(c => c.value = c.name === 'sort' ? 'new' : ''); shown = 24; render(); });
    render();
  }
})();
