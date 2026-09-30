#!/usr/bin/env python3
"""JRS real — sestaví statický web z dat v _data/*.json do kořene repozitáře.
Obsah (nabídka, tým, služby, reference, kontakty, texty) se upravuje v _data/
(připraveno pro společnou administraci webhunter-admin)."""
import hashlib, html, json, os, pathlib, re, shutil
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / '_data'
J = lambda n: json.loads((DATA / f'{n}.json').read_text())
site, listings, team, projects = J('site'), J('listings'), J('team'), J('projects')
reviews, services, process, faq = J('reviews'), J('services'), J('process'), J('faq')
listings = [l for l in listings if not l.get('hidden')]
listings.sort(key=lambda l: -int(l['id']))
TEAM = {t['id']: t for t in team}
esc = lambda s: html.escape(str(s or ''), quote=True)
h8 = lambda p: hashlib.md5((ROOT / p).read_bytes()).hexdigest()[:8]
V = {'css': h8('assets/style.css'), 'js': h8('assets/main.js')}

def md(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    return s.replace('\n', '<br>')

def fmt(n):
    return f'{int(n):,}'.replace(',', ' ') if n == int(n) else f'{n:,.1f}'.replace(',', ' ').replace('.', ',')

def tel(p): return 'tel:' + re.sub(r'[^\d+]', '', p)
def tel_h(p):
    d = re.sub(r'[^\d]', '', p)
    return f'+{d[:3]} {d[3:6]} {d[6:9]} {d[9:]}' if len(d) == 12 else p

UNIT = {'za měsíc': '/ měsíc', 'za m2': '/ m²', 'za m2/měsíc': '/ m² měsíčně'}
CAT = {'byty': 'Byty', 'domy': 'Domy', 'pozemky': 'Pozemky', 'komercni': 'Komerční', 'ostatni': 'Ostatní'}
DEAL = {'prodej': 'Prodej', 'pronajem': 'Pronájem'}
for l in listings:
    if not l.get('disposition'):
        m = re.search(r'\b(\d\+(?:kk|\d))\b', l['title'])
        l['disposition'] = m.group(1) if m else ''
    l['url'] = f"nemovitost/{l['slug']}.html"

I = {  # ikony (inline SVG, 24×24, stroke)
 'arr': '<svg class="arr" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>',
 'phone': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/></svg>',
 'mail': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
 'pin': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
 'photo': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="m21 16-5-5-9 8"/></svg>',
 'play': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4.5v15l13-7.5z"/></svg>',
 'left': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M20 12H5m6-6-6 6 6 6"/></svg>',
 'right': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>',
 'star': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8 6.6 19.7l1.1-6.1-4.5-4.2 6.1-.8z"/></svg>',
 'fb': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M14 8.5V7c0-.8.2-1.3 1.4-1.3H17V3h-2.4C11.9 3 11 4.6 11 6.9v1.6H9V11h2v10h3V11h2.4l.4-2.5z"/></svg>',
 'ig': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".8" fill="currentColor"/></svg>',
 'yt': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.8zM10 15V9l5.2 3z"/></svg>',
}
STARS = '<span class="stars" aria-label="5 hvězdiček">' + I['star'] * 5 + '</span>'

def price_html(l, small_style=''):
    if l.get('price'):
        u = UNIT.get(l.get('price_unit'), '')
        return f"{fmt(l['price'])} Kč" + (f' <small>{u}</small>' if u else '')
    return f'<small style="font-size:1rem">{esc(l.get("price_text") or "Cena na vyžádání")}</small>'

def facts(l):
    f = [l['disposition']] if l['disposition'] else []
    if l.get('area'): f.append(f"{fmt(l['area'])} m²")
    elif l.get('land'): f.append(f"pozemek {fmt(l['land'])} m²")
    return ' · '.join(f)

def card(l, root, lazy=True, big=False):
    img = l['photos'][0] if big and l['photos'] else l['thumb']
    n = len(l['photos'])
    return f'''<a class="card rv" href="{root}{l['url']}">
  <div class="card__img"><span class="card__tag{' card__tag--rent' if l['deal'] == 'pronajem' else ''}">{DEAL[l['deal']]}</span>
  {f'<img src="{root}{img}" alt="{esc(l["title"])}" loading="{"lazy" if lazy else "eager"}" width="{1200 if big else 640}" height="{900 if big else 480}">' if img else ''}
  {f'<span class="card__n">{I["photo"]}{n}</span>' if n > 1 else ''}</div>
  <div class="card__body"><span class="card__loc">{esc(l['locality'] or l['town'])}</span><h3 class="card__title">{esc(l['title'])}</h3>
  <div class="card__meta"><span class="card__price">{price_html(l)}</span><span class="card__facts">{facts(l)}</span></div></div></a>'''

def mini(l):
    return {'id': int(l['id']), 'url': l['url'], 't': l['title'], 'deal': l['deal'], 'cat': l['category'], 'sub': l['subcategory'],
            'disp': l['disposition'], 'loc': l['locality'] or l['town'], 'district': l['district'], 'price': l['price'],
            'pt': l['price_text'], 'unit': UNIT.get(l['price_unit'], ''), 'area': l['area'], 'land': l['land'],
            'img': l['thumb'], 'n': len(l['photos']), 'broker': l['broker'],
            'ps': l['price'] if l['price'] and 'm2' not in (l['price_unit'] or '') else None}

def ldata(root):
    arr = [mini(l) for l in listings]
    for a in arr:
        a['url'] = root + a['url']; a['img'] = root + a['img'] if a['img'] else ''
    return '<script id="ldata" type="application/json">' + json.dumps(arr, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'

districts = [d for d, _ in Counter(l['district'] for l in listings if l['district']).most_common()]
NAV = [('nabidka', 'nabidka.html', 'Nabídka'), ('projekty', 'projekty.html', 'Projekty'), ('sluzby', 'sluzby.html', 'Služby'),
       ('onas', 'o-nas.html', 'O nás'), ('kontakt', 'kontakt.html', 'Kontakt')]
S = site

def layout(title, desc, body, root='', active='', over=False, body_class='', extra=''):
    nav = ''.join(f'<a href="{root}{h}"{" aria-current=page" if k == active else ""}>{t}</a>' for k, h, t in NAV)
    mnav = ''.join(f'<a class="big" href="{root}{h}">{t}</a>' for k, h, t in NAV)
    return f'''<!doctype html>
<html lang="cs" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#00354C">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{root}assets/img/hero-m.webp">
<link rel="icon" type="image/png" href="{root}assets/img/favicon.png">
<link rel="apple-touch-icon" href="{root}assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/style.css?v={V['css']}">
{extra}
</head>
<body class="{body_class}">
<a class="sr" href="#main">Přeskočit na obsah</a>
<header class="hdr{' hdr--over' if over else ''}">
  <div class="shell hdr__in">
    <a class="hdr__logo" href="{root}index.html" aria-label="JRS real – úvod">
      <img class="lg-dark" src="{root}assets/img/logo.png" alt="JRS real | Jihomoravská realitní skupina" width="992" height="112">
      <img class="lg-light" src="{root}assets/img/logo-light.png" alt="" width="992" height="112">
    </a>
    <nav class="nav" aria-label="Hlavní navigace">{nav}
      <a class="hdr__tel" href="{tel(S['contact.phone'])}">{I['phone']}{esc(S['contact.phone'])}</a>
      <a class="btn" href="{root}kontakt.html?tema=odhad#formular">Odhad ceny</a>
    </nav>
    <button class="burger" aria-expanded="false" aria-controls="mnav" aria-label="Menu"><span></span><span></span></button>
  </div>
</header>
<div class="mnav" id="mnav">{mnav}
  <a class="big" href="{root}kontakt.html?tema=odhad#formular"><em>Odhad ceny</em></a>
  <div class="mnav__foot"><a href="{tel(S['contact.phone'])}">{esc(S['contact.phone'])}</a><a href="mailto:{S['contact.email']}">{S['contact.email']}</a><span>{esc(S['contact.office'])}</span></div>
</div>
<main id="main">
{body}
</main>
{footer(root)}
<div class="lb" role="dialog" aria-modal="true" aria-label="Fotogalerie">
  <button class="lb__close" aria-label="Zavřít">×</button>
  <button class="lb__btn lb__prev" aria-label="Předchozí">{I['left']}</button>
  <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="">
  <button class="lb__btn lb__next" aria-label="Další">{I['right']}</button>
  <span class="lb__count"></span>
</div>
<script src="{root}assets/main.js?v={V['js']}" defer></script>
</body>
</html>'''

def footer(root):
    return f'''<footer class="ftr">
  <div class="shell">
    <p class="ftr__giant">Jihomoravská<br><em>realitní skupina</em></p>
    <div class="ftr__grid">
      <div><img class="ftr__logo" src="{root}assets/img/logo-light.png" alt="JRS real" width="992" height="112" loading="lazy">
        <p>Prodej, pronájem a odhad nemovitostí na jižní Moravě. Právní servis a financování pod jednou střechou.</p>
        <div class="social"><a href="{S['contact.facebook']}" aria-label="Facebook" rel="noopener">{I['fb']}</a><a href="{S['contact.instagram']}" aria-label="Instagram" rel="noopener">{I['ig']}</a><a href="{S['contact.youtube']}" aria-label="YouTube" rel="noopener">{I['yt']}</a></div></div>
      <div><h4>{esc(S['contact.office_title'])}</h4><ul><li>{esc(S['contact.office'])}</li><li>{esc(S['contact.hours'])}</li><li><a href="{tel(S['contact.phone'])}">{esc(S['contact.phone'])}</a></li><li><a href="mailto:{S['contact.email']}">{S['contact.email']}</a></li></ul></div>
      <div><h4>Web</h4><ul><li><a href="{root}nabidka.html">Nabídka nemovitostí</a></li><li><a href="{root}projekty.html">Developerské projekty</a></li><li><a href="{root}sluzby.html">Služby</a></li><li><a href="{root}o-nas.html">O nás a tým</a></li><li><a href="{root}kontakt.html">Kontakt</a></li></ul></div>
      <div><h4>Firma</h4><ul><li>{esc(S['legal_name'])}</li><li>IČ {S['contact.ico']} · DIČ {S['contact.dic']}</li><li>Sídlo: {esc(S['contact.seat'])}</li><li style="font-size:.8rem">{esc(S['contact.register'])}</li></ul></div>
    </div>
    <div class="ftr__bottom"><span>© 2026 {esc(S['legal_name'])}</span><span>Návrh nového webu · ukázka · údaje o nabídce k {esc(S['data.date'])}</span></div>
  </div>
</footer>'''

def form(root, dark=False, topic_default='prodej', listing=None):
    topics = [('prodej', 'Chci prodat'), ('odhad', 'Odhad ceny'), ('koupe', 'Chci koupit'), ('pronajem', 'Pronájem'), ('jine', 'Jiný dotaz')]
    chips = ''.join(f'<label class="chip"><input type="radio" name="tema" value="{v}"{" checked" if v == topic_default else ""}><span>{t}</span></label>' for v, t in topics)
    extra = ''
    if listing:
        chips = ''
        extra = '''<div class="field"><span>Preferovaný den prohlídky</span><select name="den"><option>Všední dny</option><option>Víkend</option></select></div>
<div class="field"><span>Preferovaný čas</span><select name="cas"><option>Dopoledne</option><option>Odpoledne</option><option>Večer</option></select></div>'''
    msg = f'Mám zájem o nemovitost „{listing["title"]}“. Prosím o kontakt a termín prohlídky.' if listing else ''
    return f'''<form class="form" data-demo novalidate>
  {f'<div class="full"><div class="chips" role="radiogroup" aria-label="S čím vám pomůžeme">{chips}</div></div>' if chips else ''}
  <label class="field full"><span>Jméno a příjmení</span><input name="jmeno" autocomplete="name" required></label>
  <label class="field"><span>Telefon</span><input name="telefon" type="tel" autocomplete="tel" required></label>
  <label class="field"><span>E-mail</span><input name="email" type="email" autocomplete="email"></label>
  {extra}
  <label class="field full"><span>Zpráva</span><textarea name="zprava" placeholder="Co vás zajímá? Adresa nemovitosti, typ, termín…">{esc(msg)}</textarea></label>
  <p class="form__note full">Ozveme se nejpozději do 24 hodin. Odesláním souhlasíte se zpracováním osobních údajů.</p>
  <div class="full"><button class="btn{' btn--gold' if dark else ''}" type="submit">Odeslat poptávku {I['arr']}</button></div>
  <p class="form__ok">Děkujeme. Tohle je ukázka nového webu – formulář zatím neodesílá. Zavolejte prosím na <a href="{tel(S['contact.phone'])}"><b>{esc(S['contact.phone'])}</b></a>.</p>
</form>'''

def words(s):
    """Split heading into word-reveal spans; *x* → italic line."""
    out, i = [], 0
    for li, line in enumerate(s.split('\n')):
        em = line.startswith('*') and line.endswith('*')
        text = line.strip('*')
        ws = []
        for w in text.split(' '):
            ws.append(f'<span class="w"><span style="--i:{i}">{esc(w)}</span></span>'); i += 1
        inner = ' '.join(ws)
        out.append(f'<span class="ln">{"<em>" + inner + "</em>" if em else inner}</span>')
    return ''.join(out)

def write(path, content):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    _NB = re.compile(r'(?<![\w&;])([vszkouiaVSZKOUIA]) (?=\S)')
    parts = re.split(r'(<script.*?</script>|<style.*?</style>|<svg.*?</svg>|<[^>]+>)', content, flags=re.S)
    content = ''.join(x if i % 2 else _NB.sub(r'\1&nbsp;', x) for i, x in enumerate(parts))
    p.write_text(content)

# ---------------------------------------------------------------- HOME
def home():
    r = ''
    feat_ids = [x.strip() for x in S.get('home.featured', '').split(',') if x.strip()]
    feat = [l for l in listings if l.get('home')] or [l for l in listings if l['id'] in feat_ids]
    feat = (feat + [l for l in listings if l not in feat])[:5]
    wine = [l for l in listings if l['subcategory'] in ('Vinný sklep', 'Sady / Vinice') or 'sklep' in l['title'].lower()]
    wine.sort(key=lambda l: (l['subcategory'] != 'Vinný sklep', 'vinic' in l['title'].lower(), -int(l['id'])))
    n_all = len(listings)
    broker = TEAM[S['featured.broker']]
    n_broker = sum(1 for l in listings if l['broker'] == broker['id'])
    makleri = [t for t in team if t['group'] == 'makleri']
    hero_l = next((l for l in listings if l['id'] == '248'), None)
    dist_opts = ''.join(f'<option value="{esc(d)}">{esc(d)}</option>' for d in districts)
    cat_opts = ''.join(f'<option value="{k}">{v}</option>' for k, v in CAT.items())
    marquee = ''.join(f'<span>{esc(m)}</span>' for m in S['marquee'])
    svc = ''.join(f'''<a class="svc rv" href="sluzby.html#{s['id']}"{f' data-img="{s["image"]}"' if s['image'] else ''}><span class="svc__no">{i+1:02d}</span><h3>{esc(s['title'])}</h3><p>{esc(s['lead'])}</p></a>''' for i, s in enumerate(services))
    faces = ''.join(f'<a href="o-nas.html#tym" title="{esc(t["name"])}"><img src="{t["photo"]}" alt="{esc(t["name"])}" loading="lazy" width="300" height="480"></a>' for t in makleri if t['id'] != S['featured.broker'])
    projs = ''.join(f'''<a class="proj rv" href="projekty.html#{p['id']}" style="--i:{i}"><img src="{p['photos'][0]}" alt="{esc(p['title'])}" loading="lazy" width="1400" height="1050">
  <div class="proj__txt"><span class="label label--light">{esc(p['town'])}</span><h3>{esc(p['title'].split(' – ')[0])}</h3><div class="row"><span>Ceny od <b>{esc(p['price_from'])}</b></span><span>Detail projektu →</span></div></div></a>''' for i, p in enumerate(projects))
    rv = reviews[1]
    small_revs = ''.join(f'<article class="rev rv" style="--i:{i}"><p>{esc(x["text"])}</p><footer><b>{esc(x["name"])}</b><span>{esc(x["date"])}</span></footer></article>' for i, x in enumerate(reviews[2:5]))
    body = f'''
<section class="hero">
  <div class="hero__media"><picture><source media="(max-width: 700px)" srcset="{S['hero.image'].replace('.webp', '-m.webp')}"><img src="{S['hero.image']}" alt="Vinice na jižní Moravě" width="1920" height="1446" fetchpriority="high"></picture></div>
  <div class="shell hero__in">
    <span class="label label--light fade-in" style="--d:.2s">{esc(S['tagline'])} · Hustopeče</span>
    <h1 class="wr">{words(S['hero.title'])}</h1>
    <div class="hero__row">
      <div><p class="lead fade-in" style="--d:.9s">{esc(S['hero.lead'])}</p>
        <div class="hero__cta fade-in" style="--d:1.05s"><a class="btn btn--gold" href="nabidka.html">Prohlédnout nabídku {I['arr']}</a><a class="btn btn--ghost" href="kontakt.html?tema=prodej#formular">Chci prodat</a></div></div>
      {f'<a class="hero__cap fade-in" style="--d:1.3s" href="{hero_l["url"]}">{esc(S["hero.caption"])}</a>' if hero_l else ''}
    </div>
  </div>
  <span class="scroll-ind" aria-hidden="true">Scroll</span>
</section>

<div class="finder shell">
  <form class="finder__box" id="finder" action="nabidka.html">
    <div class="seg" role="radiogroup" aria-label="Typ nabídky">
      <label><input type="radio" name="deal" value="prodej" checked><span>Koupit</span></label>
      <label><input type="radio" name="deal" value="pronajem"><span>Pronajmout</span></label>
    </div>
    <label class="field"><span>Typ nemovitosti</span><select name="cat"><option value="">Všechny typy</option>{cat_opts}</select></label>
    <label class="field"><span>Okres</span><select name="district"><option value="">Celá nabídka</option>{dist_opts}</select></label>
    <button class="btn btn--gold" type="submit">Zobrazit <b data-n>{n_all}</b> nabídek {I['arr']}</button>
  </form>
</div>

<div class="marquee" aria-hidden="true"><div class="marquee__track">{marquee}{marquee}</div></div>

<section class="sec">
  <div class="shell">
    <div class="sec-head"><div><span class="label">Nově v nabídce</span><h2>Domy, byty a pozemky <em>od Brna po Pálavu</em></h2></div>
      <a class="link" href="nabidka.html">Celá nabídka · {n_all} nemovitostí {I['arr']}</a></div>
    <div class="fresh">{''.join(card(l, '', big=(i == 0)) for i, l in enumerate(feat))}</div>
  </div>
</section>

<section class="sec dark stats">
  <span class="stats__bg" aria-hidden="true">JRS</span>
  <div class="shell">
    <span class="label">Jihomoravská realitní skupina</span>
    <h2 class="rv" style="margin-top:1rem;max-width:18ch">Znáte nás podle nemovitostí, <em>které právě prodáváme.</em></h2>
    <div class="stats__grid">
      <div class="stat rv"><span class="stat__n" data-to="{n_all}">0</span><p>nemovitostí v aktuální nabídce na jrsreal.cz</p></div>
      <div class="stat rv" style="--i:1"><span class="stat__n"><span data-to="{S['rating.value']}">0</span><sup>/5</sup></span><p>hodnocení na <a href="{S['rating.url']}" rel="noopener">{esc(S['rating.source'])}</a> z {esc(S['rating.count'])} recenzí</p></div>
      <div class="stat rv" style="--i:2"><span class="stat__n" data-to="{len(wine)}">0</span><p>vinných sklepů, vinic a domů se sklepem v nabídce</p></div>
      <div class="stat rv" style="--i:3"><span class="stat__n" data-to="{len(makleri)}">0</span><p>makléřů a zázemí asistentek v kanceláři v Hustopečích</p></div>
    </div>
  </div>
</section>

<section class="sec">
  <div class="shell">
    <div class="wine-intro">
      <div><span class="label">Specialita jižní Moravy</span>
        <h2 style="margin-top:1rem">Sklepy, vinice <em>a&nbsp;domy pod Pálavou</em></h2>
        <p class="lead" style="margin-top:1.5rem">Vinné sklepy s ubytováním, zavedené vinice i rodinné domy se sklepem. Region, kde naši makléři žijí a který znají i mimo práci.</p></div>
      <div class="wine-photo clip"><img src="assets/img/sklep.webp" alt="Klenutý vinný sklep z naší nabídky" loading="lazy" width="1920" height="1281"></div>
    </div>
  </div>
  <div class="strip-wrap" data-strip style="margin-top:clamp(2.5rem,5vw,4rem)">
    <div class="shell" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.2rem"><span class="muted" style="font-size:.9rem">{len(wine)} nabídek · posuňte do strany</span>
      <div class="strip-ctrl"><button class="icon-btn" data-dir="-1" aria-label="Předchozí">{I['left']}</button><button class="icon-btn" data-dir="1" aria-label="Další">{I['right']}</button></div></div>
    <div class="strip">{''.join(card(l, '', big=True) for l in wine[:14])}
      <a class="card" href="nabidka.html?q=sklep" style="display:grid;place-content:center;text-align:center;background:var(--navy);color:var(--on-dark);border-radius:var(--r-md);aspect-ratio:3/4;padding:2rem"><span style="font:400 2.2rem/1.1 var(--serif)">Všechny <em style="color:var(--gold)">sklepy</em><br>a vinice</span><span style="margin-top:1rem;color:var(--gold)">{I['arr']}</span></a>
    </div>
  </div>
</section>

<section class="sec sec--paper">
  <div class="shell">
    <div class="sec-head"><div><span class="label">Realitní servis od A do Z</span><h2>Co pro vás <em>zařídíme</em></h2></div>
      <p class="muted" style="max-width:38ch">Od odhadu ceny přes marketing a prohlídky až po advokátní úschovu a předání klíčů.</p></div>
    <div class="svc-list">{svc}</div>
  </div>
  <div class="svc-preview" aria-hidden="true"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt=""></div>
</section>

<section class="sec" style="padding-bottom:0">
  <div class="shell">
    <div class="broker-feat">
      <div></div>
      <div><span class="label">Jednatel společnosti</span>
        <h2 style="margin-top:1rem">{esc(broker['name'].split()[0])} <em>{esc(broker['name'].split()[1])}</em>, MRE</h2></div>
    </div>
  </div>
</section>
<section class="sec dark" style="padding-top:clamp(3rem,6vw,5rem)">
  <div class="shell">
    <div class="broker-feat" style="align-items:start">
      <div class="broker-feat__photo clip"><img src="{broker['photo']}" alt="{esc(broker['name'])}" loading="lazy" width="673" height="1134">
        <span class="broker-feat__badge">MRE<small>Master of<br>Real Estate</small></span></div>
      <div>
        <p class="lead">{esc(broker['bio'].split(chr(10)+chr(10))[1] if broker['bio'] else '')}</p>
        <blockquote class="quote">{esc(S['featured.quote'])}</blockquote>
        <p class="quote-by">— {esc(S['featured.quote_author'])}</p>
        <div class="contact-lines"><a href="{tel(broker['phone'])}" style="color:var(--on-dark)">{I['phone']}{tel_h(broker['phone'])}</a><a href="mailto:{broker['email']}" style="color:var(--on-dark)">{I['mail']}{broker['email']}</a></div>
        <div style="display:flex;flex-wrap:wrap;gap:.8rem"><a class="btn btn--gold" href="nabidka.html?broker={broker['id']}">Jeho nabídka · {n_broker} {I['arr']}</a><a class="btn btn--ghost" href="o-nas.html#tym">Celý tým</a></div>
      </div>
    </div>
  </div>
</section>
<div class="faces-wrap"><div class="faces" style="background:linear-gradient(var(--navy-deep) 62%, var(--cream) 62%)">{faces}</div></div>

<section class="sec">
  <div class="shell">
    <div class="sec-head"><div><span class="label">Developerské projekty</span><h2>Nové bydlení <em>na jižní Moravě</em></h2></div>
      <a class="link" href="projekty.html">Oba projekty {I['arr']}</a></div>
    <div class="proj-grid">{projs}</div>
  </div>
</section>

<section class="sec sec--alt">
  <div class="shell">
    <span class="label">Reference klientů</span>
    <blockquote class="rev-big rv">„{esc(rv['text'])}“</blockquote>
    <div class="rev-meta"><span><b style="font-weight:500">{esc(rv['name'])}</b> <span class="muted">· reference na jrsreal.cz</span></span>{STARS}<a class="link" href="{S['rating.url']}" rel="noopener">{esc(S['rating.value'])} / 5 · {esc(S['rating.count'])} recenzí na {esc(S['rating.source'])} {I['arr']}</a></div>
    <div class="rev-grid">{small_revs}</div>
  </div>
</section>

<section class="sec dark cta" id="kontakt">
  <div class="shell cta__grid">
    <div><span class="label">Nezávazně</span><h2 style="margin:1rem 0 1.5rem">{md(S['cta.title'])}</h2><p class="lead">{esc(S['cta.lead'])}</p>
      <div class="contact-lines"><a href="{tel(S['contact.phone'])}">{I['phone']}{esc(S['contact.phone'])}</a><a href="mailto:{S['contact.email']}">{I['mail']}{S['contact.email']}</a><span style="display:inline-flex;gap:.8rem;align-items:center;color:var(--on-dark-muted)">{I['pin'].replace('<svg', '<svg style="width:1.1rem;height:1.1rem;color:var(--gold)"')}{esc(S['contact.office'])}</span></div></div>
    {form('', dark=True)}
  </div>
</section>
{ldata('')}'''
    write('index.html', layout(f"{S['name']} — {S['tagline']}", 'Realitní kancelář JRS real: prodej, pronájem a odhad nemovitostí na jižní Moravě. Kancelář v Hustopečích.', body, '', '', over=True))

# ---------------------------------------------------------------- NABÍDKA
def nabidka():
    deal_btns = ''.join(f'<button class="fchip" type="button" data-deal="{k}" aria-pressed="false">{t} <small></small></button>' for k, t in [('', 'Vše'), ('prodej', 'Prodej'), ('pronajem', 'Pronájem')])
    cat_btns = ''.join(f'<button class="fchip" type="button" data-cat="{k}" aria-pressed="false">{t} <small></small></button>' for k, t in [('', 'Všechny typy')] + list(CAT.items()))
    dist_opts = ''.join(f'<option value="{esc(d)}">{esc(d)}</option>' for d in districts)
    disps = sorted({l['disposition'] for l in listings if l['disposition']}, key=lambda x: (int(x[0]), x))
    disp_opts = ''.join(f'<option>{d}</option>' for d in disps)
    brokers = [t for t in team if t['group'] == 'makleri' and any(l['broker'] == t['id'] for l in listings)]
    br_opts = ''.join(f'<option value="{t["id"]}">{esc(t["name"])}</option>' for t in brokers)
    body = f'''
<section class="phead" style="padding-bottom:2rem"><div class="shell">
  <nav class="crumbs" aria-label="Drobečková navigace"><a href="index.html">Úvod</a><span aria-hidden="true">/</span><span>Nabídka</span></nav>
  <h1>Nabídka <em>nemovitostí</em></h1>
  <p class="lead">Byty, domy, pozemky, vinné sklepy i komerční prostory k prodeji a pronájmu. Každou nemovitost vám rádi ukážeme osobně.</p>
</div></section>
<div id="listing-app">
  <div class="filters"><div class="shell">
    <div class="filters__bar">{deal_btns}<span class="fsep"></span>{cat_btns}
      <button class="fchip fmore" type="button" aria-expanded="false" aria-controls="fpanel">Další filtry <small></small></button></div>
    <div class="fpanel" id="fpanel">
      <label class="field w2"><span>Hledat</span><input name="q" type="search" placeholder="Obec, typ, např. sklep"></label>
      <label class="field"><span>Okres</span><select name="district"><option value="">Všechny</option>{dist_opts}</select></label>
      <label class="field fdisp"><span>Dispozice</span><select name="disp"><option value="">Vše</option>{disp_opts}</select></label>
      <label class="field"><span>Cena od (Kč)</span><input name="pmin" inputmode="numeric" placeholder="0"></label>
      <label class="field"><span>Cena do (Kč)</span><input name="pmax" inputmode="numeric" placeholder="bez limitu"></label>
      <label class="field"><span>Makléř</span><select name="broker"><option value="">Všichni</option>{br_opts}</select></label>
    </div>
  </div></div>
  <div class="shell">
    <div class="results-bar"><div><strong id="count">{len(listings)}</strong> <span class="muted">nemovitostí</span> <button class="reset" type="button" hidden>Zrušit filtry</button></div>
      <label class="field" style="grid-template-columns:auto 1fr;align-items:center;gap:.7rem"><span>Řadit</span><select name="sort" form="none" id="sortsel"><option value="new">Nejnovější</option><option value="cheap">Nejlevnější</option><option value="dear">Nejdražší</option></select></label></div>
    <div class="grid-cards" id="grid">{''.join(card(l, '') for l in listings[:24])}</div>
    <div class="empty"><h3>Tady zatím nic není</h3><p class="muted" style="margin-inline:auto">Zkuste upravit filtry, nebo nám napište, co hledáte – dáme vědět, jakmile se objeví.</p><a class="btn" href="kontakt.html?tema=koupe#formular">Zadat poptávku</a></div>
    <div class="more-wrap"><button class="btn btn--ghost" id="more" type="button"><span>Načíst další</span></button></div>
  </div>
</div>
<section class="sec"><div class="shell"><div class="sec-head" style="margin:0"><div><span class="label">Nenašli jste?</span><h2>Řekněte nám, <em>co hledáte.</em></h2></div><a class="btn" href="kontakt.html?tema=koupe#formular">Zadat poptávku {I['arr']}</a></div></div></section>
{ldata('')}'''
    html_ = layout('Nabídka nemovitostí — JRS real', 'Aktuální nabídka nemovitostí JRS real: byty, domy, pozemky, vinné sklepy a komerční prostory na jižní Moravě.', body, '', 'nabidka')
    # sort select lives outside panel → move name into panel logic: attach to panel via id
    html_ = html_.replace('<select name="sort" form="none" id="sortsel">', '<select name="sort" id="sortsel">')
    write('nabidka.html', html_)

# ---------------------------------------------------------------- DETAIL
def detail(l):
    root = '../'
    br = TEAM.get(l['broker'])
    ph = l['photos']
    gal = json.dumps([root + p for p in ph])
    dcls = f' n{min(len(ph), 5)}' if len(ph) < 5 else ''
    dbtn = ''.join(f'<button type="button" data-lb="{i}" aria-label="Fotografie {i+1}"><img src="{root}{p}" alt="" {"fetchpriority=high" if i == 0 else "loading=lazy"} width="1200" height="900"></button>' for i, p in enumerate(ph[:5]))
    mbtn = ''.join(f'<button type="button" data-lb="{i}" aria-label="Fotografie {i+1}"><img src="{root}{p}" alt="" {"" if i == 0 else "loading=lazy"} width="1200" height="900"></button>' for i, p in enumerate(ph))
    kf = [('Typ', f"{DEAL[l['deal']]} · {CAT[l['category']]}")]
    if l['disposition']: kf.append(('Dispozice', l['disposition']))
    if l.get('area'): kf.append(('Užitná plocha', f"{fmt(l['area'])} m²"))
    if l.get('land'): kf.append(('Pozemek', f"{fmt(l['land'])} m²"))
    if l.get('condition'): kf.append(('Stav', l['condition']))
    kf_html = ''.join(f'<div><dt>{k}</dt><dd>{esc(v)}</dd></div>' for k, v in kf[:4])
    paras = ''.join(f'<p>{esc(p)}</p>' for p in l['body'].split('\n\n') if p.strip())
    params = ''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in l['params'])
    loc_params = [('Obec', l['town']), ('Okres', l['district']), ('Kraj', l['region'])]
    params = ''.join(f'<div><dt>{k}</dt><dd>{esc(v)}</dd></div>' for k, v in loc_params if v) + params
    video = f'''<h2>Videoprohlídka</h2><button class="video" type="button" data-yt="{l['video']}" aria-label="Přehrát videoprohlídku"><img src="https://i.ytimg.com/vi/{l['video']}/maxresdefault.jpg" onerror="this.onerror=null;this.src='https://i.ytimg.com/vi/{l['video']}/hqdefault.jpg'" alt="" loading="lazy" width="1280" height="720"><span class="video__play">{I['play']}</span></button>''' if l.get('video') else ''
    q = f"{l['locality'] or l['town']}".replace(' ', '+')
    maplink = f"https://mapy.cz/zakladni?q={q}" + (f"&x={l['lng']}&y={l['lat']}&z=15" if l.get('lat') else '')
    sim = [x for x in listings if x is not l and x['category'] == l['category'] and x['deal'] == l['deal']]
    sim.sort(key=lambda x: (x['district'] != l['district'], abs((x['price'] or 0) - (l['price'] or 0))))
    sim = sim[:3]
    calc = ''
    if l['deal'] == 'prodej' and l.get('price') and l['price'] > 300000:
        calc = f'''<details class="calc"><summary>Kalkulačka hypotéky</summary><div class="calc__grid">
  <label class="field" style="grid-column:1/-1"><span>Cena nemovitosti (Kč)</span><input name="c_price" inputmode="numeric" value="{l['price']}"></label>
  <label class="field"><span>Vlastní zdroje</span><select name="c_own"><option value="10">10 %</option><option value="20" selected>20 %</option><option value="30">30 %</option><option value="40">40 %</option></select></label>
  <label class="field"><span>Doba splácení</span><select name="c_years"><option>15</option><option>20</option><option>25</option><option selected>30</option></select></label>
  <label class="field" style="grid-column:1/-1"><span>Úroková sazba (% p. a.)</span><input name="c_rate" inputmode="decimal" value="4,5"></label>
  <div class="calc__out"><span>Měsíční splátka</span><b>—</b></div>
  <p class="calc__hint">Orientační výpočet. Přesné podmínky zjistíme u bank v rámci služby Financování.</p></div></details>'''
    bcard = ''
    if br:
        bcard = f'''<div class="aside-card"><div class="bcard"><div class="bcard__img"><img src="{root}{br['photo']}" alt="" loading="lazy" width="300" height="480"></div>
  <div><span class="label" style="font-size:.66rem">Váš makléř</span><h3 style="margin-top:.5rem">{esc(br['name'])}</h3><p>{esc(br['role'])}{', ' + esc(br['title']) if br.get('title') else ''}</p></div></div>
  <div class="bcard__links"><a href="{tel(br['phone'])}">{I['phone']}{tel_h(br['phone'])}</a><a href="mailto:{br['email']}?subject={esc(l['title'])}">{I['mail']}{br['email']}</a></div>
  <a class="btn btn--gold" href="#zajem">Domluvit prohlídku {I['arr']}</a>{calc}</div>'''
    body = f'''
<div class="shell det-top">
  <nav class="crumbs" aria-label="Drobečková navigace"><a href="{root}index.html">Úvod</a><span aria-hidden="true">/</span><a href="{root}nabidka.html">Nabídka</a><span aria-hidden="true">/</span><a href="{root}nabidka.html?deal={l['deal']}&amp;cat={l['category']}">{CAT[l['category']]}</a></nav>
  <div data-gal='{esc(gal)}'>
    <div class="gal gal-d{dcls}">{dbtn}{f'<span class="gal__all">{I["photo"]}Všech {len(ph)} fotografií</span>' if len(ph) > 5 else ''}</div>
    <div class="gal-m-wrap"><div class="gal gal-m">{mbtn}</div>{f'<span class="gal-m-count">1 / {len(ph)}</span>' if len(ph) > 1 else ''}</div>
  </div>
</div>
<div class="shell det">
  <div class="det__body">
    <div class="det__head">
      <span class="label">{DEAL[l['deal']]} · {esc(l['subcategory'] or CAT[l['category']])}</span>
      <h1>{esc(l['title'])}</h1>
      <a class="det__loc link" href="{maplink}" rel="noopener" target="_blank">{I['pin']}{esc(l['locality'] or l['town'])}{', okres ' + esc(l['district']) if l['district'] else ''}</a>
      <p class="det__price">{price_html(l)}</p>
      {f'<p class="det__note">{esc(l["price_note"])}</p>' if l.get('price_note') else ''}
      {f'<div class="det__bm"><div class="cl__img"><img src="{root}{br["photo"]}" alt="" loading="lazy" width="300" height="480"></div><div><b>{esc(br["name"])}</b><a href="{tel(br["phone"])}">{tel_h(br["phone"])}</a></div></div>' if br else ''}
    </div>
    <dl class="keyfacts">{kf_html}</dl>
    <h2>O nemovitosti</h2>
    <div class="det__text">{paras}</div><button class="more-btn" type="button" hidden>Číst celý popis {I['arr']}</button>
    {video}
    <h2>Parametry</h2>
    <dl class="params">{params}</dl>
    <section id="zajem" style="scroll-margin-top:100px"><h2>Máte zájem? <em>Domluvme prohlídku.</em></h2>{form(root, listing=l)}</section>
  </div>
  <aside>{bcard}
    <div class="aside-card" style="box-shadow:none;background:transparent"><span class="label" style="font-size:.66rem">Kancelář</span><p style="margin:.6rem 0 0;font-size:.92rem">{esc(S['contact.office'])}<br>{esc(S['contact.hours'])}<br><a class="link" href="{tel(S['contact.phone'])}">{esc(S['contact.phone'])}</a></p></div>
  </aside>
</div>
{f"""<section class="sec sec--alt"><div class="shell"><div class="sec-head"><div><span class="label">Podobné nemovitosti</span><h2>Mohlo by vás <em>zaujmout</em></h2></div><a class="link" href="{root}nabidka.html?deal={l['deal']}&amp;cat={l['category']}">Více v kategorii {CAT[l['category']]} {I['arr']}</a></div>
<div class="grid-cards">{''.join(card(x, root) for x in sim)}</div></div></section>""" if sim else ''}
<div class="mbar">{f'<a class="btn btn--ghost" href="{tel(br["phone"])}">{I["phone"]}Zavolat</a>' if br else f'<a class="btn btn--ghost" href="{tel(S["contact.phone"])}">Zavolat</a>'}<a class="btn btn--gold" href="#zajem">Mám zájem</a></div>'''
    desc = (l['body'][:155] + '…') if len(l['body']) > 155 else l['body']
    write(l['url'], layout(f"{l['title']} — JRS real", desc, body, root, 'nabidka', body_class='has-mbar'))

# ---------------------------------------------------------------- SLUŽBY
def sluzby():
    cards = ''.join(f'''<article class="svc-card rv{'' if s['image'] else ' svc-card--dark'}" id="{s['id']}" style="--i:{i % 3};scroll-margin-top:100px">{f'<div class="svc-card__img"><img src="{s["image"]}" alt="" loading="lazy" width="1200" height="900"></div>' if s['image'] else '<div class="svc-card__img svc-card__type">' + ' · '.join(esc(p) for p in s['points']) + '</div>'}
  <div class="svc-card__b"><span class="label">{i+1:02d}</span><h3>{esc(s['title'])}</h3><p>{esc(s['lead'])}</p><ul class="ticks">{''.join(f'<li>{esc(p)}</li>' for p in s['points'])}</ul></div></article>''' for i, s in enumerate(services))
    steps = ''.join(f'<div class="step rv"><span class="step__n">{i+1}</span><div><h3>{esc(s["title"])}</h3><p>{esc(s["text"])}</p></div></div>' for i, s in enumerate(process))
    faqs = ''.join(f'<details><summary>{esc(f["q"])}</summary><p>{esc(f["a"])}</p></details>' for f in faq)
    body = f'''
<section class="phead"><div class="shell">
  <nav class="crumbs"><a href="index.html">Úvod</a><span aria-hidden="true">/</span><span>Služby</span></nav>
  <h1>Realitní servis <em>od A do Z</em></h1>
  <p class="lead">Na jednom místě od prvotního odhadu ceny až po právní servis a předání klíčů. Aby celý proces proběhl bezpečně, rychle a za nejvýhodnějších podmínek.</p>
</div></section>
<section class="sec" style="padding-top:0"><div class="shell"><div class="svc-cards">{cards}</div></div></section>
<section class="sec dark" id="odhad" style="scroll-margin-top:60px"><div class="shell split">
  <div class="split__sticky"><span class="label">Jak prodáváme</span><h2 style="margin:1rem 0 1.5rem">Pět kroků <em>k předání klíčů</em></h2><p class="lead">Každý krok s vámi transparentně konzultujeme. Vy se mezitím můžete věnovat rodině, práci nebo plánování dalšího bydlení.</p>
    <div class="wine-photo clip" style="margin-top:2rem;aspect-ratio:4/3"><img src="assets/img/palava.webp" alt="" loading="lazy" width="1920" height="1440"></div>
    <a class="btn btn--gold" style="margin-top:2rem" href="kontakt.html?tema=odhad#formular">Chci odhad ceny {I['arr']}</a></div>
  <div class="steps">{steps}</div>
</div></section>
<section class="sec"><div class="shell split">
  <div class="split__sticky"><span class="label">Prezentace nemovitosti</span><h2 style="margin:1rem 0 1.5rem">Aby nemovitost <em>zaujala na první pohled</em></h2>
    <p class="lead">Profesionální fotografie a HDR, videoprohlídky, záběry z dronu, 3D sken, půdorysy a homestaging. K tomu inzerce na realitních serverech, sociálních sítích a výkonnostní kampaně.</p></div>
  <div class="faq">{faqs}</div>
</div></section>'''
    write('sluzby.html', layout('Služby — JRS real', 'Prodej a pronájem nemovitostí, odhad ceny, financování, právní servis a developerské projekty. JRS real, jižní Morava.', body, '', 'sluzby'))

# ---------------------------------------------------------------- O NÁS
def tm_card(t, root='', lead=False):
    return f'''<article class="tm rv{' tm--lead' if lead else ''}"><div class="tm__img">{f'<span class="tm__badge">{esc(t["title"])}</span>' if t.get('title') else ''}<img src="{root}{t['photo']}" alt="{esc(t['name'])}" loading="lazy" width="300" height="480"></div>
  <div><h3>{esc(t['name'])}</h3><p class="role">{esc(t['role'])}</p></div>
  <div class="tm__c"><a href="{tel(t['phone'])}">{tel_h(t['phone'])}</a><a href="mailto:{t['email']}">{t['email']}</a></div></article>'''

def onas():
    founders = [t for t in team if 'Jednatel' in t['role']]
    others = [t for t in team if t['group'] == 'makleri' and t not in founders]
    asst = [t for t in team if t['group'] == 'asistentky']
    fh = ''.join(f'''<article class="founder rv"><div class="tm__img"><img src="{t['photo']}" alt="{esc(t['name'])}" loading="lazy" width="300" height="480"></div>
  <div><h3>{esc(t['name'])}</h3><p class="tag">{esc(t['role'])}{' · ' + esc(t['title']) if t.get('title') else ''}</p>{''.join(f'<p>{esc(p)}</p>' for p in t['bio'].split(chr(10)+chr(10)) if p)}
  <div class="tm__c"><a href="{tel(t['phone'])}">{tel_h(t['phone'])}</a><a href="mailto:{t['email']}">{t['email']}</a></div>
  <a class="link" style="margin-top:1rem" href="nabidka.html?broker={t['id']}">Nabídka makléře ({sum(1 for l in listings if l['broker'] == t['id'])}) {I['arr']}</a></div></article>''' for t in founders)
    revs = ''.join(f'<article class="rev rv" style="--i:{i % 3}"><p>{esc(x["text"])}</p><footer><b>{esc(x["name"])}</b><span>{esc(x["date"])}</span></footer></article>' for i, x in enumerate(reviews))
    body = f'''
<section class="phead"><div class="shell">
  <nav class="crumbs"><a href="index.html">Úvod</a><span aria-hidden="true">/</span><span>O nás</span></nav>
  <h1>Jihomoravská <em>realitní skupina</em></h1>
  <p class="lead">{esc(S['about.lead'])}</p>
</div></section>
<section class="sec" style="padding-top:0"><div class="shell">
  <dl class="facts">
    <div><dt>Společnost</dt><dd>{esc(S['legal_name'])}</dd></div>
    <div><dt>Na trhu od</dt><dd>{esc(S['contact.founded'])}</dd></div>
    <div><dt>Kancelář</dt><dd>Hustopeče, Kollárova 1442/4</dd></div>
  </dl>
  <p style="margin-top:2.5rem" class="lead">{esc(S['about.body'])}</p>
</div></section>
<figure class="ibreak"><img src="assets/img/drnholec.webp" alt="Rekreační rezidence s vinnými sklepy v Drnholci" loading="lazy" width="1920" height="1280"><figcaption class="shell">Drnholec · rekreační rezidence s vinnými sklepy z naší nabídky</figcaption></figure>
<section class="sec dark" id="tym" style="scroll-margin-top:60px"><div class="shell">
  <div class="sec-head"><div><span class="label">Vedení společnosti</span><h2>Jednatelé <em>a makléři</em></h2></div></div>
  <div class="founders">{fh}</div>
</div></section>
<section class="sec"><div class="shell">
  <div class="sec-head"><div><span class="label">Náš tým</span><h2>Makléři, kteří <em>znají region</em></h2></div><p class="muted" style="max-width:36ch">Každý z nich se specializuje na jiný typ nemovitostí – doporučíme vám toho, kdo nejlépe rozumí vašim potřebám.</p></div>
  <div class="team">{''.join(tm_card(t) for t in others)}</div>
  <div class="sec-head" style="margin-top:clamp(4rem,8vw,6rem)"><div><span class="label">Zázemí kanceláře</span><h2>Asistentky, které <em>hlídají každý krok</em></h2></div></div>
  <div class="team">{''.join(tm_card(t) for t in asst)}</div>
</div></section>
<section class="sec sec--alt"><div class="shell">
  <div class="sec-head"><div><span class="label">Reference</span><h2>Co o nás <em>píší klienti</em></h2></div><a class="link" href="{S['rating.url']}" rel="noopener">{STARS} &nbsp;{esc(S['rating.value'])} / 5 · {esc(S['rating.count'])} recenzí na {esc(S['rating.source'])} {I['arr']}</a></div>
  <div class="rev-grid">{revs}</div>
</div></section>
<section class="sec sec--tight"><div class="shell sec-head" style="margin:0"><div><span class="label">Kariéra</span><h2>Přidejte se <em>k nám</em></h2><p class="lead" style="margin-top:1rem">{esc(S['career.text'])}</p></div><a class="btn" href="kontakt.html?tema=jine#formular">Ozvat se {I['arr']}</a></div></section>'''
    write('o-nas.html', layout('O nás a tým — JRS real', 'JRS real s.r.o. – Jihomoravská realitní skupina. Jednatelé Jiří Šmach a Jan Vystoupil, tým makléřů a asistentek v Hustopečích.', body, '', 'onas'))

# ---------------------------------------------------------------- PROJEKTY
def projekty():
    blocks = ''
    for p in projects:
        br = TEAM.get(p['broker'])
        gal = json.dumps(p['photos'])
        btns = ''.join(f'<button type="button" data-lb="{i}" aria-label="Fotografie {i+1}"><img src="{ph}" alt="" loading="lazy" width="1400" height="1050"></button>' for i, ph in enumerate(p['photos'][:7]))
        paras = ''.join(f'<p>{esc(x)}</p>' for x in p['body'].split('\n\n'))
        blocks += f'''<article class="shell pj" id="{p['id']}" style="scroll-margin-top:80px">
  <div><div class="pj__gal" data-gal='{esc(gal)}'>{btns}</div><div style="margin-top:2.5rem">{paras}</div></div>
  <div class="pj__side"><span class="label">{esc(p['town'])} · okres {esc(p['district'])}</span><h2>{esc(p['title'])}</h2>
    <p class="price-from"><small>Ceny jednotek od</small>{esc(p['price_from'])}</p>
    {f"""<div class="aside-card"><div class="bcard"><div class="bcard__img"><img src="{br['photo']}" alt="" loading="lazy" width="300" height="480"></div><div><span class="label" style="font-size:.66rem">Projekt má na starosti</span><h3 style="margin-top:.5rem">{esc(br['name'])}</h3><p>{esc(br['role'])}</p></div></div>
    <div class="bcard__links"><a href="{tel(br['phone'])}">{I['phone']}{tel_h(br['phone'])}</a><a href="mailto:{br['email']}">{I['mail']}{br['email']}</a></div>
    <a class="btn btn--gold" href="kontakt.html?tema=koupe#formular">Mám zájem {I['arr']}</a></div>""" if br else ''}
  </div></article>'''
    body = f'''
<section class="phead"><div class="shell">
  <nav class="crumbs"><a href="index.html">Úvod</a><span aria-hidden="true">/</span><span>Developerské projekty</span></nav>
  <h1>Developerské <em>projekty</em></h1>
  <p class="lead">Moderní rodinné domy i domy s vinnými sklepy v atraktivních lokalitách jižní Moravy. Developerům pomáháme s nastavením cen, marketingem i prodejem jednotek.</p>
</div></section>
{blocks}
<section class="sec sec--tight"><div class="shell sec-head" style="margin:0"><div><span class="label">Pro developery</span><h2>Připravujete <em>projekt?</em></h2><p class="lead" style="margin-top:1rem">Od nastavení prodejní strategie a cen přes marketing až po finální rozprodej jednotek.</p></div><a class="btn" href="kontakt.html?tema=jine#formular">Probrat projekt {I['arr']}</a></div></section>'''
    write('projekty.html', layout('Developerské projekty — JRS real', 'Rezidence Hrušovany a Vinné domy Strachotín – developerské projekty v nabídce JRS real.', body, '', 'projekty'))

# ---------------------------------------------------------------- KONTAKT
def kontakt():
    people = [t for t in team if t['group'] in ('makleri', 'asistentky')]
    cl = ''.join(f'''<div class="cl"><div class="cl__img"><img src="{t['photo']}" alt="" loading="lazy" width="300" height="480"></div><div><b>{esc(t['name'])}</b><small>{esc(t['role'])}</small><a href="{tel(t['phone'])}">{tel_h(t['phone'])}</a><a href="mailto:{t['email']}">{t['email']}</a></div></div>''' for t in people)
    body = f'''
<section class="phead" style="padding-bottom:0"><div class="shell">
  <nav class="crumbs"><a href="index.html">Úvod</a><span aria-hidden="true">/</span><span>Kontakt</span></nav>
  <h1>Pojďme to <em>probrat osobně</em></h1>
</div></section>
<section class="sec" style="padding-top:clamp(2rem,4vw,3rem)"><div class="shell kontakt-grid">
  <div class="office">
    <p class="lead" style="margin:0">Plánujete prodej, koupi či pronájem nemovitosti nebo potřebujete odhad ceny? Jsme tu pro vás od první konzultace až po předání klíčů.</p>
    <div class="office__big"><a href="{tel(S['contact.phone'])}">{esc(S['contact.phone'])}</a><a href="mailto:{S['contact.email']}">{S['contact.email']}</a></div>
    <dl>
      <div><dt>{esc(S['contact.office_title'])}</dt><dd>{esc(S['contact.office'])}<br>{esc(S['contact.hours'])}<br><a class="link" href="https://mapy.cz/zakladni?q={S['contact.office'].replace(' ', '+')}" target="_blank" rel="noopener">Otevřít v Mapy.cz {I['arr']}</a></dd></div>
      <div><dt>Fakturační údaje</dt><dd>{esc(S['legal_name'])}<br>Sídlo: {esc(S['contact.seat'])}<br>IČ {S['contact.ico']} · DIČ {S['contact.dic']}<br><span class="muted" style="font-size:.85rem">{esc(S['contact.register'])}</span></dd></div>
    </dl>
    <div class="social" style="margin:0"><a href="{S['contact.facebook']}" aria-label="Facebook" style="border-color:var(--line-strong)">{I['fb']}</a><a href="{S['contact.instagram']}" aria-label="Instagram" style="border-color:var(--line-strong)">{I['ig']}</a><a href="{S['contact.youtube']}" aria-label="YouTube" style="border-color:var(--line-strong)">{I['yt']}</a></div>
  </div>
  <div id="formular" class="aside-card" style="scroll-margin-top:100px;padding:clamp(1.4rem,3vw,2.4rem)"><h2 style="font-size:clamp(2rem,3.4vw,2.8rem);margin-bottom:1.5rem">Napište nám</h2>{form('')}</div>
</div></section>
<section class="sec sec--alt"><div class="shell">
  <div class="sec-head"><div><span class="label">Přímé kontakty</span><h2>Chcete někoho <em>konkrétního?</em></h2></div></div>
  <div class="contact-list">{cl}</div>
</div></section>'''
    write('kontakt.html', layout('Kontakt — JRS real', 'Kontakt na realitní kancelář JRS real: Kollárova 1442/4, Hustopeče. Telefon +420 736 204 402, info@jrsreal.cz.', body, '', 'kontakt'))

def notfound():
    body = f'''<section class="phead" style="min-height:70vh"><div class="shell"><span class="label">Chyba 404</span><h1>Tahle stránka <em>už není v nabídce</em></h1><p class="lead">Možná byla nemovitost prodána. Podívejte se na aktuální nabídku.</p><a class="btn" href="/jrsreal/nabidka.html">Aktuální nabídka {I['arr']}</a></div></section>'''
    write('404.html', layout('Stránka nenalezena — JRS real', '', body.replace('href="/jrsreal/', 'href="/jrsreal/'), '/jrsreal/'))

# ---------------------------------------------------------------- run
if (ROOT / 'nemovitost').exists():
    shutil.rmtree(ROOT / 'nemovitost')
home(); nabidka(); sluzby(); onas(); projekty(); kontakt(); notfound()
for l in listings:
    detail(l)
(ROOT / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')
(ROOT / '.nojekyll').touch()
(ROOT / 'version.json').write_text(json.dumps({'sha': os.environ.get('GITHUB_SHA', 'local')}))
print(f'OK · {len(listings)} nemovitostí · css {V["css"]} · js {V["js"]}')
