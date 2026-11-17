"""Download the reviewed F11 inputs listed in the repository."""
from concurrent.futures import ThreadPoolExecutor
import json
from urllib.request import Request, urlopen

from education_collect import CACHE, EUROSTAT_TITLES, ROOT, encode

MANIFEST = ROOT/'registry/education-inputs.json'


def capture(item):
    name, url = item
    destination = CACHE/name
    try:
        if not destination.exists():
            request = Request(url,headers={'User-Agent':'Pais Atlas (public education statistics)'})
            with urlopen(request,timeout=45) as response:
                raw = response.read()
            if '.px' in name and b'AXIS-VERSION' not in raw[:512]:
                raise ValueError('La respuesta no contiene una tabla PC-Axis.')
            destination.write_bytes(raw)
    except (ValueError, OSError) as error:
        return name,str(error)[:180]
    return name,None


def main():
    CACHE.mkdir(parents=True,exist_ok=True)
    manifest = json.loads(MANIFEST.read_bytes())
    tables = manifest['pcAxis']
    (CACHE/'tables.json').write_bytes(encode(tables))
    work = [(name,table['download']) for name,table in tables.items()]
    for code in EUROSTAT_TITLES:
        url = manifest['eurostat'][code]
        (CACHE/(code+'.url')).write_text(url,encoding='utf-8')
        work.append((code+'.json',url))
    with ThreadPoolExecutor(max_workers=5) as pool:
        errors={name:error for name,error in pool.map(capture,work) if error}
    (CACHE/'download-errors.json').write_bytes(encode(errors))
    print('Distribuciones revisadas:',len(work),'· Incidencias:',len(errors),flush=True)


if __name__=='__main__':
    main()
