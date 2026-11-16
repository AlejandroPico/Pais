"""Convert the official MITECO Minerva production and employment CSV files."""
import argparse
import csv
import gzip
import io
import json
import math
import re

from affiliation_collect import fetch
from demography_collect import ROOT, encode, sha

OUTPUT = ROOT / 'datos/economia/miteco'
BASE = 'https://sedeaplicaciones.minetur.gob.es/minerva/descargaCSV'
PAGE = 'https://datos.gob.es/es/catalogo/e05068001-estadisticas-de-produccion-minera1'
METHOD = 'https://www.miteco.gob.es/es/energia/mineria-explosivos/estadistica.html'
LICENSE = 'CC BY 4.0 · MITECO'
GEO_COLUMNS = ('ANIO', 'CAUTONOMIA', 'AUTONOMIA', 'CPROVINCIA', 'PROVINCIA')
DISTRIBUTIONS = (
    (942001, 'Produccion', 'Producción minera', {'PRODUCTO': 'Producto'}, {'CANTIDAD': 'Cantidad'},
     'Unidad sin especificar en el CSV', 'La moneda o unidad física no figura en la distribución. Consulta el anuario antes de comparar cantidades de productos distintos.'),
    (942002, 'Empleo', 'Empleo en el sector minero', {},
     {'HOMBRES': 'Hombres', 'MUJERES': 'Mujeres', 'EMPLEO_CONTRATA': 'Empleo de contrata'},
     'Personas', 'La contrata se publica como una medida separada. Cada serie corresponde a una sustancia y una provincia.'),
)


def capture(config, cache, refresh):
    identifier, file, title, extra, measures, unit, note = config
    url = f'{BASE}{file}.aspx'
    filename = f'{file.lower()}.csv'
    raw = fetch(url, cache / ('mineria-' + filename), refresh)
    body, marker, suffix = raw.partition(b'<!DOCTYPE html>')
    if marker:
        # The official production endpoint can append an ASP.NET error page
        # after the CSV records even when the HTTP status is 200.
        assert file == 'Produccion' and b'Error en runtime' in suffix and suffix.rstrip().endswith(b'</html>')
    reader = csv.DictReader(io.StringIO(body.decode('cp1252')))
    fields = {'TIPO_SUSTANCIA': 'Tipo de sustancia', 'SUSTANCIA': 'Sustancia', **extra}
    assert set(reader.fieldnames) == {*GEO_COLUMNS, *fields, *measures}, (title, reader.fieldnames)
    dims = {name: {} for name in fields.values()}
    if len(measures) > 1:
        dims['Indicador'] = {name: i for i, name in enumerate(measures.values())}
    provinces, periods = {}, {}
    records = []
    names = {}
    seen = set()
    for record in reader:
        assert None not in record and None not in record.values(), (title, record)
        year, province = record['ANIO'], record['CPROVINCIA']
        assert re.fullmatch(r'20\d\d', year) and '01' <= province <= '52' and re.fullmatch(r'\d\d', province)
        name = record['PROVINCIA']
        area_position = provinces.setdefault(province, len(provinces))
        names.setdefault(province, name)
        period = periods.setdefault(year, len(periods))
        dimensions = []
        for field, label in fields.items():
            values = dims[label]
            dimensions.append(values.setdefault(record[field], len(values)))
        for position, field in enumerate(measures):
            key = (area_position, period, *dimensions, *((position,) if len(measures) > 1 else ()))
            assert key not in seen, (title, record)
            seen.add(key)
            value = float(record[field].replace(',', '.'))
            assert math.isfinite(value)
            records.append([*key, value, '', identifier])

    assert seen and len(periods) > 1
    original = 'originales/' + filename
    (OUTPUT / original).write_bytes(body)
    source = dict(id=identifier, url=url, originalFile=original, bytes=len(body), sha256=sha(body),
                  downloadSha256=sha(raw), strippedErrorPage=bool(marker))
    territories = [dict(id='province:'+code, level='province', code=code, name=names[code], sourceTableIds=[identifier])
                   for code in provinces]
    shard_file = f'{identifier}-main.json.gz'
    payload = encode({'rows': records})
    compressed = gzip.compress(payload, compresslevel=6, mtime=0)
    (OUTPUT / shard_file).write_bytes(compressed)
    shard = dict(id='main', file=shard_file, rows=len(records), bytes=len(compressed),
                 sha256=sha(compressed), contentSha256=sha(payload))
    return dict(id=identifier, sourceId='F094', publisher='MITECO', title=title, label=title,
                family='Estadística minera de España', note=note, dimensions=[dict(name=name, values=list(values)) for name, values in dims.items()],
                sourceUrl=PAGE, downloadUrl=url, sourceTables=[source], methodologyUrl=METHOD, unit=unit,
                dataFolder='economia/miteco', license=LICENSE, territories=territories, rows=len(records),
                periods=[dict(id=year, label=year) for year in periods], shards=[shard], missingTokens={})


def main(refresh=False):
    config = json.loads((ROOT / 'registry/economy-tables.json').read_bytes())
    cache = ROOT / '.cache/f07'
    cache.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'originales').mkdir(parents=True, exist_ok=True)
    tables = [capture(distribution, cache, refresh) for distribution in DISTRIBUTIONS]
    (OUTPUT / 'index.json').write_bytes(encode(dict(schemaVersion=1, revision=config['revision'], tables=tables)))
    print(f'Minerva: {len(tables)} distributions, {sum(t["rows"] for t in tables):,} observations')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    main(parser.parse_args().refresh)
