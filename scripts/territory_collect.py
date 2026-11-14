"""F01 official territory index and service inventory. Standard library only.

Raw responses stay in .cache. Committed data retain identifiers, reference dates,
provenance and differences between IGN cartographic areas and INE municipalities.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from ingest import simplify

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/f01'
OUT = ROOT / 'datos/territorio'
SHEET = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
PROVENANCE = []


def fetch(name, url, refresh=False):
    path = CACHE / (name + '.raw')
    CACHE.mkdir(parents=True, exist_ok=True)
    if refresh or not path.exists():
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Pais-Atlas/0.3'}), timeout=90) as r:
            body = r.read()
        tmp = path.with_suffix('.tmp')
        tmp.write_bytes(body)
        tmp.replace(path)
    body = path.read_bytes()
    PROVENANCE.append(dict(url=url, sha256=hashlib.sha256(body).hexdigest(), bytes=len(body),
                           retrievedAt=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()))
    return body


def sheets(body):
    z = zipfile.ZipFile(io.BytesIO(body))
    shared = [''.join(s.itertext()) for s in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', SHEET)]
    for name in sorted(n for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')):
        rows = []
        for row in ET.fromstring(z.read(name)).findall('.//s:row', SHEET):
            values = {}
            for cell in row:
                value = cell.findtext('s:v', namespaces=SHEET)
                if cell.attrib.get('t') == 's' and value is not None:
                    value = shared[int(value)]
                values[''.join(c for c in cell.attrib['r'] if c.isalpha())] = value or ''
            rows.append(values)
        yield rows


def save(path, obj):
    body = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_bytes(body)
    tmp.replace(path)


def municipal_index(refresh):
    base = 'https://www.ine.es/daco/daco42/codmun/'
    municipalities = {}
    for rows in sheets(fetch('diccionario26', base + 'diccionario26.xlsx', refresh)):
        for row in rows:
            if not row.get('A', '').isdigit() or not row.get('B', '').isdigit() or not row.get('C', '').isdigit():
                continue
            code = row['B'].zfill(2) + row['C'].zfill(3)
            municipalities[code] = dict(code=code, name=row['E'], provinceCode=row['B'].zfill(2),
                                         communityCode=row['A'].zfill(2), checkDigit=row['D'], referenceDate='2026-01-01')
    assert len(municipalities) > 8000
    islands, island_headings = {}, []
    for rows in sheets(fetch('26codislas', base + '26codislas.xlsx', refresh)):
        island_headings.append(rows[0].get('A', ''))
        for row in rows:
            if not row.get('A', '').isdigit() or not row.get('D', '').isdigit():
                continue
            code = row['A'].zfill(2) + row['D'].zfill(3)
            if code not in municipalities:
                continue
            island_id = row['B']
            municipalities[code]['islandId'] = island_id
            islands[island_id] = dict(id=island_id, name=row['C'], provinceCode=row['A'].zfill(2))
    units = json.loads(fetch('units-index', 'https://api-features.ign.es/collections/administrativeunit/items?f=json&limit=10000&skipGeometry=true', refresh))
    assert len(units['features']) == units['numberMatched'], 'IGN index truncated'
    unmatched = []
    for feature in units['features']:
        p = feature['properties']
        if p['nationallevelname'] != 'Municipio':
            continue
        code = p['nationalcode'][-5:]
        if code in municipalities:
            municipalities[code]['ignFeatureId'] = feature['id']
            if p['nameunit'] != municipalities[code]['name']:
                municipalities[code]['cartographicName'] = p['nameunit']
        else:
            unmatched.append(dict(ignFeatureId=feature['id'], code=code, name=p['nameunit'],
                                  classification='Área cartográfica IGN sin correspondencia en el catálogo municipal INE 2026'))
    assert len({m['code'] for m in municipalities.values()}) == len(municipalities)
    missing = [m['code'] for m in municipalities.values() if 'ignFeatureId' not in m]
    print('Municipalities', len(municipalities), 'unmatched IGN areas', len(unmatched), 'missing geometry IDs', len(missing), flush=True)
    return dict(referenceDate='2026-01-01', source=base+'diccionario26.xlsx', municipalities=list(municipalities.values()),
                islands=list(islands.values()), islandSource=base+'26codislas.xlsx', islandSourceHeadings=island_headings,
                supplementalAreas=unmatched, missingGeometryCodes=missing)


SERVICES = [
    ('ign-wms', 'IGN · Límites actuales e históricos', 'F006', 'https://www.ign.es/wms-inspire/unidades-administrativas', 'España'),
    ('ine-wms', 'INE · Secciones censales', 'F005', 'https://www.ine.es/geoserver/ows', 'España'),
    ('catastro', 'DGC · Cartografía catastral INSPIRE', 'F008', 'https://ovc.catastro.meh.es/cartografia/INSPIRE/spadgcwms.aspx', 'Ámbito DGC; excluye Navarra y País Vasco'),
    ('addresses', 'CartoCiudad · Direcciones y códigos postales', 'F007', 'https://www.cartociudad.es/wms-inspire/direcciones-ccpp', 'España'),
    ('comarca-canarias', 'Canarias · Cartografía estadística', 'F155', 'https://idecan2.grafcan.es/ServicioWMS/CARTO_EST', 'Canarias'),
    ('cadastre-navarra', 'Navarra · Parcelas catastrales', 'F165', 'https://inspire.navarra.es/services/CP/wms', 'Navarra'),
    ('cadastre-araba', 'Álava · Parcelas catastrales', 'F177', 'https://geo.araba.eus/WMS_INSPIRE_CP', 'Álava'),
    ('cadastre-bizkaia', 'Bizkaia · Catastro', 'F178', 'https://geo.bizkaia.eus/arcgisserverinspire/services/LurraldeAntolamendua_PlanificacionTerritorial/Katastro_Catastro/MapServer/WMSServer', 'Bizkaia'),
    ('cadastre-gipuzkoa', 'Gipuzkoa · Cartografía INSPIRE', 'F179', 'https://b5m.gipuzkoa.eus/inspire/wms/gipuzkoa_wms', 'Gipuzkoa'),
]


def service_inventory(entry, refresh):
    key, name, source, url, coverage = entry
    result = dict(id=key, name=name, sourceId=source, url=url, coverage=coverage)
    try:
        root = ET.fromstring(fetch(key, url+'?service=WMS&request=GetCapabilities', refresh))
        layers = []
        for layer in root.findall('.//{*}Layer'):
            code = layer.findtext('{*}Name')
            if not code:
                continue
            layers.append(dict(name=code, title=layer.findtext('{*}Title') or code,
                               queryable=layer.attrib.get('queryable') == '1',
                               styles=[s.findtext('{*}Name') for s in layer.findall('{*}Style')],
                               dimensions=[dict(**d.attrib, values=(d.text or '').strip()) for d in layer.findall('{*}Dimension')]))
        assert layers, 'No WMS layers advertised'
        result.update(status='verificado', layers=layers,
                      infoFormats=[f.text for f in root.findall('.//{*}GetFeatureInfo/{*}Format')])
    except Exception as e:
        result.update(status='bloqueado', error=str(e), nextAction='Revisar disponibilidad y condiciones del servicio oficial; no desactivar la comprobación TLS.')
    return result


def comarca_features(refresh):
    specs = [
        ('comarca-aragon', '02', 'Aragón', 'F152', 'Comarca administrativa', 'https://idearagon.aragon.es/geoserver/VISOR2D/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=Comarca_t2m&outputFormat=application/json&srsName=EPSG:4326', 'c_comarca', 'd_comarca'),
        ('comarca-navarra', '15', 'Navarra', 'F165', 'Demarcación comarcal del mapa local', 'https://idena.navarra.es/ogc/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=IDENA:ADMLOC_Pol_MapaLocalC&outputFormat=application/json&srsName=EPSG:4326', 'CCOMARCA', 'COMARCA'),
        ('comarca-valencia', '10', 'Comunitat Valenciana', 'F160', 'Delimitación comarcal cartográfica', 'https://terramapas.icv.gva.es/0105_Delimitaciones?request=GetFeature&service=WFS&version=2.0.0&typename=ICV.Comarcas&srsName=urn:ogc:def:crs:EPSG::4326&outputformat=geojson', 'cod_comarc', 'comarca'),
        ('comarca-euskadi', '16', 'Euskadi', 'F166', 'Comarca de geoEuskadi', 'https://www.geo.euskadi.eus/geoeuskadi/rest/services/U11/WFS_CARTOGRAFIA/MapServer/3/query?where=1%3D1&outFields=*&returnGeometry=true&outSR=4326&f=geojson', 'COM_COM', 'COMARCA'),
        ('comarca-galicia', '12', 'Galicia', 'F162', 'Delimitación comarcal', 'https://ideg.xunta.gal/servizos/rest/services/LimitesAdministrativos/LimitesAdministrativos/MapServer/9/query?where=1%3D1&outFields=*&returnGeometry=true&outSR=4326&f=geojson', 'CODCOM', 'COMARCA'),
    ]
    features, coverage = [], []
    for key, community, territory, source, kind, url, code_key, name_key in specs:
        try:
            data = json.loads(fetch(key, url, refresh))
            assert data['features']
            for f in data['features']:
                polygons = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
                code_value=(str(f['properties']['COM_PROV'])+'-'+str(f['properties'][code_key])) if source=='F166' else str(f['properties'][code_key])
                properties = dict(code=community+':'+code_value, name=f['properties'][name_key], communityCode=community, kind=kind, sourceId=source, sourceUrl=url.split('?')[0], snapshot='2026-11-09')
                features.append(dict(type='Feature', id=properties['code'], properties=properties,
                                     geometry=dict(type='MultiPolygon', coordinates=[[[[round(x,6),round(y,6)] for x,y,*_ in simplify(r,.0001)] for r in p] for p in polygons])))
            coverage.append(dict(territory=territory, sourceId=source, status='integrado', count=len(data['features']), kind=kind, url=url))
        except Exception as e:
            coverage.append(dict(territory=territory, sourceId=source, status='bloqueado', reason=str(e), url=url))
    # ArcGIS WFS advertises GML rather than GeoJSON. Retain its native identifiers.
    url='https://geoserveis.icgc.cat/servei/catalunya/divisions-administratives/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=divisions_administratives_wfs:divisions_administratives_comarques_5000&srsName=urn:ogc:def:crs:EPSG::4326'
    try:
        raw=fetch('comarca-catalunya-gml-5000',url,refresh)
        root=ET.fromstring(raw)
        if 'Exception' in root.tag:
            raise ValueError(ET.tostring(root,encoding='unicode')[:250])
        added=[]
        for member in root.findall('{*}member'):
            item=list(member)[0]
            fields={el.tag.split('}')[-1]:el.text for el in item if el.text and el.text.strip()}
            name=next((v for k,v in fields.items() if k.lower() in ['nomcomar','nom_comar','nom_comarca','nomcomarca','nom_com','nom']),None)
            code=next((v for k,v in fields.items() if k.lower() in ['codicomar','codi_comar','codi_comarca','codicomarca','codi_com','ccomarca','codi']),None)
            if not name or not code:
                raise ValueError('Review ICGC field schema: '+str(list(fields)))
            polys=[]
            for polygon in item.findall('.//{*}Polygon'):
                rings=[]
                for pos in polygon.findall('{*}exterior/{*}LinearRing/{*}posList')+polygon.findall('{*}interior/{*}LinearRing/{*}posList'):
                    vals=list(map(float,pos.text.split()));coords=[[vals[i+1],vals[i]] for i in range(0,len(vals),2)]
                    assert all(-1<x<5 and 39<y<44 for x,y in coords)
                    rings.append([[round(x,6),round(y,6)] for x,y in simplify(coords,.0001)])
                if rings:polys.append(rings)
            assert polys
            kind='Entidad territorial singular' if 'Aran' in name else 'Comarca administrativa'
            p=dict(code='09:'+code, name=name, communityCode='09', kind=kind, sourceId='F159', sourceUrl=url.split('?')[0], snapshot='2026-11-09')
            added.append(dict(type='Feature',id=p['code'],properties=p,geometry=dict(type='MultiPolygon',coordinates=polys)))
        assert len(added)>40
        features.extend(added)
        coverage.append(dict(territory='Cataluña',sourceId='F159',status='integrado',count=len(added),kind='Comarcas y entidad territorial singular',url=url))
    except Exception as e:
        coverage.append(dict(territory='Cataluña',sourceId='F159',status='bloqueado',reason=str(e),url=url))
    return dict(type='FeatureCollection',features=features),coverage


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
    index=municipal_index(args.refresh)
    with ThreadPoolExecutor(max_workers=4) as pool:
        services=list(pool.map(lambda s:service_inventory(s,args.refresh),SERVICES))
    comarcas,coverage=comarca_features(args.refresh)
    print('Services',[(s['id'],s['status'],len(s.get('layers',[]))) for s in services],flush=True)
    print('Comarcas',coverage,flush=True)
    assert len({f['id'] for f in comarcas['features']})==len(comarcas['features'])
    manifest=dict(schemaVersion=1,snapshot='2026-11-09',municipalReferenceDate=index['referenceDate'],
                  municipalCount=len(index['municipalities']), supplementalAreaCount=len(index['supplementalAreas']),
                  services=services,comarcaCoverage=coverage,provenance=sorted(PROVENANCE,key=lambda p:p['url']),
                  notes=['Las geometrías vivas y la relación municipal INE pueden tener fechas distintas.',
                         'No existe una jerarquía comarcal uniforme para toda España.',
                         'El año estadístico no modifica automáticamente la fecha de los límites.'])
    save(OUT/'index.json',index);save(OUT/'comarcas.geojson',comarcas);save(OUT/'manifest.json',manifest)


if __name__=='__main__':main()
