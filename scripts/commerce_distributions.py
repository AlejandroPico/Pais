"""Convert DataComex analysis workbooks and DGOJ's online market CSVs."""
import argparse
from collections import Counter
import csv
import gzip
from html import unescape
import io
import json
import math
import re
from urllib.parse import quote, urljoin
from urllib.request import urlopen

from affiliation_collect import fetch, workbook
from commerce_bde import GEO, MONTHS, NATIONAL
from demography_collect import ROOT, encode, norm, sha
from economy_cna import sheets

CACHE = ROOT / '.cache/f08'
COMEX = 'https://comercio.gob.es/ImportacionExportacion/Informes_Estadisticas/Paginas/Historico-boletinesdatos-me.aspx'
DGOJ = 'https://www.ordenacionjuego.es/en/node/3018'
DGOJ_FILES = {
    'ggr': ('923374e4-20d7-442a-9465-eafbe9da86cd', 'Cantidades jugadas e ingresos brutos', {
        'Cantidades jugadas': 'Euros', 'GGR': 'Euros'}),
    'depositos': ('187455da-a217-43ff-9893-5fe754832b71', 'Depósitos y retiradas', {
        'Depósitos': 'Euros', 'Retiradas': 'Euros', 'Nº de depósitos': 'Operaciones'}),
    'cuentas': ('91975920-56b4-4995-a3a0-300f0b307789', 'Cuentas activas y nuevas', {
        'Cuentas activas': 'Cuentas', 'Cuentas nuevas': 'Cuentas'}),
    'publicidad': ('5fd6aafb-5bb0-47c6-b259-7bd5ccbf7ad6', 'Publicidad y promoción', {
        'Publicidad': 'Euros', 'Bonos': 'Euros', 'Afiliados': 'Euros', 'Patrocinio': 'Euros', 'Total Gastos': 'Euros'}),
}
COMEX_PROFILES = {
    'sectores': ('Sectores económicos', 'Sector'),
    'capitulos': ('Capítulos del Sistema Armonizado', 'Capítulo'),
    'paises': ('Países y áreas socias', 'Socio comercial'),
    'libre-comercio': ('Acuerdos de libre comercio', 'Socio comercial'),
    'ccaa': ('Comunidades y provincias', None),
}
AMOUNT = 'Millones de euros'


def number(value, delimiter='.'):
    text = str(value or '').strip()
    try:
        result = float(text.replace(delimiter, '.'))
        assert math.isfinite(result)
        return result, ''
    except ValueError:
        return None, text or 'Sin dato'


def publish(folder, product, input_rows, dimension_names, units, *, section='comercio', source_by_period=None,
            source_for_record=None):
    output = ROOT / 'datos' / section / folder
    identifier = product['id']
    territories, periods = {}, {}
    dimensions = [{} for _ in dimension_names]
    records, missing = [], Counter()
    area_sources = {}
    seen = set()
    for area, period_id, label, categories, value, status in input_rows:
        g = territories.setdefault(area['id'], (len(territories), area))[0]
        p = periods.setdefault(period_id, (len(periods), label))[0]
        position = (g, p, *(labels.setdefault(value, len(labels)) for labels,value in zip(dimensions,categories,strict=True)))
        assert position not in seen, (product['label'], area['name'], label, categories)
        seen.add(position)
        if value is None:
            missing[status] += 1
        source = source_for_record(period_id, categories) if source_for_record else (
            source_by_period[period_id] if source_by_period else identifier)
        area_sources.setdefault(g, set()).add(source)
        records.append([*position, value, status, source])
    assert records, product['label']
    areas = [{**area, 'sourceTableIds': sorted(area_sources[index])} for index,area in territories.values()]
    parts = {}
    for row in records:
        area=areas[row[0]]
        part=area['provinceCode'] if area['level']=='municipal' else 'main'
        parts.setdefault(part,[]).append(row)
    shards=[]
    for part,rows in sorted(parts.items()):
        file = f'{identifier}-{part}.json.gz'
        payload = encode(dict(rows=rows))
        data = gzip.compress(payload, compresslevel=6, mtime=0)
        (output / file).write_bytes(data)
        shards.append(dict(id=part,file=file,rows=len(rows),bytes=len(data),sha256=sha(data),contentSha256=sha(payload)))
    return {**product, 'title':product['label'], 'dataFolder':f'{section}/{folder}', 'rows':len(records),
        'unit':next(iter(units.values())) if len(set(units.values()))==1 else 'Según indicador',
        'unitsByCategory':dict(dimension='Indicador',values=units),
        'territories':areas,
        'periods':[dict(id=id,label=label) for id,(_,label) in periods.items()],
        'dimensions':[dict(name=name,values=list(values)) for name,values in zip(dimension_names,dimensions,strict=True)],
        'missingTokens':dict(missing), 'shards':shards}


