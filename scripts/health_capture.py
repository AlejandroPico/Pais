"""Discover official INE health tables and capture the reviewed F13 distributions."""
from concurrent.futures import ThreadPoolExecutor
from html import unescape
import json
import re
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from affiliation_collect import fetch
from demography_collect import ROOT, encode

CACHE = ROOT/'.cache/f13'
MANIFEST = ROOT/'registry/health-inputs.json'
BASE = 'https://www.ine.es/'
REVISION = '2026-11-18'
HEALTH_CATEGORY = '1254735573175'
INE_HOME = BASE+'dyngs/INEbase/es/categoria.htm?c=Estadistica_P&cid='+HEALTH_CATEGORY
ANCHOR = re.compile(r'<a\b[^>]*\bhref=["\']([^"\']+)["\'][^>]*>(.*?)</a>',re.I|re.S)
OPTION = re.compile(r'<option\b[^>]*\bvalue=["\']([^"\']+)["\'][^>]*>(.*?)</option>',re.I|re.S)
TAB = re.compile(r'<div\s+class="resultados[^"]*"\s+id="(tabs-\d+)">',re.I)
YEAR = re.compile(r'(?<!\d)(?:19|20)\d{2}(?!\d)')
EDITIONS = {'13714':'2025','12960':'2024','12964':'2024','13600':'2025'}


def label_of(title):
    return ' '.join(unescape(re.sub(r'<[^>]+>', ' ', title)).split())


def links(raw,url=BASE):
    html=raw.decode('utf-8',errors='replace') if isinstance(raw,bytes) else raw
    for pattern in (ANCHOR,OPTION):
        for path,title in pattern.findall(html):
            yield urljoin(url,unescape(path)),label_of(title)


def contexts(html,url,edition):
    page=html.decode('utf-8',errors='replace')
    sections=TAB.split(page)
    captions={path[1:]:label_of(title) for path,title in ANCHOR.findall(sections[0]) if path.startswith('#tabs-')}
    for i in range(1,len(sections),2):
        tab=captions.get(sections[i],'')
        year=YEAR.search(tab)
        yield sections[i+1],year[0] if year else edition,tab
    if len(sections)==1:
        yield page,edition,''


def operation_url(cid):
    return BASE+'dyngs/INEbase/operacion.htm?'+urlencode(dict(
        c='Estadistica_C',cid=cid,idp=HEALTH_CATEGORY,menu='resultados'))


def listing_url(parent, child):
    params=dict(padre=parent)
    if child is not None:
        params['capsel']=child
    return BASE+'dynt3/inebase/index.htm?'+urlencode(params)


def get(item):
    name,url=item
    try:
        return fetch(url,CACHE/name,False),None
    except OSError as error:
        return b'',str(error)


def discover():
    raw,error=get(('ine-health.html',INE_HOME))
    if error:
        raise OSError(error)
    operations={}
    for url,label in links(raw):
        query=parse_qs(urlsplit(url).query)
        if label and query.get('idp')==[HEALTH_CATEGORY] and query.get('cid',[HEALTH_CATEGORY])!=[HEALTH_CATEGORY]:
            operations.setdefault(query['cid'][0], label)
    assert len(operations)>=10,operations
    tables, gaps = {}, []
    for cid,name in operations.items():
        queue=[(operation_url(cid), 'Resultados', '')]
        visited=set()
        while queue:
            url,group,edition=queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            query=parse_qs(urlsplit(url).query)
            parent=query.get('padre',[None])[0]
            child=query.get('capsel',[None])[0]
            path=f'list-{parent}-{child}.html' if parent else f'op-{cid}.html'
            html,error=get((path,url))
            if error:
                gaps.append(dict(title=name+' · '+group,table=url,download=url,reason=error))
                continue
            edition=EDITIONS.get(parent,edition)
            targets=((linked,label,year,tab) for section,year,tab in contexts(html,url,edition)
                     for linked,label in links(section,url))
            for linked,label,year,tab in targets:
                if not label:
                    continue
                location=urlsplit(linked)
                params=parse_qs(location.query)
                if location.netloc!='www.ine.es':
                    continue
                if location.path.startswith('/dynt3/') and 'padre' in params:
                    p,c=params['padre'][0],params.get('capsel',[None])[0]
                    if not parent or p in {parent,child}:
                        match=YEAR.search(label) if not parent else None
                        date=EDITIONS.get(p,match[0] if match else year)
                        queue.append((listing_url(p,c),label,date))
                    continue
                match=re.search(r'/(?:jaxi|jaxiT3)/tabla\.htm$',location.path,re.I)
                kind=next((k for k in ('tpx','t') if params.get(k,[''])[0].isdigit()),None)
                if match and kind:
                    number=params[kind][0]
                    directory='jaxi/files/tpx' if kind=='tpx' else 'jaxiT3/files/t'
                    if kind=='tpx' and not year and cid in {'1254736176778','1254736176780'}:
                        year='2024'
                    tables.setdefault(number+'-'+kind,dict(operation=name,group=group,edition=year,
                        title=label,listing=url,table=linked,download=f'{BASE}{directory}/es/px/{number}.px'))
                elif params.get('path') and (location.path.startswith('/dynt3/') or
                                             location.path.lower().endswith(('/menu.do','/tabla.do'))):
                    gaps.append(dict(title=name+' · '+label,table=linked,download=linked,
                        reason='Publicación en el sistema histórico JAXI. Pendiente enumerar sus distribuciones y ediciones.'))
    assert tables
    return dict(operations=operations,ine=tables,ineListings=gaps)


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--discover',action='store_true')
    args=parser.parse_args()
    CACHE.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(MANIFEST.read_bytes())
    if args.discover:
        manifest.update(discover(),revision=REVISION)
        MANIFEST.write_bytes(encode(manifest))
    inputs=[('ine-'+key+'.px',row['download']) for key,row in manifest['ine'].items()]
    inputs.extend((name,row['download']) for name,row in manifest['external'].items())
    inputs.extend((f'farmacia-{period}.html',url) for period,url in manifest.get('pharmacy',{}).items())
    print(len(manifest['ine']),'tablas INE y',len(manifest['ineListings']),'rutas históricas o incidencias',flush=True)
    with ThreadPoolExecutor(max_workers=5) as pool:
        errors={name:error for (name,_),(_,error) in zip(inputs,pool.map(get,inputs),strict=True) if error}
    (CACHE/'errors.json').write_bytes(encode(errors))
    print(len(inputs),'descargas comprobadas ·',len(errors),'incidencias',flush=True)


if __name__=='__main__':
    main()
