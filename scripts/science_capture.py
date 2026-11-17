"""Download the reviewed F12 source distributions into the temporary capture directory."""
from concurrent.futures import ThreadPoolExecutor
import json

from affiliation_collect import fetch
from science_collect import CACHE, ROOT, encode


def download(item):
    name,url=item
    try:
        fetch(url,CACHE/name,False)
        return name,None
    except OSError as error:
        return name,str(error)


def main():
    CACHE.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'registry/science-inputs.json').read_bytes())
    for family in ('ine','epo'):
        (CACHE/(family+('-tables.json' if family=='ine' else '-books.json'))).write_bytes(encode(manifest[family]))
    inputs=[('ine-'+key+'.px',row['download']) for key,row in manifest['ine'].items()]
    inputs.extend((key,row['url']) for key,row in manifest['epo'].items())
    inputs.extend((f'cdti-{year}.json',url) for year,url in manifest.get('cdti',{}).items())
    for key,url in manifest['eurostat'].items():
        inputs.append((key+'.json',url))
        (CACHE/(key+'.url')).write_text(url,encoding='utf-8')
    with ThreadPoolExecutor(max_workers=5) as pool:
        errors={name:error for name,error in pool.map(download,inputs) if error}
    (CACHE/'ine-errors.json').write_bytes(encode({name:value for name,value in errors.items() if name.startswith('ine-')}))
    print(len(inputs),'descargas identificadas ·',len(errors),'incidencias',flush=True)


if __name__=='__main__':
    main()