def distribution(folder, path, url, refresh):
    raw = fetch(url, CACHE / path, refresh)
    original = ROOT / 'datos/comercio' / folder / 'originales' / path
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_bytes(raw)
    return raw, dict(url=url, originalFile='originales/'+path, sha256=sha(raw), bytes=len(raw))


def dgoj_products(refresh):
    for index, (file, (download, name, units)) in enumerate(DGOJ_FILES.items(), 1):
        url = 'https://www.ordenacionjuego.es/en/cmis/document/alfresco/' + download
        raw, source = distribution('dgoj', 'dgoj-'+file+'.csv', url, refresh)
        identifier = 951000 + index
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';')
        games = 'Juego' in reader.fieldnames
        expected = {'Año','Trimestre','Mes',*units}
        assert set(reader.fieldnames)==expected|({'Juego'} if games else set())
        records = []
        for row in reader:
            month = MONTHS[norm(row['Mes'])[:3].upper()]
            year = row['Año']
            assert row['Trimestre']==f'{year}.T{(month-1)//3+1}'
            for measure in units:
                categories = (measure,row['Juego']) if games else (measure,)
                records.append((NATIONAL,f'{year}M{month:02}',f'{row["Mes"]} {year}',categories,*number(row[measure],',')))
        note = 'Mercado de juego en línea de ámbito estatal. Las cuentas, los importes y el número de operaciones se mantienen en sus unidades. Distribución publicada para el segundo trimestre de 2026.'
        product = dict(id=identifier, label=name, publisher='Dirección General de Ordenación del Juego', sourceId='F127',
                       family='Juego en línea · DGOJ', license='Condiciones de reutilización de la DGOJ', note=note,
                       sourceUrl=DGOJ, downloadUrl=url, sourceTables=[dict(id=identifier,**source)])
        yield publish('dgoj',product,records,('Indicador','Juego') if games else ('Indicador',),units)


def comex_area(area, territorial):
    if not territorial:
        return NATIONAL
    key=norm(area)
    if key=='total':
        return NATIONAL
    for level in ('community','province'):
        if code := GEO.get((level,key)):
            return dict(id=f'{level}:{code}',level=level,code=code,name=area)
    return dict(id='unlocated:'+key, level='unlocated', code=key, name=area)


def repeated_label(counts, label):
    ordinal = counts[label] + 1
    counts[label] = ordinal
    return label if ordinal==1 else f'{label} · fila {ordinal}'


def annual_records(raw, territorial):
    records=[]
    for sheet,path in sheets(raw):
        measure=sheet.strip()
        years={}
        names=Counter()
        for row in workbook(raw,path):
            date_cols={k:v for k,v in row.items() if re.fullmatch(r'(?:19|20)\d\d\*?',v)}
            if len(date_cols)>=30:
                years=date_cols
                continue
            name=row.get('A','').strip()
            if not years or not name or not any(number(row.get(k))[0] is not None for k in years):
                continue
            area=comex_area(name,territorial)
            name=repeated_label(names,name)
            categories=(measure,) if territorial else (measure,name)
            for k,year in years.items():
                value,status=number(row.get(k))
                year_id=year.removesuffix('*')
                records.append((area,year_id,year_id,categories,value,status or ('Provisional' if year.endswith('*') else '')))
    return records


