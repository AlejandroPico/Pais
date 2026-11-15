"""Import the five IMSERSO PNC CSV annexes and preserve the source editions."""
import argparse
import csv
import gzip
import io
import re
import urllib.request
from datetime import datetime, timezone

import demography_collect as core

OUT = core.ROOT / 'datos/cuidados/imserso'
CACHE = core.ROOT / '.cache/f05'
PORTAL = 'https://imserso.es/el-imserso/documentacion/estadisticas/pensiones-no-contributivas-jubilacion-incapacidad-pnc'
TERMS = 'https://imserso.es/aviso-legal'
BASE = 'https://teleformacion.imserso.es/documents/20123/121856/'
ANNEXES = {
    'evolpncs': ('f652fed7-6c35-409b-5105-3e38759ce720', 'Evolución de las nóminas'),
    'provpncs': ('1c09a6ca-14ed-2065-21ab-591ad6cd716d', 'Nómina por provincia y comunidad'),
    'disterpncs': ('13fdb22c-69a9-3a7c-1a70-359c1580671b', 'Distribución territorial de las pensiones'),
    'disimppncs': ('7aeaa10d-ad84-f299-ab07-8e746c9f75c1', 'Distribución territorial del importe acumulado'),
    'evolimppncs': ('ac7f93bd-99bc-3927-f7fe-fc5c6fd9ec8b', 'Evolución y referencias de los importes medios'),
}
MONTHS = 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split()
PENSIONS = ('Jubilación', 'Incapacidad', 'Total')
COMMUNITIES = dict(zip(
    ('andalucia', 'aragon', 'asturias', 'illes balears', 'canarias', 'cantabria',
     'castilla y leon', 'castilla-la mancha', 'catalunya', 'comunidad valenciana',
     'extremadura', 'galicia', 'madrid', 'murcia', 'navarra', 'pais vasco', 'la rioja', 'ceuta', 'melilla'),
    [f'{n:02}' for n in range(1, 20)], strict=True))
COMMUNITIES['c. valenciana'] = '10'
SINGLE_PROVINCE = {'03':'33','04':'07','06':'39','13':'28','14':'30','15':'31','17':'26','18':'51','19':'52'}
PROVINCES = {'s.c. tenerife':'38','araba/alava':'01','gipuzkoa':'20','bizkaia':'48',
             'alicante':'03','castellon':'12','valencia':'46'}
NATIONAL = ('national', 'ES', 'España')


def territories(label, provincial):
    key = re.sub(r'\s+', ' ', re.sub(r'\(\*\)|\*', '', core.norm(label))).strip()
    if key == 'total estado':
        return [NATIONAL]
    if key in COMMUNITIES:
        code = COMMUNITIES[key]
        result = [('community', code, label)]
        if provincial and code in SINGLE_PROVINCE:
            result.append(('province', SINGLE_PROVINCE[code], label))
        return result
    code = PROVINCES.get(key) or core.GEO_NAMES.get(('province', key))
    assert provincial and code, label
    return [('province', code, label)]


def field(kind, metric, unit):
    return f'{kind} · {metric}', unit


def captures(rows, key, edition):
    year = edition[:4]
    if key == 'evolpncs':
        columns = [(i, field(kind, metric, unit))
                   for start, metric, unit in [(3, 'Importe bruto', '€'), (7, 'Número de pensiones', 'pensiones')]
                   for i, kind in enumerate(PENSIONS, start)]
        for row in rows:
            label = core.norm(row[1]).rstrip('*')
            annual = re.fullmatch(r'(?:total )?ano (\d{4})(?: \(1\))?', label)
            if annual:
                period = annual[1]
                year = period
                period_label = period if not label.startswith('total') else f'{period} · acumulado hasta {MONTHS[int(edition[-2:])-1]}'
            elif label in MONTHS:
                period = f'{year}M{MONTHS.index(label)+1:02}'
                period_label = period
            else:
                continue
            for i, metric in columns:
                if row[i].strip():
                    yield NATIONAL, (period, period_label), metric, row[i]
        return
    if key == 'evolimppncs':
        annual_metrics = { 'importe medio': ('Importe medio (resumen anual publicado)', '€'),
            'establecido': ('Importe mensual establecido', '€'),
            'con comp. 50% t. p. (1)': ('Importe con complemento del 50 % por tercera persona', '€'),
            'minimo 25%': ('Importe mínimo del 25 %', '€'),
            'd interanual': ('Variación interanual publicada', '%')}
        for i, value in enumerate(rows[4]):
            if not re.fullmatch(r'\d{4}', value.strip()):
                continue
            kind = 'Jubilación' if i < 12 else 'Incapacidad'
            for row in rows[6:27]:
                label = core.norm(row[1]).rstrip('*')
                if label in MONTHS:
                    period = f'{value.strip()}M{MONTHS.index(label)+1:02}'
                    metric = 'Importe medio mensual', '€'
                elif label in annual_metrics:
                    period, metric = value.strip(), annual_metrics[label]
                else:
                    continue
                if row[i].strip():
                    period_label = f'{period} · edición {edition}' if period == year else period
                    yield NATIONAL, (period, period_label), field(kind, *metric), row[i]
        return
    columns = {
        'provpncs': [(i, field(kind, metric, unit))
                     for start, kind in zip((3,7,11), PENSIONS, strict=True)
                     for i, (metric, unit) in enumerate((('Número de pensiones','pensiones'),
                         ('Importe bruto','€'), ('Promedio mensual','€/pensión')), start)],
        'disterpncs': [(i, field(kind, metric, unit))
                       for start, kind in zip((3,5,7), PENSIONS, strict=True)
                       for i, (metric, unit) in enumerate((('Número de pensiones','pensiones'),
                           ('Porcentaje del total estatal del mismo tipo','%')), start)],
        'disimppncs': [(i, field(kind, 'Importe bruto acumulado', '€')) for i, kind in enumerate(PENSIONS, 3)]
                      + [(6, field('Total', 'Porcentaje del importe estatal acumulado', '%'))],
    }[key]
    label = f'{year} · enero a {MONTHS[int(edition[-2:])-1]}' if key == 'disimppncs' else edition
    for row in rows:
        name = row[1].strip()
        if not name:
            continue
        if key == 'provpncs' and core.norm(name).startswith(('deducciones en nomina', 'importe neto de la nomina')):
            yield NATIONAL, (edition, label), field('Total', name.split(' (')[0].rstrip(':').capitalize(), '€'), row[5]
        elif core.number(row[3]) is not None or core.number(row[5]) is not None:
            for area in territories(name, key == 'provpncs'):
                for i, metric in columns:
                    yield area, (edition, label), metric, row[i]


