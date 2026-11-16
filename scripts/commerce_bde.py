"""Convert the Boletín Estadístico distributions to territorial and series cubes."""
import argparse
from collections import Counter
import csv
import gzip
import io
import json
import math
import re
from zipfile import ZipFile

from affiliation_collect import fetch
from demography_collect import GEO_NAMES, ROOT, encode, norm, sha

OUTPUT = ROOT / 'datos/comercio/bde'
BASE = 'https://www.bde.es/webbe/es/estadisticas/'
BULLETIN = BASE + 'otras-clasificaciones/publicaciones/boletin-estadistico/capitulo-{}.html'
TERMS = 'https://www.bde.es/wbe/es/estadisticas/recursos/terminos/terminos-de-uso.html'
CHAPTERS = {
    4: 'Crédito, depósitos y entidades financieras',
    5: 'Instituciones financieras',
    9: 'Instituciones financieras no monetarias',
    10: 'Seguros y fondos de pensiones',
    18: 'Comercio exterior de bienes · Aduanas',
    19: 'Tipos de interés',
    20: 'Tipos de cambio y competitividad',
    21: 'Mercado primario de valores',
    22: 'Mercados secundarios de valores',
}
TITLES = {
    '0428': 'Crédito y depósitos por provincias',
    '0429': 'Crédito y depósitos por comunidades autónomas',
    '0430': 'Detalle del crédito por comunidades autónomas',
    '0431': 'Detalle de los depósitos por comunidades autónomas',
    '0447': 'Oficinas operativas y de representación',
}
MONTHS = {month: i for i, month in enumerate('ENE FEB MAR ABR MAY JUN JUL AGO SEP OCT NOV DIC'.split(), 1)}
NATIONAL = dict(id='national:ES', level='national', code='ES', name='España')
PUBLIC_SOURCES = (
    'banco de espana', 'banco de datos de la oficina de instituciones financieras', 'balance de instituciones financieras',
    'direccion general de aduanas', 'ministerio de economia', 'comision nacional del mercado de valores',
    'direccion general de seguros', 'banco central europeo', 'cuentas financieras de la economia espanola',
    'segun la cnae', 'ministerio de hacienda',
)
FIELD_KEYS = ('CÓDIGO DE LA SERIE', 'NOMBRE DE LA SERIE', 'NÚMERO SECUENCIAL', 'ALIAS DE LA SERIE',
              'DESCRIPCIÓN DE LA SERIE', 'DESCRIPCIÓN DE LAS UNIDADES', 'FRECUENCIA', 'FUENTE', 'NOTAS')
GEO = {**GEO_NAMES}
GEO.update({('province', name): code for name, code in {
    'principado de asturias':'33', 'comunidad foral de navarra':'31', 'la coruna':'15', 'la rioja':'26',
    'islas baleares':'07', 'illes balears':'07', 'las palmas':'35', 'vizcaya':'48', 'guipuzcoa':'20',
    'orense':'32', 'ceuta':'51', 'melilla':'52', 'alicante':'03', 'castellon':'12', 'castello':'12',
    'valencia':'46', 'guipuzkoa':'20', 'comunidad de madrid':'28', 'region de murcia':'30',
    'tenerife':'38', 'sta. cruz de tenerife':'38',
}.items()})
GEO.update({('community', name): code for name, code in {
    'comunidad de madrid':'13', 'principado de asturias':'03', 'illes balears':'04', 'islas baleares':'04',
    'comunidad foral de navarra':'15', 'region de murcia':'14', 'castilla-la mancha':'08', 'la rioja':'17',
    'comunidad valenciana':'10', 'ceuta':'18', 'melilla':'19', 'castilla-leon':'07',
    'comunidad foral de navarra, comunidad foral de':'15',
}.items()})


def clean(value):
    if 'Ã' in value or 'Â' in value or 'â€' in value:
        try:
            return value.encode('cp1252').decode('utf-8')
        except UnicodeError:
            pass
    return value


