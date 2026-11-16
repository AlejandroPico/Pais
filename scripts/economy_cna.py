"""Capture the full annual national accounts workbooks from the INE."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
from io import BytesIO
import json
from pathlib import PurePosixPath
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from affiliation_collect import SHEET, fetch, workbook
from demography_collect import ROOT, encode

OUTPUT = ROOT / 'datos/economia/cna'
BASE = 'https://www.ine.es/daco/daco42/cne24/'
PAGE = 'https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177057&idp=1254735576581&menu=resultados'
FAMILY = 'Contabilidad Nacional Anual de España'
INDEX_UNIT = 'Índice de volumen encadenado (2020 = 100)'
WORKBOOKS = (
    ('pib95_25.xlsx', 'PIB y sus componentes', 'C', [
        ('Precios corrientes', ['Millones de euros']), ('Variación interanual de precios corrientes', ['%']),
        ('Estructura porcentual', ['%']), ('Volumen encadenado', [INDEX_UNIT]),
        ('Variación interanual en volumen', ['%']),
    ]),
    ('rnd_95_25.xlsx', 'Renta nacional disponible', 'C', [('Precios corrientes', ['Millones de euros'])]),
    ('rem_empleo95_25.xlsx', 'Remuneración y empleo', 'C', [
        ('Remuneración', ['Millones de euros'] * 3), ('Puestos de trabajo', ['Miles de puestos'] * 2),
        ('Equivalentes a tiempo completo', ['Miles de puestos'] * 2), ('Horas', ['Miles de horas'] * 2),
        ('Personas', ['Miles de personas'] * 2), ('Productividad y costes laborales', ['%']),
    ]),
    ('fbc95_25.xlsx', 'Formación bruta de capital por tipo de activo', 'B', [
        ('Precios y volumen', ['Millones de euros', INDEX_UNIT, '%']),
    ]),
)


def sheets(raw):
    rel_ns = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    with ZipFile(BytesIO(raw)) as archive:
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        relations = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.get('Id'): r.get('Target') for r in relations}
    for sheet in book.find(SHEET + 'sheets'):
        name = sheet.get('name')
        if name != 'Lista_Tablas':
            target = targets[sheet.get('{' + rel_ns + '}id')]
            yield name, target.lstrip('/') if target.startswith('/') else str(PurePosixPath('xl') / target)


def measure(label, default):
    label = label.lower()
    if 'per cápita' in label:
        return 'Euros por habitante' if default == 'Millones de euros' else default
    if 'miles de habitantes' in label or 'miles de personas' in label:
        return 'Miles de personas'
    if '(*)' in label and default == '%':
        return 'Puntos porcentuales'
    return default


def parse_sheet(raw, path, label_column, units):
    sections, records, notes = [], [], []
    columns = {}
    sections_heading = ''
    for row in workbook(raw, path):
        text = ' '.join(row.get(label_column, '').split())
        years = {column: match.groups() for column, value in row.items()
                 if (match := re.fullmatch(r'((?:19|20)\d\d)\s*(?:\(([PA])\))?', value))}
        year_range = [int(year) for year, _ in years.values()]
        if len(year_range) >= 29 and year_range == list(range(min(year_range), max(year_range) + 1)):
            columns = years
            sections.append(text if text not in ('Ramas de actividad', 'Operaciones') else sections_heading)
            continue
        if not text:
            continue
        if text.startswith(('(P)', '(A)', '(*)', 'Nota:', 'Fuentes:', 'Unidades:')):
            notes.append(text)
            continue
        if not columns or not any(row.get(column) for column in columns):
            if not text.startswith('Unidad:'):
                sections_heading = text
            continue
        block = len(sections) - 1
        assert 0 <= block < len(units), (path, block)
        heading = sections[block] or sections_heading
        records.append((block, heading, text, measure(text, units[block]), dict(columns), row))
    assert len(sections) == len(units) and records, (path, len(sections), len(units))
    return records, notes


def capture(identifier, name, raw, sheet, path, label_column, units, source):
    records, notes = parse_sheet(raw, path, label_column, units)
    duplicates = Counter((block, heading, label) for block, heading, label, _, _, _ in records)
    occurrences = Counter()
    indicators, periods, status_by_year, rows, unit_rules = [], {}, {}, [], []
    missing = Counter()
    for block, heading, label, unit, columns, cells in records:
        key = (block, heading, label)
        occurrences[key] += 1
        label = f'{heading} · {label}' if heading and heading != label else label
        if duplicates[key] > 1:
            label += f' · fila {occurrences[key]}'
        index = len(indicators)
        assert label not in indicators, (name, label)
        indicators.append(label)
        unit_rules.append(dict(when={'Indicador': label}, unit=unit))
        for column, (year, status) in columns.items():
            value = cells.get(column, '')
            try:
                number = float(value)
            except ValueError:
                assert value in ('', '..', '.', '-', '…'), (name, label, year, value)
                number = None
            state = {None: '', 'P': 'Provisional', 'A': 'Avance'}[status]
            assert year not in status_by_year or status_by_year[year] == state
            status_by_year[year] = state
            if number is None:
                state = value or 'Sin dato'
                missing[state] += 1
            period = periods.setdefault(year, len(periods))
            rows.append([0, period, index, number, state, identifier])

    filename = f'{identifier}-main.json.gz'
    payload = encode({'rows': rows})
    data = gzip.compress(payload, compresslevel=6, mtime=0)
    (OUTPUT / filename).write_bytes(data)
    return dict(id=identifier, label=name, title=name, family=FAMILY, publisher='INE',
                unit='Según indicador publicado', unitsByConditions=unit_rules,
                dimensions=[dict(name='Indicador', values=indicators)], dataFolder='economia/cna',
                territories=[dict(id='national:ES', level='national', code='ES', name='España', sourceTableIds=[identifier])],
                periods=[dict(id=year, label=' · '.join(filter(None, (year, status_by_year[year])))) for year in periods],
                rows=len(rows), missingTokens=dict(missing), sourceUrl=PAGE, downloadUrl=source['url'],
                license='CC BY 4.0 · INE',
                note='España. Revisión Estadística 2024. Los precios corrientes, volúmenes encadenados y tasas conservan sus unidades publicadas.',
                sourceTables=[dict(id=identifier, sheet=sheet, notes=notes, **source)],
                shards=[dict(id='main', file=filename, rows=len(rows), bytes=len(data),
                             sha256=sha256(data).hexdigest(), contentSha256=sha256(payload).hexdigest())])


def main(refresh=False):
    cache = ROOT / '.cache/f07'
    originals = OUTPUT / 'originales'
    originals.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    config = json.loads((ROOT / 'registry/economy-tables.json').read_bytes())
    tables = []
    for file_index, (file, title, column, sheet_config) in enumerate(WORKBOOKS):
        url = BASE + file
        raw = fetch(url, cache / file, refresh)
        (originals / file).write_bytes(raw)
        source = dict(url=url, originalFile=f'originales/{file}', bytes=len(raw), sha256=sha256(raw).hexdigest())
        for sheet_index, ((sheet, path), (name, units)) in enumerate(zip(sheets(raw), sheet_config, strict=True)):
            label_column = 'B' if file.startswith('rem_empleo') and sheet == 'Tabla_1' else column
            id = 941000 + file_index * 100 + sheet_index + 1
            tables.append(capture(id, f'{title} · {name}', raw, sheet, path, label_column, units, source))
    (OUTPUT / 'index.json').write_bytes(encode(dict(schemaVersion=1, revision=config['revision'], tables=tables)))
    print(f'CNA: {len(tables)} sheets, {sum(t["rows"] for t in tables):,} published cells')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    main(parser.parse_args().refresh)
