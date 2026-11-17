"""Capture annual municipal debt, SEC public accounts and collection by tax office."""
import argparse
from collections import Counter
from html import unescape
import math
from pathlib import Path
import re
import sys
from urllib.parse import quote, urljoin
from urllib.request import urlopen

from affiliation_collect import fetch, workbook
from commerce_bde import GEO, NATIONAL
from commerce_distributions import number, publish
from demography_collect import ROOT, encode, norm, sha
from economy_cna import sheets
from fiscal_bde import REVISION

CACHE = ROOT / '.cache/f09'
BASE = 'https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/paginas/'
QUARTERLY = BASE + 'itnofinancierastotal.aspx'
REGIONAL = BASE + 'ianofinancierasca.aspx'
DEBT = 'https://www.hacienda.gob.es/es-ES/CDI/paginas/sistemasfinanciaciondeuda/informacioneells/deudaviva.aspx'
TAX = 'https://sede.agenciatributaria.gob.es/Sede/datosabiertos/catalogo/hacienda/Informe_mensual_de_Recaudacion_Tributaria.shtml'
TAX_FILE = 'https://sede.agenciatributaria.gob.es/static_files/Sede/Tema/Estadisticas/Recaudacion_Tributaria/Informes_mensuales/Ingresos_por_Delegaciones.xlsx'
MILLIONS = 'Millones de euros'
RATIO = 'Porcentaje del PIB'
DEBT_INDICATOR = 'Deuda viva'
PEOPLE = 'Población publicada con la edición de 2008'


def links(url):
    with urlopen(url,timeout=35) as response:
        html=response.read().decode('utf-8')
    for path, text in re.findall(r'<a[^>]*?href="([^"]+?\.xlsx?)"[^>]*>(.*?)</a>',html,re.I|re.S):
        label=' '.join(re.sub('<[^>]*>',' ',unescape(text)).split())
        yield urljoin(url,quote(unescape(path),safe=':/%')),label


def download(url, refresh, *, original=None):
    name=Path(url).name
    data=fetch(url,CACHE/name,refresh)
    source=dict(url=url, bytes=len(data), sha256=sha(data))
    if original:
        path=ROOT/'datos/hacienda'/original/'originales'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        source['originalFile']='originales/'+name
    return data,source


def area(label, level, code):
    return dict(id=f'{level}:{code}',level=level,code=code,name=label)


def no_geometry(label):
    return area(label,'unlocated',norm(label))


def community(name):
    alias={'baleares':'04','comunitat valencia':'10','valencia':'10','asturias':'03','navarra':'15','murcia':'14','madrid':'13'}
    label=norm(name)
    code=alias.get(label) or GEO.get(('community',label))
    return area(name,'community',code) if code else no_geometry(name)


def excel_rows(data, sheet_index=0):
    if data.startswith(b'PK'):
        yield from workbook(data,list(sheets(data))[sheet_index][1])
        return
    # xlrd is only needed when refreshing the 12 original XLS editions.
    sys.path.insert(0,str(CACHE/'deps'))
    try:
        import xlrd
        book=xlrd.open_workbook(file_contents=data,on_demand=True)
        try:
            sheet=book.sheet_by_index(sheet_index)
            for row in sheet.get_rows():
                yield {chr(65+i):str(c.value).strip() for i,c in enumerate(row[:26])}
        finally:
            book.release_resources()
    finally:
        sys.path.pop(0)


def coded(value, size):
    text=str(value).removesuffix('.0').strip()
    if text.isdigit() and len(text)<=size:
        return text.zfill(size)
    return None


def debt_records(data, year):
    for row in excel_rows(data):
        if year=='2011':
            province,municipality,name,value=(row.get(c,'') for c in 'BCDE')
        else:
            if coded(row.get('A',''),4)!=year:
                continue
            province,municipality,name,value=(row.get(c,'') for c in 'DFGH')
        province=coded(province,2)
        municipality=coded(municipality,3)
        if not province or not municipality or not name:
            continue
        code=province+municipality
        place={**area(name,'municipal',code),'provinceCode':province}
        yield place,year,year,(DEBT_INDICATOR,),*number(value)
        if year=='2008':
            yield place,year,year,(PEOPLE,),*number(row.get('I'))


