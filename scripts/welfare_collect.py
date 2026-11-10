"""F03: complete, metadata-bearing INE JSON responses; grouped territorial cubes.

The API is used without nult, date or tv filters. CSV exports are deliberately
not substituted: a reviewed Atlas CSV did not match its API geography.
"""
import argparse
import concurrent.futures
import codecs
import gzip
import json
import math
import os
import sqlite3
import tempfile
from pathlib import Path
import demography_collect as core

ROOT=core.ROOT
OUT=ROOT/'public/data/welfare'
CONFIG=json.loads((ROOT/'registry/welfare-tables.json').read_text(encoding='utf-8'))
core.CONFIG=CONFIG
core.CACHE=ROOT/'.cache/f03'
GEO={**core.GEO_HEADERS,'distritos':'district','secciones':'section','comunidad autonoma de residencia':'community','ambito geografico':'national','totales territoriales':'national'}
NAMES={'SALDOS CONTABLES':'Indicador','Indicadores de renta media':'Indicador','Indicadores de renta media y mediana':'Indicador','Semiintervalos de edad':'Grupos de edad'}

def area(meta):
    candidates=[(GEO[core.norm(m['T3_Variable'])],m) for m in meta if core.norm(m['T3_Variable']) in GEO]
    if not candidates:return {'id':'national:ES','level':'national','code':'ES','name':'España'}
    rank={'national':0,'community':1,'province':2,'island':3,'municipal':4,'district':5,'section':6}
    level,m=max(candidates,key=lambda c:rank[c[0]])
    name=m['Nombre'];code=str(m.get('Codigo') or '').strip()
    if core.norm(name) in ['total','total nacional','espana','total comunidades autonomas'] or code=='00':return {'id':'national:ES','level':'national','code':'ES','name':'España'}
    if not code:code=core.GEO_NAMES.get((level,core.norm(name)))
    if not code and level=='island':code=name
    if not code:raise ValueError('Unresolved geography '+repr(m))
    if code.isdigit():code=code.zfill({'community':2,'province':2,'municipal':5,'district':7,'section':10}.get(level,len(code)))
    return {'id':level+':'+code,'level':level,'code':code,'name':name,'provinceCode':code[:2] if level in ['municipal','district','section'] else None,'municipalityCode':code[:5] if level in ['district','section'] else None}

def fetch_table(tid):
    url=f'https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{tid}?tip=AM'
    path,provenance=core.fetch(url)
    return tid,path,provenance

def iter_series(path):
    """Bounded streaming reader for a top-level JSON array, no extra packages."""
    with gzip.open(path,'rb') as source:sample=source.read(16384)
    try:codecs.getincrementaldecoder('utf-8-sig')().decode(sample,final=False);encoding='utf-8-sig'
    except UnicodeDecodeError:encoding='cp1252'
    decoder=json.JSONDecoder();buffer='';pos=0;eof=False;started=False
    with gzip.open(path,'rt',encoding=encoding) as source:
        while True:
            if pos>=len(buffer):
                buffer=source.read(65536);pos=0
                if not buffer:raise ValueError('Truncated JSON array')
            while pos<len(buffer) and buffer[pos].isspace():pos+=1
            if pos>=len(buffer):continue
            if not started:
                assert buffer[pos]=='[','Expected series array';pos+=1;started=True;continue
            if buffer[pos]==',':pos+=1;continue
            if buffer[pos]==']':return
            try:value,end=decoder.raw_decode(buffer,pos)
            except json.JSONDecodeError:
                more=source.read(65536)
                if not more:raise
                buffer=buffer[pos:]+more;pos=0;continue
            yield value;pos=end
            if pos>1048576:buffer=buffer[pos:];pos=0

def infer_units(combinations,dimension_names):
    keys=list(range(len(dimension_names)))
    # Drop irrelevant dimensions only when the mapping remains unambiguous.
    def mapping(indices):
        result={}
        for dims,unit in combinations:
            k=tuple(dims[i] for i in indices)
            if k in result and result[k]!=unit:return None
            result[k]=unit
        return result
    assert mapping(keys) is not None,'Units differ for identical dimension signatures'
    for i in list(keys):
        candidate=[x for x in keys if x!=i]
        if mapping(candidate) is not None:keys=candidate
    rules=mapping(keys)
    if not keys:return next(iter(rules.values())),[]
    return 'Según indicador y escala publicados',[{'when':{dimension_names[i]:dims[j] for j,i in enumerate(keys)},'unit':unit} for dims,unit in rules.items()]

