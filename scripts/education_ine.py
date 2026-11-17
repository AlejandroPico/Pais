"""Import the INE household education expenditure table groups and their source editions."""
from concurrent.futures import ThreadPoolExecutor
from html import unescape
import re
from urllib.parse import urlencode

from affiliation_collect import fetch
from education_collect import CACHE, OUTPUT, REVISION, encode, px_product

BASE='https://www.ine.es/'
EDITIONS = (
    ('2023-2024',12748,(12749,12750,12751,12753,12752)),
    ('2019-2020',7436,(7437,7438,7439,7440)),
)


def results():
    for course,parent,children in EDITIONS:
        for child in children:
            listing=BASE+'dynt3/inebase/index.htm?'+urlencode(dict(padre=parent,capsel=child))
            raw=fetch(listing,CACHE/f'ine-list-{child}.html',False)
            html=raw.decode('utf-8')
            tables = re.findall(r'<a[^>]+href="([^"]*/Tabla\.htm\?[^"]+)"[^>]*>(.*?)</a>',html,re.I|re.S)
            for path,title in tables:
                table=BASE+unescape(path).lstrip('/')
                code=re.search(r'tpx=(\d+)',table)
                if not code:
                    continue
                title=' '.join(unescape(re.sub(r'<[^>]+>','',title)).split())
                yield dict(table=table,title=title,edition=course,topic='ine',
                           listing=listing,download=BASE+'jaxi/files/tpx/es/px/'+code[1]+'.px')


def get(info):
    name=info['download'].rsplit('/',1)[-1]
    try:
        return px_product(info,fetch(info['download'],CACHE/('ine-'+name),False)),None
    except (ValueError, OSError, AssertionError, KeyError) as error:
        return None,{**info,'reason':str(error)[:220]}


def main():
    links = {entry['download']:entry for entry in results()}
    assert links,'No table links found in INE release result groups'
    with ThreadPoolExecutor(max_workers=5) as pool:
        result=list(pool.map(get,links.values()))
    tables=[table for table,_ in result if table]
    gaps=[error for _,error in result if error]
    (OUTPUT/'ine/index.json').write_bytes(encode(dict(revision=REVISION,tables=tables)))
    (CACHE/'ine-summary.json').write_bytes(encode(dict(reviewed=len(result),available=len(tables),gaps=gaps)))
    print('INE',len(tables),'celdas',sum(t['rows'] for t in tables),'incidencias',len(gaps),flush=True)


if __name__=='__main__':
    main()
