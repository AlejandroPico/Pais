"""Import the Ministry of Housing open-data CSV distributions into atlas cubes."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal
import gzip
from pathlib import Path
import re
from urllib.request import urlopen
import shutil

import demography_collect as core

CACHE = core.ROOT / '.cache/f06'
OUT = core.ROOT / 'datos/vivienda/mivau'
CDN = 'https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/'
CATALOG = 'https://datos.gob.es/es/catalogo/e05233601-'
SERPAVI = 'https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi'
METHODOLOGY = 'https://cdn.mivau.gob.es/portal-web-mivau/vivienda/serpavi/2026-03-18_Metodologia_SERPAVI.pdf'
SOURCE_NOTES = {
    1: ('Alquiler declarado por municipio · SERPAVI', SERPAVI,
        'Cuantía mensual, superficie y recuento de las viviendas del estudio. El código COD_POSTAL identifica el municipio INE en este fichero. El CSV contiene el ámbito municipal.'),
    2: ('Estimación del parque de viviendas', CATALOG + 'estimacion-del-parque-de-viviendas1',
        'Viviendas principales, no principales y total. La distribución contiene provincias.'),
    3: ('Transacciones notariales de viviendas', CATALOG + 'transacciones-inmobiliarias-de-vivienda',
        'Escrituras notariales. Las filas complementarias se conservan. El fichero identifica el importe como EUR y su guía lo describe como valor medio en millones, por lo que se conserva el campo con unidad pendiente de verificación.'),
    4: ('Precio medio del suelo urbano', CATALOG + 'precio-medio-del-suelo',
        'Precio medio publicado en euros por metro cuadrado de suelo urbano, total y por tramos de población. Los estados como n.s. se conservan.'),
    5: ('Viviendas iniciadas y terminadas', CATALOG + 'numero-de-viviendas-iniciadas-y-terminadas-por-regimen-de-proteccion',
        'Cifras mensuales por régimen y estado de construcción tal como se publican en esta distribución.'),
    6: ('Valor tasado de la vivienda', CATALOG + 'valor-tasado-de-la-vivienda',
        'Valor medio tasado en euros por metro cuadrado. El ámbito conjunto Ceuta y Melilla se consulta como serie sin polígono propio.'),
    7: ('Vivienda y rehabilitación protegidas', CATALOG + 'vivienda-y-rehabilitacion-protegida',
        'Se conservan las calificaciones, solicitudes y aprobaciones. El CSV publica valores distintos con claves idénticas; los registros que coinciden se pueden consultar individualmente.'),
}
MEASURE = 'Indicador'
UNITS = {
    'Cuantía mensual': '€/mes', 'Superficie': 'm²', 'Viviendas arrendadas': 'viviendas',
    'Viviendas': 'viviendas', 'Número de transacciones': 'transacciones',
    'Importe · campo IMPORTE_TRANSACCIONES_EUR': 'Unidad pendiente de verificación',
    'Precio medio del suelo': '€/m²', 'Valor tasado': '€/m²',
}
PART_COUNTS = {'PERCENT25': 'Percentil 25', 'PERCENT75': 'Percentil 75', 'MEDIANA': 'Mediana', 'RECUENTO': 'Recuento'}
COMBINED = ('unlocated', 'Ceuta y Melilla', 'Ceuta y Melilla')


def coded(level, code, label):
    assert code.isdigit(), (level, code, label)
    return level, code.zfill(5 if level == 'municipal' else 2), label


def territory(n, r):
    if n == 1:
        code = r['COD_POSTAL']
        assert len(code) == 5 and code.startswith(r['COD_PROVINCIA']), r
        return coded('municipal', code, r['NOMBRE_MUNICIPIO'])
    if n == 6:
        pc, pn, cc, cn = (r[k] for k in ('CPRO','Provincia','CODAUTO','Comunidad_Autónoma'))
        if cn == 'Ceuta y Melilla':
            return COMBINED
        if core.norm(cn) == 'total nacional':
            return 'national', 'ES', 'España'
        if pc.isdigit():
            return coded('province', pc, pn)
        if cn:
            return coded('community', cc or core.GEO_NAMES['community', core.norm(cn)], cn)
        return 'unlocated', 'Sin ámbito identificado', 'Sin ámbito identificado'
    pc, pn, cc, cn = (r[k] for k in ('COD_PROV','NOM_PROV','COD_CCAA','NOM_CCAA'))
    level = r.get('NIVEL_TERRITORIAL')
    if cn == 'Ceuta y Melilla':
        return COMBINED
    if level == 'NACIONAL' or (pc == '00' and cc == '00'):
        return 'national', 'ES', 'España'
    if level == 'CCAA' or pc == '00':
        return coded('community', cc, cn)
    return coded('province', pc, pn)


def period(n, row):
    year = row.get('ANIO') or row.get('AÑO') or row['Año']
    assert re.fullmatch(r'\d{4}',year), row
    q = row.get('TRIMESTRE') or row.get('Trimestre')
    m = row.get('MES')
    if q:
        assert 1 <= int(q) <= 4, row
        return f'{year}T{q}'
    if m:
        assert 1 <= int(m) <= 12, row
        return f'{year}M{int(m):02}'
    return year


def data(n, r):
    if n == 1:
        kind = {'PRECIO':'Cuantía mensual','SUPERFICIE':'Superficie','VIVIENDA':'Viviendas arrendadas'}[r['ELEMENTO']]
        yield {MEASURE:kind,'Tipo de vivienda':r['TIPO_VIVIENDA'].capitalize(),
               'Estadístico':PART_COUNTS[r['TIPO_MEDIDA']]}, r['VALOR']
    elif n == 2:
        category = {'TOTALES':'Total', 'PRINCIPAL':'Principal', 'NO_PRINCIPAL':'No principal'}[r['CATEGORIA_PARQUE']]
        yield {MEASURE:'Viviendas','Tipo de ocupación':category}, r['NUM_VIVIENDAS']
    elif n == 3:
        common = {'Tipo de vivienda':r['TIPO_TRANSACCION'].replace('_',' ').capitalize(),
                  'Régimen':r['REGIMEN_VIVIENDA'].capitalize()}
        yield {MEASURE:'Número de transacciones',**common}, r['NUM_TRANSACCIONES']
        yield {MEASURE:'Importe · campo IMPORTE_TRANSACCIONES_EUR',**common}, r['IMPORTE_TRANSACCIONES_EUR']
    elif n == 4:
        bracket = r['TRAMO_POBLACION'].removeprefix('PMS ')
        yield {MEASURE:'Precio medio del suelo','Tamaño del municipio':'Total' if bracket=='General' else bracket}, r['PRECIO_MEDIO_SUELO_EUR_M2']
    elif n == 5:
        yield {MEASURE:'Viviendas','Régimen publicado':r['REGIMEN_VIVIENDA'],'Estado de construcción':r['ESTADO_CONSTRUCCION']}, r['NUM_VIVIENDAS']
    elif n == 6:
        yield {MEASURE:'Valor tasado','Régimen':r['Régimen']}, r['Valor']
    elif n == 7:
        yield {MEASURE:'Viviendas','Tipo de actuación':r['TIPO_VIVIENDA'],'Trámite':r['TIPO_TRAMITE'],
               'Estado de tramitación':r['ESTADO_TRAMITACION']}, r['NUM_VIVIENDAS']


def parse_value(token):
    if not re.fullmatch(r'-?\d+(?:[.,]\d+)?',token):
        return None, token or 'Celda vacía'
    value = Decimal(token.replace(',','.'))
    return int(value) if value == value.to_integral_value() else float(value), ''


def receive(n, refresh):
    code = f'VDP{n:03}_01'
    url = CDN + 'CSV/' + code + '.csv'
    path = CACHE / (code + '.csv')
    if refresh or not path.is_file():
        temp = path.with_suffix('.part')
        with urlopen(url, timeout=90) as response, temp.open('wb') as handle:
            shutil.copyfileobj(response, handle)
        temp.replace(path)
    with path.open('rb') as handle:
        import hashlib
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    return path, dict(url=url, bytes=path.stat().st_size, sha256=digest,
                      retrievedAt=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat())


def preferred(field, values):
    order = {'Indicador': ['Cuantía mensual','Número de transacciones'],
             'Tipo de vivienda':['Colectiva','Nueva'],'Estadístico':['Mediana'],
             'Régimen':['Libre'],'Régimen publicado':['Libre'],'Tipo de actuación':['Protegida']}
    choices = order.get(field, [])
    return sorted(values, key=lambda value:(choices.index(value) if value in choices else len(choices),value))


def build(n, path, source):
    tid = 940000+n
    observations = defaultdict(list)
    geo_names = {}
    dimensions = {}
    dates = set()
    raw_rows = 0
    with path.open(encoding='utf-8-sig',newline='') as handle:
        reader = csv.DictReader(handle, delimiter=';')
        for raw in reader:
            assert None not in raw and all(v is not None for v in raw.values()), raw
            row = {k:v.strip() for k,v in raw.items()}
            raw_rows += 1
            level, code, name = territory(n, row)
            area = level, code
            geo_names.setdefault(area, name)
            date = period(n, row)
            dates.add(date)
            for dims, value in data(n,row):
                for field, choice in dims.items():
                    dimensions.setdefault(field, set()).add(choice)
                observations[area, date, tuple(dims.values())].append(value)
    assert raw_rows and observations, path
    areas = sorted(geo_names)
    dates = sorted(dates)
    geo_index = {area:i for i,area in enumerate(areas)}
    date_index = {date:i for i,date in enumerate(dates)}
    options = [preferred(field,values) for field,values in dimensions.items()]
    indexes = [{v:i for i,v in enumerate(group)} for group in options]
    unique_count = sum(len(set(values)) for values in observations.values())
    identical_count = sum(map(len,observations.values())) - unique_count
    conflicts = sum(len(set(values)) > 1 for values in observations.values())
    max_variants = max(len(set(values)) for values in observations.values())
    dimensions = [dict(name=name,values=group) for name,group in zip(dimensions,options,strict=True)]
    if conflicts:
        dimensions.append(dict(name='Registro', values=['Serie principal', *[f'Coincidencia {i}' for i in range(1,max_variants+1)]]))
    parts = defaultdict(list)
    missing = Counter()
    for (area,date,labels), published in sorted(observations.items()):
        base = [geo_index[area],date_index[date],*[indices[label] for indices,label in zip(indexes,labels,strict=True)]]
        variants = list(dict.fromkeys(published))
        if not conflicts:
            rows = [([],parse_value(variants[0]))]
        elif len(variants)==1:
            rows = [([0],parse_value(variants[0]))]
        else:
            nonzero = [x for x in variants if parse_value(x)[0] not in (None,0)]
            main = parse_value(nonzero[0]) if n==3 and len(variants)==2 and '0' in variants and len(nonzero)==1 else (None,'Varios valores publicados para la misma clave')
            rows = [([0],main)] + [([i],parse_value(x)) for i,x in enumerate(variants,1)]
        part = area[1][:2] if area[0]=='municipal' else 'main'
        for suffix,(value,status) in rows:
            parts[part].append([*base,*suffix,value,status,tid])
            if status:
                missing[status] += 1
    shards = []
    for part, rows in sorted(parts.items()):
        content = core.encode({'rows':rows})
        blob = gzip.compress(content,compresslevel=9,mtime=0)
        filename = f'{tid}-{part}.json.gz'
        (OUT/filename).write_bytes(blob)
        shards.append(dict(id=part,file=filename,rows=len(rows),bytes=len(blob),sha256=core.sha(blob),
                           contentSha256=core.sha(content)))
    label,url,note = SOURCE_NOTES[n]
    if n==3 and conflicts:
        note += ' Cuando coinciden dos valores, uno cero y otro positivo, la serie principal muestra el valor informado distinto de cero. Las dos filas originales se consultan en Coincidencias.'
    source = dict(id=tid,year=int(dates[-1][:4]),**source)
    return dict(id=tid, label=label, title=label, family='Datos del Ministerio de Vivienda', publisher='MIVAU',
        sourceId='F111', dataFolder='vivienda/mivau', sourceUrl=url, downloadUrl=source['url'],
        license='Condiciones de reutilización del MIVAU' if n==1 else 'CC BY 4.0 · MIVAU',
        methodologyUrl=METHODOLOGY if n==1 else CDN+f'Info/Readme_VDP{n:03}_01.pdf',
        note=note, unit='Según el indicador', unitsByCategory=dict(dimension=MEASURE,values={m:UNITS[m] for m in options[0]}),
        rows=sum(s['rows'] for s in shards), rawRows=raw_rows, identicalCells=identical_count,
        distinctPublishedCells=unique_count, conflictingKeys=conflicts, dimensions=dimensions,
        territories=[dict(id=f'{level}:{code}',level=level,code=code,name=geo_names[level,code],sourceTableIds=[tid],
                          **({'provinceCode':code[:2]} if level=='municipal' else {})) for level,code in areas],
        periods=[dict(id=d,label=d) for d in dates], shards=shards, sourceTables=[source],missingTokens=dict(missing))


def main(refresh=False):
    CACHE.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    captures=[(n,*receive(n,refresh)) for n in SOURCE_NOTES]
    tables=[]
    for n,path,source in captures:
        table=build(n,path,source)
        tables.append(table)
        print(f'{path.stem}: {table["rawRows"]} source rows / {table["rows"]} query rows',flush=True)
    (OUT/'index.json').write_bytes(core.encode(dict(schemaVersion=1,tables=tables)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
