"""Capture the IGN services and official municipal boundaries used by El Bierzo."""
import argparse
import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor

import territory_collect as territory

LAW = 'https://www.boe.es/buscar/act.php?id=BOE-A-1991-9704'
GEOMETRY = 'https://api-features.ign.es/collections/administrativeunit/items/'
SERVICES = [
    ('pnoa-historico', 'IGN · Ortofotografía histórica', 'F006', 'https://www.ign.es/wms/pnoa-historico', 'Por vuelo y edición'),
    ('lidar-mdt', 'IGN · Modelo Digital del Terreno', 'F006', 'https://servicios.idee.es/wms-inspire/mdt', 'España'),
]

def normalized(name):
    return ''.join(c for c in unicodedata.normalize('NFD', name.casefold().strip()) if not unicodedata.combining(c))

def capture(refresh):
    manifest_path = territory.OUT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    index = json.loads((territory.OUT / 'index.json').read_text(encoding='utf-8'))
    names = {normalized(row['name']): row for row in index['municipalities'] if row['provinceCode'] == '24'}
    names['candin'] = names['valle de ancares']
    source = territory.fetch('bierzo-boe', LAW, refresh).decode('utf-8')
    match = re.search(r'La Comarca de El Bierzo est[aá] integrada por los municipios siguientes:\s*(.*?)\.</p>', source, flags=re.S)
    if not match:
        raise ValueError('No se encontró la relación de municipios en el BOE')
    members = re.split(r',\s*|\s+y\s+(?=Villafranca)', match.group(1))
    municipalities = [names[normalized(member)] for member in members]
    if len({row['code'] for row in municipalities}) != 38:
        raise ValueError('La relación de El Bierzo no contiene 38 municipios distintos')
    def polygon(row):
        source_url = GEOMETRY+str(row['ignFeatureId'])+'?f=json'
        feature = json.loads(territory.fetch('bierzo-'+row['code'], source_url, refresh))
        if feature['geometry']['type'] not in {'Polygon','MultiPolygon'}:
            raise ValueError(source_url)
        return {'code':row['code'],'sourceUrl':source_url,'geometry':feature['geometry']}
    with ThreadPoolExecutor(max_workers=6) as pool:
        boundaries = list(pool.map(polygon,municipalities))
        services = list(pool.map(lambda entry: territory.service_inventory(entry,refresh),SERVICES))
    if any(s['status']!='verificado' for s in services):
        raise ValueError(services)
    current = {s['id']:s for s in manifest['services']}
    current.update({s['id']:s for s in services})
    manifest['services'] = list(current.values())
    editions = {}
    for family, service_id in [('orthophoto', 'pnoa-historico'), ('elevation', 'lidar-mdt'), ('canary', 'comarca-canarias')]:
        excluded = {'WMS_CARTO_EST', 'ALJTUR2015', 'CME1', 'CME2'} if family == 'canary' else set()
        editions[family] = [
            {'id': layer['name'], 'name': layer['title'], 'queryable': layer['queryable']}
            for layer in current[service_id]['layers'] if layer['name'] not in excluded
        ]
    registry = territory.ROOT / 'registry' / 'ign-territory-editions.json'
    registry.write_text(json.dumps(editions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

    provenance = {p['url']:p for p in manifest['provenance']}
    provenance.update({p['url']:p for p in territory.PROVENANCE})
    manifest['provenance'] = sorted(provenance.values(),key=lambda row:row['url'])
    territory.save(territory.OUT/'bierzo-boundaries.json',{'law':LAW,'boundaries':boundaries})
    territory.save(manifest_path,manifest)
    print('El Bierzo:',len(boundaries),'municipios. Servicios:',[(s['id'],len(s['layers']),s['infoFormats']) for s in services])

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    capture(parser.parse_args().refresh)
