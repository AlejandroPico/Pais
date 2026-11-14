"""Preserve the municipal monthly SEPE CSV series and their published suppressions."""
import csv
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/f04'
OUTPUT = ROOT / 'public/data/labor'
DOWNLOAD = 'https://sede.sepe.gob.es/es/portaltrabaja/resources/sede/datos_abiertos/datos/'
PRODUCTS = [
    (900001, 'Paro', 'Paro registrado', 'paro-registrado-por-municipio', 'personas',
     'Paro registrado en el municipio de domicilio de la persona demandante.'),
    (900002, 'Contratos', 'Contratos registrados', 'contratos-registrados-por-municipio', 'contratos',
     'Contratos registrados, asignados al municipio del centro de trabajo.'),
    (900003, 'Dtes_empleo', 'Demandantes de empleo', 'demandantes-de-empleo-por-municipio', 'personas',
     'Demandantes de empleo inscritos en el municipio de domicilio. Incluye situaciones distintas del paro registrado.'),
]
YEARS = range(2006, 2027)
DECEMBER_2020 = ('https://www.sepe.es/HomeSepe/dam/'
                 'jcr%3A1aaf1791-53e2-4c1e-8a6f-42aefeec1c42/ESTADISTICA_MUNICIPIOS.xls')

def open_workbook(url, path, refresh):
    library = str(CACHE / 'python')
    if Path(library).is_dir() and library not in sys.path:
        sys.path.insert(0, library)
    import xlrd

    if refresh or not path.exists():
        with urlopen(url, timeout=45) as response:
            raw = response.read()
        if not raw.startswith(b'\xd0\xcf'):
            raise ValueError(f'Invalid workbook: {url}')
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(raw)
        temporary.replace(path)
    raw = path.read_bytes()
    return raw, xlrd.open_workbook(file_contents=raw, on_demand=True)


def cell_text(value):
    return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)


def workbook_rows(kind, year, half, refresh):
    url = f'{DOWNLOAD}{kind}_por_municipios_{half}_semestre_{year}_xls.xls'
    raw, book = open_workbook(url, CACHE / f'sepe-{kind}-{year}-{half}.xls', refresh)
    sheet = book.sheet_by_index(0)
    rows = [[cell_text(value) for value in sheet.row_values(i)] for i in range(2, sheet.nrows)]
    book.release_resources()
    return url, raw, rows


def december_rows(kind, original, width):
    # The monthly workbook supplies official municipal codes in its first column.
    # It was published as a separate edition from the national open-data CSV.
    raw, book = open_workbook(DECEMBER_2020, CACHE / 'sepe-202012.xls', False)
    reference = {row[6].strip().zfill(5): row[2:8] for row in original if row and row[0] == '202011'}
    rows = {}
    prefix = 'PARO ' if kind == 'Paro' else 'CONTR'
    sheets = [name for name in book.sheet_names() if name.startswith(prefix)]
    assert len(sheets) == 52
    for name in sheets:
        sheet = book.sheet_by_name(name)
        assert 'DICIEMBRE 2020' in sheet.row_values(3) and sheet.ncols == width + 2, name
        for i in range(8, sheet.nrows):
            code, _, *values = sheet.row_values(i)
            if not isinstance(code, float):
                assert not str(code).strip(), (name, code)
                continue
            assert code.is_integer()
            key = f'{int(code):05}'
            assert key not in rows, (name, key)
            rows[key] = ['202012', 'Diciembre de 2020', *reference[key], *map(cell_text, values)]
    book.release_resources()
    assert rows.keys() == reference.keys()
    return raw, list(rows.values())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()


def fetch(kind, year, refresh):
    url = f'{DOWNLOAD}{kind}_por_municipios_{year}_csv.csv'
    path = CACHE / f'sepe-{kind}-{year}.csv'
    if refresh or not path.exists():
        with urlopen(url, timeout=45) as response:
            data = response.read()
        if b'Codigo Municipio' not in data[:1000]:
            raise ValueError(f'Invalid CSV: {url}')
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(data)
        temporary.replace(path)
    return year, url, path


