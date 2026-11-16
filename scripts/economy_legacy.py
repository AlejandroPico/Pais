"""Preserve the INE's PC-Axis editions of business demography (2008–2013)."""
import argparse
import csv
import gzip
from html import unescape
import io
import json
import re
from urllib.parse import urljoin

import welfare_collect as cubes

core = cubes.core
ROOT = core.ROOT
OUTPUT = ROOT / 'datos/economia/dae-historica'
DOMAIN = 'https://www.ine.es'
FAMILY = 'Demografía armonizada de empresas'
LICENSE = 'CC BY 4.0 · INE'


def catalogue(edition):
    year, url = edition['year'], edition['url']
    path, provenance = core.fetch(url)
    html = gzip.decompress(path.read_bytes()).decode('utf-8-sig')
    pattern = r'<a href="(/jaxi/Tabla\.htm\?[^"]*file=(\d+)\.px[^"]*)"[^>]*>([^<]+)</a>'
    records = {file: (urljoin(url, unescape(link)), unescape(title).strip())
               for link, file, title in re.findall(pattern, html)}
    assert len(records) == 10, (year, list(records))
    return records, provenance


def make_table(year, file, url, title):
    identifier = 943000 + (year - 2008) * 100 + int(file) - 1000
    download = f'{DOMAIN}/jaxi/files/_px/es/csv_bdsc/t37/p204/a{year}/l0/{file}.csv'
    path, provenance = core.fetch(download)
    reader = csv.DictReader(io.StringIO(gzip.decompress(path.read_bytes()).decode('utf-8-sig')), delimiter=';')
    assert reader.fieldnames[-1] == 'Total'
    geo_field = 'Comunidades y Ciudades Autónomas'
    fields = [f for f in reader.fieldnames if f not in ('Total Nacional', geo_field, 'Periodo', 'Total')]
    dimensions = [{'name': name, 'values': []} for name in fields]
    periods, territories, rows = [], [], []
    period_ids, territory_ids = {}, {}
    dim_ids = [{} for _ in fields]
    seen = set()

    for row in reader:
        assert None not in row and None not in row.values(), (title, row)
        community = row.get(geo_field)
        area = cubes.area([{'T3_Variable': geo_field, 'Nombre': community}] if community else [])
        if area['id'] not in territory_ids:
            territory_ids[area['id']] = len(territories)
            territories.append({**area, 'sourceTableIds': [identifier]})
        period = row.get('Periodo', str(year))
        period_id = re.search(r'\b20\d{2}\b', period)[0]
        if period_id not in period_ids:
            period_ids[period_id] = len(periods)
            periods.append(dict(id=period_id, label=period))
        position = [territory_ids[area['id']], period_ids[period_id]]
        for index, name in enumerate(fields):
            value = row[name]
            if value not in dim_ids[index]:
                dim_ids[index][value] = len(dimensions[index]['values'])
                dimensions[index]['values'].append(value)
            position.append(dim_ids[index][value])
        assert tuple(position) not in seen, (title, row)
        seen.add(tuple(position))
        value = row['Total']
        assert re.fullmatch(r'\d+(?:\.\d{3})*(?:,\d+)?', value), (title, value)
        value = float(value.replace('.', '').replace(',', '.'))
        rows.append([*position, value, '', identifier])

    assert rows
    filename = f'{identifier}-main.json.gz'
    payload = core.encode({'rows': rows})
    compressed = gzip.compress(payload, compresslevel=6, mtime=0)
    (OUTPUT / filename).write_bytes(compressed)
    shard = dict(id='main', file=filename, rows=len(rows), bytes=len(compressed),
                 sha256=core.sha(compressed), contentSha256=core.sha(payload))
    return dict(id=identifier, label=f'{title.rstrip(".")} · {year}', title=title, family=FAMILY,
                rows=len(rows), territories=territories, periods=periods, dimensions=dimensions,
                dataFolder='economia/dae-historica', publisher='INE', sourceUrl=url, downloadUrl=download,
                sourceTables=[dict(id=identifier, year=year, file=file, **provenance)], shards=[shard],
                unit='empresas', license=LICENSE, missingTokens={},
                note=f'Edición PC-Axis de {year}. En tablas de supervivencia se conserva también el recuento de nacimientos de la cohorte.')


def main(refresh=False):
    config = json.loads((ROOT / 'registry/economy-tables.json').read_bytes())
    core.CACHE = ROOT / '.cache/f07'
    core.CACHE.mkdir(parents=True, exist_ok=True)
    core.REFRESH = refresh
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tables, sources = [], []
    for edition in reversed(config['daeLegacyEditions']):
        records, provenance = catalogue(edition)
        sources.append(provenance)
        for file, (url, title) in sorted(records.items()):
            tables.append(make_table(edition['year'], file, url, title))
    (OUTPUT / 'index.json').write_bytes(core.encode(dict(schemaVersion=1, revision=config['revision'],
        tables=tables, provenance=sources)))
    print(f'DAE PC-Axis: {len(tables)} tables, {sum(t["rows"] for t in tables):,} observations')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    main(parser.parse_args().refresh)
