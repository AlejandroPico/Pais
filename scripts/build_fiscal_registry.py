"""Build the F09–F12 catalogues after checking their saved distributions."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPICS = {
    'fiscal': ('F09','hacienda',('deuda-local','bde','igae','aeat','conprel')),
    'funding': ('F10','ayudas',('contratos','placsp','ted','feder','cohesion','bdns')),
    'education': ('F11','educacion',('educabase','siiu','ine','eurostat')),
    'science': ('F12','ciencia',('ine','eurostat','epo','cordis','resultados')),
}
LEVELS = dict(national='España', community='Comunidades autónomas', province='Provincias',
              municipal='Municipios', unlocated='Ámbitos de consulta')


def read(path):
    return json.loads(path.read_bytes())


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=TOPICS, default='fiscal')
    kind = parser.parse_args().kind
    category, section, folders = TOPICS[kind]
    compact = kind in {'education','science'}
    products, inventory, checked = [], [], set()
    grids, groups = [], {}
    for name in folders:
        folder = ROOT/'datos'/section/name
        index = read(folder/'index.json')
        revision = index['revision']
        for table in index['tables']:
            for part in table['shards']:
                data = (folder/part['file']).read_bytes()
                payload = gzip.decompress(data)
                assert checksum(data)==part['sha256'] and checksum(payload)==part['contentSha256']
                cube = json.loads(payload)
                if 'cells' in cube:
                    lengths = {-2:len(table['territories']),-1:len(table['periods']),
                               **{i:len(d['values']) for i,d in enumerate(table['dimensions'])}}
                    assert set(lengths)==set(cube['axes']) and len(lengths)==len(cube['axes'])
                    assert len(cube['cells'])==part['rows']==math.prod(lengths.values())
                    assert all(0<=int(cell)<part['rows'] for cell in cube.get('flags',{}))
                else:
                    assert len(cube['rows'])==part['rows']
            assert sum(part['rows'] for part in table['shards'])==table['rows']
            for source in table['sourceTables']:
                if 'originalFile' in source:
                    origin = folder/source['originalFile']
                    if origin not in checked:
                        assert checksum(origin.read_bytes())==source['sha256'], origin
                        checked.add(origin)
            key = kind+':'+str(table['id'])
            periods = sorted(table['periods'],key=lambda period: period['id'])
            entry = dict(id=key,title=table['label'],sourceId=table['sourceId'],categoryIds=[category],
                status='integrado',url=table['sourceUrl'],mapAction=key,
                period={'from':periods[0]['label'],'to':periods[-1]['label']},
                coverage=' · '.join(LEVELS[key] for key in sorted({a['level'] for a in table['territories']})),
                unit=table['unit'],license=table['license'],notes=table['note'],
                dataFile=f'{section}/viewer.json.gz' if compact else f'{section}/{name}/index.json')
            products.append(entry)
            inventory.append({**entry,'id':kind+'-distribution:'+str(table['id']),
                'links':{'Descarga oficial':table['downloadUrl']},
                'review':dict(implementedProductId=key,updatedAt=revision,
                    reason=f'Distribución cotejada. {table["rows"]:,} celdas conservadas con sus estados y unidades.')})
            if compact:
                grid = dict(table)
                territories = grid.pop('territories')
                group = checksum(json.dumps(territories,ensure_ascii=False,separators=(',',':')).encode())
                groups.setdefault(group,territories)
                grids.append(dict(grid,territoryGroup=group))
    for source in read(ROOT/f'registry/{kind}-sources.json'):
        inventory.append({**source,'status':'por_revisar','categoryIds':[],'suggestedCategoryIds':[category],'license':None})
    if compact:
        capture = read(ROOT/f'registry/{kind}-capture.json')
        for gap in capture['gaps']:
            source_id=gap.get('sourceId','F005') if kind=='science' else (
                'F005' if gap['topic']=='ine' else 'F074' if gap['topic'].startswith('ue') else 'F073')
            inventory.append(dict(id=kind+'-pending:'+checksum(gap['download'].encode())[:20],
                title=gap['title'], sourceId=source_id,
                url=gap['table'],status='bloqueado',categoryIds=[category],license=None,notes=gap['reason'],
                links={'Descarga oficial':gap['download']},review=dict(
                    updatedAt=revision,reason=gap['reason'])))
        data = json.dumps(dict(revision=revision,inventoryTables=len(grids),operations=0,tables=grids,
                               territoryGroups=groups),ensure_ascii=False,separators=(',',':')).encode()
        (ROOT/'datos'/section/'viewer.json.gz').write_bytes(gzip.compress(data,compresslevel=6,mtime=0))
    assert len({p['id'] for p in products})==len(products)
    output=dict(revision=revision,available=products,inventory=inventory)
    (ROOT/f'registry/{kind}-products.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{category}: {len(products)} productos, {len(inventory)} fichas de inventario')


if __name__=='__main__':
    main()
