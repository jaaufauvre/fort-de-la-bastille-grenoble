import json, os, re, html, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

THEMES = [
    ('histoire', 'Historical documents', 'Plans, engravings, drawings, photographs and postcards made between the 16th and the mid-20th century.'),
    ('fortifications', 'Fortifications', 'Ramparts, casemates, bartizans, city gates, Fort Rabot and the keep.'),
    ('escaliers', 'Stairways', 'Covered stairways, steps up the slope and stair turrets.'),
    ('tunnels', 'Tunnels, galleries and caves', 'Underground passages, vaulted galleries and the so-called Mandrin caves.'),
    ('telepherique', 'Cable car', 'The cabins of 1934 and today\'s bubbles.'),
    ('vues', 'General views', 'The hill, the fort and the city seen from above or below.'),
]
CENTURY = {'16': 1550, '17': 1650, '18': 1750, '19': 1850, '20': 1950, '21': 2010}


def year(d):
    d = d or ''
    m = re.search(r'(1[5-9]\d\d|20\d\d)', d)
    if m:
        return int(m.group(1))
    m = re.search(r'\b(1[6-9]|2[01])th century|\b(1[6-9]|2[01])th or ', d)
    if m:
        y = CENTURY[m.group(1) or m.group(2)]
        if 'early' in d:
            y -= 45
        elif 'late' in d:
            y += 45
        return y
    return 9999


def clean(s):
    s = html.unescape(re.sub(r'<[^>]+>', '', s or ''))
    s = s.replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"').replace('\u2014', ', ').replace('\u00a9', '')
    return re.sub(r'\s+', ' ', s).strip(' .,')