def read_annex(key, refresh):
    url = BASE + key + '.csv/' + ANNEXES[key][0]
    path = CACHE / (key + '.csv')
    if refresh or not path.exists():
        with urllib.request.urlopen(url, timeout=90) as response:
            payload = response.read()
        assert not payload.lstrip().startswith(b'<'), url
        path.write_bytes(payload)
    payload = path.read_bytes()
    text = payload.decode('cp1252')
    rows = [row + [''] * max(0, 20-len(row)) for row in csv.reader(io.StringIO(text), delimiter=';')]
    return rows, payload, dict(url=url, sha256=core.sha(payload), bytes=len(payload),
                               retrievedAt=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat())


def main(refresh=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    annexes = {key: read_annex(key, refresh) for key in ANNEXES}
    prov = annexes['provpncs'][0]
    year = re.search(r'\d{4}', prov[3][1])[0]
    month = core.norm(prov[3][9])
    edition = f'{year}M{MONTHS.index(month)+1:02}'
    for key in ('disterpncs', 'disimppncs'):
        title = core.norm(annexes[key][0][2][1])
        assert year in title and month in title, (key, title, edition)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'originales').mkdir(exist_ok=True)
    tables = []
    for tid, (key, (source_rows, payload, source)) in enumerate(annexes.items(), 930001):
        label = 'PNC · ' + ANNEXES[key][1]
        observations = list(captures(source_rows, key, edition))
        assert observations, key
        areas = list(dict.fromkeys(area for area, *_ in observations))
        assert len({(level, code) for level, code, _ in areas}) == len(areas), key
        periods = sorted(set(period for _, period, *_ in observations))
        metrics = sorted({metric for _, _, metric, _ in observations},
                         key=lambda metric:(metric[0] != 'Total · Número de pensiones', metric[0]))
        references = [{value:i for i, value in enumerate(items)} for items in (areas, periods, metrics)]
        rows, keys, missing = [], set(), {}
        for area, period, metric, raw in observations:
            position = tuple(index[value] for index, value in zip(references, (area, period, metric), strict=True))
            assert position not in keys, (key, area, period, metric)
            keys.add(position)
            token = raw.strip()
            value = core.number(token.rstrip('%'))
            status = '' if value is not None else token or 'celda vacía'
            if status:
                missing[status] = missing.get(status, 0) + 1
            rows.append([*position, value, status, tid])
        document = core.encode({'rows':rows})
        compressed = gzip.compress(document, compresslevel=6, mtime=0)
        filename = f'{tid:06}.json.gz'
        (OUT/filename).write_bytes(compressed)
        original = f'originales/{edition}-{key}.csv'
        (OUT/original).write_bytes(payload)
        footnotes = [row[1].strip() for row in source_rows if row[1].strip().startswith(('*','(1)','FUENTES:'))]
        notes = (f'Origen de los datos: Imserso. Edición {edition}. '
                 + ('Los ámbitos uniprovinciales figuran en los dos niveles de consulta cuando la fuente agrupa ambos. ' if key=='provpncs' else '')
                 + ('El total anual en curso es acumulado; las pensiones anuales y mensuales son recuentos publicados. ' if key=='evolpncs' else '')
                 + ' '.join(footnotes))
        tables.append(dict(id=tid, publisher='IMSERSO', sourceId='F059', label=label, title=label,
            dataFolder='cuidados/imserso', family='Pensiones no contributivas', unit='Según el indicador',
            sourceUrl=PORTAL, downloadUrl=source['url'], license='Condiciones de reutilización del Imserso',
            licenseUrl=TERMS, note=notes.strip(), rows=len(rows), dimensions=[{'name':'Indicador','values':[m[0] for m in metrics]}],
            unitsByCategory={'dimension':'Indicador','values':dict(metrics)}, missingTokens=missing,
            periods=[dict(id=id,label=period_label) for id, period_label in periods],
            territories=[dict(id=f'{level}:{code}', level=level, code=code, name=name, sourceTableIds=[tid]) for level, code, name in areas],
            sourceTables=[dict(id=tid,year=int(year),edition=edition,originalFile=original,**source)],
            shards=[dict(id='main',file=filename,rows=len(rows),bytes=len(compressed),sha256=core.sha(compressed),contentSha256=core.sha(document))]))
    (OUT/'index.json').write_bytes(core.encode({'schemaVersion':1, 'edition':edition, 'tables':tables}))
    print(f'IMSERSO: {len(tables)} annexes; {sum(table["rows"] for table in tables)} observations; edition {edition}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    main(parser.parse_args().refresh)
