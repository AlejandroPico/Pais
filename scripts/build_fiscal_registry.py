"""Build the F09 catalogue after checking its saved distributions."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('deuda-local','bde','igae','aeat','conprel')
LEVELS = dict(national='España', community='Comunidades autónomas', province='Provincias',
              municipal='Municipios', unlocated='Ámbitos de consulta')


def read(path):
    return json.loads(path.read_bytes())


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def main():
    products, inventory, checked = [], [], set()
    for name in FOLDERS:
        folder = ROOT/'datos/hacienda'/name
        index = read(folder/'index.json')
        revision = index['revision']
        for table in index['tables']:
            for part in table['shards']:
                data = (folder/part['file']).read_bytes()
                payload = gzip.decompress(data)
                assert checksum(data)==part['sha256'] and checksum(payload)==part['contentSha256']
                assert len(json.loads(payload)['rows'])==part['rows']
            assert sum(part['rows'] for part in table['shards'])==table['rows']
            for source in table['sourceTables']:
                if 'originalFile' in source:
                    origin = folder/source['originalFile']
                    if origin not in checked:
                        assert checksum(origin.read_bytes())==source['sha256'], origin
                        checked.add(origin)
            key = 'fiscal:'+str(table['id'])
            periods = sorted(table['periods'],key=lambda period: period['id'])
            entry = dict(id=key,title=table['label'],sourceId=table['sourceId'],categoryIds=['F09'],
                status='integrado',url=table['sourceUrl'],mapAction=key,
                period={'from':periods[0]['label'],'to':periods[-1]['label']},
                coverage=' · '.join(LEVELS[key] for key in sorted({a['level'] for a in table['territories']})),
                unit=table['unit'],license=table['license'],notes=table['note'],dataFile=f'hacienda/{name}/index.json')
            products.append(entry)
            inventory.append({**entry,'id':'fiscal-distribution:'+str(table['id']),
                'links':{'Descarga oficial':table['downloadUrl']},
                'review':dict(implementedProductId=key,updatedAt=revision,
                    reason=f'Distribución cotejada. {table["rows"]:,} celdas conservadas con sus estados y unidades.')})
    for source in read(ROOT/'registry/fiscal-sources.json'):
        inventory.append({**source,'status':'por_revisar','categoryIds':[],'suggestedCategoryIds':['F09'],'license':None})
    assert len({p['id'] for p in products})==len(products)
    output=dict(revision=revision,available=products,inventory=inventory)
    (ROOT/'registry/fiscal-products.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'F09: {len(products)} productos, {len(inventory)} fichas de inventario')


if __name__=='__main__':
    main()
