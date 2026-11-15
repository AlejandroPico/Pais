"""Capture official statistical tables by topic in the atlas cube format."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
import welfare_collect as cubes

ROOT = cubes.ROOT
core = cubes.core
CAPTURES = {'labor': ('trabajo', 'f04'), 'care': ('cuidados', 'f05'), 'housing': ('vivienda', 'f06')}

def main(refresh=False, kind='labor'):
    folder, cache = CAPTURES[kind]
    output = ROOT / 'datos' / folder / 'ine'
    config = json.loads((ROOT / f'registry/{kind}-tables.json').read_text(encoding='utf-8'))
    core.CACHE = ROOT / '.cache' / cache
    core.CACHE.mkdir(parents=True, exist_ok=True)
    core.REFRESH = refresh
    output.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(cubes.fetch_table, [table['id'] for table in config['tables']]))
    core.REFRESH = False
    catalog = json.loads((ROOT/'datos/catalogo/investigacion/ine-catalog.json').read_text(encoding='utf-8'))
    operations = [{'id': op['Id'], 'tables': op['tables']} for op in catalog['operations']
                  if op['Id'] in config['operationIds']]
    assert {op['id'] for op in operations} == set(config['operationIds']), 'Incomplete operations'
    for operation in operations:
        additions = config.get('additionalTables', {}).get(str(operation['id']), [])
        known_ids = {table['Id'] for table in operation['tables']}
        operation['tables'] = [*operation['tables'], *(t for t in additions if t['Id'] not in known_ids)]
    metadata = {table['Id']: table for op in operations for table in op['tables']}
    previous = json.loads((output / 'index.json').read_text(encoding='utf-8')) if (output / 'index.json').exists() and not refresh else {}
    existing = {table['id']: table for table in previous.get('tables', [])}
    tables = []
    failures = {}
    for table in config['tables']:
        tid = table['id']
        checkpoint = core.CACHE / f'{kind}-{tid}.json'
        candidates = [existing.get(tid)]
        if checkpoint.exists() and not refresh:
            candidates.append(json.loads(checkpoint.read_text(encoding='utf-8')))
        saved = next((item for item in candidates if item and all(
            (output / part['file']).is_file()
            and core.sha((output / part['file']).read_bytes()) == part['sha256']
            for part in item['shards']
        )), None)
        if saved is None:
            try:
                saved = cubes.build_group({**table, 'preserveMissingDimensions': True}, [tid], metadata, output=output)
            except (AssertionError, ValueError) as error:
                if kind != 'housing':
                    raise
                failures[tid] = str(error)
                print(f'INE {tid}: {error}', flush=True)
                continue
            checkpoint.write_bytes(core.encode(saved))
        tables.append({**saved, **table})
    if failures:
        (core.CACHE / 'failures.json').write_bytes(core.encode(failures))
        raise ValueError(f'{len(failures)} tables require review')
    (output / 'inventory.json').write_bytes(core.encode({'revision': config['revision'], 'operations': operations}))
    index = {
        'schemaVersion': 1, 'revision': config['revision'],
        'rowLayout': 'territoryIndex,periodIndex,dimensionIndices...,value,statusToken,sourceTableId',
        'tables': tables, 'inventoryTables': len(metadata), 'operations': len(operations),
        'provenance': sorted({p['url']: p for p in core.PROVENANCE}.values(), key=lambda p: p['url']),
    }
    (output / 'index.json').write_bytes(core.encode(index))
    print(f"{cache.upper()}: {len(tables)} tables, {sum(t['rows'] for t in tables):,} observations", flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--kind', choices=CAPTURES, default='labor')
    args = parser.parse_args()
    main(args.refresh, args.kind)
