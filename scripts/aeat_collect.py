"""Import every column of the official AEAT municipal IRPF bulk distribution."""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import re
import sys
from urllib.request import urlopen

from demography_collect import ROOT, encode, sha

CACHE = ROOT / '.cache/f03'
OUT = ROOT / 'datos/renta/aeat'
BASE = 'https://sede.agenciatributaria.gob.es'
CATALOG = BASE + '/Sede/estadisticas/anuario-estadistico/acceso-descarga-masiva-datos.html'
DOWNLOAD = 'https://www3.agenciatributaria.gob.es/static_files/Sede/Tema/Estadisticas/Anuario_estadistico/Exportacion/IRPFmunicipios.csv'
DICTIONARY = BASE + '/static_files/Sede/Tema/Estadisticas/Anuario_estadistico/Exportacion/AyudaCSV_AnuarioMunicipal.pdf'
BANDS = {'1': 'Más de 500.000', '2': '100.001–500.000', '3': '50.001–100.000',
         '4': '20.001–50.000', '5': '10.001–20.000', '6': '5.001–10.000',
         '7': '1.000–5.000', '10': 'Menos de 1.000'}


def snapshot(name, url, refresh):
    path = CACHE / name
    if refresh or not path.exists():
        with urlopen(url, timeout=90) as response:
            data = response.read()
        path.write_bytes(data)
    return path


def dictionary(path):
    if (CACHE/'python').is_dir():
        sys.path.insert(0, str(CACHE/'python'))
    from pypdf import PdfReader

    variables, municipalities = {}, {}
    for index, page in enumerate(PdfReader(path).pages):
        lines = page.extract_text(extraction_mode='layout').splitlines()
        for position, line in enumerate(lines):
            if index < 3:
                match = re.match(r'\s*(MUNI_\d+)\s+(.+)', line)
                if match:
                    variables[match[1]] = match[2].strip()
                continue
            fields = re.split(r'\s{2,}', line.strip())
            if len(fields) == 4 and fields[0].isdigit():
                identifier, region, province, label = fields
                if label.endswith('-') and position+1 < len(lines) and re.fullmatch(r'\s+\d{5}\s*', lines[position+1]):
                    label += lines[position+1].strip()
                municipalities[identifier] = label
    municipalities.update({'8116':'Ceuta-51001','8117':'Melilla-52001','8118':'No residentes'})
    assert len(municipalities) > 3100 and len(variables) >=112
    return variables, municipalities


def main(refresh):
    CACHE.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    source = snapshot('aeat-irpf.csv',DOWNLOAD,refresh)
    guide = snapshot('aeat-diccionario.pdf',DICTIONARY,refresh)
    desc, names = dictionary(guide)
    definitions = Counter(match[1] for label in names.values() if (match := re.search(r'-(\d{5})$', label)))
    ambiguous = set()
    territories, periods, geos, times, parts, seen = [], [], {}, {}, defaultdict(list), set()
    unknown = set()
    missing = Counter()
    with source.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f,delimiter=';')
        assert next(reader)[:3] == ['EJER','TRAMO','MUNI_DEF']
        f.seek(0)
        columns=next(reader)[3:]
        labels=[f'{desc[c]} · {c}' for c in columns]
        for year, band, identifier, *cells in reader:
            assert len(cells)==len(labels) and (year,band,identifier) not in seen
            seen.add((year,band,identifier))
            if year not in times:
                times[year]=len(periods)
                periods.append(dict(id=year,label=year))
            if identifier not in geos:
                label=names.get(identifier)
                if label is None:
                    unknown.add(identifier)
                    label=f'Código AEAT {identifier}'
                match=re.search(r'-(\d{5})$',label)
                if match and definitions[match[1]] > 1:
                    ambiguous.add(identifier)
                    label=f'{label} · código AEAT {identifier}, correspondencia ambigua'
                    match=None
                level='municipal' if match else 'unlocated'
                code=match[1] if match else identifier
                geos[identifier]=len(territories)
                territories.append(dict(id=f'{level}:{code}',level=level,code=code,
                    name=label[:-6] if match else label,provinceCode=code[:2] if match else None))
            g=geos[identifier]
            part=territories[g]['provinceCode'] or 'main'
            band_index=list(BANDS).index(band)
            values=[]
            for token in cells:
                if re.fullmatch(r'-?\d+(?:,\d+)?',token):
                    values.append(float(token.replace(',','.')) if ',' in token else int(token))
                else:
                    status=token or 'Sin dato'
                    values.append(status)
                    missing[status]+=1
            parts[part].append([g,times[year],int(year),band_index,*values])
    by_area = {}
    for identifier, i in geos.items():
        area = territories[i]
        if area['id'] in by_area:
            # Keep both original codes distinct if the guide points them to the same geography.
            prior = by_area[area['id']]
            raise ValueError(f'Duplicate dictionary mapping {area}, {prior} and {identifier}')
        by_area[area['id']] = identifier
    shards=[]
    for part, rows in sorted(parts.items()):
        table_rows=[]
        for g,p,year,band,*values in rows:
            # The population band is a published observation dimension, including years where it changes.
            table_rows.extend([g,p,i,band,v if not isinstance(v,str) else None,v if isinstance(v,str) else '',year]
                              for i,v in enumerate(values))
        payload=encode(dict(rows=table_rows))
        compressed=gzip.compress(payload,compresslevel=5,mtime=0)
        filename=f'920001-{part}.json.gz'
        (OUT/filename).write_bytes(compressed)
        shards.append(dict(id=part,file=filename,rows=len(table_rows),bytes=len(compressed),
                           sha256=sha(compressed),contentSha256=sha(payload)))
    counted={'MUNI_1':'declaraciones','MUNI_2':'titulares','MUNI_3':'municipios','MUNI_4':'habitantes',
             'MUNI_31':'hijos declarados','MUNI_32':'declaraciones con hijos'}
    units={}
    for c,label in zip(columns,labels):
        units[label]=counted.get(c) or ('recuento publicado' if re.search(r':\s*número\b|^número\b',desc[c],re.I)
                                      else 'euros')
    title='Anuario municipal del IRPF · AEAT'
    original=source.read_bytes()
    legend=guide.read_bytes()
    table=dict(id=920001,title=title,label=title,family='Renta declarada · AEAT',publisher='AEAT',
        dataFolder='renta/aeat',sourceId='F042',unit='Según variable',sourceUrl=CATALOG,downloadUrl=DOWNLOAD,
        license='Agencia Tributaria · condiciones generales de reutilización',rows=sum(s['rows'] for s in shards),
        dimensions=[dict(name='Variable',values=labels),dict(name='Tramo de población',values=list(BANDS.values()))],
        unitsByCategory=dict(dimension='Variable',values=units),
        note='Territorio fiscal común. Importe y recuentos conservan los conceptos del anuario. Las agrupaciones y códigos sin equivalencia oficial se consultan como series sin sombreado.',
        periods=periods,territories=territories,shards=shards,missingTokens=dict(missing),
        sourceTables=[dict(id=int(p['id']),year=int(p['id']),url=DOWNLOAD,sha256=sha(original),bytes=len(original),
                           periods=[p['id']]) for p in periods],
        dictionary=dict(url=DICTIONARY,sha256=sha(legend),bytes=len(legend),unresolvedCodes=sorted(unknown | ambiguous)))
    (OUT/'index.json').write_bytes(encode(dict(tables=[table])))
    print(f'AEAT: {table["rows"]:,} cells, {len(periods)} years, {len(territories)} areas, unknown {sorted(unknown)}',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
