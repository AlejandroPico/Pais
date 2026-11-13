"""F02: complete INE tables, dictionary encoded and split for lazy consultation.

Only the standard library. No interpolation, temporal concatenation or geographic
allocation. Raw downloads are cached; every published shard has a content hash.
"""
import argparse
import concurrent.futures
import csv
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/f02'
OUT = ROOT / 'public/data/demography'
CONFIG = json.loads((ROOT / 'registry/demography-tables.json').read_text(encoding='utf-8'))
REFRESH = False
PROVENANCE = []

def encode(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def content_sha(path):
    h=hashlib.sha256()
    with gzip.open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if not unicodedata.combining(c)).strip()

def number(s):
    """Spanish INE format. Preserve absent/suppressed tokens independently of zero."""
    s = s.strip()
    if re.fullmatch(r'-?\d{1,3}(?:\.\d{3})*(?:,\d+)?|-?\d+(?:,\d+)?', s):
        f = float(s.replace('.', '').replace(',', '.'))
        return int(f) if f.is_integer() else f
    return None

def period_key(s):
    months = {'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'octubre':10,'noviembre':11,'diciembre':12}
    m = re.fullmatch(r'(\d{1,2}) de (\w+) de (\d{4})', s)
    if m:
        return f'{m[3]}-{months[m[2]]:02}-{int(m[1]):02}'
    if re.fullmatch(r'\d{4}(?:M\d{2}|T[1-4])?', s):
        return s
    raise ValueError('Unrecognized period: '+s)

def fetch(url):
    path = CACHE / (sha(url.encode())+'.gz')
    if REFRESH or not path.exists():
        tmp = path.with_suffix('.tmp')
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Pais-Atlas/0.4 (official open data)'}), timeout=240) as response, gzip.open(tmp, 'wb') as out:
                    shutil.copyfileobj(response, out)
                os.replace(tmp, path)
                break
            except Exception:
                tmp.unlink(missing_ok=True)
                if attempt == 3: raise
                time.sleep(2**attempt)
    h = hashlib.sha256()
    size = 0
    with gzip.open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b);size+=len(b)
    p = {'url':url,'sha256':h.hexdigest(),'bytes':size,'retrievedAt':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()}
    PROVENANCE.append(p)
    return path,p

def read_json(url):
    path,_ = fetch(url)
    b = gzip.decompress(path.read_bytes())
    try: return json.loads(b.decode('utf-8-sig'))
    except UnicodeDecodeError: return json.loads(b.decode('cp1252'))

def collect_inventory():
    def operation(oid):
        tables = {}
        for page in range(1,20):
            part=read_json(f'https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/{oid}?det=2&page={page}')
            assert isinstance(part,list), oid
            fresh=[t for t in part if t['Id'] not in tables]
            tables.update({t['Id']:t for t in fresh})
            if len(part)<500 or not fresh: break
        else: raise ValueError('Pagination not exhausted')
        return {'id':oid,'tables':list(tables.values())}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(operation,CONFIG['operationIds']))

GEO_HEADERS = {'total nacional':'national','provincias':'province','provincia':'province','comunidades y ciudades autonomas':'community','comunidades autonomas':'community','municipios':'municipal','islas':'island','isla':'island','secciones':'section','nacional':'national','provincia de inscripcion':'province'}
GEO_NAMES = {}
for level,file in [('province','provinces.geojson'),('community','communities.geojson')]:
    for f in json.loads((ROOT/'public/data'/file).read_text(encoding='utf-8'))['features']:
        p=f['properties'];GEO_NAMES[level,norm(p['name'])]=p['code']
# Names published without codes by older tables; only exact official alternatives.
for name,code in [('Álava','01'),('Araba/Álava','01'),('Alicante/Alacant','03'),('Castellón/Castelló','12'),('Coruña, A','15'),('Girona','17'),('Illes Balears','07'),('Rioja, La','26'),('Palmas, Las','35'),('Valencia/València','46'),('Bizkaia','48'),('Gipuzkoa','20')]:
    GEO_NAMES['province',norm(name)]=code
GEO_NAMES['province',norm('Balears, Illes')]='07'
for name,code in [('Asturias, Principado de','03'),('Balears, Illes','04'),('Castilla - La Mancha','08'),('Cataluña','09'),('Madrid, Comunidad de','13'),('Murcia, Región de','14'),('Navarra, Comunidad Foral de','15'),('País Vasco','16'),('Rioja, La','17'),('Ceuta','18'),('Melilla','19')]:
    GEO_NAMES['community',norm(name)]=code

def geography(values, geo_columns):
    candidates=[(i,level,values[i].strip()) for i,level in geo_columns if values[i].strip()]
    assert candidates, values
    _,level,label=candidates[-1]
    if norm(label) in ['total','total nacional','espana']:
        return 'national:ES',{'id':'national:ES','level':'national','code':'ES','name':'España'}
    code=re.match(r'^(\d{2,10})\s+',label)
    code=code[1] if code else GEO_NAMES.get((level,norm(label)))
    if level=='island':code=label
    if level=='municipal' and code in {'51','52'}:code+='001'
    if level=='national' or not code:
        # The source may contain "Extranjero" / "No consta". Keep, never map it.
        code=label
        level='unlocated'
    identity=level+':'+code
    return identity,{'id':identity,'level':level,'code':code,'name':label,'provinceCode':code[:2] if level in {'municipal','section'} else None,**({'municipalityCode':code[:5]} if level=='section' else {})}