def build_group(config,table_ids,metadata,recover_rows=None):
    tid=config['id'];work=Path(tempfile.gettempdir())/'Pais-F03';work.mkdir(exist_ok=True)
    # Keep the scratch database outside cloud-synced project directories.
    dbpath=work/f'cube-{tid}-{os.getpid()}.sqlite'
    dbpath.unlink(missing_ok=True)
    db=sqlite3.connect(dbpath);db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF')
    db.execute('CREATE TABLE observations (g INTEGER,p INTEGER,d TEXT,v REAL,status TEXT,src INTEGER,unit TEXT,PRIMARY KEY(g,p,d)) WITHOUT ROWID')
    territories=[];geo_ids={};periods=[];period_ids={};dimension_names=None;dimensions=[];dim_ids=[];sources=[];raw_rows=0;duplicates=0;combinations={};aliases={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        # A bounded batch avoids retaining every downloaded table in memory.
        for start in range(0,len(table_ids),3):
            for input_id,path,provenance in pool.map(fetch_table,table_ids[start:start+3]):
                sources.append({'id':input_id,**provenance})
                series_count=0
                for s in iter_series(path):
                    series_count+=1
                    meta=s.get('MetaData',[]);assert meta,(input_id,'Missing metadata')
                    a=area(meta)
                    if a['id'] not in geo_ids:geo_ids[a['id']]=len(territories);territories.append({**a,'sourceTableIds':[]})
                    g=geo_ids[a['id']]
                    if input_id not in territories[g]['sourceTableIds']:territories[g]['sourceTableIds'].append(input_id)
                    non_geo=[m for m in meta if core.norm(m['T3_Variable']) not in GEO]
                    def dimension_name(m):
                        name=m['T3_Variable']
                        # These published EPF tables have one classification
                        # dimension. The API uses different hierarchy variables
                        # for its total, aggregates and detailed categories.
                        role=config.get('classificationDimension')
                        if role and core.norm(name)!='tipo de dato' and not core.norm(name).startswith('gastos '):
                            aliases[name]=role
                            return role
                        # The total of the four-digit table is labelled using
                        # the parent classification in the API; keep it as Total.
                        if input_id==73993 and name in ['Clases COICOP/EPF','Subgrupos COICOP/EPF']:return 'Clasificación de gasto COICOP/EPF'
                        name=NAMES.get(name,name)
                        return aliases.get(name,name)
                    pairs={dimension_name(m):m['Nombre'] for m in non_geo}
                    assert len(pairs)==len(non_geo),(input_id,'Conflicting dimension aliases')
                    if dimension_names is None:
                        dimension_names=list(pairs);dimensions=[{'name':n,'values':[]} for n in dimension_names];dim_ids=[{} for _ in dimension_names]
                    if set(pairs)!=set(dimension_names):
                        missing=set(dimension_names)-set(pairs);extra=set(pairs)-set(dimension_names)
                        # Some INE totals use a separate variable (e.g. Totales
                        # de edad). Only align an unambiguous single Total slot.
                        if len(missing)==len(extra)==1:
                            old=next(iter(missing));new=next(iter(extra));i=dimension_names.index(old)
                            total=lambda v:core.norm(v) in ['total','todos','todas las edades','ambos sexos']
                            if total(pairs[new]):
                                aliases[new]=old;pairs[old]=pairs.pop(new)
                            elif dimensions[i]['values'] and all(total(v) for v in dimensions[i]['values']):
                                aliases[old]=new
                                for a,target in list(aliases.items()):
                                    if target==old:aliases[a]=new
                                dimension_names[i]=new;dimensions[i]['name']=new
                    assert set(pairs)==set(dimension_names),(input_id,'Dimension mismatch',pairs,dimension_names)
                    ds=[]
                    for i,name in enumerate(dimension_names):
                        value=pairs[name]
                        if value not in dim_ids[i]:dim_ids[i][value]=len(dimensions[i]['values']);dimensions[i]['values'].append(value)
                        ds.append(dim_ids[i][value])
                    signature=core.encode(ds).decode()
                    unit=str(s.get('T3_Unidad') or 'Sin unidad publicada').strip();scale=str(s.get('T3_Escala') or '').strip()
                    if scale and core.norm(scale) not in ['unidades','unidad']:unit=scale+' · '+unit
                    labels=tuple(pairs[n] for n in dimension_names)
                    assert labels not in combinations or combinations[labels]==unit,(tid,'Ambiguous unit',labels,unit)
                    combinations[labels]=unit
                    for datum in s.get('Data',[]):
                        assert datum.get('T3_Periodo') in ['A','Anual'],(tid,'Non-annual period',datum)
                        key=str(datum['Anyo']);label=key
                        if config.get('incomeOffset') is not None:label+=f" · ingresos de {int(key)+config['incomeOffset']}"
                        if key not in period_ids:period_ids[key]=len(periods);periods.append({'id':key,'label':label})
                        value=datum.get('Valor');assert value is None or isinstance(value,(int,float)) and math.isfinite(value),(tid,value)
                        status=str(datum.get('T3_TipoDato') or '')
                        if value is None:status='Sin dato'+(' · '+status if status else '')
                        raw_rows+=1
                        if recover_rows is not None:continue
                        inserted=db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?,?)',(g,period_ids[key],signature,value,status,input_id,unit))
                        if not inserted.rowcount:
                            old=db.execute('SELECT v,status,src FROM observations WHERE g=? AND p=? AND d=?',(g,period_ids[key],signature)).fetchone()
                            assert old[0]==value,(tid,'Conflicting observations',a,key,pairs,old,value,input_id)
                            duplicates+=1
                assert series_count,(input_id,'Empty response')
                db.commit();print(f'INE {input_id}: {series_count:,} complete series',flush=True)
    unit,rules=infer_units(list(combinations.items()),dimension_names or [])
    shards=[];files={};counts={}
    if recover_rows is not None:
        for path in sorted(OUT.glob(f'{tid}-*.json.gz')):
            data=path.read_bytes();rows=json.loads(gzip.decompress(data))['rows'];part=path.name[len(str(tid))+1:].split('.')[0]
            assert all(len(r)==len(dimensions)+5 and 0<=r[0]<len(territories) and 0<=r[1]<len(periods) for r in rows),'Recovered dictionaries do not match'
            shards.append({'id':part,'file':path.name,'rows':len(rows),'bytes':len(data),'sha256':core.sha(data),'contentSha256':core.content_sha(path)})
        counts={s['id']:s['rows'] for s in shards};assert sum(counts.values())==recover_rows,'Incomplete recovered group'
        duplicates=raw_rows-recover_rows
    for g,p,d,v,status,src in db.execute('SELECT g,p,d,v,status,src FROM observations ORDER BY g,p,d'):
        a=territories[g];part=a['provinceCode'] if a['level'] in ['municipal','district','section'] else 'main'
        if part not in files:
            filename=f'{tid}-{part}.json.gz';handle=gzip.GzipFile(filename='',mode='wb',fileobj=(OUT/filename).open('wb'),mtime=0);handle.write(b'{"rows":[');files[part]=(filename,handle);counts[part]=0
        if counts[part]:files[part][1].write(b',')
        files[part][1].write(core.encode([g,p,*json.loads(d),v,status,src]));counts[part]+=1
    for part,(filename,handle) in files.items():
        handle.write(b']}');handle.close();path=OUT/filename;data=path.read_bytes()
        shards.append({'id':part,'file':filename,'rows':counts[part],'bytes':len(data),'sha256':core.sha(data),'contentSha256':core.content_sha(path)})
    db.close();dbpath.unlink(missing_ok=True);assert counts,(tid,'No observations')
    result={**config,'title':metadata[tid]['Nombre'],'unit':unit,'unitsByConditions':rules,'dimensionAliases':aliases,'sourceUrl':f'https://www.ine.es/jaxiT3/Tabla.htm?t={tid}','downloadUrl':sources[0]['url'],'license':'CC BY 4.0 · INE','rows':sum(counts.values()),'rawRows':raw_rows,'duplicateRows':duplicates,'dimensions':dimensions,'periods':periods,'territories':territories,'shards':shards,'sourceTables':sources,'missingTokens':{},'publisher':'INE'}
    print(f'F03 group {tid}: {result["rows"]:,} observations / {len(territories):,} areas',flush=True)
    return result

