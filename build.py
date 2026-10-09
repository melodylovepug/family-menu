#!/usr/bin/env python3
"""Build index.html for the family menu site from menu.json (no Notion dependency).
Usage: python3 build.py   (run from the repo root; writes index.html next to this file)"""
import html, json, os, re
from datetime import date, timedelta
ROOT = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(ROOT, 'menu.json'), encoding='utf-8'))
E = html.escape

# Google Apps Script web app URL for the "添加新菜" form (see apps-script/Code.gs). Empty = form hidden and no fetch.
SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxx3byFZ09adGhHPDE4liQxCP2Bwx8OIErUbe2fIzKc0RCoq-Vt53IrNb8TV2yJHbSi/exec'
SCRIPT_URL = os.environ.get('MENU_SCRIPT_URL', SCRIPT_URL)   # test override only
# Protein spellings that mean the same thing for the no-repeat rule
PROT_CANON = {'虾': '龙虾/虾', '蛋': '豆腐/蛋'}
def canon(m): return PROT_CANON.get(m, m)
def is_skip(d):
    """'skip' tag: never drawn by the random picker. Accepts tag:'skip', tags:[...,'skip'] or skip:true in menu.json."""
    t = d.get('tags') or []
    if isinstance(t, str): t = re.split(r'[,\s]+', t)
    return bool(d.get('skip')) or str(d.get('tag') or '').strip().lower() == 'skip' or 'skip' in [str(x).lower() for x in t]

