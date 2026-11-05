"""Reproducible official-source ingestion. Python standard library only.

Raw HTTP responses are cached locally; committed outputs include provenance hashes.
No statistical interpolation, geographic inference or invented observations.
"""
import concurrent.futures as futures
import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public' / 'data'
CACHE = ROOT / '.cache'
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(exist_ok=True)
PROVENANCE = []
REFRESH = False
INE = 'https://servicios.ine.es/wstempus/js/ES/'
NS = {'au': 'http://inspire.ec.europa.eu/schemas/au/4.0', 'gml': 'http://www.opengis.net/gml/3.2', 'gn': 'http://inspire.ec.europa.eu/schemas/gn/4.0', 'wfs': 'http://www.opengis.net/wfs/2.0'}

def fetch(url):
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + '.raw')
    if REFRESH or not path.exists():
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Pais-OpenAtlas/0.1'}), timeout=180) as response:
                    body = response.read()
                path.write_bytes(body)
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
    body = path.read_bytes()
    PROVENANCE.append({'url': url, 'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body), 'retrievedAt': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()})
    return body

def js(url):
    body = fetch(url)
    try:
        return json.loads(body.decode('utf-8-sig'))
    except UnicodeDecodeError:
        return json.loads(body.decode('windows-1252'))

def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

def simplify(points, tolerance=0.00025):
    # Iterative Douglas-Peucker, ~28 m latitude; same tolerance at all admin levels.
    if len(points) <= 4:
        return points
    keep = {0, len(points)-1}
    stack = [(0, len(points)-1)]
    while stack:
        a, b = stack.pop()
        x, y = points[a]
        dx, dy = points[b][0]-x, points[b][1]-y
        length = dx*dx+dy*dy
        best, index = 0, a
        for i in range(a+1, b):
            px, py = points[i]
            t = max(0, min(1, ((px-x)*dx+(py-y)*dy)/length)) if length else 0
            d = (px-x-t*dx)**2+(py-y-t*dy)**2
            if d > best:
                best, index = d, i
        if best > tolerance*tolerance:
            keep.add(index)
            stack.extend([(a, index), (index, b)])
    result = [points[i] for i in sorted(keep)]
    return result if len(result) >= 4 else points

def ring_area(ring):
    # Spherical area (km²). Kept separate from simplification, approximate denominator.
    return abs(sum(math.radians(b[0]-a[0]) * (2+math.sin(math.radians(a[1]))+math.sin(math.radians(b[1]))) for a, b in zip(ring, ring[1:])) * 6371.0088**2 / 2)

def boundaries(order, filename):
    filter_xml = f'<fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:au="{NS["au"]}" xmlns:xlink="http://www.w3.org/1999/xlink"><fes:PropertyIsEqualTo><fes:ValueReference>au:nationalLevel/@xlink:href</fes:ValueReference><fes:Literal>https://inspire.ec.europa.eu/codelist/AdministrativeHierarchyLevel/{order}Order</fes:Literal></fes:PropertyIsEqualTo></fes:Filter>'
    query = urllib.parse.urlencode({'service':'WFS','request':'GetFeature','version':'2.0.0','typenames':'au:AdministrativeUnit','count':100,'filter':filter_xml})
    url = 'https://www.ign.es/wfs-inspire/unidades-administrativas?' + query
    root = ET.fromstring(fetch(url))
    if 'Exception' in root.tag:
        raise RuntimeError(ET.tostring(root, encoding='unicode'))
    features = []
    for unit in root.findall('wfs:member/au:AdministrativeUnit', NS):
        national = unit.findtext('au:nationalCode', namespaces=NS)
        polygons, area = [], 0
        for poly in unit.findall('.//gml:Polygon', NS):
            rings = []
            for ring in poly.findall('gml:exterior/gml:LinearRing/gml:posList', NS) + poly.findall('gml:interior/gml:LinearRing/gml:posList', NS):
                values = [float(v) for v in ring.text.split()]
                coords = [[values[i+1], values[i]] for i in range(0, len(values), 2)]
                area += ring_area(coords) * (1 if not rings else -1)
                rings.append(simplify(coords))
            if rings:
                polygons.append(rings)
        code = national[4:6] if order == '3rd' else national[2:4]
        features.append({'type':'Feature','id':code,'properties':{'code':code,'name':unit.findtext('.//gn:text', namespaces=NS),'communityCode':national[2:4],'areaKm2':round(area,3)},'geometry':{'type':'MultiPolygon','coordinates':polygons}})
    # IGN also publishes code 54 / community 20: territories not attached to a province.
    expected = 53 if order == '3rd' else 20
    assert len(features) == expected, (filename, len(features), ET.tostring(root,encoding='unicode')[:300])
    save(filename, {'type':'FeatureCollection','features':features})
    print(f'{filename}: {len(features)} territories', flush=True)

def population():
    result = {}
    for table, level in [(2852,'province'), (2853,'community')]:
        rows = js(INE+f'DATOS_TABLA/{table}?tip=AM')
        grouped = {}
        for row in rows:
            meta = row['MetaData']
            geo = next((m for m in meta if m['T3_Variable'] in ('Provincias','Comunidades y Ciudades Autónomas')), None)
            sex = next((m for m in meta if m['T3_Variable'] == 'Sexo'), None)
            if not geo or not sex:
                continue
            code = str(geo['Codigo']).zfill(2)
            territory = grouped.setdefault(code, {'name':geo['Nombre'],'series':{}})
            for datum in row['Data']:
                if datum['Valor'] is not None:
                    territory['series'].setdefault(str(datum['Anyo']), {})[sex['Codigo']] = datum['Valor']
        result[level] = grouped
        print(f'Population {level}: {len(grouped)} series groups; variables: {sorted({m["T3_Variable"] for r in rows for m in r["MetaData"]})}', flush=True)
    assert len(result['province']) == 53, len(result['province'])
    assert len(result['community']) == 20, len(result['community'])
    save('population.json', {'source':'INE · Padrón municipal · tablas 2852 y 2853','sourceUrl':'https://www.ine.es/jaxiT3/Tabla.htm?t=2852','license':'CC BY 4.0','note':'Serie histórica publicada 1996–2021. No hay observación de 1997. No se interpolan años ni se mezcla con otras operaciones. Densidad aproximada calculada con superficie esférica IGN actual; no reconstruye límites históricos.','data':result})

def catalog():
    def operations_list(query):
        entries = js(INE+'OPERACIONES_DISPONIBLES?'+query)
        page, last_size = 2, len(entries)
        while last_size == 500:
            chunk = js(INE+'OPERACIONES_DISPONIBLES?'+query+f'&page={page}')
            if not chunk:
                break
            assert not {o['Id'] for o in entries}.intersection(o['Id'] for o in chunk), 'Repeated page in operation inventory'
            entries.extend(chunk)
            page, last_size = page+1, len(chunk)
        return entries
    operations = operations_list('det=2')
    geographic = {o['Id'] for o in operations_list('geo=1')}
    errors = []
    def tables(op):
        try:
            # Paginate explicitly: API defaults must not silently truncate the inventory.
            all_tables, page = [], 1
            while True:
                chunk = js(INE+f'TABLAS_OPERACION/{op["Id"]}?det=2&page={page}')
                if not isinstance(chunk, list):
                    raise ValueError(str(chunk)[:200])
                existing = {t['Id'] for t in all_tables}
                fresh = [t for t in chunk if t['Id'] not in existing]
                all_tables.extend(fresh)
                if len(chunk) < 500 or not fresh:
                    break
                page += 1
            return {**op,'geographic':op['Id'] in geographic,'tables':all_tables}
        except Exception as error:
            errors.append({'operation':op['Id'],'error':str(error)})
            return {**op,'geographic':op['Id'] in geographic,'tables':[],'error':str(error)}
    with futures.ThreadPoolExecutor(max_workers=4) as pool:
        entries = list(pool.map(tables, operations))
    save('ine-catalog.json', {'sourceUrl':'https://www.ine.es/dyngs/DAB/es/index.htm?cid=1100','license':'CC BY 4.0','generatedAt':datetime.now(timezone.utc).isoformat(),'scope':'Inventario de operaciones y tablas expuesto por la API JSON INE. No equivale a haber descargado o cartografiado todas las observaciones de INEbase.','operations':entries,'errors':errors})
    print(f'INE catalog: {len(entries)} operations, {sum(len(o["tables"]) for o in entries)} table references, {len(errors)} errors', flush=True)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', choices=['geo','population','catalog'])
    parser.add_argument('--refresh', action='store_true', help='Revalidate remote sources instead of using the raw response cache')
    args = parser.parse_args()
    REFRESH = args.refresh
    if args.only in (None,'geo'):
        boundaries('3rd','provinces.geojson')
        boundaries('2nd','communities.geojson')
        import subprocess
        subprocess.run(['node', str(ROOT / 'scripts' / 'mask.mjs')], check=True)
    if args.only in (None,'population'):
        population()
    if args.only in (None,'catalog'):
        catalog()
    previous_path = OUT / 'provenance.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else []
    save('provenance.json', list({p['url']:p for p in previous+PROVENANCE}.values()))
