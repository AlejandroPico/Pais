"""Capture the INSS monthly IMV workbooks and the official July 2024 PDF."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
from html import unescape
from io import BytesIO
import re
from datetime import datetime, timezone

from affiliation_collect import fetch, workbook
from pnc_collect import CACHE, COMMUNITIES, MONTHS, NATIONAL, PROVINCES, SINGLE_PROVINCE, core

BASE = 'https://www.seg-social.es'
ROOT = BASE + '/wps/portal/wss/internet/EstadisticasPresupuestosEstudios/Estadisticas/cbe2fda1-3ac7-4bc8-a5ec-06c178839e11/d1fee385-f3ad-4e58-a129-d8818d93ea4b/'
PAGES = ('ae6d943c-a7eb-4112-aa8e-002f268f5d73', '531c050e-e879-4de4-bff7-099af492edd7', 'ef51a713-7a93-4a5e-a6bb-9e5adf310de6')
OUT = core.ROOT / 'datos/cuidados/seguridad-social'
TABLE = 931001
COLUMNS = [*'CDEFGHIJKLMNOPQRSTUVWXYZ', 'AA', 'AB', 'AC']
COMMUNITY_LABELS = {'asturias (principado de)':'asturias', 'balears (illes)':'illes balears',
    'castilla - la mancha':'castilla-la mancha', 'cataluna':'catalunya', 'comunitat valenciana':'comunidad valenciana',
    'madrid (comunidad de)':'madrid', 'murcia (region de)':'murcia', 'navarra (comunidad foral de)':'navarra', 'rioja (la)':'la rioja'}
PROVINCE_CODES = {**PROVINCES, 'palmas (las)':'35', 's.c.tenerife':'38', 'coruna (a)':'15'}
TITLE = 'Ingreso Mínimo Vital · Nómina por comunidad y provincia'


def source_urls(refresh):
    urls = {}
    for page in PAGES:
        html = fetch(ROOT + page + '?changeLanguage=es', CACHE / f'imv-{page}.html', refresh).decode()
        for link, month, extension in re.findall(r'href="(/wps/wcm/connect/wss/[^"/]+/(20\d{4})_IMV[^"]+\.(xlsx|pdf)\?[^"]+)"', html, re.I):
            if extension == 'xlsx' or month == '202407':
                urls.setdefault(month, (extension, BASE + unescape(link)))
    last = max(urls)
    expected = {f'{year}{month:02}' for year in range(2024, int(last[:4])+1)
                for month in range(1, 13) if f'{year}{month:02}' <= last}
    assert last >= '202610' and urls.keys() == expected, sorted(expected - urls.keys())
    return sorted(urls.items())


def territory(a, b, community):
    if not b:
        assert a == 'TOTAL', a
        return NATIONAL
    if b == 'Total':
        key = re.sub(r' \(\d+\)', '', core.norm(a))
        code = COMMUNITIES[COMMUNITY_LABELS.get(key, key)]
        return 'community', code, re.sub(r' \(\d+\)', '', a).capitalize()
    key = core.norm(b)
    code = SINGLE_PROVINCE.get(community) or PROVINCE_CODES.get(key) or core.GEO_NAMES.get(('province', key))
    assert code, b
    return 'province', code, b


def indicators(head, sub):
    simple = {'C':('Número de prestaciones', 'prestaciones'),
        'U':('Prestaciones con API' if 'Prestaciones' in head['U'] else 'Hogares con CAPI', 'prestaciones' if 'Prestaciones' in head['U'] else 'hogares'),
        'V':('Número de beneficiarios', 'personas'),
        'AA':('Importe bruto mensual de la nómina', '€'),
        'AB':('Cuantía media mensual por hogar', '€/hogar'),
        'AC':('Importe bruto acumulado desde junio de 2020', '€')}
    groups = [('DE','Titulares · ', 'personas'), ('FGHIJKLMNOPQRST','Tipo de hogar · ', 'hogares'),
              ('WXYZ','Beneficiarios · ', 'personas')]
    for columns, prefix, unit in groups:
        for key in columns:
            simple[key] = prefix + ' '.join(sub[key].split()), unit
    assert set(simple) == set(COLUMNS)
    return simple


def excel_records(raw, month):
    rows = list(workbook(raw))
    assert MONTHS[int(month[-2:])-1] + ' ' + month[:4] in core.norm(rows[0]['A']), month
    assert rows[2]['A'] == 'COMUNIDADES AUTÓNOMAS' and rows[2]['B'] == 'PROVINCIAS', month
    data = [r for r in rows[4:] if r.get('C')]
    notes = [r['A'] for r in rows[4:] if re.match(r'^\(\d+\)', r.get('A',''))]
    return data, indicators(rows[2], rows[3]), notes


def pdf_records(raw, template):
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(raw))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text(extraction_mode='layout')
    assert 'julio 2024' in text
    data = []
    for line in text.splitlines():
        label = line[32:53].strip()
        if line[:53].strip() == 'TOTAL':
            label = ''
        values = re.findall(r'\S+(?: €)?', line[53:])
        if len(values) != len(COLUMNS):
            continue
        previous = template[len(data)]
        assert core.norm(label) == core.norm(previous.get('B','')), (label, previous.get('B'))
        assert all(core.number(value.removesuffix(' €')) is not None for value in values), label
        data.append(dict(A=previous.get('A',''), B=label, **{
            key: value.removesuffix(' €').replace('.', '').replace(',', '.')
            for key, value in zip(COLUMNS, values, strict=True)}))
    assert len(data) == len(template), len(data)
    return data, [line.strip() for line in text.splitlines() if re.match(r'^\s*\(\d+\) [A-Z]', line)]


def main(refresh=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    urls = source_urls(refresh)

    def download(item):
        month,(ext,url) = item
        path = CACHE / f'imv-{month}.{ext}'
        raw = fetch(url, path, refresh)
        return month,(ext,url,path,raw)

    with ThreadPoolExecutor(max_workers=5) as pool:
        editions = dict(pool.map(download, urls))
    template, template_columns, _ = excel_records(editions['202406'][3], '202406')
    areas, periods, metrics, rows, sources, missing = {}, [], {}, [], [], {}
    for month, (ext,url,path,raw) in editions.items():
        if ext == 'pdf':
            records, notes = pdf_records(raw, template)
            fields = template_columns
        else:
            records, fields, notes = excel_records(raw, month)
        assert len(records) == 72 and len(notes) >= 7, (month, len(records), len(notes))
        period = month[:4] + 'M' + month[-2:]
        periods.append(dict(id=period,label=period))
        source_id = int(month)
        coverage = set()
        community = ''
        for record in records:
            level, code, area_name = territory(record.get('A',''), record.get('B',''), community)
            if level == 'community':
                community = code
            key = f'{level}:{code}'
            assert key not in coverage, (month, key)
            coverage.add(key)
            area = areas.setdefault(key, dict(id=key,level=level,code=code,name=area_name,index=len(areas),sourceTableIds=[]))
            area['sourceTableIds'].append(source_id)
            for column in COLUMNS:
                label, unit = fields[column]
                index, _ = metrics.setdefault(label, (len(metrics), unit))
                token = record.get(column,'')
                if re.fullmatch(r'-?\d+(?:\.\d+)?',token):
                    value = int(token) if '.' not in token else float(token)
                    status = ''
                else:
                    value = None
                    status = token or 'celda vacía'
                    missing[status] = missing.get(status,0) + 1
                rows.append([area['index'],len(periods)-1,index,value,status,source_id])
        assert coverage == areas.keys(), (month, sorted(areas.keys() - coverage))
        sources.append(dict(id=source_id,year=int(month[:4]),edition=period,periods=[period],
            url=url,sha256=core.sha(raw),bytes=len(raw),originalFile=f'originales/imv-{month}.{ext}',notes=notes,
            retrievedAt=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()))
    for area in areas.values():
        del area['index']
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'originales').mkdir(exist_ok=True)
    for source in sources:
        (OUT/source['originalFile']).write_bytes(editions[str(source['id'])][3])
    payload = core.encode(dict(rows=rows))
    compressed = gzip.compress(payload, compresslevel=6, mtime=0)
    filename = f'{TABLE:06}.json.gz'
    (OUT/filename).write_bytes(compressed)
    table = dict(id=TABLE,publisher='INSS',sourceId='F056',label=TITLE,title=TITLE,
        dataFolder='cuidados/seguridad-social',family='Ingreso Mínimo Vital',unit='Según el indicador',
        sourceUrl=ROOT+PAGES[-1],downloadUrl=sources[-1]['url'],license='Reutilización de la información de la Seguridad Social · aviso legal del portal',
        licenseUrl=BASE+'/wps/portal/wss/internet/AvisoLegal',
        note='Datos de nómina. El número de prestaciones equivale al de titulares. Los importes brutos incluyen atrasos; la cuantía media mensual por hogar los excluye. Cada edición incluye sus notas de cobertura, incluida la gestión de Cataluña en octubre de 2026.',
        rows=len(rows),dimensions=[dict(name='Indicador',values=list(metrics))],
        unitsByCategory=dict(dimension='Indicador',values={label:unit for label,(_,unit) in metrics.items()}),
        missingTokens=missing,territories=list(areas.values()),periods=periods,sourceTables=sources,
        shards=[dict(id='all',file=filename,rows=len(rows),bytes=len(compressed),sha256=core.sha(compressed),contentSha256=core.sha(payload))])
    (OUT/'index.json').write_bytes(core.encode(dict(schemaVersion=1,edition=periods[-1]['id'],tables=[table])))
    print(f'INSS: {len(sources)} IMV editions; {len(rows)} observations')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