def inline(t):
    t = E(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    return t

def link(url, label, cls="lnk"):
    return f'<a class="{cls}" href="{E(url)}" target="_blank" rel="noopener">{E(label)}</a>'

def link_label(label, url):
    if 'xhslink' in url and not label.startswith('📕'): return '📕 ' + label
    if 'youtube' in url and not label.startswith('▶️'): return label if label.startswith('▶') else '▶️ ' + label
    return label if label[:1] in '📕▶🔗' else '🔗 ' + label

def md(text, photos=None, photo_ai=None):
    """Tiny markdown: ## h, > tip, - ul, 1. ol, ![](img:..), [label](url), **bold**."""
    out, lst, links = [], None, []
    def close():
        nonlocal lst
        if lst: out.append(f'</{lst}>'); lst = None
    def flush_links():
        if links: out.append('<div class="links">' + ''.join(links) + '</div>'); links.clear()
    for raw in text.splitlines():
        s = raw.strip()
        if not s: continue
        m_img = re.fullmatch(r'!\[\]\(img:[^)]*\)', s)
        m_lnk = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', s)
        if m_lnk:
            close(); links.append(link(m_lnk.group(2), link_label(m_lnk.group(1), m_lnk.group(2)))); continue
        flush_links()
        if m_img:
            close()
            if photos and photo_ai:   # real vs AI-enhanced, side by side
                fig = lambda src, cap, cls: (f'<figure class="{cls}"><a href="{E(src)}" target="_blank" rel="noopener">'
                                             f'<img class="ph" src="{E(src)}" alt="{cap}" loading="lazy"></a><figcaption>{cap}</figcaption></figure>')
                out.insert(0, '<div class="phc">' + fig(photos, '实拍', 'real') + fig(photo_ai, 'AI 美化', 'ai') + '</div>')
            elif photos: out.insert(0, f'<img class="ph" src="{E(photos)}" alt="" loading="lazy">')  # photo first
            continue
        if s.startswith('## '): close(); out.append(f'<h4>{inline(s[3:])}</h4>'); continue
        if s.startswith('> '): close(); out.append(f'<p class="tip">{inline(s[2:])}</p>'); continue
        m = re.match(r'^(\d+)\.\s*(.*)', s)
        if m:
            if lst != 'ol': close(); out.append('<ol>'); lst = 'ol'
            out.append(f'<li>{inline(m.group(2))}</li>'); continue
        if s.startswith('- '):
            if lst != 'ul': close(); out.append('<ul>'); lst = 'ul'
            out.append(f'<li>{inline(s[2:])}</li>'); continue
        close(); out.append(f'<p>{inline(s)}</p>')
    close(); flush_links()
    return ''.join(out)

LINK_SVG = ('<svg class="ri" viewBox="0 0 16 16" aria-hidden="true"><path d="M6.7 9.3a2.5 2.5 0 0 0 3.5 0l2.4-2.4a2.5 2.5 0 0 0-3.5-3.5l-.8.8'
            'M9.3 6.7a2.5 2.5 0 0 0-3.5 0L3.4 9.1a2.5 2.5 0 0 0 3.5 3.5l.8-.8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>')
REF_STATS = {'linked': [], 'nourl': []}

def pick_url(text, links):
    """Best card link for a '参考' line: match the platform it names, else the first card link."""
    t = text.lower()
    for l in links:
        u = l['url']
        if ('小红书' in text and 'xhslink' in u) or ('youtube' in t and ('youtube' in u or 'youtu.be' in u)): return u
    return links[0]['url'] if links else None

def split_refs(recipe, links):
    """Pull source lines out of a dish recipe ('[label](url)' lines and '> 参考：…' lines).
    Returns (recipe without them, [(url or None, text)]). Card links not mentioned anywhere get a fallback line."""
    keep, refs = [], {}
    for raw in recipe.splitlines():
        s = raw.strip()
        m = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', s)
        if m:
            label, url = m.group(1).lstrip('📕▶🔗\ufe0f '), m.group(2)
            if ('youtube' in url or 'youtu.be' in url) and not label.lower().startswith('youtube'): label = f'YouTube · {label}'
            refs.setdefault(url, label); continue
        m = re.fullmatch(r'>\s*参考\s*[：:]\s*(.+)', s)
        if m:
            refs[pick_url(m.group(1), links) or ('nourl', len(refs))] = m.group(1); continue   # 参考 text wins
        keep.append(raw)
    for l in links:
        if l['url'] not in refs: refs[l['url']] = link_label(l['label'], l['url']).lstrip('📕▶🔗\ufe0f ')
    return '\n'.join(keep), [(u if isinstance(u, str) else None, t) for u, t in refs.items()]

def ref_html(refs, name):
    """Source / tutorial links as tag pills for the top of the recipe sheet."""
    if not refs: return ''
    out = []
    for url, text in refs:
        if url:
            REF_STATS['linked'].append(name)
            ic = '📕 ' if 'xhslink' in url or 'xiaohongshu' in url else ('▶ ' if 'youtube' in url or 'youtu.be' in url else '🔗 ')
            out.append(f'<a class="lnk" href="{E(url)}" target="_blank" rel="noopener">{ic}{E(text)}</a>')
        else:
            REF_STATS['nourl'].append(name)
            out.append(f'<span class="lnk nolink">📖 {E(text)}</span>')
    return '<div class="srcs">' + ''.join(out) + '</div>'

def plain(text):
    t = re.sub(r'!\[\]\([^)]*\)|\]\([^)]*\)|[#>*\[\]]', ' ', text)
    return re.sub(r'\s+', ' ', t).lower()

CATS = D['categories']

def norm(t): return re.sub(r'\s+', '', t.replace('（', '(').replace('）', ')')).lower()
def last_eaten():
    """Most recent date each menu dish appears in D['history'] (matched on name or its explicit 'aliases')."""
    idx = {}
    for c in CATS:
        for d in c['dishes']:
            for k in [d['name']] + d.get('aliases', []): idx[norm(k)] = d['name']
    for t in D['todo']:
        if t.get('recent'): idx.setdefault(norm(t['name']), t['name'])
    last = {}
    for h in D.get('history', []):
        for raw in h['dishes']:
            nm = idx.get(norm(raw))
            if nm and h['date'] > last.get(nm, ''): last[nm] = h['date']
    return last
LAST = last_eaten()

# 📅 最近每周菜单 is derived from D['history'] (the same log the picker uses), grouped by week (Monday start), newest first.
# A week that also has a hand-written entry in D['weeks'] (older Notion weeks with extra notes) renders that entry verbatim.
WD = '一二三四五六日'
def week_key(iso): return (date.fromisoformat(iso) - timedelta(days=date.fromisoformat(iso).weekday())).isoformat()
def week_label(iso): x = date.fromisoformat(iso); return f'{x.month}.{x.day}.{x.year % 100}'
def build_weeks():
    curated = {w['date']: w for w in D['weeks']}
    groups = {}
    for h in D.get('history', []): groups.setdefault(week_key(h['date']), []).append(h)
    for w in D['weeks']:   # curated weeks without any history entry still show
        mo, dd, yy = map(int, w['date'].split('.')); groups.setdefault(date(2000 + yy, mo, dd).isoformat(), [])
    weeks = []
    for wk in sorted(groups, reverse=True):
        lab = week_label(wk)
        if lab in curated: weeks.append(dict(curated[lab], src='weeks')); continue
        lines = []
        for h in sorted(groups[wk], key=lambda h: (h['date'], h.get('who', ''))):
            x = date.fromisoformat(h['date'])
            day = f'{(h["who"] + " ") if h.get("who") else ""}周{WD[x.weekday()]} {x.month}/{x.day}' + (' · 计划' if h.get('planned') else '')
            lines.append(dict(day=day, items=h['dishes'], planned=bool(h.get('planned'))))
        weeks.append(dict(date=lab, lines=lines, src='history'))
    return weeks
WEEKS = build_weeks()

def extra_js():
    """Client code for dishes added through the Google Sheet form. Only emitted when SCRIPT_URL is set."""
    if not SCRIPT_URL: return ''
    known = sorted({norm(k) for c in CATS for d in c['dishes'] for k in [d['name']] + d.get('aliases', [])} | {norm(t['name']) for t in D['todo']})
    hist = {}
    for h in D.get('history', []):
        for raw in h['dishes']:
            k = norm(raw)
            if h['date'] > hist.get(k, ''): hist[k] = h['date']
    secs = {c['id']: [c['icon'], c['zh'], c['en']] + list(PAL[c['id']]) for c in CATS}
    cfg = dict(url=SCRIPT_URL, known=known, hist=hist, secs=secs, noPick=sorted(NO_PICK), canon=PROT_CANON, base=EB)
    return 'const ADD=' + json.dumps(cfg, ensure_ascii=False).replace('</', '<\\/') + ';\n' + open(os.path.join(ROOT, 'add.js'), encoding='utf-8').read()
def has_recipe(d): return bool(re.sub(r'^\s*\[[^\]]+\]\([^)]+\)\s*$', '', d['recipe'], flags=re.M).strip())
def has_body(d):
    """Real recipe content: anything besides link lines, photo markers and '>' tips."""
    return any(l.strip() and not re.fullmatch(r'\[[^\]]+\]\([^)]+\)|!\[\]\([^)]*\)|>.*', l.strip()) for l in d['recipe'].splitlines())
# Stable card ids (#d<n> deep links): dishes without an explicit 'id' are numbered in page order;
# newer dishes carry their own 'id' so adding them never renumbers existing links.
DID, _n = {}, 0
for c in CATS:
    for d in c['dishes']:
        if d.get('id'): DID[id(d)] = d['id']
        else: _n += 1; DID[id(d)] = f'd{_n}'
assert len(set(DID.values())) == len(DID), 'duplicate dish ids'
NO_PICK = {'sweet', 'lunch', 'other'}   # sections the picker never draws from
PICK = []
for c in CATS:
    for d in c['dishes']:
        m = canon(d.get('meat'))
        if is_skip(d) or c['id'] in NO_PICK or m == '甜品' or d.get('tag') == '甜品': continue      # never 午餐 / 其他 / dessert
        kind = 'cold' if c['id'] == 'cold' else ('main' if m and m != '素' else None)
        if not kind: continue                                                    # veg-only mains/staples are skipped
        PICK.append(dict(id=DID[id(d)], n=d['name'], k=kind, m=m, s=(c['id'] == 'soup' or '汤' in d['name']), t=bool(d.get('recent')),
                         r=has_body(d), o=bool(has_recipe(d) or d['ingredients'] or d['note'] or d['links'] or d.get('photo')), p=d.get('photo') or '', i=c['icon'], c=c['id'], l=LAST.get(d['name'], '')))
# 最近-tagged 待做 items join the pool as mains (needs a protein tag); at most ONE 待做/最近 dish per pick or swap result.
TID = {id(t): t.get('id') or f't{i}' for i, t in enumerate(D['todo'], 1)}
for t in D['todo']:
    if t.get('recent') and t.get('meat') and not is_skip(t) and t['meat'] not in ('素', '甜品'):
        PICK.append(dict(id=TID[id(t)], n=t['name'], k='main', m=canon(t['meat']), s=bool(t.get('soup')) or '汤' in t['name'], t=True, r=False,
                         o=bool(t.get('link') or t.get('details') or t.get('ingredients')), p='', i='🌸', c='todo', l=LAST.get(t['name'], '')))
total = sum(len(c['dishes']) for c in CATS)
out = []
PAL = {"beef":("#e2cdc4","#8a5f4f","#f6efeb"),"pork":("#efd9dc","#a36f78","#fbf2f3"),"poultry":("#e8dfc8","#8c7a4e","#f8f5ec"),"sea":("#d9e0e7","#66778a","#f2f4f6"),
 "cold":("#dbe2d4","#6f7f67","#f3f5f0"),"soup":("#ead8cc","#93705a","#f8f1ec"),"staple":("#e6dccd","#8e7b62","#f8f4ee"),"sweet":("#e2d8e2","#7d6a7d","#f6f2f6"),
 "lunch":("#cfe0dd","#4f7d76","#eef5f4"),"other":("#d8d6e8","#67658f","#f3f3f9")}
ONI = '''<svg class="oni" viewBox="0 0 120 110" aria-hidden="true">
<path d="M60 8C40 8 10 58 10 80c0 16 12 24 50 24s50-8 50-24C110 58 80 8 60 8z" fill="#fff" stroke="#4a403a" stroke-width="3.5" stroke-linejoin="round"/>
<rect x="34" y="70" width="52" height="34" rx="6" fill="#4a4e46"/>
<path d="M40 70h40" stroke="#5a5e55" stroke-width="2"/>
<circle cx="45" cy="56" r="4" fill="#4a403a"/><circle cx="75" cy="56" r="4" fill="#4a403a"/>
<circle cx="46.5" cy="54.5" r="1.3" fill="#fff"/><circle cx="76.5" cy="54.5" r="1.3" fill="#fff"/>
<ellipse cx="37" cy="64" rx="6" ry="3.5" fill="#e2bdb8"/><ellipse cx="83" cy="64" rx="6" ry="3.5" fill="#e2bdb8"/>
<path d="M54 62q6 6 12 0" fill="none" stroke="#4a403a" stroke-width="3" stroke-linecap="round"/>
</svg>'''
STEAM = '<svg class="steam" viewBox="0 0 60 40" aria-hidden="true"><path d="M12 36c-6-8 6-12 0-20s4-12 0-14M30 36c-6-8 6-12 0-20s4-12 0-14M48 36c-6-8 6-12 0-20s4-12 0-14" fill="none" stroke="#c9c0b8" stroke-width="3" stroke-linecap="round"/></svg>'
PETAL = '<svg class="petal {c}" viewBox="0 0 40 40" aria-hidden="true"><g fill="#e3cbc7" stroke="#c9a9a6" stroke-width="1"><path d="M20 20C14 10 16 3 20 6c4-3 6 4 0 14z"/><path d="M20 20C14 10 16 3 20 6c4-3 6 4 0 14z" transform="rotate(72 20 20)"/><path d="M20 20C14 10 16 3 20 6c4-3 6 4 0 14z" transform="rotate(144 20 20)"/><path d="M20 20C14 10 16 3 20 6c4-3 6 4 0 14z" transform="rotate(216 20 20)"/><path d="M20 20C14 10 16 3 20 6c4-3 6 4 0 14z" transform="rotate(288 20 20)"/></g><circle cx="20" cy="20" r="2.6" fill="#c8b78e"/></svg>'
out.append(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>家庭菜单 · Home Menu</title>
<style>
:root{{--bg:#f6f2ec;--card:#fcfaf6;--ink:#4a403a;--mute:#958a80;--line:#e6ded3;--pink:#b8928e;--pinkbg:#efe3e1;--matcha:#8f9e87;--sky:#d5dde4;--yel:#ede6d3;
--sc:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans SC","Source Han Sans SC","Noto Sans CJK SC","WenQuanYi Micro Hei",sans-serif}}
*{{box-sizing:border-box}}
html,body{{margin:0;color:var(--ink);font-family:var(--sc);-webkit-text-size-adjust:100%;
background-color:var(--bg);background-image:radial-gradient(#e6ddd2 1.3px,transparent 1.4px);background-size:22px 22px}}
.wrap{{max-width:980px;margin:0 auto;padding:0 14px 40px}}
/* noren curtain */
.noren{{display:flex;gap:6px;justify-content:center;padding:0 6px;margin:0 -14px}}
.noren::before{{content:"";position:absolute}}
.rod{{height:10px;margin:0 -14px;background:linear-gradient(#a89580,#857260);border-radius:0 0 6px 6px;box-shadow:0 2px 0 rgba(0,0,0,.06)}}
.noren span{{flex:1;max-width:96px;height:58px;border-radius:0 0 16px 16px;display:flex;align-items:center;justify-content:center;
font-size:22px;font-weight:800;color:#fff;letter-spacing:0;box-shadow:inset 0 -6px 0 rgba(255,255,255,.18)}}
.noren span:nth-child(1){{background:#b8928e}}.noren span:nth-child(2){{background:#8f9e87}}.noren span:nth-child(3){{background:#8394a3}}.noren span:nth-child(4){{background:#b5a273}}
header{{position:relative;text-align:center;padding:16px 8px 6px}}
.hero{{position:relative;display:inline-block;padding:6px 10px 0}}
.oni{{width:74px;height:68px;display:block;margin:0 auto -2px;animation:bob 3s ease-in-out infinite}}
.steam{{width:40px;height:26px;position:absolute;left:50%;top:-18px;transform:translateX(-50%);opacity:.8;animation:puff 2.6s ease-in-out infinite}}
@keyframes bob{{50%{{transform:translateY(-3px) rotate(-2deg)}}}}
@keyframes puff{{0%,100%{{opacity:.35;transform:translate(-50%,2px)}}50%{{opacity:.9;transform:translate(-50%,-3px)}}}}
h1{{margin:4px 0 0;font-size:36px;font-weight:800;letter-spacing:.12em;color:var(--ink);text-shadow:3px 3px 0 #e6d6d3}}
.jp{{display:inline-block;margin-top:6px;font-size:15px;color:#9c7773;background:#fff;border:2px dashed #d9c1be;border-radius:999px;padding:3px 14px;letter-spacing:.12em}}
.sub{{color:var(--mute);font-size:12.5px;margin-top:8px}}
.hanko{{position:absolute;right:-50px;top:44px;width:44px;height:44px;border:2.5px solid #a65e4e;color:#a65e4e;border-radius:10px;
display:flex;align-items:center;justify-content:center;font-size:12px;line-height:1.05;font-weight:800;transform:rotate(12deg);background:rgba(255,255,255,.7);
font-family:"Songti SC","STSong","Noto Serif SC","Source Han Serif SC","Noto Serif CJK SC",serif;text-align:center;opacity:.9}}
.petal{{position:absolute;width:24px;height:24px;opacity:.95}}
.p1{{left:4%;top:20px;transform:rotate(-15deg)}}.p2{{right:6%;top:6px;width:18px;height:18px}}.p3{{left:14%;top:112px;width:16px;height:16px;transform:rotate(30deg)}}.p4{{right:14%;top:120px;width:20px;height:20px}}
.washi{{height:14px;margin:12px auto 4px;max-width:260px;border-radius:2px;opacity:.85;transform:rotate(-1.2deg);
background:repeating-linear-gradient(45deg,#ddcbc8 0 8px,#fff 8px 14px)}}
nav{{position:sticky;top:0;z-index:5;padding:10px 2px 10px;display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;
background:linear-gradient(var(--bg) 78%,rgba(246,242,236,0))}}
nav::-webkit-scrollbar{{display:none}}
nav a{{flex:0 0 auto;text-decoration:none;color:var(--ink);background:#fff;border:2px solid var(--c,#e6d3d0);padding:6px 13px;border-radius:999px;font-size:14px;font-weight:700;white-space:nowrap;box-shadow:0 3px 0 var(--c,#e6d3d0)}}
nav a:active{{transform:translateY(2px);box-shadow:0 1px 0 var(--c,#e6d3d0)}}
.search{{width:100%;padding:12px 16px;border-radius:999px;border:2px solid #e3d7d2;background:#fff;font-size:16px;color:var(--ink);margin:4px 0 18px;font-family:inherit;outline:none;box-shadow:0 3px 0 #e8ded8}}
.search:focus{{border-color:var(--pink)}}
.grid{{display:grid;grid-template-columns:1fr;gap:24px;align-items:start}}
@media(min-width:760px){{.grid{{grid-template-columns:1fr 1fr}} h1{{font-size:44px}} .noren span{{max-width:130px;height:74px;font-size:28px}} .oni{{width:90px;height:82px}}}}
@media(max-width:420px){{.hanko{{right:-40px;top:40px;width:38px;height:38px;font-size:11px}}}}
.card{{position:relative;background:var(--cb);border:2px solid var(--ca);border-radius:26px;padding:0 14px 6px;box-shadow:0 6px 0 var(--ca),0 12px 22px -14px rgba(90,75,60,.22)}}
.card::before{{content:"";position:absolute;top:-9px;left:50%;width:84px;height:18px;transform:translateX(-50%) rotate(-3deg);border-radius:2px;opacity:.9;
background:repeating-linear-gradient(90deg,var(--ca) 0 6px,rgba(255,255,255,.75) 6px 12px)}}
.card h2{{margin:0 -14px 4px;padding:16px 16px 10px;background:var(--ca);border-radius:24px 24px 0 0;font-size:20px;font-weight:800;display:flex;align-items:center;gap:8px}}
.card h2 .ic{{display:inline-flex;width:36px;height:36px;border-radius:50%;background:#fff;align-items:center;justify-content:center;font-size:20px;box-shadow:0 2px 0 var(--cd)}}
.card h2 small{{font-size:10.5px;letter-spacing:.14em;color:var(--cd);text-transform:uppercase;font-weight:700}}
.card h2 .n{{margin-left:auto;font-size:12px;color:#fff;background:var(--cd);border-radius:999px;min-width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;padding:0 8px}}
.dish{{border-top:2px dotted var(--ca);padding:11px 2px}}
.dish:first-of-type{{border-top:0}}
.row{{display:flex;align-items:center;gap:7px;flex-wrap:wrap}}
.row::before{{content:"";width:8px;height:8px;border-radius:50%;background:var(--cd);opacity:.55;flex:0 0 8px}}
.name{{font-size:17px;font-weight:800;color:var(--ink);text-decoration:none}}
.tag{{font-size:11px;padding:1px 8px;border-radius:999px;background:#fff;color:var(--cd);border:1.5px solid var(--cd);font-weight:700}}
.ing{{font-size:13.5px;color:#6e625a;margin-top:4px;line-height:1.55;padding-left:15px}}
.note{{font-size:12.5px;color:var(--mute);margin-top:3px;padding-left:15px}}
.links{{margin-top:7px;display:flex;gap:6px;flex-wrap:wrap;padding-left:15px}}
.lnk{{font-size:12px;font-weight:700;text-decoration:none;color:#8f6560;background:#f3e9e7;padding:4px 10px;border-radius:999px;border:1.5px solid #e3d2cf}}
.lnk.nt{{color:#66778a;background:#ebeff2;border-color:#d5dde4}}
.sec{{margin-top:34px}}
.sec h3{{font-size:22px;font-weight:800;margin:0 0 14px;text-align:center}}
.sec h3 span{{display:inline-block;background:#fff;border:2px solid var(--hc,#e6d3d0);border-radius:999px;padding:6px 18px;box-shadow:0 4px 0 var(--hc,#e6d3d0)}}
.sec h3 small{{display:block;font-size:10.5px;letter-spacing:.24em;color:var(--mute);text-transform:uppercase;font-weight:700;margin-top:8px}}
.todo{{display:grid;grid-template-columns:1fr;gap:10px}}
@media(min-width:760px){{.todo{{grid-template-columns:1fr 1fr}}}}
.ti{{position:relative;background:#fff;border:2px solid #e8d8d5;border-radius:18px;padding:11px 14px 11px 44px;box-shadow:0 4px 0 #eadfdc}}
.ti::before{{content:"🌸";position:absolute;left:13px;top:11px;font-size:18px}}
.ti b{{font-size:16px;font-weight:800}}
.ti .note,.ti .links{{padding-left:0}}
.weeks{{display:grid;grid-template-columns:1fr;gap:14px}}
@media(min-width:760px){{.weeks{{grid-template-columns:1fr 1fr}}}}
.wk{{background:#fff;border:2px solid #d5dde4;border-radius:20px;padding:12px 16px;box-shadow:0 4px 0 #dde3e9}}
.wk .d{{display:inline-block;font-weight:800;color:#fff;background:#8394a3;border-radius:999px;padding:2px 12px;font-size:14px;margin-bottom:6px}}
.wk .l{{display:flex;gap:10px;font-size:14px;padding:6px 0;border-top:2px dotted #e4e8ec;line-height:1.5}}
.wk .l:first-of-type{{border-top:0}}
.wk .l>span:first-child{{flex:0 0 auto;min-width:62px;white-space:nowrap;color:#66778a;font-weight:700}}
.wkd{{color:inherit;text-decoration:none;border-bottom:1px dotted #b7c1ca;cursor:pointer}}
.wkd:hover{{border-bottom-style:solid}}
.dish.flash{{animation:flash 1.6s ease-out}}
@keyframes flash{{0%,40%{{background:rgba(255,255,255,.95);box-shadow:0 0 0 2px var(--cd)}}100%{{background:none;box-shadow:none}}}}
.tipbox{{background:#f8f5ec;border:2px solid #e2d8bc;border-radius:20px;padding:14px 16px;box-shadow:0 4px 0 #e8e0c9;font-size:13.5px;line-height:1.7;color:#5e544a}}
.tipbox b{{color:#8c7a4e}}
details.past{{background:#fff;border:2px solid #dce3d6;border-radius:20px;padding:12px 16px;box-shadow:0 4px 0 #e3e8de}}
details.past summary{{cursor:pointer;font-weight:800;color:#6f7f67;list-style:none}}
details.past summary::before{{content:"🍙 "}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}}
.chips span{{font-size:13px;background:#f1f4ee;border:1.5px solid #dce3d6;border-radius:999px;padding:4px 10px}}
.chips span:nth-child(3n+2){{background:#f5edeb;border-color:#e8d8d5}}.chips span:nth-child(3n){{background:#eef1f4;border-color:#d5dde4}}
footer{{text-align:center;color:var(--mute);font-size:12px;margin-top:30px}}
footer::before{{content:"🍙 🍡 🍵";display:block;font-size:18px;margin-bottom:6px;letter-spacing:.3em}}
.hide{{display:none!important}}
/* v4: tappable dishes + recipe sheet */
.dish{{cursor:pointer;border-radius:14px;margin:0 -6px;padding:11px 8px;transition:background .15s}}
.dish:hover{{background:rgba(255,255,255,.55)}}
.dish.empty{{cursor:default}}.dish.empty:hover{{background:none}}
.open{{font-size:12px;font-weight:700;color:var(--cd);background:#fff;border:1.5px solid var(--ca);padding:4px 10px;border-radius:999px;font-family:inherit;cursor:pointer}}
.cam{{font-size:12px;opacity:.75}}
.addw{{margin:-6px 0 16px;text-align:center}}
.add-btn{{font-family:inherit;font-size:13px;font-weight:800;color:#8f6560;background:#fff;border:2px dashed #d9c1be;border-radius:999px;padding:7px 16px;cursor:pointer}}
.addf{{margin:12px auto 0;max-width:560px;text-align:left;background:#fffdf9;border:2px solid #e8d8d5;border-radius:22px;padding:14px 16px 12px;box-shadow:0 5px 0 #eadfdc;display:flex;flex-direction:column;gap:10px}}
.addf.hide{{display:none}}
.af-l{{display:flex;flex-direction:column;gap:4px;font-size:12px;font-weight:800;color:#8f6560}}
.af-l b{{color:#c0716a}}
.addf input:not([type=radio]):not([type=checkbox]),.addf select{{font-family:inherit;font-size:16px;color:var(--ink);background:#fff;border:2px solid #e3d7d2;border-radius:14px;padding:8px 12px;outline:none;width:100%}}
.addf input[type=file]{{font-size:13px;padding:6px 8px}}
.af-row{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.af-seg,.af-chk{{display:flex;gap:8px;flex-wrap:wrap}}
.af-seg input,.af-chk input{{position:absolute;opacity:0;pointer-events:none}}
.af-seg span,.af-chk span{{display:inline-block;font-size:13px;font-weight:700;color:#7d7468;background:#fff;border:2px solid #e3ddd5;border-radius:999px;padding:6px 13px;cursor:pointer}}
.af-seg input:checked+span,.af-chk input:checked+span{{color:#fff;background:#a89a8c;border-color:#a89a8c}}
.af-hp{{position:absolute;left:-9999px;width:1px;height:1px}}
.af-act{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.af-go{{font-family:inherit;font-size:15px;font-weight:800;color:#fff;background:#b8928e;border:2px solid #a8817d;border-radius:999px;padding:8px 22px;box-shadow:0 4px 0 #9c7773;cursor:pointer}}
.af-go:disabled{{opacity:.6}}
.af-msg{{font-size:12.5px;color:var(--mute)}}
.skp{{font-size:10px;font-weight:700;color:#9a9188;background:#efebe6;border:1.2px solid #ddd6ce;border-radius:999px;padding:0 7px;line-height:1.6;letter-spacing:.04em;flex:0 0 auto}}
.ed-btn{{display:block;margin:0 0 12px auto;padding:5px 14px;font-size:12.5px}}
.addf.edf{{margin:0 0 14px;max-width:none}}
.recent{{font-size:10px;font-weight:800;color:#fff;background:#a89a8c;border-radius:999px;padding:0 8px;line-height:1.7;letter-spacing:.08em;flex:0 0 auto}}
.tbd{{font-size:10.5px;font-weight:700;color:var(--mute);border:1.2px dashed #d6ccc2;border-radius:999px;padding:0 7px;line-height:1.6;background:rgba(255,255,255,.6)}}
.dish.bare{{padding-top:9px;padding-bottom:9px}}
.dish.bare .name{{font-weight:700;color:#5e544a}}
.rcp-src{{display:none}}
.todo-card{{margin-top:34px}}
.todo-card h2 .ic{{font-size:18px}}
/* compact sizing (~12% smaller) */
h1{{font-size:31px}} .jp{{font-size:13.5px}} .sub{{font-size:11.5px}}
.noren span{{height:50px;font-size:19px}}
nav{{padding:8px 2px;gap:7px}} nav a{{font-size:12.5px;padding:5px 11px}}
.search{{padding:10px 14px;margin:2px 0 14px}}
.grid{{gap:20px}}
.card{{padding:0 12px 5px;border-radius:23px}}
.card h2{{margin:0 -12px 3px;padding:13px 14px 8px;font-size:17.5px;border-radius:21px 21px 0 0}}
.card h2 .ic{{width:31px;height:31px;font-size:17px}} .card h2 small{{font-size:9.5px}}
.card h2 .n{{font-size:11px;min-width:23px;height:23px;padding:0 7px}}
.dish{{padding:7px 7px}} .dish.bare{{padding-top:7px;padding-bottom:7px}}
.name{{font-size:15px}} .dish .row{{gap:9px}}
.dth{{flex:0 0 35px;width:35px;height:35px;border-radius:10px}} span.dth{{font-size:16.5px}}
.tbd{{font-size:9.5px}} .dish:not(.empty) .row::after{{font-size:18px}}
.sec h3{{font-size:19px}} .tipbox{{font-size:12.5px}} .wk .l{{font-size:13px}}
.pick-btn{{font-size:15px;padding:10px 19px}} .pick-n{{font-size:13.5px}} .pick-cap{{font-size:10.5px}}
.pr-head span{{font-size:14px}} .pr-th{{flex:0 0 46px;width:46px;height:46px}} .pr-n{{font-size:14px}}
.pr-tags span{{font-size:9.5px}} .pr-go{{font-size:10.5px}} .pr-sw{{flex:0 0 43px}} .pr-tool{{font-size:11.5px;min-height:38px}}
.sh-top h3{{font-size:19.5px}} .rcp{{font-size:13.5px}} .ing{{font-size:12.5px}} .note{{font-size:11.5px}} .lnk{{font-size:11px}}
@media(min-width:760px){{h1{{font-size:38px}} .noren span{{height:64px;font-size:24px}}
 .todo-list{{display:grid;grid-template-columns:1fr 1fr;column-gap:18px}}
 .todo-list .dish{{border-top:2px dotted var(--ca)}} .todo-list .dish:nth-child(-n+2){{border-top:0}}}}
@media(min-width:900px){{.wrap{{max-width:1240px}} .grid{{grid-template-columns:repeat(3,1fr)}}
 .todo-list{{grid-template-columns:repeat(3,1fr)}} .todo-list .dish:nth-child(3){{border-top:0}}}}
/* v6: simple cards (thumb + name), link tags at the top of the sheet */
.dish .row{{flex-wrap:nowrap;gap:10px}}
.dish .row::before{{display:none}}
.dish:not(.empty) .row::after{{content:"›";margin-left:auto;padding-left:6px;color:var(--cd);opacity:.45;font-size:20px;line-height:1}}
.dth{{flex:0 0 40px;width:40px;height:40px;border-radius:12px;object-fit:cover;border:2px solid #fff;box-shadow:0 2px 0 var(--ca);background:#fff}}
span.dth{{display:inline-flex;align-items:center;justify-content:center;font-size:19px;background:var(--ca)}}
.dish.bare span.dth{{opacity:.55;box-shadow:none}}
.dish{{padding-top:9px;padding-bottom:9px}}
.rcp .srcs{{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}}
.rcp .srcs .lnk{{display:inline-block;line-height:1.5;white-space:normal;border-radius:14px}}
.rcp .srcs .nolink{{color:var(--mute);background:#f4f0eb;border-color:#e6ded3}}
.rcp .tbd-steps{{margin:12px 0 0;font-size:12.5px;color:var(--mute);border:1.5px dashed var(--ca,#e6ded3);border-radius:12px;padding:7px 12px;text-align:center}}
.ov{{position:fixed;inset:0;z-index:50;background:rgba(74,64,58,.46);display:flex;align-items:flex-end;justify-content:center;opacity:0;pointer-events:none;transition:opacity .2s}}
.ov.on{{opacity:1;pointer-events:auto}}
.sheet{{position:relative;width:100%;max-width:640px;max-height:88vh;overflow:auto;background:var(--cb,#fcfaf6);border:2px solid var(--ca,#e6ded3);border-bottom:0;border-radius:28px 28px 0 0;box-shadow:0 -10px 30px -12px rgba(74,64,58,.35);transform:translateY(24px);transition:transform .22s;-webkit-overflow-scrolling:touch}}
.ov.on .sheet{{transform:none}}
@media(min-width:760px){{.ov{{align-items:center}} .sheet{{border-radius:28px;border-bottom:2px solid var(--ca,#e6ded3);max-height:84vh;box-shadow:0 8px 0 var(--ca),0 20px 40px -18px rgba(74,64,58,.4)}}}}
.sh-top{{position:sticky;top:0;z-index:2;background:var(--ca,#e6ded3);padding:20px 58px 12px 18px}}
.sh-top::before{{content:"";position:absolute;top:7px;left:50%;width:44px;height:5px;border-radius:9px;background:rgba(255,255,255,.8);transform:translateX(-50%)}}
.sh-top h3{{margin:4px 0 0;font-size:22px;font-weight:800;letter-spacing:.04em}}
.sh-top .ic{{display:inline-flex;width:32px;height:32px;border-radius:50%;background:#fff;align-items:center;justify-content:center;font-size:17px;margin-right:8px;vertical-align:-5px;box-shadow:0 2px 0 var(--cd)}}
.sh-top .cat{{font-size:11px;letter-spacing:.16em;color:var(--cd);font-weight:700}}
.x{{position:absolute;right:14px;top:18px;width:34px;height:34px;border-radius:50%;border:2px solid var(--cd,#958a80);background:#fff;color:var(--cd,#958a80);font-size:20px;line-height:1;cursor:pointer;font-family:inherit;display:flex;align-items:center;justify-content:center;padding:0}}
.sh-body{{padding:14px 18px 28px}}
.sh-sum{{display:flex;flex-direction:column;gap:3px;margin-bottom:4px}}
.sh-sum .ing,.sh-sum .note{{padding-left:0}}
.rcp{{font-size:14.5px;line-height:1.75;color:#5e544a}}
.rcp h4{{margin:16px 0 6px;font-size:14px;font-weight:800;color:var(--cd,#8f6560);display:flex;align-items:center;gap:8px}}
.rcp h4::before{{content:"";flex:0 0 14px;height:8px;border-radius:2px;background:repeating-linear-gradient(90deg,var(--cd,#b8928e) 0 3px,transparent 3px 5px);opacity:.7}}
.rcp p{{margin:4px 0}}
.rcp ol{{margin:6px 0;padding:0;list-style:none;counter-reset:s}}
.rcp ol li{{counter-increment:s;position:relative;padding:7px 10px 7px 40px;margin:6px 0;background:#fff;border:1.5px dashed var(--ca,#e6ded3);border-radius:14px}}
.rcp ol li::before{{content:counter(s);position:absolute;left:9px;top:8px;width:22px;height:22px;border-radius:50%;background:var(--cd,#b8928e);color:#fff;font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;line-height:1}}
.rcp ul{{margin:6px 0;padding-left:4px;list-style:none}}
.rcp ul li{{position:relative;padding:2px 0 2px 18px}}
.rcp ul li::before{{content:"";position:absolute;left:3px;top:.8em;width:7px;height:7px;border-radius:50%;background:var(--cd,#b8928e);opacity:.55}}
.rcp .tip{{margin:10px 0;padding:9px 12px;border-radius:14px;background:#f8f5ec;border:1.5px solid #e2d8bc;font-size:13.5px;color:#6e625a}}
.rcp .tip::before{{content:"💡 "}}
.rcp .ph{{display:block;width:100%;aspect-ratio:4/3;max-height:300px;object-fit:cover;border-radius:20px;border:3px solid #fff;box-shadow:0 4px 0 var(--ca,#e6ded3);margin:4px 0 12px;background:#eee}}
.rcp .links{{padding-left:0;margin:10px 0}}
.rcp b{{color:var(--ink)}}
/* in-sheet source reference (参考) */
.rcp .refs{{margin:18px 0 0;padding-top:12px;border-top:1.5px dashed var(--ca,#e6ded3);display:flex;flex-direction:column;gap:6px}}
.rcp .ref{{display:flex;align-items:flex-start;gap:6px;margin:0;font-size:12.5px;line-height:1.6;color:var(--cd,#958a80);text-decoration:none;opacity:.9;-webkit-tap-highlight-color:transparent}}
.rcp a.ref .rt{{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px;text-decoration-color:rgba(149,138,128,.45);text-decoration-color:color-mix(in srgb,currentColor 40%,transparent)}}
.rcp .ref .ri{{flex:0 0 14px;width:14px;height:14px;margin-top:3px}}
.rcp .ref .ext{{flex:0 0 auto;font-size:11px;opacity:.55}}
.rcp a.ref:hover,.rcp a.ref:active{{opacity:1}}
.rcp .ref.nolink{{color:var(--mute)}}
details.more{{margin-top:8px}}
details.more summary{{cursor:pointer;font-size:12.5px;font-weight:700;color:var(--mute);list-style:none}}
details.more summary::-webkit-details-marker{{display:none}}
details.more summary::before{{content:"▸ "}}details.more[open] summary::before{{content:"▾ "}}
.ti .rcp,.wk .rcp,.tipbox .rcp{{font-size:13.5px}}
.wk .rcp{{--cd:#66778a;--ca:#d5dde4}}
.ti .rcp{{--cd:#9c7773;--ca:#e8d8d5}}
.ti .rcp .links{{margin:6px 0 0}}
.tipbox .rcp{{--cd:#8c7a4e;--ca:#e2d8bc}}
.chips span.hasn{{border-style:dashed}}
.pnote{{font-size:12.5px;color:#6e625a;margin-top:12px;line-height:1.65;display:flex;flex-direction:column;gap:4px}}
.pnote b{{color:#6f7f67}}
.pnote .lnk{{padding:2px 8px}}
body.lock{{overflow:hidden}}
/* photo compare (real vs AI) */
.rcp .phc{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:4px 0 14px}}
.rcp .phc figure{{margin:0;text-align:center}}
.rcp .phc a{{display:block}}
.rcp .phc .ph{{aspect-ratio:4/5;max-height:none;margin:0 0 7px}}
.rcp .phc figcaption{{display:inline-block;font-size:12px;font-weight:700;line-height:1.4;color:var(--cd,#8f6560);background:#fff;border:1.5px solid var(--ca,#e6ded3);border-radius:999px;padding:2px 11px}}
.rcp .phc .ai figcaption::before{{content:"✨ "}}
/* v5: 帮我选菜 picker */
.pick{{margin:2px 0 16px;text-align:center}}
.pick-btn{{font-family:inherit;font-size:17px;font-weight:800;letter-spacing:.06em;color:#fff;background:#b8928e;border:2px solid #a8817d;border-radius:999px;padding:11px 22px;box-shadow:0 4px 0 #9c7773;cursor:pointer;-webkit-tap-highlight-color:transparent}}
.pick-btn:active,.pr-re:active{{transform:translateY(3px);box-shadow:0 1px 0 #9c7773}}
.pick-cap span{{white-space:nowrap}}
.pick-row{{display:flex;justify-content:center;align-items:center;gap:10px;flex-wrap:wrap}}
.pick-n{{-webkit-appearance:none;appearance:none;font-family:inherit;font-size:15px;font-weight:800;color:#9c7773;cursor:pointer;
background:#fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%239c7773' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") no-repeat right 13px center/10px 6px;
border:2px solid #e3d2cf;border-radius:999px;padding:11px 32px 11px 16px;line-height:1.2;box-shadow:0 4px 0 #eadfdc;-webkit-tap-highlight-color:transparent}}
.pick-n:focus{{outline:none;border-color:#b8928e}}
.pick-n:active{{transform:translateY(3px);box-shadow:0 1px 0 #eadfdc}}
.pick-cap{{font-size:11.5px;color:var(--mute);margin:9px auto 0;max-width:330px;line-height:1.55}}
.pick-res{{position:relative;margin:18px auto 0;max-width:560px;text-align:left;background:#fffdf9;border:2px solid #e8d8d5;border-radius:24px;padding:14px 14px 10px;box-shadow:0 5px 0 #eadfdc,0 12px 22px -14px rgba(90,75,60,.22);animation:pop .25s ease-out}}
.pick-res::before{{content:"";position:absolute;top:-9px;left:50%;width:84px;height:18px;transform:translateX(-50%) rotate(2deg);border-radius:2px;opacity:.9;background:repeating-linear-gradient(90deg,#ddcbc8 0 6px,rgba(255,255,255,.8) 6px 12px)}}
@keyframes pop{{0%{{transform:translateY(6px) scale(.98);opacity:0}}100%{{transform:none;opacity:1}}}}
.pr-head{{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:2px 2px 8px}}
.pr-head span{{font-size:15.5px;font-weight:800}}
.pr-head small{{font-size:10.5px;color:var(--mute);letter-spacing:.14em;font-weight:700;margin-left:4px}}
.pr-re{{font-family:inherit;font-size:12.5px;font-weight:700;color:#9c7773;background:#fff;border:1.5px solid #e3d2cf;border-radius:999px;padding:5px 12px;box-shadow:0 3px 0 #eadfdc;cursor:pointer;white-space:nowrap}}
.pr-list{{display:flex;flex-direction:column;gap:8px}}
.pr-item{{display:flex;align-items:center;gap:11px;width:100%;text-align:left;font-family:inherit;color:var(--ink);background:var(--cb);border:1.5px solid var(--ca);border-radius:16px;padding:7px 10px 7px 7px;cursor:pointer;-webkit-tap-highlight-color:transparent}}
.pr-item:active{{transform:translateY(1px)}}
.pr-th{{flex:0 0 52px;width:52px;height:52px;border-radius:13px;object-fit:cover;border:2px solid #fff;box-shadow:0 2px 0 var(--ca);background:#fff}}
span.pr-th{{display:flex;align-items:center;justify-content:center;font-size:24px;background:var(--ca)}}
.pr-tx{{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}}
.pr-n{{font-size:15.5px;font-weight:800;line-height:1.3}}
.pr-tags{{display:flex;flex-wrap:wrap;gap:4px;align-items:center}}
.pr-tags span{{font-size:10.5px;font-weight:700;padding:0 7px;border-radius:999px;background:#fff;color:var(--cd);border:1.2px solid var(--ca);line-height:1.6}}
.pr-tags .pr-last{{border:0;background:none;padding:0 2px;color:var(--mute);font-weight:500}}
.pr-go{{flex:0 0 auto;font-size:11.5px;font-weight:700;color:var(--cd)}}
/* swap: per-row 换 + multi-select */
.pr-row{{display:flex;align-items:stretch;gap:6px}}
.pr-row .pr-item{{flex:1;min-width:0;width:auto}}
.pr-sw{{flex:0 0 48px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-family:inherit;color:var(--cd);background:#fff;border:1.5px solid var(--ca);border-radius:16px;box-shadow:0 2px 0 var(--ca);cursor:pointer;padding:0;-webkit-tap-highlight-color:transparent}}
.pr-sw b{{font-size:15px;line-height:1;font-weight:400}}.pr-sw small{{font-size:10.5px;font-weight:800;line-height:1}}
.pr-sw:active{{transform:translateY(2px);box-shadow:none}}
.pr-chk{{display:none;flex:0 0 22px;width:22px;height:22px;border-radius:50%;border:2px solid var(--ca);background:#fff;align-items:center;justify-content:center}}
.pick-res.sel .pr-chk{{display:inline-flex}}
.pick-res.sel .pr-go{{display:none}}
.pr-row.on .pr-chk{{background:var(--cd);border-color:var(--cd)}}
.pr-row.on .pr-chk::after{{content:"✓";color:#fff;font-size:12px;font-weight:800;line-height:1}}
.pr-row.on .pr-item{{border-color:var(--cd);box-shadow:0 0 0 1.5px var(--cd);background:#fff}}
.pr-row.new .pr-item{{animation:swapin .45s ease-out}}
@keyframes swapin{{0%{{opacity:0;transform:translateX(12px)}}100%{{opacity:1;transform:none}}}}
.pr-bar{{display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;margin:12px 0 2px}}
.pr-hint{{flex-basis:100%;text-align:center;font-size:11px;color:var(--mute)}}.pr-hint:empty{{display:none}}
.pr-tool{{font-family:inherit;font-size:12.5px;font-weight:700;color:#9c7773;background:#fff;border:1.5px solid #e3d2cf;border-radius:999px;padding:8px 15px;min-height:40px;box-shadow:0 3px 0 #eadfdc;cursor:pointer;-webkit-tap-highlight-color:transparent}}
.pr-tool:active{{transform:translateY(2px);box-shadow:0 1px 0 #eadfdc}}
.pr-do{{color:#fff;background:#b8928e;border-color:#a8817d;box-shadow:0 3px 0 #9c7773}}
.pr-do:disabled{{opacity:.45;cursor:default}}
.pick-res:not(.sel) .pr-do{{display:none}}
.pr-foot{{font-size:11px;color:var(--mute);text-align:center;margin:8px 0 2px;line-height:1.5}}
.pr-foot:empty{{display:none}}
.dish.flash{{animation:flash 1.4s ease-out}}
@keyframes flash{{0%,40%{{background:rgba(255,255,255,.95);box-shadow:0 0 0 2px var(--cd)}}100%{{background:none;box-shadow:none}}}}
</style></head><body><div class="wrap">
<div class="rod"></div><div class="noren"><span>家</span><span>庭</span><span>菜</span><span>单</span></div>
<header>{PETAL.format(c="p1")}{PETAL.format(c="p2")}{PETAL.format(c="p3")}{PETAL.format(c="p4")}
<div class="hero">{STEAM}{ONI}<div class="hanko">おい<br>しい</div></div>
<h1>{E(D["title"])}</h1><div class="jp">「{E(D["subtitle"])}」</div>
<div class="sub">Home Menu · {total} 道拿手菜 · {len(CATS)} 类 · 点菜名看做法</div><div class="washi"></div></header>
<section class="pick" id="pick"><div class="pick-row"><select class="pick-n" id="pick-n" aria-label="选几道菜">{"".join(f'<option value="{i}"{" selected" if i == 4 else ""}>{i} 道</option>' for i in range(2, 9))}</select><button class="pick-btn" id="pick-go" type="button">🎲 帮我选 4 道菜</button></div>
<div class="pick-cap"><span id="pick-capn">1 道凉菜/蔬菜 + 3 道荤菜</span> · <span>主蛋白不重复</span> · <span>最多 1 个汤</span> · <span>最多 1 道「最近」待做</span> · <span>不选午餐/其他/甜品</span> · <span>尽量避开近 2 周吃过的</span></div>
<div class="pick-res hide" id="pick-res" aria-live="polite"><div class="pr-head"><span>🍱 今日菜单 <small>きょうのこんだて</small></span><button class="pr-re" id="pick-re" type="button">🔄 换一组</button></div>
<div class="pr-list" id="pick-list"></div>
<div class="pr-bar"><span class="pr-hint" id="pick-hint"></span><button class="pr-tool" id="pick-sel" type="button">☑️ 多选换菜</button><button class="pr-tool pr-do" id="pick-swap" type="button" disabled>换掉选中的</button></div>
<div class="pr-foot" id="pick-foot"></div></div></section>
<script type="application/json" id="pick-data">{json.dumps(PICK, ensure_ascii=False).replace("</", "<\\/")}</script>
<nav>''')
for c in CATS: out.append(f'<a href="#{c["id"]}" style="--c:{PAL[c["id"]][1]}55">{c["icon"]} {E(c["zh"])}</a>')
out.append('<a href="#todo" style="--c:#c9a9a666">📝 待做</a><a href="#weeks" style="--c:#9aa8b566">📅 每周</a></nav>')
out.append('<input class="search" id="q" type="search" placeholder="🔍 搜菜名或食材，比如 冬瓜、鸡腿…">')
if SCRIPT_URL:
    sec_opts = ''.join(f'<option value="{c["id"]}"{" selected" if c["id"] == "other" else ""}>{c["icon"]} {E(c["zh"])}</option>' for c in CATS)
    prot_opts = ''.join(f'<option value="{p}">{p or "（不填）"}</option>' for p in ['', '牛', '猪', '羊', '鸡', '鸭', '鱼', '龙虾/虾', '蟹', '蛤蜊/贝', '豆腐/蛋', '素'])
    out.append(f'''<div class="addw"><button class="add-btn" id="add-open" type="button" aria-expanded="false">＋ 添加新菜</button>
<form class="addf hide" id="addf" autocomplete="off">
<label class="af-l"><span>菜名 <b>*</b></span><input id="af-name" maxlength="60" required placeholder="比如 葱油拌面"></label>
<div class="af-l">加到哪里<div class="af-seg"><label><input type="radio" name="af-where" value="menu" checked><span>🍽 菜单</span></label><label><input type="radio" name="af-where" value="todo"><span>📝 待做</span></label></div></div>
<label class="af-l" id="af-secw">分类<select id="af-sec">{sec_opts}</select></label>
<div class="af-row"><label class="af-l">主蛋白<select id="af-prot">{prot_opts}</select></label>
<div class="af-l">标签<div class="af-chk"><label><input type="checkbox" id="af-recent"><span>最近</span></label><label title="不参与随机选菜"><input type="checkbox" id="af-skip"><span>skip</span></label></div></div></div>
<label class="af-l">食谱链接<input id="af-link" type="url" inputmode="url" placeholder="https://…（可不填）"></label>
<label class="af-l">食材<input id="af-ing" maxlength="500" placeholder="比如 面 · 葱 · 酱油（可不填）"></label>
<label class="af-l">照片<input id="af-photo" type="file" accept="image/*"></label>
<input class="af-hp" id="af-hp" tabindex="-1" aria-hidden="true" placeholder="website">
<div class="af-act"><button class="af-go" id="af-go" type="submit">保存</button><span class="af-msg" id="af-msg" aria-live="polite"></span></div>
</form></div>''')
out.append('<div class="grid">')
n = 0
EB = {}   # editable base state per dish id (for ✏️ 编辑 overrides from the sheet)
for c in CATS:
    ca, cd, cb = PAL[c['id']]
    out.append(f'<section class="card" id="{c["id"]}" style="--ca:{ca};--cd:{cd};--cb:{cb}"><h2><span class="ic">{c["icon"]}</span>{E(c["zh"])} <small>{E(c["en"])}</small><span class="n">{len(c["dishes"])}</span></h2>')
    for d in c['dishes']:
        n += 1
        has = has_recipe(d)
        bare = not (has or d['ingredients'] or d['note'] or d['links'] or d.get('photo'))   # name only -> no sheet
        th = (f'<img class="dth" src="{E(d["photo"])}" alt="" loading="lazy">' if d.get('photo')
              else f'<span class="dth ic" aria-hidden="true">{c["icon"]}</span>')
        s = (f'<div class="dish{" empty bare" if bare else ""}" id="{DID[id(d)]}" data-cat="{c["id"]}" '
             f'data-s="{E((d["name"]+" "+d["ingredients"]+" "+d["note"]+" "+plain(d["recipe"])).lower())}">'
             f'<div class="row">{th}<span class="name">{E(d["name"])}</span>')
        if d.get('recent'): s += '<span class="recent">最近</span>'
        if is_skip(d): s += '<span class="skp" title="不参与随机选菜">skip</span>'
        if bare or d.get('tbd'): s += '<span class="tbd" title="做法待补充">待补充</span>'
        s += '</div>'
        _refs = split_refs(d['recipe'], d['links'])[1]
        EB[DID[id(d)]] = dict(w='menu', sec=c['id'], m=canon(d.get('meat') or ''), r=bool(d.get('recent')),
            s=bool(d.get('soup')) or c['id'] == 'soup' or '汤' in d['name'], link=next((u for u, _ in _refs if u), ''),
            ing=d['ingredients'], photo=d.get('photo') or '', tbd=bool(bare or d.get('tbd')), rb=has_body(d),
            dess=(d.get('meat') == '甜品' or d.get('tag') == '甜品'), k=is_skip(d), l=LAST.get(d['name'], ''))
        if not bare:   # sheet: link tags on top, then ingredients/notes, photo(s), steps
            body, refs = split_refs(d['recipe'], d['links'])
            summ = ''
            if d['ingredients']: summ += f'<div class="ing">{E(d["ingredients"])}</div>'
            if d['note']: summ += f'<div class="note">⏱ {E(d["note"])}</div>'
            if summ: summ = f'<div class="sh-sum">{summ}</div>'
            steps = md(body, d.get("photo"), d.get("photo_ai"))
            if not has_body(d) and (d['ingredients'] or d['note'] or has): steps += '<p class="tbd-steps">做法步骤 待补充</p>'
            s += (f'<div class="rcp-src" data-ic="{c["icon"]}" data-cat="{E(c["zh"])} · {E(c["en"])}">'
                  f'{ref_html(refs, d["name"])}{summ}{steps}</div>')
        out.append(s + '</div>')
    out.append('</section>')
out.append('</div>')

TODO_PAL = ("#e3ddd5", "#7d7468", "#f7f5f2")
out.append(f'<section class="card todo-card" id="todo" style="--ca:{TODO_PAL[0]};--cd:{TODO_PAL[1]};--cb:{TODO_PAL[2]}">'
           f'<h2><span class="ic">📝</span>待做 <small>To try</small><span class="n">{len(D["todo"])}</span></h2><div class="todo-list">')
for i, t in enumerate(D['todo'], 1):   # same card component as the menu; a sheet when there is a link / ingredients
    links = [dict(label='小红书' if 'xhslink' in t['link'] else '食谱', url=t['link'])] if t.get('link') else []
    body, refs = split_refs(t['details'], links)
    ing = t.get('ingredients', '')
    sheet = bool(refs or ing or body.strip())
    EB[TID[id(t)]] = dict(w='todo', sec='', m=canon(t.get('meat') or ''), r=bool(t.get('recent')), s=bool(t.get('soup')) or '汤' in t['name'],
        link=t.get('link') or '', ing=ing, photo='', tbd=bool(t.get('tbd')), rb=False, dess=t.get('meat') == '甜品', k=is_skip(t), l=LAST.get(t['name'], ''))
    s = (f'<div class="dish{"" if sheet else " empty"}" id="{TID[id(t)]}" data-cat="todo" data-s="{E((t["name"]+" "+t["note"]+" "+ing+(" 最近" if t.get("recent") else "")).lower())}">'
         f'<div class="row"><span class="dth ic" aria-hidden="true">🌸</span><span class="name">{E(t["name"])}</span>'
         + ('<span class="recent">最近</span>' if t.get('recent') else '') + ('<span class="skp" title="不参与随机选菜">skip</span>' if is_skip(t) else '')
         + ('<span class="tbd" title="做法待补充">待补充</span>' if t.get('tbd') else '') + '</div>')
    if sheet:
        summ = f'<div class="sh-sum"><div class="ing">{E(ing)}</div></div>' if ing else ''
        steps = md(body, t.get('ing_photo')) if body.strip() else ''
        if ing or body.strip(): steps += '<p class="tbd-steps">做法步骤 待补充</p>'
        s += f'<div class="rcp-src" data-ic="📝" data-cat="待做 · To try">{ref_html(refs, "待做:" + t["name"])}{summ}{steps}</div>'
    out.append(s + '</div>')
out.append('</div></section>')

out.append('<section class="sec" id="weeks"><h3 style="--hc:#d5dde4"><span>📅 最近每周菜单</span><small>Recent weekly menus · こんしゅう</small></h3><div class="weeks">')
ALIAS_ID = {norm(k): DID[id(d)] for c in CATS for d in c['dishes'] for k in [d['name']] + d.get('aliases', [])}
def wk_dish(raw):
    i = ALIAS_ID.get(norm(raw))
    return f'<a class="wkd" href="#{i}" data-d="{i}">{E(raw)}</a>' if i else f'<span class="wkx">{E(raw)}</span>'
for w in WEEKS:
    if w['src'] == 'history':
        rows = ''.join(f'<div class="l{" plan" if l["planned"] else ""}"><span>{E(l["day"])}</span><span>{" · ".join(wk_dish(x) for x in l["items"])}</span></div>' for l in w['lines'])
    else:
        rows = ''.join(f'<div class="l"><span>{E(l["day"])}</span><span>{E(l["dishes"])}</span></div>' for l in w['lines'])
    s = f'<div class="wk"><div class="d">{E(w["date"])}</div>' + rows
    if w.get('details'): s += f'<details class="more"><summary>原始笔记</summary><div class="rcp">{md(w["details"])}</div></details>'
    out.append(s + '</div>')
out.append('</div></section>')

cp = D['chicken_prep']
out.append('<section class="sec"><h3 style="--hc:#e2d8bc"><span>🍗 处理鸡肉小贴士</span><small>Chicken prep · コツ</small></h3><div class="tipbox">'
           + '<br>'.join(f'<b>{E(k)}：</b>{E(v)}' for k, v in cp['summary'])
           + f'<details class="more"><summary>完整指南 Full guide</summary><div class="rcp">{md(cp["full"])}</div></details></div></section>')

out.append('''<footer>家庭菜单 · 自家食谱 · おうちごはん</footer></div>
<div class="ov" id="ov" aria-hidden="true"><div class="sheet" role="dialog" aria-modal="true" aria-labelledby="sh-t">
<div class="sh-top"><div class="cat" id="sh-c"></div><h3 id="sh-t"></h3><button class="x" id="sh-x" type="button" aria-label="关闭">×</button></div>
<div class="sh-body"><div class="sh-sum" id="sh-s"></div><div class="rcp" id="sh-r"></div></div></div></div>
<script>
const q=document.getElementById('q');
q.addEventListener('input',()=>{const v=q.value.trim().toLowerCase();
document.querySelectorAll('[data-s]').forEach(el=>el.classList.toggle('hide',v&&!el.dataset.s.includes(v)));
document.querySelectorAll('.card').forEach(c=>c.classList.toggle('hide',v&&!c.querySelector('.dish:not(.hide)')));
});
const ov=document.getElementById('ov'),sh=ov.querySelector('.sheet');
function openDish(d){const src=d.querySelector('.rcp-src');if(!src)return;
 const card=d.closest('.card');['--ca','--cd','--cb'].forEach(k=>sh.style.setProperty(k,card.style.getPropertyValue(k)));
 document.getElementById('sh-c').textContent=src.dataset.cat;
 document.getElementById('sh-t').innerHTML='<span class="ic">'+src.dataset.ic+'</span>'+d.querySelector('.name').innerHTML;
 document.getElementById('sh-s').innerHTML='';
 document.getElementById('sh-r').innerHTML=src.innerHTML;
 sh.scrollTop=0;ov.classList.add('on');ov.setAttribute('aria-hidden','false');document.body.classList.add('lock');
 if(location.hash!=='#'+d.id)history.replaceState(null,'','#'+d.id);}
function closeDish(){ov.classList.remove('on');ov.setAttribute('aria-hidden','true');document.body.classList.remove('lock');
 if(/^#[dtg]\\d+$/.test(location.hash))history.replaceState(null,'',location.pathname+location.search);}
const bindDish=d=>d.addEventListener('click',e=>{if(e.target.closest('a'))return;openDish(d);});
document.querySelectorAll('.dish').forEach(bindDish);
document.getElementById('sh-x').addEventListener('click',closeDish);
ov.addEventListener('click',e=>{if(e.target===ov)closeDish();});
document.querySelectorAll('a.wkd').forEach(a=>a.addEventListener('click',e=>{const d=document.getElementById(a.dataset.d);if(!d)return;e.preventDefault();
 if(d.querySelector('.rcp-src'))openDish(d);else{d.scrollIntoView({behavior:'smooth',block:'center'});d.classList.remove('flash');void d.offsetWidth;d.classList.add('flash');}}));
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDish();});
/* 帮我选菜: N dishes (2-8) = exactly 1 cold/veg + (N-1) meat/seafood mains; no protein repeated across ALL picks
   (the cold dish's protein counts unless it is 素), <=1 soup, <=1 dish from 待做/最近, no dessert,
   skip dishes eaten <=14 days ago. Relax order: the 2-week rule first; protein repeats only if there aren't enough proteins. */
const PK=JSON.parse(document.getElementById('pick-data').textContent);
const PAL_JS={todo:["#e3ddd5","#7d7468","#f7f5f2"],beef:["#e2cdc4","#8a5f4f","#f6efeb"],pork:["#efd9dc","#a36f78","#fbf2f3"],poultry:["#e8dfc8","#8c7a4e","#f8f5ec"],sea:["#d9e0e7","#66778a","#f2f4f6"],cold:["#dbe2d4","#6f7f67","#f3f5f0"],soup:["#ead8cc","#93705a","#f8f1ec"],staple:["#e6dccd","#8e7b62","#f8f4ee"]};
function daysAgo(iso,today){if(!iso)return Infinity;const p=iso.split('-').map(Number);
 const t=Date.UTC(today.getFullYear(),today.getMonth(),today.getDate());return Math.round((t-Date.UTC(p[0],p[1]-1,p[2]))/864e5);}
function wOrder(arr,w,rnd){return arr.map(x=>[Math.pow(rnd(),1/w(x)),x]).sort((p,q)=>q[0]-p[0]).map(p=>p[1]);}
const isMeat=x=>x.m&&x.m!=='素';
/* Core: fill the given slot kinds ('cold'/'main') next to the dishes that stay (kept), never using excluded ids.
   Rules across the WHOLE set: distinct non-素 proteins, <=1 soup; prefer recipes; skip dishes eaten <=14 days ago.
   Loosening order: the 2-week rule first (凉菜 slot, then mains), protein repeats only if still impossible. */
function fillSlots(kept,kinds,excl,today,rnd,accept){today=today||new Date();rnd=rnd||Math.random;
 const recent=x=>daysAgo(x.l,today)<=14, ex=new Set(excl.concat(kept.map(x=>x.id)));
 const nc=kinds.filter(k=>k==='cold').length, nm=kinds.length-nc;
 const allC=PK.filter(x=>x.k==='cold'&&!ex.has(x.id)), allM=PK.filter(x=>x.k==='main'&&!ex.has(x.id));
 const frC=allC.filter(x=>!recent(x)), frM=allM.filter(x=>!recent(x));
 const tiers=[[0,0,0],[1,0,0],[0,1,0],[1,1,0],[0,0,1],[1,0,1],[0,1,1],[1,1,1]];
 for(const [ca,ma,rp] of tiers){if((ca&&!nc)||(ma&&!nm))continue;   /* skip tiers that relax a slot type we aren't filling */
  let cs=ca?allC:frC;const ms=ma?allM:frM;
  if(rp){const veg=cs.filter(x=>!isMeat(x));if(veg.length)cs=veg;}   /* if repeats must be allowed, a 素 凉菜 adds none */
  if(cs.length<nc||ms.length<nm)continue;
  const w=x=>(x.r?3:1)*(recent(x)?.25:1);
  let first=null;
  for(let t=0;t<80;t++){
   const used=new Set(kept.filter(isMeat).map(x=>x.m));let soups=kept.filter(x=>x.s).length,tds=kept.filter(x=>x.t).length;const got=[];
   const ok=(x,strict)=>!got.includes(x)&&!(x.s&&soups)&&!(x.t&&tds)&&(!strict||!isMeat(x)||!used.has(x.m));
   const take=x=>{got.push(x);if(isMeat(x))used.add(x.m);if(x.s)soups++;if(x.t)tds++;};
   const fill=(pool,need)=>{const o=wOrder(pool,w,rnd);let c=0;
    for(const x of o){if(c===need)break;if(ok(x,true)){take(x);c++;}}
    if(rp)for(const x of o){if(c===need)break;if(ok(x,false)){take(x);c++;}}
    return c===need;};
   if(nc&&!fill(cs,nc))continue;
   if(nm&&!fill(ms,nm))continue;
   const prot=kept.concat(got).filter(isMeat).map(x=>x.m);
   const res={got,relaxed:(ca||ma)?1:0,relaxedProtein:rp&&new Set(prot).size<prot.length?1:0,skipped:PK.filter(recent).map(x=>x.n)};
   if(!accept||accept(got))return res;first=first||res;}
  if(first)return first;}
 return null;}
const setKey=s=>s.map(x=>x.id).sort().join(',');
function pickMenu(today,prevKey,rnd,n){n=Math.min(8,Math.max(2,+n||4));
 const kinds=['cold'].concat(Array(n-1).fill('main'));
 const r=fillSlots([],kinds,[],today,rnd,g=>setKey(g)!==prevKey);if(!r)return null;
 return {dishes:r.got,key:setKey(r.got),relaxed:r.relaxed,relaxedProtein:r.relaxedProtein,skipped:r.skipped,n};}
/* Replace only the dishes at idxs; slot type kept, removed dishes never come back in this swap. */
function swapPick(cur,idxs,today,rnd){idxs=[...new Set(idxs)].filter(i=>i>=0&&i<cur.length).sort((a,b)=>a-b);if(!idxs.length)return null;
 const kept=cur.filter((x,i)=>!idxs.includes(i)), removed=idxs.map(i=>cur[i]);
 const r=fillSlots(kept,removed.map(x=>x.k),removed.map(x=>x.id),today,rnd);if(!r)return null;
 const pool={cold:r.got.filter(x=>x.k==='cold'),main:r.got.filter(x=>x.k==='main')};
 const dishes=cur.slice();idxs.forEach(i=>{dishes[i]=pool[cur[i].k].shift();});
 return {dishes,key:setKey(dishes),relaxed:r.relaxed,relaxedProtein:r.relaxedProtein,skipped:r.skipped,n:cur.length,replaced:idxs};}
let pickPrev='',cur=null,marked=new Set(),selMode=false,fresh=[];
const pickN=document.getElementById('pick-n');
function syncN(){const v=+pickN.value;document.getElementById('pick-go').textContent='🎲 帮我选 '+v+' 道菜';
 document.getElementById('pick-capn').textContent='1 道凉菜/蔬菜 + '+(v-1)+' 道荤菜';}
try{const sv=localStorage.getItem('pickN');if(sv&&+sv>=2&&+sv<=8)pickN.value=sv;}catch(e){}
syncN();
pickN.addEventListener('change',()=>{syncN();try{localStorage.setItem('pickN',pickN.value)}catch(e){}
 pickPrev='';if(!document.getElementById('pick-res').classList.contains('hide'))showPick();});
function noteFor(res){return res.relaxedProtein?'荤菜的种类不够分，这次有主蛋白重复':res.relaxed?'近 2 周吃过的太多，这次放宽了「避开近 2 周」这一条':(res.skipped.length?'已避开近 2 周吃过的：'+res.skipped.join('、'):'');}
function renderPick(note){const L=document.getElementById('pick-list');L.innerHTML='';
 const box=document.getElementById('pick-res');box.classList.toggle('sel',selMode);
 cur.forEach((x,i)=>{const pal=PAL_JS[x.c]||PAL_JS.beef;const row=document.createElement('div');
  row.className='pr-row'+(marked.has(i)?' on':'')+(fresh.includes(i)?' new':'');row.dataset.id=x.id;row.dataset.i=i;
  row.style.cssText='--ca:'+pal[0]+';--cd:'+pal[1]+';--cb:'+pal[2];
  const th=x.p?'<img class="pr-th" src="'+x.p+'" alt="" loading="lazy">':'<span class="pr-th">'+x.i+'</span>';
  const tags=[x.k==='cold'?'凉菜·蔬菜':x.m];if(x.k==='cold'&&x.m!=='素')tags.push(x.m);if(x.s)tags.push('汤');if(x.t)tags.push('最近');
  const last=x.l?'<span class="pr-last">'+(daysAgo(x.l,new Date())<0?'已计划 ':'上次 ')+Number(x.l.slice(5,7))+'/'+Number(x.l.slice(8))+'</span>':'';
  row.innerHTML='<button type="button" class="pr-item" aria-pressed="'+marked.has(i)+'"><span class="pr-chk" aria-hidden="true"></span>'+th+
   '<span class="pr-tx"><span class="pr-n"></span><span class="pr-tags">'+tags.map(t=>'<span>'+t+'</span>').join('')+last+'</span></span>'+
   '<span class="pr-go">'+(x.o?'做法 ›':'卡片 ›')+'</span></button><button type="button" class="pr-sw" aria-label="换掉这道"><b>🔄</b><small>换</small></button>';
  row.querySelector('.pr-n').textContent=x.n;
  row.querySelector('.pr-item').addEventListener('click',()=>{
   if(selMode){marked.has(i)?marked.delete(i):marked.add(i);fresh=[];renderPick(document.getElementById('pick-foot').textContent);return;}
   const d=document.getElementById(x.id);if(!d)return;
   if(x.o)openDish(d);else{d.scrollIntoView({behavior:'smooth',block:'center'});d.classList.remove('flash');void d.offsetWidth;d.classList.add('flash');}});
  row.querySelector('.pr-sw').addEventListener('click',()=>doSwap([i]));
  L.appendChild(row);});
 const go=document.getElementById('pick-swap');go.textContent='换掉选中的'+(marked.size?' ('+marked.size+')':'');go.disabled=!marked.size;
 document.getElementById('pick-sel').textContent=selMode?'取消':'☑️ 多选换菜';
 document.getElementById('pick-hint').textContent=selMode?'点菜名勾选，可以选好几道':'';
 document.getElementById('pick-foot').textContent=note||'';}
function doSwap(idxs){if(!cur)return;const res=swapPick(cur,idxs);
 if(!res){fresh=[];renderPick('没有其他符合规则的菜可以换了，先保留原来的');window.__swapFail=(window.__swapFail||0)+1;return;}
 cur=res.dishes;pickPrev=res.key;window.__pick=res;idxs.forEach(i=>marked.delete(i));fresh=res.replaced;renderPick(noteFor(res));}
function showPick(){const res=pickMenu(null,pickPrev,null,pickN.value);if(!res)return;pickPrev=res.key;window.__pick=res;
 cur=res.dishes;marked=new Set();selMode=false;fresh=[];renderPick(noteFor(res));
 const box=document.getElementById('pick-res');box.classList.remove('hide');box.style.animation='none';void box.offsetWidth;box.style.animation='';}
document.getElementById('pick-go').addEventListener('click',showPick);
document.getElementById('pick-re').addEventListener('click',showPick);
document.getElementById('pick-sel').addEventListener('click',()=>{selMode=!selMode;marked=new Set();fresh=[];renderPick(document.getElementById('pick-foot').textContent);});
document.getElementById('pick-swap').addEventListener('click',()=>{if(marked.size)doSwap([...marked]);});
__EXTRA_JS__
function openFromHash(){const h=location.hash.match(/^#([dtg]\\d+)$/)||(location.search.match(/[?&]dish=([dtg]\\d+)/));if(h){const d=document.getElementById(h[1]);if(d){ov.style.transition='none';sh.style.transition='none';openDish(d);requestAnimationFrame(()=>{ov.style.transition='';sh.style.transition='';});}}}
openFromHash();
</script></body></html>''')
page = "\n".join(out).replace('__EXTRA_JS__', extra_js())
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(page)
print(total, len(CATS), 'todo', len(D['todo']), len(page.encode()), 'form' if SCRIPT_URL else 'no form')
print('sheet link tags:', len(REF_STATS['linked']), REF_STATS['linked'])
if REF_STATS['nourl']: print('参考 lines without a URL:', REF_STATS['nourl'])
