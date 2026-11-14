"""Discover base-cartography WMS services and verify their browser map responses."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
import math
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

import territory_collect as territory

DIRECTORY = 'https://www.idee.es/web/idee/segun-tipo-de-servicio'
ORIGIN = 'https://alejandropico.github.io'
REGIONS = {
    'andalucia': 'F151', 'aragon': 'F152', 'principado de asturias': 'F153', 'illes balears': 'F154',
    'canarias': 'F155', 'cantabria': 'F156', 'castilla y leon': 'F157', 'castilla-la mancha': 'F158',
    'cataluna / catalunya': 'F159', 'comunitat valenciana': 'F160', 'extremadura': 'F161', 'galicia': 'F162',
    'comunidad de madrid': 'F163', 'region de murcia': 'F164', 'comunidad foral de navarra': 'F165',
    'pais vasco / euskadi': 'F166', 'la rioja': 'F167', 'ceuta': 'F168', 'melilla': 'F169',
}
EXPLICIT = [
    ('F165', 'Navarra', 'Edificios INSPIRE', 'https://inspire.navarra.es/services/BU/wms', 'catastro'),
    ('F165', 'Navarra', 'Direcciones INSPIRE', 'https://inspire.navarra.es/services/AD/wms', 'catastro'),
    ('F177', 'Álava', 'Edificios INSPIRE', 'https://geo.araba.eus/WMS_INSPIRE_BU', 'catastro'),
    ('F177', 'Álava', 'Catastro foral', 'https://geo.araba.eus/WMS_Katastroa', 'catastro'),
    ('F177', 'Álava', 'Divisiones administrativas INSPIRE', 'https://geo.araba.eus/WMS_INSPIRE_AU', 'divisiones'),
    ('F177', 'Álava', 'Cartografía base y divisiones', 'https://geo.araba.eus/WMS_Lurraldea', 'base'),
    ('F006', 'España', 'Fototeca', 'https://wms-fototeca.idee.es/fototeca', 'imagen'),
    ('F006', 'España', 'Mosaicos de satélite históricos', 'https://wms-satelites-historicos.idee.es/satelites-historicos', 'imagen'),
    ('F006', 'España', 'Ortofotos provisionales PNOA', 'https://wms-pnoa.idee.es/pnoa-provisionales', 'imagen'),
    ('F006', 'España', 'Cartografía ráster del IGN', 'https://www.ign.es/wms-inspire/mapa-raster', 'base'),
    ('F006', 'España', 'Cuadrículas cartográficas', 'https://www.ign.es/wms-inspire/cuadriculas', 'base'),
    ('F006', 'España', 'Hojas kilométricas', 'https://www.ign.es/wms/hojas-kilometricas', 'base'),
    ('F006', 'España', 'Planimetrías', 'https://www.ign.es/wms/minutas-cartograficas', 'base'),
    ('F006', 'España', 'Primera edición del MTN', 'https://www.ign.es/wms/primera-edicion-mtn', 'base'),
    ('F006', 'España', 'Redes geodésicas', 'https://www.ign.es/wms-inspire/redes-geodesicas', 'base'),
    ('F006', 'España', 'Nomenclátor geográfico', 'https://www.ign.es/wms-inspire/ngbe', 'base'),
    ('F006', 'España', 'Modelo digital de pendientes', 'https://wms-pendientes.idee.es/pendientes', 'relieve'),
]


def normalized(value):
    return unicodedata.normalize('NFKD', value.casefold()).encode('ascii', 'ignore').decode()


def family(title):
    title = normalized(title)
    if re.search(r'ndvi|ordenacion del litoral|vulnerabilidad|geotecn|catastro minero|plantaciones|incendio|residuos|patrimonio|escolar|sanitari|policial', title):
        return None
    for key, pattern in [
        ('imagen', r'ortofot|ortoimagen|ortoimagene|fototeca|fotografia aerea|mosaicos de satelite'),
        ('divisiones', r'limites administr|divisiones administr|delimitaciones territoriales|limites municipal|comarcal|distritos y barrios|secciones censales|seccionado censal|entidades locales menores|demarcaciones municipales'),
        ('relieve', r'modelo digital (?:del terreno|de elevac|de superficie|sombreado|de pendientes)|^relieve|\blidar\b|curvas de nivel|hipsometr'),
        ('catastro', r'parcelas catastral|catastro|edificios inspire|direcciones inspire'),
        ('base', r'cartografia basica|cartografia de referencia|mapa base|mapa topografico|nomenclator geografico|cuadriculas cartograficas|callejero|planimetria|redes geodesicas|toponimia|cartografia urbana'),
    ]:
        if re.search(pattern, title):
            return key
    return None


def endpoint(url, **params):
    parts = urlsplit(url)
    keys = {key.lower() for key in params}
    query = [(key, value) for key, value in parse_qsl(parts.query) if key.lower() not in keys]
    return urlunsplit(parts._replace(query=urlencode([*query, *params.items()]), fragment=''))


def clean_url(url):
    parts = urlsplit(html.unescape(url))
    query = [(key, value) for key, value in parse_qsl(parts.query) if key.lower() not in {'service', 'request', 'version'}]
    return urlunsplit(parts._replace(scheme='https', path=re.sub(r'/+', '/', parts.path), query=urlencode(query), fragment=''))


def walk(node, context=()):
    label = node.get('name')
    context = (*context, label) if label else context
    for row in node.get('listserv', []):
        yield context, row
    for key in ('listorg', 'listsuborg'):
        for child in node.get(key, []):
            yield from walk(child, context)


def discover(refresh):
    page = territory.fetch('idee-directory', DIRECTORY, refresh).decode('utf-8')
    template = re.search(r'var url="([^"]+p_p_lifecycle=2[^"]+)"', page)[1]
    portlet = dict(parse_qsl(urlsplit(template).query))['p_p_id']
    tasks = [('supVisWmsEst', 'est'), ('supVisWmsAut', 'aut'), ('supVisWmsLoc', 'loc')]
    found = {}
    for tab, scope in tasks:
        url = endpoint(template, **{f'_{portlet}_id': tab, f'_{portlet}_actionName': 'cargaTablaSrv'})
        data = json.loads(territory.fetch(f'idee-{tab}', url, refresh))
        for org in data['datos'][scope]:
            for context, row in walk(org):
                title = row['name'].strip()
                group = family(title)
                if not group or not row['url'].startswith(('https://', 'http://')):
                    continue
                url = clean_url(row['url'])
                if '/rest/services/' in url.lower() or url.endswith('.xml'):
                    continue
                region = context[0] if scope != 'est' else 'España'
                source = REGIONS.get(normalized(region), 'F004')
                found.setdefault(url, (source, region, title, url, group))
    for entry in EXPLICIT:
        found[entry[3]] = entry
    return found


def bounds(layer):
    box = layer.find('{*}EX_GeographicBoundingBox')
    if box is not None:
        result = [float(box.findtext('{*}'+name)) for name in ('westBoundLongitude','southBoundLatitude','eastBoundLongitude','northBoundLatitude')]
    else:
        box = layer.find('{*}LatLonBoundingBox')
        if box is None:
            return None
        result = [float(box.attrib[name]) for name in ('minx','miny','maxx','maxy')]
    if all(map(math.isfinite,result)) and result[0] < result[2] and result[1] < result[3]:
        return result


def layers(node, inherited=(), box=None, queryable=False, dimensions=None):
    crs = {*inherited, *(word for child in node.findall('{*}CRS')+node.findall('{*}SRS') for word in (child.text or '').split())}
    box = bounds(node) or box
    queryable = node.attrib.get('queryable', str(int(queryable))) in {'1', 'true'}
    dims = {**(dimensions or {}), **{d.attrib.get('name',''): {**d.attrib, 'values': (d.text or '').strip()} for d in node.findall('{*}Dimension')}}
    children = node.findall('{*}Layer')
    name = node.findtext('{*}Name')
    if name:
        yield dict(name=name, title=node.findtext('{*}Title') or name, queryable=queryable, bounds=box,
                   crs=sorted(crs), container=bool(children), dimensions=list(dims.values()))
    for child in children:
        yield from layers(child, crs, box, queryable, dims)


def mercator(x, y):
    y = min(85.051, max(-85.051, y))
    return 6378137*math.radians(x), 6378137*math.asinh(math.tan(math.radians(y)))


def verify(url, layer, box, version, arcgis=False):
    box = [max(-19,box[0]),max(27,box[1]),min(5,box[2]),min(44,box[3])]
    if box[0]>=box[2] or box[1]>=box[3]:
        return 'Extensión fuera de España'
    x1,y1 = mercator(box[0], box[1])
    x2,y2 = mercator(box[2], box[3])
    test = endpoint(url, SERVICE='WMS', REQUEST='GetMap', VERSION=version, LAYERS=layer, STYLES='',
                    FORMAT='image/png', TRANSPARENT='TRUE', WIDTH=64, HEIGHT=64,
                    **{('CRS' if version=='1.3.0' else 'SRS'): 'EPSG:3857'},
                    BBOX=','.join(map(str,(x1,y1,x2,y2))))
    if arcgis:
        test = endpoint(url, f='image', format='png32', transparent='true', bboxSR=3857, imageSR=3857,
                        size='64,64', layers='show:'+layer, bbox=','.join(map(str,(x1,y1,x2,y2))))
    with urlopen(Request(test,headers={'Origin':ORIGIN,'User-Agent':'Pais Atlas (public WMS)'}),timeout=8) as r:
        if r.read(8) != b'\x89PNG\r\n\x1a\n':
            return 'GetMap no devuelve PNG'
        if r.headers.get('Access-Control-Allow-Origin') not in {'*',ORIGIN}:
            return 'GetMap no permite la lectura desde el visor público'
    return None


def probe(url, layer, version, arcgis=False):
    try:
        return verify(url, layer['name'], layer['bounds'], version, arcgis)
    except Exception as error:
        return str(error)


def capture(entry, refresh):
    source, region, title, url, group = entry
    key = hashlib.sha256(url.encode()).hexdigest()[:15]
    info = dict(id='idee-'+key, sourceId=source, region=region, title=title, url=url, group=group, layers=[])
    try:
        capabilities = endpoint(url, SERVICE='WMS', REQUEST='GetCapabilities', VERSION='1.3.0')
        data = territory.fetch(info['id'], capabilities, refresh)
        root = ET.fromstring(data)
        capability = root.find('{*}Capability')
        if capability is None:
            raise ValueError('respuesta sin capacidades WMS')
        version = root.attrib.get('version')
        if version not in {'1.3.0','1.1.1'}:
            raise ValueError('versión WMS incompatible')
        info['version'] = version
        info['infoFormats'] = [f.text for f in capability.findall('{*}Request/{*}GetFeatureInfo/{*}Format')]
        info['capabilities'] = capabilities
        records = []
        for base in capability.findall('{*}Layer'):
            records.extend(layers(base))
        if not records:
            raise ValueError('el servicio no anuncia capas con nombre')
        info['layers'] = records
        leaves = [layer for layer in records if not layer['container'] and 'EPSG:3857' in layer['crs'] and layer['bounds']]
        if not leaves:
            raise ValueError('no ofrece capas con extensión y EPSG:3857')
        sample = leaves[0]
        problem = probe(url, sample, version)
        if problem:
            raise ValueError(problem)
        info.update(status='verificado', sample=sample['name'])
    except Exception as error:
        info.update(status='bloqueado', error=str(error))
    return info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    entries = discover(args.refresh)
    old = json.loads((territory.OUT/'manifest.json').read_bytes())
    covered = {clean_url(service['url']) for service in old['services'] if service['status']=='verificado'}
    candidates = [entry for url, entry in entries.items() if url not in covered]
    print('Servicios candidatos:',len(candidates),flush=True)
    previous_path = territory.OUT/'official-wms.json'
    previous = {s['url']:s for s in json.loads(previous_path.read_bytes())['services']} if previous_path.exists() else {}
    def get(entry):
        existing = previous.get(entry[3])
        if existing and not args.refresh and existing.get('version'):
            return existing
        return capture(entry, args.refresh)
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(get,candidates))
    jobs = []
    for service in results:
        for layer in service['layers']:
            layer['group'] = family(layer['title'])
            if not layer['group'] and len(service['layers']) <= 12:
                layer['group'] = service['group']
            if layer['group'] and not layer['container'] and 'EPSG:3857' in layer['crs'] and layer['bounds'] and service.get('version'):
                if service['status']=='verificado' or service.get('error') in {'GetMap no devuelve PNG','The read operation timed out'}:
                    if args.refresh or 'mapError' not in layer or layer['mapError'] is not None:
                        jobs.append((service,layer))
    arcgis_jobs = []
    for service in results:
        parts=urlsplit(service['url'])
        if parts.hostname!='ideg.xunta.gal' or not parts.path.lower().endswith('/mapserver/wmsserver'):
            continue
        image_url=urlunsplit(parts._replace(path=parts.path.replace('/servizos/services/','/servizos/rest/services/').rsplit('/',1)[0]+'/export'))
        for layer in service['layers']:
            if layer['group'] and not layer['container'] and layer['bounds'] and layer['name'].isdigit():
                arcgis_jobs.append((image_url,layer))
    print('Capas candidatas:',len(jobs)+len(arcgis_jobs),flush=True)
    with ThreadPoolExecutor(max_workers=24) as pool:
        errors = pool.map(lambda pair:probe(pair[0]['url'],pair[1],pair[0]['version']), jobs)
        for (service,layer),error in zip(jobs,errors):
            layer['mapError'] = error
        errors=pool.map(lambda pair:probe(pair[0],pair[1],None,True),arcgis_jobs)
        for (url,layer),error in zip(arcgis_jobs,errors):
            if not error:
                layer['tileEndpoint']=url
            layer['mapError']=error
    print('Capas verificadas:',sum('mapError' in layer and layer['mapError'] is None for service in results for layer in service['layers']),flush=True)
    provenance={row['url']:row for row in old.get('provenance',[])}
    if previous_path.exists():
        provenance.update({row['url']:row for row in json.loads(previous_path.read_bytes()).get('provenance',[])})
    provenance.update({row['url']:row for row in territory.PROVENANCE})
    data = dict(source=DIRECTORY, revision='2026-11-14', services=results,
                provenance=sorted(provenance.values(),key=lambda row:row['url']))
    territory.save(territory.OUT/'official-wms.json',data)
    print('Verificados:',sum(s['status']=='verificado' for s in results),flush=True)


if __name__ == '__main__':
    main()
