"""Preserve all national INE Nomenclátor editions in province files."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/f02/nomenclator'
OUT = ROOT / 'datos/territorio/nomenclator'
SOURCE = 'https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177010&idp=1254735572981'
DOWNLOAD = 'https://www.ine.es/nomen2/Descarga'

def fetch(year, refresh):
    path = CACHE / f'{year}.zip'
    if refresh or not path.exists():
        request = Request(DOWNLOAD, data=urlencode({'anioNacional': year}).encode(), headers={'Referer':SOURCE})
        with urlopen(request, timeout=90) as response:
            body = response.read()
        with ZipFile(io.BytesIO(body)) as archive:
            assert archive.namelist(), year
        path.write_bytes(body)
    return path

def parse(path):
    year = int(path.stem)
    encoding = 'utf-8' if year >= 2024 else 'cp1252'
    id_width = 9 if year == 1981 else 11
    with ZipFile(path) as archive:
        for member in archive.namelist():
            if member.lower().endswith(('.xls','.xlsx')):
                continue
            measure = next((key for key in ('edad','naci','sex') if member.endswith('_'+key+'.txt')), 'sex')
            numeric_width = 28 if year == 1981 or measure == 'edad' else 21
            with archive.open(member) as body:
                for raw in body:
                    line = raw.decode(encoding).rstrip('\r\n')
                    code = line[:id_width]
                    name = line[id_width:-numeric_width].strip()
                    values = [int(line[offset:offset+7]) for offset in range(len(line)-numeric_width,len(line),7)]
                    assert code.isdigit() and name and all(value>=0 for value in values), (year,member,code)
                    if year != 1981:
                        assert values[0] == sum(values[1:]), (year,member,code,values)
                    yield code, name, measure, values

def encode(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()

def main(refresh=False):
    CACHE.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    with urlopen(SOURCE,timeout=30) as response:
        page=response.read().decode('utf-8')
    selector=re.search(r'<select[^>]*id="anioNacional"[^>]*>(.*?)</select>',page,re.S)
    assert selector, 'No se encontró el selector nacional'
    years=sorted({int(year) for year in re.findall(r'<option value="(\d{4})">',selector[1])})
    assert years, 'El INE no devolvió ediciones'
    with ThreadPoolExecutor(max_workers=5) as pool:
        paths=list(pool.map(lambda year:fetch(year,refresh),years))
    temporary=CACHE/'provinces'
    temporary.mkdir(exist_ok=True)
    files={}
    editions=[]
    try:
        for path in paths:
            year=int(path.stem)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            stamp=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()
            counts={}
            for code,name,measure,values in parse(path):
                province=code[:2]
                if province not in files:
                    files[province]=(temporary/(province+'.jsonl')).open('wb')
                files[province].write(encode([code,year,name,measure,*values])+b'\n')
                counts[measure]=counts.get(measure,0)+1
            assert counts
            editions.append({'year':year,'archiveSha256':digest,'retrievedAt':stamp,'files':counts})
            print('Nomenclátor',year,counts,flush=True)
    finally:
        for stream in files.values():
            stream.close()
    parts={}
    for province in sorted(files):
        name=province+'.json.gz'
        content=(temporary/(province+'.jsonl')).read_bytes()
        packed=gzip.compress(content,mtime=0)
        (OUT/name).write_bytes(packed)
        parts[province]={'file':name,'rows':content.count(b'\n'),'contentSha256':hashlib.sha256(content).hexdigest()}
    (OUT/'index.json').write_bytes(encode({'source':SOURCE,'editions':editions,'provinces':parts}))
    print('Total:',sum(part['rows'] for part in parts.values()),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
