#!/usr/bin/env python3
"""Build index.html for the family menu site from menu.json (no Notion dependency).
Usage: python3 build.py   (run from the repo root; writes index.html next to this file)"""
import html, json, os, re
ROOT = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(ROOT, 'menu.json'), encoding='utf-8'))
E = html.escape

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

def md(text, photos=None):
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
            if photos: out.insert(0, f'<img class="ph" src="{E(photos)}" alt="" loading="lazy">')  # photo first
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

def plain(text):
    t = re.sub(r'!\[\]\([^)]*\)|\]\([^)]*\)|[#>*\[\]]', ' ', text)
    return re.sub(r'\s+', ' ', t).lower()

CATS = D['categories']
total = sum(len(c['dishes']) for c in CATS)
out = []
PAL = {"meat":("#e8d6d3","#9c7773","#f7f0ee"),"poultry":("#e8dfc8","#8c7a4e","#f8f5ec"),"sea":("#d9e0e7","#66778a","#f2f4f6"),
 "cold":("#dbe2d4","#6f7f67","#f3f5f0"),"soup":("#ead8cc","#93705a","#f8f1ec"),"staple":("#e6dccd","#8e7b62","#f8f4ee"),"sweet":("#e2d8e2","#7d6a7d","#f6f2f6")}
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
.wk .l span:first-child{{flex:0 0 62px;white-space:nowrap;color:#66778a;font-weight:700}}
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
.rcp-src{{display:none}}
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
</style></head><body><div class="wrap">
<div class="rod"></div><div class="noren"><span>家</span><span>庭</span><span>菜</span><span>单</span></div>
<header>{PETAL.format(c="p1")}{PETAL.format(c="p2")}{PETAL.format(c="p3")}{PETAL.format(c="p4")}
<div class="hero">{STEAM}{ONI}<div class="hanko">おい<br>しい</div></div>
<h1>{E(D["title"])}</h1><div class="jp">「{E(D["subtitle"])}」</div>
<div class="sub">Home Menu · {total} 道拿手菜 · {len(CATS)} 类 · 点菜名看做法</div><div class="washi"></div></header>
<nav>''')
for c in CATS: out.append(f'<a href="#{c["id"]}" style="--c:{PAL[c["id"]][1]}55">{c["icon"]} {E(c["zh"])}</a>')
out.append('<a href="#todo" style="--c:#c9a9a666">📝 待做</a><a href="#weeks" style="--c:#9aa8b566">📅 每周</a><a href="#past" style="--c:#a8b5a066">📚 之前做的</a></nav>')
out.append('<input class="search" id="q" type="search" placeholder="🔍 搜菜名或食材，比如 冬瓜、鸡腿…">')
out.append('<div class="grid">')
n = 0
for c in CATS:
    ca, cd, cb = PAL[c['id']]
    out.append(f'<section class="card" id="{c["id"]}" style="--ca:{ca};--cd:{cd};--cb:{cb}"><h2><span class="ic">{c["icon"]}</span>{E(c["zh"])} <small>{E(c["en"])}</small><span class="n">{len(c["dishes"])}</span></h2>')
    for d in c['dishes']:
        n += 1
        # link-only pages (no text, no photo) just show their links on the card
        has = bool(re.sub(r'^\s*\[[^\]]+\]\([^)]+\)\s*$', '', d['recipe'], flags=re.M).strip())
        tag = d.get('tag')
        if tag and tag in c['zh']: tag = None   # never repeat the section name as a pill
        s = (f'<div class="dish{"" if has else " empty"}" id="d{n}" data-cat="{c["id"]}" '
             f'data-s="{E((d["name"]+" "+d["ingredients"]+" "+d["note"]+" "+plain(d["recipe"])).lower())}">'
             f'<div class="row"><span class="name">{E(d["name"])}</span>')
        if tag: s += f'<span class="tag">{E(tag)}</span>'
        if d.get('photo'): s += '<span class="cam" title="有照片">📷</span>'
        s += '</div>'
        if d['ingredients']: s += f'<div class="ing">{E(d["ingredients"])}</div>'
        if d['note']: s += f'<div class="note">⏱ {E(d["note"])}</div>'
        s += '<div class="links">' + ''.join(link(l['url'], link_label(l['label'], l['url'])) for l in d['links'])
        if has: s += '<button class="open" type="button">📖 看做法</button>'
        s += '</div>'
        if has:
            s += f'<div class="rcp-src" data-ic="{c["icon"]}" data-cat="{E(c["zh"])} · {E(c["en"])}">{md(d["recipe"], d.get("photo"))}</div>'
        out.append(s + '</div>')
    out.append('</section>')
out.append('</div>')

out.append('<section class="sec" id="todo"><h3 style="--hc:#e8d8d5"><span>📝 待做</span><small>To try · やってみたい</small></h3><div class="todo">')
for t in D['todo']:
    s = f'<div class="ti" data-s="{E((t["name"]+" "+t["note"]+" "+plain(t["details"])).lower())}"><b>{E(t["name"])}</b>'
    if t['note']: s += f'<div class="note">{E(t["note"])}</div>'
    det = t['details']
    if det:
        body = md(det)
        if re.fullmatch(r'\s*\[[^\]]+\]\([^)]+\)\s*', det): s += f'<div class="rcp">{body}</div>'
        else: s += f'<details class="more"><summary>展开</summary><div class="rcp">{body}</div></details>'
    elif t.get('link'):
        s += f'<div class="links">{link(t["link"], "📕 小红书" if "xhslink" in t["link"] else "🔗 食谱")}</div>'
    out.append(s + '</div>')
out.append('</div></section>')

out.append('<section class="sec" id="weeks"><h3 style="--hc:#d5dde4"><span>📅 最近每周菜单</span><small>Recent weekly menus · こんしゅう</small></h3><div class="weeks">')
for w in D['weeks']:
    s = f'<div class="wk"><div class="d">{E(w["date"])}</div>' + ''.join(f'<div class="l"><span>{E(l["day"])}</span><span>{E(l["dishes"])}</span></div>' for l in w['lines'])
    if w.get('details'): s += f'<details class="more"><summary>原始笔记</summary><div class="rcp">{md(w["details"])}</div></details>'
    out.append(s + '</div>')
out.append('</div></section>')

cp = D['chicken_prep']
out.append('<section class="sec"><h3 style="--hc:#e2d8bc"><span>🍗 处理鸡肉小贴士</span><small>Chicken prep · コツ</small></h3><div class="tipbox">'
           + '<br>'.join(f'<b>{E(k)}：</b>{E(v)}' for k, v in cp['summary'])
           + f'<details class="more"><summary>完整指南 Full guide</summary><div class="rcp">{md(cp["full"])}</div></details></div></section>')

P = D['past']
chips = []
for p in P:
    cls = ' class="hasn"' if (p['note'] or p.get('link')) else ''
    chips.append(f'<span{cls} data-s="{E((p["name"]+" "+p["note"]).lower())}"{" title=%s" % chr(34)+E(p["note"])+chr(34) if p["note"] else ""}>{E(p["name"])}</span>')
notes = ''.join(f'<div><b>{E(p["name"])}</b>：{E(p["note"])}</div>' for p in P if p['note'])
notes += ''.join(f'<div><b>{E(p["name"])}</b>：{link(p["link"], "📕 小红书")}</div>' for p in P if p.get('link'))
out.append(f'<section class="sec" id="past"><h3 style="--hc:#dce3d6"><span>📚 之前做的</span><small>Idea bank · {len(P)}</small></h3><details class="past"><summary>展开看看以前做过的菜</summary><div class="chips">'
           + ''.join(chips) + f'</div><div class="pnote">{notes}</div></details></section>')

out.append('''<footer>家庭菜单 · 自家食谱 · おうちごはん</footer></div>
<div class="ov" id="ov" aria-hidden="true"><div class="sheet" role="dialog" aria-modal="true" aria-labelledby="sh-t">
<div class="sh-top"><div class="cat" id="sh-c"></div><h3 id="sh-t"></h3><button class="x" id="sh-x" type="button" aria-label="关闭">×</button></div>
<div class="sh-body"><div class="sh-sum" id="sh-s"></div><div class="rcp" id="sh-r"></div></div></div></div>
<script>
const q=document.getElementById('q');
q.addEventListener('input',()=>{const v=q.value.trim().toLowerCase();
document.querySelectorAll('[data-s]').forEach(el=>el.classList.toggle('hide',v&&!el.dataset.s.includes(v)));
document.querySelectorAll('.card').forEach(c=>c.classList.toggle('hide',v&&!c.querySelector('.dish:not(.hide)')));
if(v)document.querySelector('details.past').open=true;});
const ov=document.getElementById('ov'),sh=ov.querySelector('.sheet');
function openDish(d){const src=d.querySelector('.rcp-src');if(!src)return;
 const card=d.closest('.card');['--ca','--cd','--cb'].forEach(k=>sh.style.setProperty(k,card.style.getPropertyValue(k)));
 document.getElementById('sh-c').textContent=src.dataset.cat;
 document.getElementById('sh-t').innerHTML='<span class="ic">'+src.dataset.ic+'</span>'+d.querySelector('.name').innerHTML;
 const sum=[...d.querySelectorAll(':scope > .ing, :scope > .note')].map(e=>e.outerHTML).join('');
 document.getElementById('sh-s').innerHTML=sum;
 document.getElementById('sh-r').innerHTML=src.innerHTML;
 sh.scrollTop=0;ov.classList.add('on');ov.setAttribute('aria-hidden','false');document.body.classList.add('lock');
 if(location.hash!=='#'+d.id)history.replaceState(null,'','#'+d.id);}
function closeDish(){ov.classList.remove('on');ov.setAttribute('aria-hidden','true');document.body.classList.remove('lock');
 if(/^#d\\d+$/.test(location.hash))history.replaceState(null,'',location.pathname+location.search);}
document.querySelectorAll('.dish').forEach(d=>d.addEventListener('click',e=>{if(e.target.closest('a'))return;openDish(d);}));
document.getElementById('sh-x').addEventListener('click',closeDish);
ov.addEventListener('click',e=>{if(e.target===ov)closeDish();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDish();});
const h=location.hash.match(/^#(d\\d+)$/)||(location.search.match(/[?&]dish=(d\\d+)/));if(h){const d=document.getElementById(h[1]);if(d){ov.style.transition='none';sh.style.transition='none';openDish(d);requestAnimationFrame(()=>{ov.style.transition='';sh.style.transition='';});}}
</script></body></html>''')
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write("\n".join(out))
print(total, len(CATS), len(P), len("\n".join(out).encode()))