def collect_table(config, metadata):
    tid=config['id'];url=f'https://www.ine.es/jaxiT3/files/t/es/csv_bd/{tid}.csv'
    path,provenance=fetch(url)
    dimensions=[];periods=[];territories=[];geo_ids={};period_ids={};dim_ids=[]
    geo_cache={}; period_labels={}
    temp=CACHE/('parts-'+str(tid));temp.mkdir(exist_ok=True)
    handles={};counts={};missing={};seen=set();finished=set();last_gid=None;row_count=0
    interleaved=config.get('interleaved',False)
    with gzip.open(path,'rt',encoding='utf-8-sig',newline='') as f:
        sample=f.read(2000);f.seek(0)
        delimiter='\t' if '\t' in sample.splitlines()[0] else ';'
        reader=csv.reader(f,delimiter=delimiter)
        headers=next(reader)
        assert headers[-1]=='Total' and 'Periodo' in headers, (tid,headers)
        pi=headers.index('Periodo');geo_columns=[(i,GEO_HEADERS[norm(h)]) for i,h in enumerate(headers) if norm(h) in GEO_HEADERS]
        assert geo_columns or config.get('national'),(tid,headers)
        di=[i for i,h in enumerate(headers[:-1]) if i!=pi and i not in [x[0] for x in geo_columns]]
        dimensions=[{'name':headers[i],'values':[]} for i in di];dim_ids=[{} for _ in di]
        for row in reader:
            if not row: continue
            assert len(row)==len(headers),(tid,row)
            geo_key=tuple(row[i] for i,_ in geo_columns)
            if geo_key not in geo_cache:
                geo_cache[geo_key]=geography(row,geo_columns) if geo_columns else geography(['Total Nacional'],[(0,'national')])
            gid,geo=geo_cache[geo_key]
            if not interleaved and gid!=last_gid:
                if last_gid is not None: finished.add(last_gid)
                assert gid not in finished,(tid,'Non-contiguous geography block',gid)
                seen.clear();last_gid=gid
            if gid not in geo_ids: geo_ids[gid]=len(territories);territories.append(geo)
            period=row[pi].strip()
            if period not in period_labels:period_labels[period]=period_key(period)
            key=period_labels[period]
            if key not in period_ids: period_ids[key]=len(periods);periods.append({'id':key,'label':period})
            record=[geo_ids[gid],period_ids[key]]
            for n,col in enumerate(di):
                value=row[col].strip()
                if value not in dim_ids[n]: dim_ids[n][value]=len(dimensions[n]['values']);dimensions[n]['values'].append(value)
                record.append(dim_ids[n][value])
            ident=tuple(record)
            assert ident not in seen, (tid,'Duplicate observation',ident)
            seen.add(ident)
            value=number(row[-1]);status='' if value is not None else row[-1].strip() or 'ausente'
            record.extend([value,status])
            if status: missing[status]=missing.get(status,0)+1
            part=geo['provinceCode'] if geo['level'] in {'municipal','section'} else 'main'
            if part not in handles: handles[part]=(temp/(part+'.jsonl')).open('wb');counts[part]=0
            handles[part].write(encode(record)+b'\n');counts[part]+=1;row_count+=1
    for h in handles.values(): h.close()
    shards=[]
    for part in sorted(handles):
        name=f'{tid}-{part}.json.gz';output=OUT/name
        # One bounded JSON shard, no repeated dimension labels in observations.
        with gzip.GzipFile(filename='',mode='wb',fileobj=output.open('wb'),mtime=0,compresslevel=config.get('compression',9)) as target:
            target.write(b'{"rows":[')
            with (temp/(part+'.jsonl')).open('rb') as source:
                first=True
                for line in source:
                    if not first: target.write(b',')
                    target.write(line.rstrip(b'\n'));first=False
            target.write(b']}')
        data=output.read_bytes()
        shards.append({'id':part,'file':name,'rows':counts[part],'bytes':len(data),'sha256':sha(data),'contentSha256':content_sha(output)})
    print(f'{tid}: {row_count:,} rows, {len(shards)} shards, {len(territories)} areas',flush=True)
    return {**config,'title':metadata['Nombre'],'sourceUrl':f'https://www.ine.es/jaxiT3/Tabla.htm?t={tid}','downloadUrl':url,'license':'CC BY 4.0 · INE', 'rows':row_count,'dimensions':dimensions,'periods':periods,'territories':territories,'shards':shards,'missingTokens':missing,'source':provenance}

def main(only=None):
    CACHE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    inventory=collect_inventory();metadata={t['Id']:t for op in inventory for t in op['tables']}
    (OUT/'inventory.json').write_bytes(encode({'reviewedAt':CONFIG['revision'],'operations':inventory,'scope':'Complete table metadata of the selected demographic operations; not all observations are integrated.'}))
    # Large municipal cubes are processed sequentially to bound memory usage.
    previous=json.loads((OUT/'index.json').read_text(encoding='utf-8')) if only else None
    old={t['id']:t for t in previous['tables']} if previous else {}
    tables=[collect_table(t,metadata[t['id']]) if not only or t['id'] in only else {**old[t['id']],**t} for t in CONFIG['tables']]
    for t in tables:
        for s in t['shards']:
            if 'contentSha256' not in s:s['contentSha256']=content_sha(OUT/s['file'])
    provenance={p['url']:p for p in (previous['provenance'] if previous else [])+PROVENANCE}
    index={'schemaVersion':1,'revision':CONFIG['revision'],'rowLayout':'territoryIndex,periodIndex,dimensionIndices...,value,statusToken','tables':tables,'inventoryTables':len(metadata),'operations':len(inventory),'provenance':sorted(provenance.values(),key=lambda p:p['url'])}
    (OUT/'index.json').write_bytes(encode(index))
    print('Complete:',sum(t['rows'] for t in tables),'observations',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');parser.add_argument('--only',help='Comma-separated table IDs; retain the others from the previous validated snapshot');args=parser.parse_args();REFRESH=args.refresh;main({int(i) for i in args.only.split(',')} if args.only else None)