def load(name):
    p = os.path.join(HERE, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []


items = []

gp_caps = load('gp_captions.json')
for x in load('gp_sel.json'):
    fn = x['file'].replace('\\', '/').split('/')[-1]
    key = re.match(r'gp\d+-\d+', fn).group(0)
    cap, date, credit, theme = gp_caps[key]
    items.append(dict(file=x['file'], caption=cap, date=date, credit=credit, theme=theme,
                      source_name='grenoble-patrimoine.fr (Ville de Grenoble)', source_url=x['source_url'], image_url=x['image_url']))

for name in ('bg_man.json', 'manifest_web.json', 'commons_man.json'):
    items += load(name)

# The manifests keep the French metadata as scraped. translations_en.json maps each cleaned French string to English.
EN = load('translations_en.json') or {}
missing = set()

seen = set()
out = []
for x in items:
    x['file'] = x['file'].replace('\\', '/')
    if x['file'] in seen:
        continue
    seen.add(x['file'])
    assert os.path.exists(os.path.join(ROOT, x['file'])), x['file']
    for k in ('caption', 'date', 'credit', 'source_name'):
        fr = clean(x.get(k, ''))
        x[k] = EN.get(k, {}).get(fr)
        if x[k] is None:
            missing.add((k, fr))
            x[k] = fr
    out.append(x)

if missing:
    print('No English translation in translations_en.json for:', *(f'{k}: {v}' for k, v in sorted(missing)), sep='\n  ')

json.dump(out, open(os.path.join(ROOT, 'images.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

on_disk = {os.path.relpath(os.path.join(dp, f), ROOT).replace('\\', '/')
           for dp, _, fs in os.walk(os.path.join(ROOT, 'images')) for f in fs}
orphans = sorted(on_disk - seen)
if orphans:
    print('Files on disk but not in the page:', *orphans, sep='\n  ')

e = html.escape
sections = []
toc = []
n = 0
for key, title, intro in THEMES:
    group = sorted([x for x in out if x['theme'] == key], key=lambda x: (year(x['date']), x['source_name'], x['file']))
    if not group:
        continue
    toc.append(f'<li><a href="#{key}">{e(title)}</a> <span class="count">{len(group)}</span></li>')
    figs = []
    for x in group:
        n += 1
        src = urllib.parse.quote(x['file'])
        meta = ' · '.join(e(v) for v in (x['date'], x['credit']) if v)
        figs.append(
            f'<figure data-i="{n}"><a href="{src}" class="zoom"><img src="{src}" loading="lazy" alt="{e(x["caption"])}"></a>'
            f'<figcaption><span class="cap">{e(x["caption"])}</span>'
            + (f'<span class="meta">{meta}</span>' if meta else '')
            + f'<span class="src">Source: <a href="{e(x["source_url"])}" target="_blank" rel="noopener">{e(x["source_name"])}</a>'
            + (f' · <a href="{e(x["image_url"])}" target="_blank" rel="noopener">original image</a>' if x.get('image_url') else '')
            + '</span></figcaption></figure>')
    sections.append(f'<section id="{key}"><h2>{e(title)} <span class="count">{len(group)}</span></h2><p class="intro">{e(intro)}</p>'
                    f'<div class="grid">{"".join(figs)}</div></section>')

by_src = {}
for x in out:
    by_src[x['source_name']] = by_src.get(x['source_name'], 0) + 1
src_list = ''.join(f'<li>{e(k)}: {v}</li>' for k, v in sorted(by_src.items(), key=lambda kv: -kv[1]))

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Bastille fort in Grenoble in pictures</title>
<style>
:root {{ --bg:#f6f4ef; --fg:#222; --muted:#666; --accent:#8a3b12; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font:15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; background:var(--bg); color:var(--fg); }}
header {{ padding:2rem 1.5rem 1rem; max-width:1400px; margin:auto; }}
h1 {{ margin:0 0 .5rem; font-size:2rem; }}
header p {{ max-width:60rem; color:#333; }}
nav {{ position:sticky; top:0; z-index:5; background:#fffc; backdrop-filter:blur(6px); border-bottom:1px solid #ddd; }}
nav ul {{ list-style:none; margin:0 auto; padding:.6rem 1.5rem; display:flex; flex-wrap:wrap; gap:.4rem 1.2rem; max-width:1400px; }}
nav a {{ color:var(--accent); text-decoration:none; font-weight:600; }}
.count {{ font-size:.75em; background:#e7ded3; color:#555; border-radius:1em; padding:.1em .6em; font-weight:normal; vertical-align:middle; }}
main {{ max-width:1400px; margin:auto; padding:0 1.5rem 3rem; }}
section {{ scroll-margin-top:3.5rem; }}
h2 {{ margin:2.2rem 0 .2rem; border-bottom:2px solid var(--accent); padding-bottom:.3rem; }}
.intro {{ color:var(--muted); margin:.3rem 0 1rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:1rem; }}
figure {{ margin:0; background:#fff; border-radius:6px; overflow:hidden; box-shadow:0 1px 3px #0002; display:flex; flex-direction:column; }}
figure img {{ width:100%; height:220px; object-fit:cover; display:block; background:#ddd; cursor:zoom-in; }}
figcaption {{ padding:.6rem .7rem .7rem; display:flex; flex-direction:column; gap:.3rem; font-size:.88rem; }}
.meta {{ color:var(--muted); }}
.src {{ font-size:.8rem; color:var(--muted); }}
.src a {{ color:var(--accent); }}
#sources {{ columns:2; font-size:.9rem; color:#444; }}
#lb {{ position:fixed; inset:0; background:#000e; display:none; z-index:10; color:#eee; }}
#lb.on {{ display:flex; flex-direction:column; align-items:center; justify-content:center; }}
#lb img {{ max-width:94vw; max-height:80vh; object-fit:contain; }}
#lb .txt {{ max-width:70rem; padding:.8rem 1rem; text-align:center; font-size:.95rem; }}
#lb .txt a {{ color:#f3b48b; }}
#lb .txt span {{ display:block; margin-top:.2rem; }}
#lb button {{ position:absolute; background:none; border:0; color:#fff; font-size:2.4rem; cursor:pointer; padding:1rem; }}
#lb .prev {{ left:0; top:45%; }} #lb .next {{ right:0; top:45%; }} #lb .close {{ right:0; top:0; }}
footer {{ max-width:1400px; margin:auto; padding:1rem 1.5rem 3rem; color:var(--muted); font-size:.85rem; }}
</style>
</head>
<body>
<header>
<h1>The Bastille fort in Grenoble in pictures</h1>
<p>The Bastille is the fort that overlooks Grenoble from the right bank of the Isère. The first fortifications on the hill date from the late 16th century, under the Duke of Lesdiguières. General Haxo rebuilt the whole site between the 1820s and the 1840s: the fort at the top, the walls that run down to the Isère, the covered stairways, the casemates and the galleries dug into the rock. Since 1934, a cable car has linked the embankment to the summit.</p>
<p>This page brings together {len(out)} images found online: old plans, engravings, 19th-century photographs, postcards and recent photos. Each image shows its caption, its date when known, its author or collection, and the page where it was found. Click an image to enlarge it. Use the arrow keys to move from one image to the next.</p>
</header>
<nav><ul>{"".join(toc)}<li><a href="#sources-section">Sources</a></li></ul></nav>
<main>
{"".join(sections)}
<section id="sources-section"><h2>Sources</h2><p class="intro">Number of images per website. These images are downloaded for personal use. The rights remain with their authors and with the institutions that keep them.</p><ul id="sources">{src_list}</ul></section>
</main>
<footer>Page generated from the images.json file.</footer>
<div id="lb"><button class="close" aria-label="Close">&times;</button><button class="prev" aria-label="Previous">&#8249;</button><img alt=""><div class="txt"></div><button class="next" aria-label="Next">&#8250;</button></div>
<script>
const figs=[...document.querySelectorAll('figure')], lb=document.getElementById('lb'), li=lb.querySelector('img'), lt=lb.querySelector('.txt');
let cur=0;
function show(i){{cur=(i+figs.length)%figs.length;const f=figs[cur];li.src=f.querySelector('a.zoom').href;lt.innerHTML=f.querySelector('figcaption').innerHTML;lb.classList.add('on');}}
figs.forEach((f,i)=>f.querySelector('a.zoom').addEventListener('click',ev=>{{ev.preventDefault();show(i);}}));
lb.querySelector('.close').onclick=()=>lb.classList.remove('on');
lb.querySelector('.prev').onclick=()=>show(cur-1);
lb.querySelector('.next').onclick=()=>show(cur+1);
lb.addEventListener('click',ev=>{{if(ev.target===lb)lb.classList.remove('on');}});
document.addEventListener('keydown',ev=>{{if(!lb.classList.contains('on'))return;if(ev.key==='Escape')lb.classList.remove('on');if(ev.key==='ArrowLeft')show(cur-1);if(ev.key==='ArrowRight')show(cur+1);}});
</script>
</body>
</html>
'''
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(page)
print(len(out), 'images in index.html')
for k, v in sorted(by_src.items(), key=lambda kv: -kv[1]):
    print(f'  {v:3d}  {k}')