def monthly_records(raw, territorial):
    monthly, accumulated, headings = [], [], []
    units={
        'Exportaciones':AMOUNT, 'Exportaciones · porcentaje del total':'Porcentaje',
        'Exportaciones · variación interanual':'Porcentaje', 'Importaciones':AMOUNT,
        'Importaciones · porcentaje del total':'Porcentaje','Importaciones · variación interanual':'Porcentaje',
        'Saldo del periodo':AMOUNT, 'Saldo del periodo de comparación':AMOUNT,
    }
    for sheet,path in sheets(raw):
        rows=list(workbook(raw,path))
        heading=next(r['A'].split(' / ')[0].removeprefix('Periodo: ') for r in rows if r.get('A','').startswith('Periodo: '))
        month=MONTHS[norm(heading.split()[0].split('-')[-1])[:3].upper()]
        year=re.search(r'\d{4}',heading)[0]
        first=next(i for i,r in enumerate(rows) if r.get('B','').startswith('Mill.'))
        data=[r for r in rows[first+1:] if r.get('A') and any(r.get(k) for k in 'BCDEFGHI')]
        if not any(number(r.get('B'))[0] is not None for r in data):
            continue
        names=Counter()
        records=accumulated if sheet=='Acumulado' else monthly
        headings.append(f'{sheet} ({heading}): H={rows[first].get("H", "")}, I={rows[first].get("I", "")}')
        for row in data:
            name=row['A'].strip()
            if norm(name).startswith(('fuente:', 'source:', 'datos de aduanas')):
                continue
            area=comex_area(name,territorial)
            name=repeated_label(names,name)
            exports,_=number(row.get('B'))
            imports,_=number(row.get('E'))
            balance,_=number(row.get('H'))
            if all(x is not None for x in (exports,imports,balance)):
                assert math.isclose(exports-imports,balance,abs_tol=1e-5), (sheet,name,exports,imports,balance)
            for column,measure in zip('BCDEFGHI',units,strict=True):
                value,status=number(row.get(column))
                categories=(measure,) if territorial else (measure,name)
                records.append((area,f'{year}M{month:02}',heading,categories,value,status or 'Provisional'))
    return monthly, accumulated, units, headings


def comex_products(refresh):
    with urlopen(COMEX, timeout=30) as response:
        html=response.read().decode('utf-8')
    links={}
    for match in re.findall(r'href="([^"]+\.xlsx[^"]*)"',html,re.I):
        url=urljoin(COMEX,quote(unescape(match),safe='/%'))
        links[unescape(match).rsplit('/',1)[-1]]=url
    expected=('1_comex_sectores.xlsx','2_comex_capitulos.xlsx','3_comex_paises.xlsx',
              '3a_comex_libre-comercio.xlsx','4_comex_ccaa.xlsx','1_comex_anual_sectores.xlsx',
              '2_comex_anual_capitulos.xlsx','3_comex_anual_paises.xlsx','4_comex_anual_ccaa.xlsx')
    assert set(expected)<=links.keys()
    for index, file in enumerate(expected,1):
        download=links[file]
        raw,source=distribution('datacomex',file,download,refresh)
        profile=file.removesuffix('.xlsx').rsplit('_',1)[-1]
        title, dimension=COMEX_PROFILES[profile]
        names=('Indicador',dimension) if dimension else ('Indicador',)
        note='Secretaría de Estado de Comercio, DataComex y Aduanas de la AEAT. Comercio declarado de mercancías. El socio comercial o sector se conserva como filtro y se respeta la cobertura publicada de cada cuadro.'
        groups=[]
        if '_anual_' in file:
            groups.append(('Anual',annual_records(raw,dimension is None),dict(Exportaciones=AMOUNT,Importaciones=AMOUNT),[]))
        else:
            monthly, accumulated, units, headings=monthly_records(raw,dimension is None)
            groups.extend([('Mensual',monthly,units,headings),('Acumulado del año',accumulated,units,headings[:1])])
        for offset,(group,records,units,headings) in enumerate(groups):
            identifier=950000 + index*10 + offset
            product=dict(id=identifier,label=f'{title} · {group}',sourceId='F051',publisher='Secretaría de Estado de Comercio',
                         family='Comercio exterior declarado · DataComex',sourceUrl=COMEX,downloadUrl=download,
                         license='Aviso legal y condiciones de reutilización de Comercio',
                         note=note+(' El encabezado original de saldo acumulado arrastra rótulos de otros años. Se verificó el saldo del periodo contra exportaciones menos importaciones.' if dimension is None and group=='Acumulado del año' else ''),
                         sourceTables=[dict(id=identifier,notes=headings,**source)])
            yield publish('datacomex',product,records,names,units)


def main(only=None, refresh=False):
    CACHE.mkdir(parents=True,exist_ok=True)
    revision=json.loads((ROOT/'registry/commerce-tables.json').read_bytes())['revision']
    for folder,collect in [('dgoj',dgoj_products),('datacomex',comex_products)]:
        if only and folder!=only:
            continue
        tables=list(collect(refresh))
        output=ROOT/'datos/comercio'/folder/'index.json'
        output.write_bytes(encode(dict(schemaVersion=1,revision=revision,tables=tables)))
        print(f'{folder}: {len(tables)} products, {sum(t["rows"] for t in tables):,} observations')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    parser.add_argument('--only',choices=('datacomex','dgoj'))
    args=parser.parse_args()
    main(args.only,args.refresh)