def build(spec, refresh=False):
    tid, kind, title, slug, unit, definition = spec
    areas, periods, known_areas, known_periods = [], [], {}, {}
    parts = {}
    edition_sources = []
    headers = []
    all_rows = set()
    missing = {}
    month_sets = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(lambda year: fetch(kind, year, refresh), YEARS))
    for year, url, path in files:
        raw = path.read_bytes()
        source_id = tid * 10000 + year
        annual_source = dict(id=source_id, url=url, year=year, sha256=digest(raw), bytes=len(raw))
        edition_sources.append(annual_source)
        reader = csv.reader(io.StringIO(raw.decode('cp1252')), delimiter=';')
        next(reader)
        header = [' '.join(value.split()) for value in next(reader)][8:]
        if not headers:
            headers = header
        assert header == headers, (kind, year, header)
        original=list(reader)
        month_sets[year] = {row[0].strip() for row in original if row and row[0].strip()}
        annual_months=set(month_sets[year])
        batches=[(source_id,original)]
        if year<max(YEARS) and len(annual_months)<12:
            for number,half in enumerate(('primer','segundo'),1):
                local_url, workbook, rows=workbook_rows(kind,year,half,refresh)
                additional=[row for row in rows if re.fullmatch(str(year)+r'(0[1-9]|1[0-2])',row[0]) and row[0] not in annual_months]
                if additional:
                    fallback_id=tid*10000+year+number*10000000
                    batches.append((fallback_id,additional))
                    edition_sources.append(dict(id=fallback_id,url=local_url,year=year,sha256=digest(workbook),
                       bytes=len(workbook),periods=sorted({row[0] for row in additional})))
        annual_source['periods'] = sorted(annual_months)
        covered_months = annual_months | {row[0] for _, rows in batches[1:] for row in rows}
        if year == 2020 and kind in {'Paro', 'Contratos'} and '202012' not in covered_months:
            workbook, rows = december_rows(kind, original, len(headers))
            monthly_id = source_id + 30000000
            batches.append((monthly_id, rows))
            edition_sources.append(dict(id=monthly_id, url=DECEMBER_2020, year=year,
                sha256=digest(workbook), bytes=len(workbook), periods=['202012']))
        for actual_source,row in ((source,row) for source,rows in batches for row in rows):
            if not row or not any(row):
                continue
            month, label, _, _, province, _, code, name, *values = [v.strip() for v in row]
            province, code = province.zfill(2), code.zfill(5)
            assert re.fullmatch(r'\d{5}',code) and code.startswith(province), (kind,year,code,province)
            assert len(values) == len(headers) and re.fullmatch(str(year)+r'(0[1-9]|1[0-2])',month)
            assert (code,month) not in all_rows, (kind,year,code,month)
            all_rows.add((code,month))
            month_sets[year].add(month)
            if code not in known_areas:
                known_areas[code] = len(areas)
                areas.append(dict(id='municipal:'+code,level='municipal',code=code,name=name,provinceCode=province))
            else:
                areas[known_areas[code]]['name'] = name
            if month not in known_periods:
                known_periods[month] = len(periods)
                periods.append(dict(id=month[:4]+'M'+month[4:],label=label))
            cells = []
            for value in values:
                if value.isdecimal():
                    cells.append(int(value))
                else:
                    assert value in {'<5',''}, (kind,year,value)
                    status = value or 'Sin dato'
                    cells.append(status)
                    missing[status] = missing.get(status,0)+1
            parts.setdefault(province, []).append([known_areas[code],known_periods[month],actual_source,*cells])
    shards = []
    for province, rows in sorted(parts.items()):
        filename = f'{tid}-{province}.json.gz'
        payload = json_bytes(dict(rows=rows))
        body = gzip.compress(payload, compresslevel=5, mtime=0)
        path = OUTPUT/filename
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(body)
        temporary.replace(path)
        shards.append(dict(id=province,file=filename,rows=len(rows)*len(headers),bytes=len(body),
                           sha256=digest(body),contentSha256=digest(payload)))
    url = 'https://datos.gob.es/es/catalogo/ea0041513-'+slug
    count = len(all_rows)*len(headers)
    print(f'{title}: {count:,} observations, {len(periods)} months, {len(areas)} codes',flush=True)
    for year, months in month_sets.items():
        if year != max(YEARS) and len(months) != 12:
            print(f'{title} {year}: published months {sorted(months)}',flush=True)
    return dict(id=tid,title=title,label=title+' · SEPE',family='Estadísticas municipales · SEPE',
                compactColumns=True,publisher='SEPE',sourceId='F055',unit=unit,note=definition+
                ' Las cifras «<5» se conservan como dato protegido. El visor usa el código municipal original para cada mes.',
                sourceUrl=url,downloadUrl=edition_sources[-1]['url'],license='CC BY 4.0 · SEPE',rows=count,rawRows=count,
                duplicateRows=0,dimensions=[dict(name='Desglose publicado',values=['Total',*headers[1:]])],periods=periods,
                territories=areas,shards=shards,sourceTables=edition_sources,missingTokens=missing)


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    args=parser.parse_args()
    CACHE.mkdir(parents=True,exist_ok=True)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    tables=[build(product,args.refresh) for product in PRODUCTS]
    target=OUTPUT/'sepe.json'
    temporary=target.with_suffix('.tmp')
    temporary.write_bytes(json_bytes(dict(tables=tables)))
    temporary.replace(target)
