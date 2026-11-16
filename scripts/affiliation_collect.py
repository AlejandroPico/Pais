"""Municipal affiliation at month end from the TGSS public historical workbooks."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import gzip
from html import unescape
from io import BytesIO
import re
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from sepe_collect import ROOT, digest, json_bytes

BASE = 'https://www.seg-social.es'
STATISTICS = '/wps/portal/wss/internet/EstadisticasPresupuestosEstudios/Estadisticas/'
HISTORY = STATISTICS + 'EST8/EST167/5b11b695-cf1c-4abe-8a12-ecd2d0d15271/2683/'
RECENT = STATISTICS + 'est8/est10/est305/c43ad8ea-fe79-4329-ac8e-e5758f3c4d7a/6609c55f-65e4-4e64-b1ab-8917fce27a84?changeLanguage=es'
PAGES = [HISTORY + suffix for suffix in ('2684', '3460', '0985c546-dd0e-491b-b5e3-4e5e621c69b8')] + [RECENT]
CACHE = ROOT / '.cache/f04/afiliacion'
OUTPUT = ROOT / 'datos/trabajo/seguridad-social'
MONTHS = 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split()
COLUMNS = ['Total', 'Régimen General', 'Agrario', 'Mar', 'Hogar', 'Autónomos', 'Carbón']
SHEET = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def fetch(url, path, refresh):
    if path.exists() and not refresh:
        return path.read_bytes()
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60) as response:
        raw = response.read()
    temporary = path.with_suffix('.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)
    return raw


def editions(refresh):
    urls = {}
    for index, page in enumerate(PAGES):
        raw = fetch(BASE + page, CACHE.parent / f'afiliacion-{index}.html', refresh)
        source = raw.decode('utf-8')
        for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', source, flags=re.S | re.I):
            label = ' '.join(unescape(re.sub(r'<[^>]+>', ' ', row)).split())
            link = re.search(r'href="(/descarga/es/[^"]+)"', row)
            month = re.search(r'(' + '|'.join(MONTHS) + r') (20\d{2,3})\b', label, re.I)
            if not link or not month:
                continue
            year = 2018 if month[2] == '20108' and link[1].endswith('/230527') else int(month[2])
            assert 2003 <= year < 2100, label
            period = f'{year}M{MONTHS.index(month[1].lower()) + 1:02}'
            assert period not in urls, period
            path = quote(unescape(link[1]), safe='/%')
            urls[period] = BASE + path + ('?revision=2' if period == '2009M12' else '')
    first, last = min(urls), max(urls)
    assert first == '2003M01'
    expected = {f'{year}M{month:02}' for year in range(2003, int(last[:4])+1)
                for month in range(1,13) if f'{year}M{month:02}' <= last}
    assert urls.keys() == expected, sorted(expected - urls.keys())
    return sorted(urls.items())


def workbook(raw, sheet_path='xl/worksheets/sheet1.xml'):
    with ZipFile(BytesIO(raw)) as archive:
        texts = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            texts = [''.join(t.text or '' for t in node.iter(SHEET + 't')) for node in strings]
        with archive.open(sheet_path) as sheet:
            for _, row in ET.iterparse(sheet, events=['end']):
                if row.tag != SHEET + 'row':
                    continue
                cells = {}
                for cell in row.findall(SHEET + 'c'):
                    value = cell.findtext(SHEET + 'v')
                    if cell.get('t') == 's':
                        value = texts[int(value)]
                    elif cell.get('t') == 'inlineStr':
                        value = ''.join(n.text or '' for n in cell.iter(SHEET + 't'))
                    cells[re.match(r'[A-Z]+', cell.get('r'))[0]] = (value or '').strip()
                yield cells
                row.clear()


def column_name(label):
    for pattern, name in zip(('total', 'general', 'agrario', r'\bmar\b', 'hogar', 'aut.nomos', 'carb.n'), COLUMNS):
        if re.search(pattern, label, flags=re.I):
            return name
    raise ValueError(label)


def read_period(item, refresh):
    period, url = item
    name = period + ('-alt1' if period == '2009M12' else '') + '.xlsx'
    raw = fetch(url, CACHE / name, refresh)
    rows = workbook(raw)
    date = next(rows)['A']
    assert f'{MONTHS[int(period[-2:]) - 1].upper()} DE {period[:4]}' in date, (period, date)
    heading = next(rows)
    assert heading['A'] == 'PROVINCIA' and heading['B'] == 'MUNICIPIO'
    fields = {column_name(label): key for key, label in heading.items() if key not in 'ABC' and label}
    assert set(fields) == set(COLUMNS), (period, fields)
    records = {}
    for row in rows:
        label = row.get('B', '')
        code = re.match(r'^(\d{5})(?:\s|$)', label)
        if not code:
            values = [row.get(fields[name], '') for name in COLUMNS]
            if row.get('C') != 'TRAB.' or not any(values):
                continue
            province_name = row.get('A', '')
            province = re.match(r'^(\d{2})(?:\s|$)', province_name)
            if province and label == 'PROVINCIAL':
                key = 'province:' + province[1]
                area = dict(id=key, level='province', code=province[1], name=province_name)
            elif province_name == 'NACIONAL' and not label:
                key = 'national:ES'
                area = dict(id=key, level='national', code='ES', name='España')
            else:
                published_label = 'Sin distribución municipal' if re.match(r'^(SIN DISTRIBUCI|NO DISTRIBUID)', label) else label
                code = (province[1] if province else province_name) + ':' + published_label
                key = 'unlocated:' + code
                area = dict(id=key, level='unlocated', code=code, name=f'{province_name} · {published_label}')
        else:
            code = code[1]
            key = 'municipal:' + code
            area = dict(id=key,level='municipal',code=code,name=label[5:].strip() or label,provinceCode=code[:2])
        if key in records:
            original = key
            ordinal = 2
            while key in records:
                key = f'unlocated:{original}:{ordinal}'
                ordinal += 1
            area = dict(id=key, level='unlocated', code=key.removeprefix('unlocated:'),
                        name=f'{area["name"]} · fila adicional publicada')
        assert key not in records, (period, key)
        values = [row.get(fields[name], '') for name in COLUMNS]
        records[key] = (area, [int(v) if v.isdecimal() else v or 'Sin dato' for v in values])
    assert sum(k.startswith('municipal:') for k in records) > 7900, period
    source = dict(id=int(period.replace('M', '')),url=url,year=int(period[:4]),sha256=digest(raw),bytes=len(raw),periods=[period.replace('M','')])
    return source, records


def main(refresh):
    CACHE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    areas, area_indices, periods, sources, parts = [], {}, [], [], defaultdict(list)
    missing = Counter()
    catalog = editions(refresh)
    # Consume bounded batches, since parsed workbooks are larger than the XLSX files.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for start in range(0, len(catalog), 4):
            batch = catalog[start:start+4]
            for (period, _), (source, records) in zip(batch, pool.map(lambda item:read_period(item, refresh), batch), strict=True):
                sources.append(source)
                month = MONTHS[int(period[-2:])-1].capitalize()
                period_index = len(periods)
                periods.append(dict(id=period,label=f'{month} de {period[:4]}'))
                for key, (area, values) in records.items():
                    if key not in area_indices:
                        area_indices[key] = len(areas)
                        areas.append(area)
                    else:
                        areas[area_indices[key]] = area
                    missing.update(v for v in values if isinstance(v,str))
                    parts[area.get('provinceCode') or 'main'].append([area_indices[key],period_index,source['id'],*values])
            if start % 40 == 0:
                print(f'TGSS: {len(periods)} / {len(catalog)} months',flush=True)
    shards = []
    for part, rows in sorted(parts.items()):
        filename = f'910001-{part}.json.gz'
        payload = json_bytes(dict(rows=rows))
        compressed = gzip.compress(payload,compresslevel=5,mtime=0)
        (OUTPUT/filename).write_bytes(compressed)
        shards.append(dict(id=part,file=filename,rows=len(rows)*len(COLUMNS),bytes=len(compressed),
                           sha256=digest(compressed),contentSha256=digest(payload)))
    title = 'Afiliación municipal por régimen a fin de mes'
    table = dict(id=910001,title=title,label=title+' · TGSS',family='Afiliación · Seguridad Social',
                 compactColumns=True,publisher='TGSS',dataFolder='trabajo/seguridad-social',sourceId='F056',
                 unit='afiliaciones',note='Último día del mes. Conserva las cifras protegidas y los límites que publica la TGSS. Las columnas Agrario y Hogar siguen la clasificación de cada edición.',
                 sourceUrl=BASE+RECENT,downloadUrl=sources[-1]['url'],license='Reutilización de la información de la Seguridad Social · aviso legal del portal',
                 rows=sum(part['rows'] for part in shards),dimensions=[dict(name='Régimen publicado',values=COLUMNS)],
                 periods=periods,territories=areas,shards=shards,sourceTables=sources,missingTokens=dict(missing))
    (OUTPUT/'index.json').write_bytes(json_bytes(dict(tables=[table])))
    print(f'TGSS: {table["rows"]:,} cells, {len(periods)} months and {len(areas)} areas',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    main(parser.parse_args().refresh)