def debt_product(refresh):
    editions={}
    for url,label in links(DEBT):
        year=re.search(r'31/12/(20\d\d)',label)
        if 'deuda viva de los ayuntamientos' in label.lower() and year:
            editions[year[1]]=url
    assert set(editions)>={str(y) for y in range(2008,2026)}
    observations, sources, by_period = [], [], {}
    identifier=961001
    for year,url in sorted(editions.items(),reverse=True):
        data,source=download(url,refresh)
        rows=list(debt_records(data,year))
        assert len({a['id'] for a,*_ in rows}) >= 8100, (year,len(rows))
        by_period[year]=962000+int(year)
        sources.append(dict(id=by_period[year],year=int(year),**source))
        observations.extend(rows)
    product=dict(id=identifier,label='Deuda viva de los ayuntamientos',family='Deuda municipal · Ministerio de Hacienda',
        publisher='Ministerio de Hacienda',sourceId='F043',sourceUrl=DEBT,downloadUrl=sources[0]['url'],sourceTables=sources,
        license='Condiciones de reutilización del Ministerio de Hacienda',
        note='Saldo a 31 de diciembre, en miles de euros. Se conserva el código provincial y municipal de cada edición y la población que acompaña a la edición de 2008. El total de un ayuntamiento no incluye el de las diputaciones y entidades supramunicipales.')
    return publish('deuda-local',product,observations,('Indicador',),{DEBT_INDICATOR:'Miles de euros',PEOPLE:'Personas'},
        section='hacienda',source_by_period=by_period)


def sec_value_rows(raw, path, year, percent):
    rows=[r for r in workbook(raw,path) if any(r.values())]
    position=next(i for i,row in enumerate(rows) if norm(row.get('B',''))=='conceptos')
    header=rows[position]
    columns={}
    previous=rows[position-1]
    current_year=''
    for column,label in header.items():
        if column in {'A','B'} or not label:
            continue
        if year:
            date=year
            place=area(label,'national','ES') if norm(label).startswith('total administracion regional') else community(label)
            state='Provisional' if any(year+'(P)' in r.get('A','') for r in rows[:position]) else ''
        else:
            if label in {'T1','T2','T3','T4'}:
                current_year=previous.get(column) or current_year
                date=current_year[:4]+label
                state='Provisional' if '(P)' in current_year else ''
            else:
                date=label[:4]
                state='Provisional' if '(P)' in label else ''
            assert re.fullmatch(r'\d{4}(?:T[1-4])?',date), (path,column,date)
            place=NATIONAL
        if any(row.get(column) for row in rows[position+1:]):
            columns[column]=(place,date,state)
    group='Recursos'
    seen=Counter()
    for row in rows[position+1:]:
        code,label=(row.get(c,'') for c in 'AB')
        if norm(label)=='empleos no financieros':
            group='Empleos'
        if not any(row.get(col) for col in columns):
            continue
        if not label and norm(code).startswith('pib'):
            indicator,unit='PIB utilizado',MILLIONS
        elif label or code:
            indicator=' · '.join(filter(None,(group,code,label)))
            seen[indicator]+=1
            if seen[indicator]>1:
                indicator+=f' · fila {seen[indicator]}'
            unit=RATIO if percent else MILLIONS
        else:
            raise ValueError(('Unlabelled SEC observation',path,row))
        for col,(place,date,state) in columns.items():
            value,missing=number(row.get(col))
            yield (place,date,date,(indicator,),value,missing or state),indicator,unit


def sec_books(refresh):
    profiles={'T_AAPP.xlsx':'Administraciones públicas (S.13)', 'T_AACC.xlsx':'Administración central (S.1311)',
        'T_CCAA.xlsx':'Administración regional (S.1312)', 'T_CCLL.xlsx':'Administración local (S.1313)',
        'T_AASS.xlsx':'Fondos de la Seguridad Social (S.1314)', 'A_CCAA.xlsx':'Administración regional · serie anual'}
    results=[]
    editions={'a':[],'b':[]}
    for page in (QUARTERLY,REGIONAL):
        for url,_ in links(page):
            name=Path(url).name
            match=re.fullmatch(r'A_CCAA_Det_(\d{4})\.xlsx',name,re.I)
            if name not in profiles and not match:
                continue
            raw,source=download(url,refresh,original='igae')
            by_sheet={}
            for sheet,path in sheets(raw):
                if sheet.lower().strip() not in {'tabla1a','tabla1b'}:
                    continue
                percent=sheet.lower().strip().endswith('b')
                year=match[1] if match else None
                entries=list(sec_value_rows(raw,path,year,percent))
                by_sheet['b' if percent else 'a']=entries
                if match:
                    editions['b' if percent else 'a'].append((year,source,entries))
                else:
                    identifier=963001+list(profiles).index(name)*2+int(percent)
                    title=profiles[name]+' · '+(RATIO if percent else MILLIONS)
                    results.append(sec_cube(identifier,title,page,[(None,source,entries)],page==QUARTERLY))
            assert len(by_sheet)==2, name
            if match and match[1] in {'2024','2025'}:
                sec_check_denominator(by_sheet,name)
    for suffix,items in sorted(editions.items()):
        assert {year for year,_,_ in items} >= {str(y) for y in range(2000,2026)}
        identifier=963091+int(suffix=='b')
        title='Operaciones no financieras por comunidad · '+(RATIO if suffix=='b' else MILLIONS)
        results.append(sec_cube(identifier,title,REGIONAL,sorted(items,reverse=True),False))
    return sorted(results,key=lambda t:t['id'])