def main(refresh=False,recover=None):
    OUT.mkdir(parents=True,exist_ok=True);core.CACHE.mkdir(parents=True,exist_ok=True);core.REFRESH=refresh
    inventory=core.collect_inventory();metadata={t['Id']:t for o in inventory for t in o['tables']}
    (OUT/'inventory.json').write_bytes(core.encode({'revision':CONFIG['revision'],'operations':inventory}))
    tables=[]
    for config in CONFIG['tables']:
        ids=[config['id']]
        if config['id']==53689:
            ids=[t['Id'] for o in inventory if o['id']==353 for t in o['tables'] if t['Nombre']=='Indicadores de renta media y mediana']
            ids=[53689]+[i for i in ids if i!=53689]
        checkpoint=core.CACHE/f'group-{config["id"]}.json'
        fingerprint=core.sha(core.encode({'format':1,'config':config,'ids':ids}))
        previous=json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() and not refresh else None
        if previous and previous.get('fingerprint')==fingerprint and all((OUT/s['file']).exists() and core.sha((OUT/s['file']).read_bytes())==s['sha256'] for s in previous['table']['shards']):
            tables.append(previous['table']);print(f'Reused complete group {config["id"]}',flush=True)
        else:
            table=build_group(config,ids,metadata,(recover or {}).get(config['id']));tables.append(table)
            checkpoint.write_bytes(core.encode({'fingerprint':fingerprint,'table':table}))
    index={'schemaVersion':1,'revision':CONFIG['revision'],'rowLayout':'territoryIndex,periodIndex,dimensionIndices...,value,statusToken,sourceTableId','tables':tables,'inventoryTables':len(metadata),'operations':len(inventory),'provenance':sorted(core.PROVENANCE,key=lambda p:p['url'])}
    (OUT/'index.json').write_bytes(core.encode(index));print('F03 complete:',sum(t['rows'] for t in tables),'observations',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');parser.add_argument('--recover',help='Explicit completed group id:rowcount; rebuild dictionaries while verifying preserved shards');args=parser.parse_args();main(args.refresh,{int(p.split(':')[0]):int(p.split(':')[1]) for p in args.recover.split(',')} if args.recover else None)
