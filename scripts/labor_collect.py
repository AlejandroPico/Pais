"""Capture the selected official labor tables in the atlas cube format."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
import welfare_collect as cubes

ROOT = cubes.ROOT
core = cubes.core
OUTPUT = ROOT / 'datos/trabajo/ine'

def main(refresh=False):
    config = json.loads((ROOT / 'registry/labor-tables.json').read_text(encoding='utf-8'))
    core.CACHE = ROOT / '.cache/f04'
    core.CACHE.mkdir(parents=True, exist_ok=True)
    core.REFRESH = refresh
    OUTPUT.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(cubes.fetch_table, [table['id'] for table in config['tables']]))
    core.REFRESH = False
    catalog = json.loads((ROOT/'datos/catalogo/investigacion/ine-catalog.json').read_text(encoding='utf-8'))
    operations = [{'id': op['Id'], 'tables': op['tables']} for op in catalog['operations']
                  if op['Id'] in config['operationIds']]
    assert {op['id'] for op in operations} == set(config['operationIds']), 'Incomplete labor operations'
    metadata = {table['Id']: table for op in operations for table in op['tables']}
    tables = [cubes.build_group(table, [table['id']], metadata, output=OUTPUT) for table in config['tables']]
    (OUTPUT / 'inventory.json').write_bytes(core.encode({'revision': config['revision'], 'operations': operations}))
    index = {
        'schemaVersion': 1, 'revision': config['revision'],
        'rowLayout': 'territoryIndex,periodIndex,dimensionIndices...,value,statusToken,sourceTableId',
        'tables': tables, 'inventoryTables': len(metadata), 'operations': len(operations),
        'provenance': sorted({p['url']: p for p in core.PROVENANCE}.values(), key=lambda p: p['url']),
    }
    (OUTPUT / 'index.json').write_bytes(core.encode(index))
    print(f"F04: {len(tables)} tables, {sum(t['rows'] for t in tables):,} observations", flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    main(parser.parse_args().refresh)
