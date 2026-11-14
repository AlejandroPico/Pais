"""Capture official metadata for the preserved datos.gob.es title inventory."""

import csv
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'datos/catalogo/investigacion'
ENDPOINT = 'https://datos.gob.es/virtuoso/sparql'
PAGE = 3500
GRAPH = 'http://datos.gob.es/catalogo'
DATASET = 'http://www.w3.org/ns/dcat#Dataset'


def query(body):
    address = ENDPOINT + '?' + urlencode({'query': body, 'format': 'application/sparql-results+json'})
    with urlopen(Request(address, headers={'User-Agent': 'Pais Atlas (public metadata)'}), timeout=50) as response:
        return [{key: item['value'] for key, item in row.items()} for row in json.load(response)['results']['bindings']]


PROPERTIES = {
    'themes': 'http://www.w3.org/ns/dcat#theme',
    'areas': 'http://purl.org/dc/terms/spatial',
    'licenses': 'http://purl.org/dc/terms/license',
    'identifiers': 'http://purl.org/dc/terms/identifier',
}


def pattern(predicate):
    return f'GRAPH <{GRAPH}> {{ ?d a <{DATASET}> . ?d <{predicate}> ?v }}'


def capture_property(item):
    key, predicate = item
    where = pattern(predicate)
    count_query = 'SELECT (COUNT(DISTINCT ?d) AS ?count) WHERE { '+where+' }'
    expected = int(query(count_query)[0]['count'])
    records = {}
    for offset in range(0, expected, PAGE):
        rows = query(f'''SELECT ?d (GROUP_CONCAT(DISTINCT STR(?v); SEPARATOR="|") AS ?values)
          WHERE {{ {where} }} GROUP BY ?d ORDER BY ?d LIMIT {PAGE} OFFSET {offset}''')
        if len(rows) != min(PAGE, expected-offset):
            raise ValueError(f'Incomplete {key} page at offset {offset}: {len(rows)}')
        for row in rows:
            url = row['d']
            if url in records:
                raise ValueError(f'Duplicate across {key} pages: {url}')
            records[url] = sorted(set(row.get('values', '').split('|')) - {''})
    if int(query(count_query)[0]['count']) != expected:
        raise ValueError(f'The official catalogue changed while collecting {key}. Run the capture again.')
    print(key, len(records), flush=True)
    return key, records


def main():
    count_query = f'SELECT (COUNT(DISTINCT ?d) AS ?count) WHERE {{ GRAPH <{GRAPH}> {{ ?d a <{DATASET}> }} }}'
    expected = int(query(count_query)[0]['count'])
    records = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for key, entries in pool.map(capture_property, PROPERTIES.items()):
            for url, values in entries.items():
                if values:
                    records.setdefault(url, {})[key] = values
    with gzip.open(RESEARCH/'datasets-catalogo-nacional.csv.gz', 'rt', encoding='utf-8-sig') as source:
        targets = [row['url_catalogo'] for row in csv.DictReader(source, delimiter=';')]
    by_slug = {}
    for url in records:
        if urlsplit(url).hostname == 'datos.gob.es':
            by_slug.setdefault(urlsplit(url).path.rsplit('/', 1)[-1], []).append(url)
    matched = {}
    for url in targets:
        candidates = by_slug.get(urlsplit(url).path.rsplit('/', 1)[-1], [])
        original = url if url in records else candidates[0] if len(candidates) == 1 else None
        if original:
            matched[url] = records[original]
    print('Matched', len(matched), 'of', len(targets), flush=True)
    output = RESEARCH/'datosgob-metadata.json.gz'
    payload = {'source': ENDPOINT, 'revision': '2026-11-14', 'catalogueCount': expected, 'records': matched}
    temporary = output.with_suffix('.tmp')
    temporary.write_bytes(gzip.compress(json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode(), mtime=0))
    temporary.replace(output)


if __name__ == '__main__':
    main()
