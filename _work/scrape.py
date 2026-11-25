import requests,re,sys,json
from urllib.parse import urljoin
from html.parser import HTMLParser
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36','Accept-Language':'fr-FR,fr;q=0.9'}
class P(HTMLParser):
    def __init__(s,base): super().__init__(); s.base=base; s.imgs=[]; s.links=[]; s.title=''; s._t=False
    def handle_starttag(s,t,a):
        a=dict(a)
        if t=='img':
            src=a.get('data-src') or a.get('data-lazy-src') or a.get('src') or ''
            ss=a.get('srcset') or a.get('data-srcset') or ''
            if ss:
                best=sorted([(int(re.sub(r'\D','',x.split()[-1]) or 0) if len(x.split())>1 else 0,x.split()[0]) for x in ss.split(',') if x.strip()])[-1][1]
                src=best
            if src and not src.startswith('data:'): s.imgs.append((urljoin(s.base,src),a.get('alt','') or a.get('title','')))
        if t=='a' and a.get('href') and re.search(r'\.(jpe?g|png|webp)(\?|$)',a['href'],re.I): s.imgs.append((urljoin(s.base,a['href']),'[link] '+(a.get('title') or '')))
        if t=='meta' and a.get('property')=='og:image': s.imgs.append((urljoin(s.base,a.get('content','')),'[og]'))
        if t=='title': s._t=True
    def handle_data(s,d):
        if s._t: s.title+=d
    def handle_endtag(s,t):
        if t=='title': s._t=False
for url in sys.argv[1:]:
    try:
        r=requests.get(url,headers=H,timeout=30); p=P(url); p.feed(r.text)
        print('=====',r.status_code,url,'|',p.title.strip()[:80])
        seen=set()
        for u,a in p.imgs:
            if u in seen or re.search(r'logo|icon|sprite|avatar|pixel|\.svg|gravatar|emoji',u,re.I): continue
            seen.add(u); print('  ',u,'|',a[:100])
    except Exception as e: print('ERR',url,e)