def period(label, frequency):
    if re.fullmatch(r'\d{4}', label):
        return label
    if match := re.fullmatch(r'([A-Z]{3}) (\d{4})', label):
        month, year = match.groups()
        number = MONTHS[month]
        if frequency == 'TRIMESTRAL' and number % 3 == 0:
            return f'{year}T{number // 3}'
        return year if frequency == 'ANUAL' and number == 12 else f'{year}M{number:02}'
    return None


def geography(key, description, chapter):
    level = 'province' if key.startswith('0428') else 'community' if key in {'0429','0430','0431'} else None
    if level:
        parts = description.split('. ')
        for i in range(len(parts)-1, -1, -1):
            place = parts[i].removesuffix(' [discontinuada]')
            name = norm(place)
            if name == 'total nacional':
                return NATIONAL, '. '.join(parts[:i]+parts[i+1:])
            if code := GEO.get((level, name)):
                return dict(id=f'{level}:{code}', level=level, code=code, name=place), '. '.join(parts[:i]+parts[i+1:])
            if name.startswith(('sin clasificar','banca electronica','total ccaa')):
                return dict(id='unlocated:'+name, level='unlocated', code=name, name=place), '. '.join(parts[:i]+parts[i+1:])
        if key in {'0430','0431'} and any('porcentaje sobre' in norm(p) for p in parts):
            return NATIONAL, description
        return dict(id='unlocated:otros', level='unlocated', code='otros', name='Otros ámbitos publicados'), description
    if chapter in {19,20,22}:
        return dict(id='unlocated:serie', level='unlocated', code='serie', name='Ámbito de la serie publicada'), description
    return NATIONAL, description


def series_dates(body):
    metadata, rows = {}, []
    for row in csv.reader(io.StringIO(body.decode('cp1252'))):
        if not row:
            continue
        label, *values = row
        if label in FIELD_KEYS or not label:
            metadata[label] = [clean(x).strip() for x in values]
        elif re.fullmatch(r'(?:[A-Z]{3} )?\d{4}', label):
            rows.append((label, values))
        else:
            raise ValueError(f'Unexpected row: {label!r}')
    width = len(metadata['DESCRIPCIÓN DE LA SERIE'])
    assert rows and all(len(r) == width for _, r in rows)
    return metadata, rows


