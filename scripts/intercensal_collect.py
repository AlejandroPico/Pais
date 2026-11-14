"""Capture all pages of the INE historical census tables, by province."""
import argparse
import concurrent.futures
import hashlib
import html
from http.cookiejar import CookieJar
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode, urljoin
from urllib.request import build_opener, HTTPCookieProcessor, Request

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://www.ine.es/intercensal/'
QUERY = SOURCE + 'intercensal.do'
DOWNLOAD = SOURCE + 'download.do?typeDownload=3&descargarformato=Ir'
CACHE = ROOT / '.cache/f02/intercensal'
OUT = ROOT / 'datos/poblacion/intercensal'


def request(opener, url, fields=None):
    data = urlencode(fields).encode() if fields else None
    req = Request(url, data, headers={'User-Agent': 'El Pais Atlas (official public census tables)'})
    with opener.open(req, timeout=70) as response:
        return response.read().decode(response.headers.get_content_charset() or 'utf-8')


def capture(code, region, refresh):
    path = CACHE / (code + '.json')
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding='utf-8'))
    fields = {'search': '2', 'cmbCCAA': str(int(region)), 'cmbProv': str(int(code))}
    for attempt in range(3):
        try:
            opener = build_opener(HTTPCookieProcessor(CookieJar()))
            menu = request(opener, QUERY+'?nocab=1', {**fields, 'btnBuscarMuni': 'Consultar municipios'})
            select = re.search(r'<select[^>]*name="cmbMuni"[^>]*>(.*?)</select>', menu, re.I | re.S)
            if not select:
                raise ValueError((code, region, 'missing municipal selector'))
            expected = len(re.findall(r'<option\b', select[1], re.I))
            page = request(opener, QUERY, {**fields, 'btnBuscarGeo': 'Consultar selección'})
            pages = []
            while True:
                csv = request(opener, DOWNLOAD)
                if not csv.startswith('Alteraciones de los municipios'):
                    raise ValueError((code, 'invalid download'))
                pages.append(csv)
                next_page = re.search(r'<form name="formNext" action="([^"]+)"', page, re.I)
                if not next_page:
                    break
                if len(pages) > expected // 50 + 2:
                    raise ValueError((code, 'pagination loop'))
                page = request(opener, urljoin(SOURCE, html.unescape(next_page[1].replace("&regFin=", "&amp;regFin="))), {'search': '2', 'btnNext': 'Siguientes'})
            entries = [block.strip() for csv in pages for block in re.split(r'\n(?=Provincia: )', csv.replace('\r\n','\n'))[1:]]
            entries = [re.split(r'\n\s*NOTAS\b', block, maxsplit=1)[0].strip() for block in entries]
            if len(entries) != expected or len({e.splitlines()[0] for e in entries}) != expected:
                raise ValueError((code, expected, len(entries), 'missing or duplicate entries'))
            notes = re.search(r'\nNOTAS\s*\n(.*)', pages[-1], re.S)
            result = {'entries': entries, 'notes': notes[1].strip() if notes else '', 'pages': len(pages),
                      'sourceHashes': [hashlib.sha256(csv.encode('utf-8')).hexdigest() for csv in pages]}
            path.write_text(json.dumps(result,ensure_ascii=False), encoding='utf-8')
            print(code, len(entries), len(pages), flush=True)
            return result
        except (OSError, UnicodeError, ValueError) as error:
            if attempt == 2:
                raise RuntimeError(f'Provincia {code}') from error
            time.sleep(2 ** attempt)


def main(refresh=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    provinces = json.loads((ROOT/'datos/territorio/provinces.geojson').read_text(encoding='utf-8'))['features']
    # The historical application uses INE community codes, including both autonomous cities.
    territories = [(f['properties']['code'],f['properties']['communityCode']) for f in provinces if 1 <= int(f['properties']['code']) <= 52]
    if {code for code, _ in territories} != {f'{n:02d}' for n in range(1, 53)}:
        raise ValueError('No se encontraron las 52 provincias y ciudades autónomas del INE')
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {code:pool.submit(capture,code,region,refresh) for code,region in territories}
        results = {code:future.result() for code,future in futures.items()}
    descriptors = {}
    for code, result in results.items():
        file = code + '.json'
        payload = json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()
        (OUT/file).write_bytes(payload)
        descriptors[code] = {'file':file,'count':len(result['entries']),'sha256':hashlib.sha256(payload).hexdigest()}
    index = {'source':SOURCE,'provinces':descriptors,'records':sum(p['count'] for p in descriptors.values())}
    (OUT/'index.json').write_text(json.dumps(index,ensure_ascii=False), encoding='utf-8')
    print('Registros históricos:', index['records'], flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
