"""F00: build a reproducible, offline registry from the preserved research.

Cataloguing is not ingestion. Keep the three discovery inventories separate;
only explicitly registered, working map products are labelled integrated.
"""
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
from catalog_relationships import enrich_national, link_ine

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/data/registry'
RESEARCH = ROOT / 'docs/research'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def atomic(path, body):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_bytes(body)
    os.replace(tmp, path)


def build():
    plan = read(ROOT / 'docs/planning/fasciculos.json')
    research = read(RESEARCH / 'fuentes-tematicas.json')
    publishers = read(RESEARCH / 'publicadores-catalogo-nacional.json')
    ioe = read(RESEARCH / 'operaciones-ioe-detalladas.json')
    ine = read(ROOT / 'public/data/ine-catalog.json')
    registered = read(ROOT / 'registry/products.json')
    categories = [{'id': f['id'], 'name': f['title']} for f in plan['fascicles'] if f['id'] != 'F00']
    routes = {r['sourceId']: r for r in plan['sourceRoutes']}
    sector_routes = {r['sector']: r['candidateFascicles'] for r in plan['ioeSectorRoutes']}
    sources = []
    for s in research['sources']:
        route = routes[s['id']]
        sources.append(dict(id=s['id'], name=s['name'], url=s['url'], kind='research',
                            group=s['group'], families=s['families'], coverage=s['geography'],
                            access=s['access'], notes=s['note'], reviewedAt=s['reviewedAt'],
                            candidateCategories=route['candidateFascicles'],
                            routingMode=route['mode'], license=None,
                            complementary=route['complementaryOperator'],
                            links=s.get('links', [])))
    for s in publishers['publishers']:
        sources.append(dict(id='publisher:' + s['id'], name=s['name'], url=s['catalogUrl'],
                            kind='publisher', officialId=s['id'], datasetCount=s['datasets'],
                            coverage='Según cada producto', license=None,
                            notes='Entrada del catálogo federado; puede corresponder a una fuente ya descrita en el directorio. No sumar ambos directorios como organismos únicos.',
                            families=[], candidateCategories=[], access='Revisar las distribuciones de cada conjunto',
                            apiUrl=s['apiUrl']))
    sources.append(dict(id='aux:terrain', name='Mapzen / USGS y fuentes del DEM Terrarium',
                        kind='auxiliary', url='https://github.com/tilezen/joerd/blob/master/docs/attribution.md',
                        coverage='Modelo global utilizado en España', families=['Elevación del terreno'],
                        notes='Modelo auxiliar; no es el MDT de alta resolución del IGN.',
                        license='Según las fuentes originales del modelo', candidateCategories=['F01']))
    products = dict(available=registered['products'], ioe=[], ine=[], national=[])
    territory_path = ROOT / 'registry/territory-products.json'
    if territory_path.exists():
        territory = read(territory_path)
        products['available'] = products['available'] + territory['available']
        products['territory'] = territory['inventory']
    demography_path = ROOT / 'registry/demography-products.json'
    if demography_path.exists():
        demography = read(demography_path)
        products['available'] += demography['available']
        products['demography'] = demography['inventory']
    welfare_path=ROOT/'registry/welfare-products.json'
    if welfare_path.exists():
        welfare=read(welfare_path);products['available']+=welfare['available'];products['welfare']=welfare['inventory']
    labor_path=ROOT/'registry/labor-products.json'
    if labor_path.exists():
        labor=read(labor_path)
        products['available']+=labor['available']
        products['labor']=labor['inventory']
    for o in ioe['operations']:
        fields = o['fields']
        products['ioe'].append(dict(id='ioe:' + o['code'], title=o['title'], sourceId='F002',
                                    responsible=fields.get('Servicio responsable'),
                                    categoryIds=[], suggestedCategoryIds=[x for x in sector_routes[fields['Sector o tema']] if x != 'F00'],
                                    status='por_revisar', url=o['url'],
                                    coverage=fields.get('Nivel de desagregación', 'Por verificar'),
                                    period=fields.get('Periodicidad de la difusión', 'Por verificar'),
                                    license=None, fields=fields, links=o['links'],
                                    notes='Ficha estadística recuperada. Reutilización, series y adaptación al mapa pendientes. Los destinos temáticos son orientativos.'))
    tables = {}
    for op in ine['operations']:
        for t in op['tables']:
            key = t['Id']
            if key not in tables:
                tables[key] = dict(id='ine:' + str(key), title=t['Nombre'], sourceId='F005',
                                   categoryIds=[], suggestedCategoryIds=[], status='por_revisar',
                                   url='https://www.ine.es/jaxiT3/Tabla.htm?t=' + str(key),
                                   coverage='Desglose por verificar', license=None,
                                   period={'from': t.get('Anyo_Periodo_ini'), 'to': t.get('Anyo_Periodo_fin')},
                                   operationIds=[], notes='Metadatos de tabla; no implica observaciones descargadas.')
            tables[key]['operationIds'].append(op['Id'])
    products['ine'] = list(tables.values())
    with gzip.open(RESEARCH / 'datasets-catalogo-nacional.csv.gz', 'rt', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter=';'):
            products['national'].append(dict(id=r['url_catalogo'], title=r['titulo'],
                                             sourceId='publisher:' + r['publicador_id'],
                                             url=r['url_catalogo'], categoryIds=[], suggestedCategoryIds=[],
                                             status='por_revisar', license=None))
    metadata_path = RESEARCH / 'datosgob-metadata.json.gz'
    with gzip.open(metadata_path, 'rt', encoding='utf-8') as source:
        federated_metadata = json.load(source)
    enrich_national(products['national'], federated_metadata['records'])
    # Editorial decisions live outside generated outputs and survive regeneration.
    reviews = read(ROOT / 'registry/reviews.json')['reviews']
    implemented = {p['id']: p for p in products['available']}
    applied = set()
    for review in reviews:
        inventory, product_id = review['inventory'], review['productId']
        assert inventory in {'ioe', 'ine', 'national'}, 'Invalid review inventory'
        assert (inventory, product_id) not in applied, 'Duplicate review'
        applied.add((inventory, product_id))
        product = next((p for p in products[inventory] if p['id'] == product_id), None)
        assert product is not None, 'Review refers to missing product'
        assert review.get('reason') and review.get('updatedAt'), 'Review needs reason and date'
        status = review.get('status', product['status'])
        assert status in registered['statusLabels'], 'Unknown integration state'
        history = review.get('history', [])
        previous = product['status']
        for event in history:
            assert event['from'] == previous and event.get('at') and event.get('reason'), 'Broken state history'
            assert event['to'] in registered['statusLabels']
            previous = event['to']
        assert previous == status, 'State change requires complete history'
        if status == 'bloqueado':
            assert review.get('nextAction'), 'Blocked product needs a next action'
        if status == 'integrado':
            target = implemented.get(review.get('implementedProductId'))
            assert target is not None, 'Integrated discovery entry needs a working map product'
            product['mapAction'] = target['mapAction']
        for key in ['status', 'categoryIds', 'coverage', 'period', 'license', 'unit', 'notes']:
            if key in review:
                product[key] = review[key]
        product['review'] = review
    link_ine(products, ine['operations'])
    source_ids = {s['id'] for s in sources}
    valid_categories = {c['id'] for c in categories}
    assert len(source_ids) == len(sources), 'Duplicate source IDs'
    assert len(products['national']) == publishers['datasetCount']
    assert not ioe['detailErrors'], 'Incomplete IOE snapshot'
    for kind, records in products.items():
        assert len({r['id'] for r in records}) == len(records), kind
        for r in records:
            assert r['sourceId'] in source_ids, r['id']
            assert set(r['categoryIds'] + r.get('suggestedCategoryIds', [])) <= valid_categories
            assert r['status'] != 'integrado' or kind == 'available' or r.get('review', {}).get('implementedProductId') in implemented
    # Validate before replacing any published registry. Existing files survive input errors.
    OUT.mkdir(parents=True, exist_ok=True)
    files = {}
    for kind, records in products.items():
        content = encode(records)
        body = gzip.compress(content, mtime=0)
        filename = kind + '.json.gz'
        atomic(OUT / filename, body)
        files[kind] = dict(file=filename, count=len(records), bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), contentSha256=hashlib.sha256(content).hexdigest())
    input_paths = ['docs/planning/fasciculos.json', 'docs/research/fuentes-tematicas.json',
                   'docs/research/publicadores-catalogo-nacional.json', 'docs/research/operaciones-ioe-detalladas.json',
                   'docs/research/datasets-catalogo-nacional.csv.gz', 'docs/research/datosgob-metadata.json.gz',
                   'public/data/ine-catalog.json', 'registry/products.json', 'registry/reviews.json']
    if territory_path.exists():
        input_paths.extend(['registry/territory-products.json', 'registry/local-territory.json', 'registry/section-archives.json', 'registry/cnig-history.json', 'public/data/territory/manifest.json', 'public/data/territory/official-wms.json', 'public/data/territory/official-layers.json', 'public/data/territory/section-vectors.json', 'public/data/territory/index.json', 'public/data/territory/comarcas.geojson', 'public/data/territory/bierzo-boundaries.json', 'public/data/territory/municipal-changes.json', 'registry/ign-territory-editions.json', 'public/data/territory/country.geojson', 'public/data/territory/country-atlas.geojson', 'public/data/territory/sea-atlas.geojson', 'public/data/territory/islets-atlas.geojson'])
    if demography_path.exists():
        input_paths.extend(['registry/demography-tables.json','registry/demography-products.json','public/data/demography/index.json','public/data/demography/inventory.json','public/data/nomenclator/index.json','public/data/intercensal/index.json'])
    if welfare_path.exists():
        input_paths.extend(['registry/welfare-tables.json','registry/welfare-external.json','registry/welfare-products.json','public/data/welfare/index.json','public/data/welfare/inventory.json'])
    if labor_path.exists():
        input_paths.extend(['registry/labor-tables.json','registry/labor-products.json','public/data/labor/index.json','public/data/labor/inventory.json','public/data/labor/sepe.json'])
    provenance = [dict(path=p, sha256=hashlib.sha256((ROOT / p).read_bytes()).hexdigest()) for p in input_paths]
    revisions=[registered['revision'], federated_metadata['revision']]
    for path in [territory_path,demography_path,welfare_path,labor_path]:
        if path.exists():revisions.append(read(path)['revision'])
    index = dict(schemaVersion=1, researchSnapshot='2026-11-05', revision=max(revisions),
                 scope='Registro de metadatos. Los inventarios se solapan y sus recuentos no se suman como productos únicos. Solo Disponibles contiene productos utilizables en el mapa.',
                 categories=categories, sources=sources, files=files, provenance=provenance,
                 statusLabels=registered['statusLabels'],
                 categoryCoverage=[dict(categoryId=c['id'], available=sum(c['id'] in p['categoryIds'] for p in products['available']),
                                        ioeCandidates=sum(c['id'] in p['suggestedCategoryIds'] for p in products['ioe']),
                                        status='parcial' if any(c['id'] in p['categoryIds'] for p in products['available']) else 'pendiente') for c in categories])
    atomic(OUT / 'index.json', encode(index))
    print(json.dumps({k: v['count'] for k, v in files.items()}))


if __name__ == '__main__':
    build()