def capture(chapter, file, body, archive):
    key = file[2:-4]
    identifier = 9_000_000 + chapter * 36**5 + int('1'+key[2:],36)
    metadata, cells = series_dates(body)
    field = lambda key, i, default='': metadata.get(key, [])[i] if i < len(metadata.get(key, [])) else default
    descriptions = metadata['DESCRIPCIÓN DE LA SERIE']
    territories, measures, periods = {}, {}, {}
    units, metadata_by_series, observations, missing = {}, {}, [], Counter()
    omitted = []
    used_keys = set()
    for i, description in enumerate(descriptions):
        code = field('CÓDIGO DE LA SERIE', i) or field('NOMBRE DE LA SERIE', i) or field('', i) or field('NÚMERO SECUENCIAL', i)
        source = field('FUENTE', i)
        if source not in {'','_'} and not norm(source).startswith(PUBLIC_SOURCES):
            omitted.append(dict(code=code, source=source))
            continue
        area, measure = geography(key, description, chapter)
        area_index = territories.setdefault(area['id'], (len(territories), area))[0]
        unit = field('DESCRIPCIÓN DE LAS UNIDADES', i) or 'Según la publicación'
        # Names from territorial tables are compared across territories. Keep
        # a separate key for any genuinely distinct series at the same place.
        if (area_index, measure) in used_keys or measure in units and units[measure] != unit:
            measure = f'{measure} · {code}'
        used_keys.add((area_index, measure))
        measure_index = measures.setdefault(measure, len(measures))
        units[measure] = unit
        frequency = field('FRECUENCIA', i)
        metadata_by_series.setdefault(measure, {})[area['id']] = dict(code=code, publisher=source,
            description=description, note=field('NOTAS', i), frequency=frequency, alias=field('ALIAS DE LA SERIE', i))
        series_periods = set()
        for label, values in cells:
            value = values[i].strip()
            status = ''
            id = period(label, frequency)
            assert id and id not in series_periods, (file, code, label)
            series_periods.add(id)
            position = periods.setdefault(id, (len(periods), label))[0]
            try:
                number = float(value)
                assert math.isfinite(number)
            except ValueError:
                number = None
                status = value or 'Sin dato'
                missing[status] += 1
            observations.append([area_index, position, measure_index, number, status, identifier])

    if not observations:
        return None, omitted
    filename = f'{identifier}-main.json.gz'
    payload = encode(dict(rows=observations))
    compressed = gzip.compress(payload, compresslevel=6, mtime=0)
    (OUTPUT / filename).write_bytes(compressed)
    title = TITLES.get(key, f'{CHAPTERS[chapter]} · cuadro {chapter}.{key[2:].lstrip("0")}')
    source_url = BASE + 'compartido/datos/csv/' + file
    note = 'Elaboración propia con datos extraídos del sitio web del Banco de España (www.bde.es). Se conservan la unidad, los códigos de serie, las notas y el símbolo de cada dato ausente.'
    if omitted:
        note += f' {len(omitted)} series con fuente externa quedan en el inventario de revisión.'
    return dict(id=identifier, label=title, title=title, family=f'Banco de España · {CHAPTERS[chapter]}',
                publisher='Banco de España', sourceId='F041', dataFolder='comercio/bde',
                sourceUrl=BULLETIN.format(chapter), downloadUrl=source_url, license='Términos de las estadísticas del Banco de España',
                note=note, rows=len(observations), unit=next(iter(units.values())) if len(set(units.values()))==1 else 'Según serie',
                unitsByCategory=dict(dimension='Serie',values=units), dimensions=[dict(name='Serie', values=list(measures))],
                seriesMetadata=metadata_by_series,
                territories=[{**area, 'sourceTableIds':[identifier]} for _, area in territories.values()],
                periods=[dict(id=id, label=label) for id, (_, label) in periods.items()],
                missingTokens=dict(missing), sourceTables=[dict(id=identifier, url=source_url, sha256=sha(body), bytes=len(body),
                    member=file, archive=archive['url'], sourceCodes=len(descriptions))],
                licenseUrl=TERMS, shards=[dict(id='main', file=filename, rows=len(observations), bytes=len(compressed),
                sha256=sha(compressed), contentSha256=sha(payload))]), omitted


def main(refresh=False):
    cache = ROOT / '.cache/f08'
    cache.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    revision = json.loads((ROOT / 'registry/commerce-tables.json').read_bytes())['revision']
    tables, exceptions, downloads = [], [], []
    for chapter in CHAPTERS:
        name = f'be{chapter:02}.zip'
        url = BASE + 'compartido/datos/zip/' + name
        data = fetch(url, cache / name, refresh)
        archive = dict(chapter=chapter, url=url, sha256=sha(data), bytes=len(data))
        downloads.append(archive)
        with ZipFile(io.BytesIO(data)) as zip:
            for file in sorted(zip.namelist()):
                assert re.fullmatch(r'be[0-9a-z]{3,6}\.csv', file), file
                table, omitted = capture(chapter, file, zip.read(file), archive)
                if table:
                    tables.append(table)
                if omitted:
                    exceptions.append(dict(archive=url, file=file, omitted=omitted))
    ids = [t['id'] for t in tables]
    assert len(set(ids))==len(ids)
    (OUTPUT / 'index.json').write_bytes(encode(dict(schemaVersion=1, revision=revision, tables=tables,
        provenance=downloads, excludedSeries=exceptions)))
    print(f'BdE: {len(tables)} tables, {sum(t["rows"] for t in tables):,} observations, {sum(len(t["omitted"]) for t in exceptions)} external series to review')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    main(parser.parse_args().refresh)