def sec_check_denominator(sheets_data, filename):
    amounts={row[0]['id']:row[4] for row,label,_ in sheets_data['a'] if row[0]['level']=='community' and 'B.9 · CAPACIDAD' in label}
    ratios={row[0]['id']:row[4] for row,label,_ in sheets_data['b'] if row[0]['level']=='community' and 'B.9 · CAPACIDAD' in label}
    gdp={row[0]['id']:row[4] for row,label,_ in sheets_data['b'] if row[0]['level']=='community' and label=='PIB utilizado'}
    assert len(amounts)==len(ratios)==len(gdp)==17,(filename,amounts.keys(),ratios.keys(),gdp.keys())
    assert all(math.isclose(amounts[key]*100/gdp[key],ratios[key],abs_tol=1e-8) for key in amounts),filename


def sec_cube(identifier,title,page,editions,quarterly):
    rows, units, sources, period_sources=[],{},[],{}
    for year,source,entries in editions:
        edition=identifier if not year else identifier*10000+int(year)
        sources.append(dict(id=edition,**({'year':int(year)} if year else {}),**source))
        for row,indicator,unit in entries:
            rows.append(row)
            units[indicator]=unit
            period_sources[row[1]]=edition
    note='IGAE, SEC 2010, Revisión Estadística 2024. Los saldos se refieren al subsector público declarado. El PIB de referencia se conserva en millones.'
    if quarterly:
        note+=' Datos trimestrales acumulados desde el comienzo del ejercicio.'
    if identifier==963092:
        note+=' Las portadas de la hoja Tabla1b rotulan «Millones de euros» en 2024 y 2025. Se verificó la unidad de porcentaje con los importes de Tabla1a y el PIB de referencia.'
    product=dict(id=identifier,label=title,family='Cuentas públicas · IGAE',publisher='IGAE',sourceId='F044',
        sourceUrl=page,downloadUrl=sources[0]['url'],sourceTables=sources,license='Condiciones de reutilización de la IGAE',note=note)
    return publish('igae',product,rows,('Indicador',),units,section='hacienda',source_by_period=period_sources)


def tax_product(refresh):
    raw,source=download(TAX_FILE,refresh)
    path=dict(sheets(raw))['datos_delegaciones']
    rows=workbook(raw,path)
    header=next(rows)
    places={}
    for column,name in header.items():
        if column in {'A','B','C'} or not name:
            continue
        if name=='Total':
            places[column]=NATIONAL
        elif name.startswith('D.E. '):
            place=community(name.removeprefix('D.E. '))
            places[column]={**place,'name':name}
        else:
            places[column]=no_geometry(name)
    entries=[]
    units={}
    for row in rows:
        year,month,measure=(row.get(c,'') for c in 'ABC')
        if not year.isdigit():
            continue
        date=f'{year}M{int(month):02}'
        units[measure]='Miles de euros'
        for col,place in places.items():
            entries.append((place,date,date,(measure,),*number(row.get(col))))
    identifier=964001
    product=dict(id=identifier,label='Ingresos, devoluciones y conceptos por delegación',family='Recaudación tributaria · AEAT',
        publisher='Agencia Tributaria',sourceId='F042',sourceUrl=TAX,downloadUrl=TAX_FILE,sourceTables=[dict(id=identifier,**source)],
        license='Condiciones de reutilización de la AEAT',note='Ingresos tributarios en términos de caja. Las Delegaciones Especiales se dibujan en su ámbito de gestión. La recaudación contabilizada por una oficina no equivale a la recaudación generada en el territorio. Se conserva el resto de las oficinas y partidas centrales como fichas.')
    return publish('aeat',product,entries,('Indicador',),units,section='hacienda')


def main(only=None, refresh=False):
    CACHE.mkdir(parents=True,exist_ok=True)
    for name, collector in [('deuda-local',lambda:[debt_product(refresh)]),('igae',lambda:sec_books(refresh)),('aeat',lambda:[tax_product(refresh)])]:
        if only and only!=name:
            continue
        folder=ROOT/'datos/hacienda'/name
        folder.mkdir(parents=True,exist_ok=True)
        tables=collector()
        (folder/'index.json').write_bytes(encode(dict(schemaVersion=1,revision=REVISION,tables=tables)))
        print(f'{name}: {len(tables)} productos, {sum(t["rows"] for t in tables)} observaciones')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    parser.add_argument('--only',choices=('deuda-local','igae','aeat'))
    args=parser.parse_args()
    main(args.only,args.refresh)
