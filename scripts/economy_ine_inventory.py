"""Discover DAE editions and table identifiers from the official INEbase menus."""
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen
import json
import re

ROOT=Path(__file__).resolve().parents[1]
PAGE='https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736161927&idp=1254735576550&menu=resultados'


def get(url):
    with urlopen(url,timeout=35) as response:
        return response.read().decode('utf-8')


def branches(item):
    year,url=item
    html=get(url)
    pages=set(urljoin(url,unescape(link)) for link in re.findall(r'href="(\?padre=\d+(?:&amp;|&)capsel=\d+)"',html))
    return [(year,page) for page in sorted(pages)]


def tables(item):
    year,url=item
    html=get(url)
    return [(int(id),unescape(re.sub('<[^>]*>','',title)).strip(),year)
            for id,title in re.findall(r'<a href="/jaxi/Tabla\.htm\?tpx=(\d+)[^"]*"[^>]*>(.*?)</a>',html,re.S)]


def main():
    html=get(PAGE)
    years=[(int(year),urljoin(PAGE,unescape(link)))
           for link,year in re.findall(r'<option value="(/dynt3/[^"]+)">(20\d{2})</option>',html)]
    current=[(2024,'https://www.ine.es/dynt3/inebase/index.htm?capsel='+str(branch)+'&padre=14111') for branch in (14112,14113)]
    assert {y for y,_ in years}==set(range(2008,2024)),years
    legacy=[dict(year=year,url=url) for year,url in years if 'type=pcaxis' in url]
    years=[(year,url) for year,url in years if 'type=pcaxis' not in url]
    with ThreadPoolExecutor(max_workers=5) as pool:
        pages=[*current,*(entry for part in pool.map(branches,years) for entry in part)]
        year_tables={year:set() for year in range(2014,2025)}
        records={}
        for page,releases in zip(pages,pool.map(tables,pages),strict=True):
            for id,title,year in releases:
                assert id not in records or records[id]==(title,year),id
                records[id]=(title,year)
                year_tables[year].add(id)
    assert all(year_tables.values()),year_tables
    print({year:len(ids) for year,ids in year_tables.items()},flush=True)
    config_path=ROOT/'registry/economy-tables.json'
    config=json.loads(config_path.read_bytes())
    config['daeLegacyEditions']=sorted(legacy,key=lambda item:item['year'])
    config['additionalTables']={**config.get('additionalTables',{}),'166':[]}
    known=set(records)
    config['tables']=[t for t in config['tables'] if t['id'] not in known]
    for id,(title,year) in sorted(records.items(),key=lambda item:(-item[1][1],item[0])):
        url=f'https://www.ine.es/jaxiPx/Tabla.htm?tpx={id}'
        cohort=title.lower().startswith('supervivencias')
        note=(f'Edición {year}. Las cifras se refieren a la empresa estadística y a su actividad. '
              +('Cada cohorte conserva el ejercicio observado.' if cohort else 'Se conserva el carácter provisional cuando figura en el título.'))
        config['additionalTables']['166'].append(dict(Id=id,Nombre=title,sourceUrl=url))
        config['tables'].append(dict(id=id,label=f'{title.rstrip(".")} · {year}',family='Demografía armonizada de empresas',
            sourceUrl=url,note=note,dae=True,
            **({'periodDimension':'Año'} if cohort else {'fixedPeriod':str(year)}),
            **({'fixedStatus':'Provisional'} if 'provisional' in title.lower() else {})))
    config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
