"""Offline F02 registry. Availability follows preserved, checked cube manifests."""
import argparse
import hashlib
import gzip
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def main(kind="demography",category="F02"):
    index=read(f'public/data/{kind}/index.json');inventory=read(f'public/data/{kind}/inventory.json')
    if kind in {'welfare','labor'}:
        provenance={p['url']:p for p in index.get('provenance',[])}
        for t in index['tables']:
            missing={}
            coverage={s['id']:set() for s in t['sourceTables']}
            for a in t['territories']:
                province=a.get('provinceCode') or (a['code'] if a['level']=='province' else None)
                if province:
                    for source_id in a['sourceTableIds']:coverage[source_id].add(province)
            for a in t['territories']:
                specific=[sid for sid in a['sourceTableIds'] if len(coverage[sid])<=1]
                if specific:a['publicationTableId']=specific[0]
                elif a['level'] not in ['municipal','district','section']:a['publicationTableId']=t['id']
            for s in t['shards']:
                content=gzip.decompress((ROOT/f'public/data/{kind}'/s['file']).read_bytes())
                assert hashlib.sha256(content).hexdigest()==s['contentSha256']
                rows=json.loads(content)['rows'];assert len(rows)==s['rows']
                for r in rows:
                    if r[-3] is None:missing[r[-2]]=missing.get(r[-2],0)+1
            t['missingTokens']=missing
            for source in t['sourceTables']:provenance[source['url']]={k:v for k,v in source.items() if k!='id'}
        index['provenance']=sorted(provenance.values(),key=lambda p:p['url'])
        (ROOT/f'public/data/{kind}/index.json').write_text(json.dumps(index,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    if kind=='demography':
        shared = {}
        compact = {**index, 'tables': [], 'territoryGroups': shared}
        for table in index['tables']:
            fields = dict(table)
            territories = fields.pop('territories')
            digest = hashlib.sha256(json.dumps(territories, ensure_ascii=False, separators=(',',':')).encode()).hexdigest()
            shared.setdefault(digest, territories)
            fields['territoryGroup'] = digest
            compact['tables'].append(fields)
        payload = json.dumps(compact, ensure_ascii=False, separators=(',',':')).encode()
        (ROOT/'public/data/demography/viewer.json.gz').write_bytes(gzip.compress(payload, compresslevel=6, mtime=0))
    available=[]
    for t in index['tables']:
        for s in t['shards']:
            path=ROOT/f'public/data/{kind}'/s['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==s['sha256'],path
        assert sum(s['rows'] for s in t['shards'])==t['rows']
        periods=sorted(t['periods'],key=lambda p:p['id'])
        available.append(dict(id=kind+':'+str(t['id']),title=t['label'],sourceId='F005',categoryIds=[category],status='integrado',url=t['sourceUrl'],mapAction=kind+':'+str(t['id']),coverage=' · '.join({'national':'España','community':'Comunidades','province':'Provincias','municipal':'Municipios','district':'Distritos (series)','section':'Secciones (series)','island':'Islas (series)','unlocated':'Sin localización'}.get(l,l) for l in sorted({a['level'] for a in t['territories']})),period={'from':periods[0]['label'],'to':periods[-1]['label']},unit=t['unit'],license=t['license'],notes=t['note']+f" Tabla completa: {t['rows']:,} observaciones, todas las categorías y periodos de la descarga preservada. Detalle municipal por provincia cuando existe.",dataFile=f'{kind}/index.json'))
    canonical={str(source['id']):p for t,p in zip(index['tables'],available) for source in t.get('sourceTables',[{'id':t['id']}])}
    records={}
    for o in inventory['operations']:
        for t in o['tables']:
            key=str(t['Id'])
            if key not in records:
                records[key]=dict(id=kind+'-inventory:'+key,title=t['Nombre'],sourceId='F005',categoryIds=[],suggestedCategoryIds=[category],status='por_revisar',url='https://www.ine.es/jaxiT3/Tabla.htm?t='+key,license=None,operationIds=[],notes='Tabla anunciada en el inventario temático. Puede contener variables de otros fascículos. No implica descarga ni representación de sus observaciones.')
            records[key]['operationIds'].append(o['id'])
            if key in canonical:
                p=canonical[key];records[key].update(status='integrado',categoryIds=[category],license=p['license'],mapAction=p['mapAction'],period=p['period'],coverage=p['coverage'],notes=p['notes'],review={'implementedProductId':p['id'],'updatedAt':index['revision'],'reason':'Todas las observaciones de la descarga se conservan en cubos consultables; sin selección de columnas ni de último periodo.'})
    if kind=='welfare':records.update({p['id']:p for p in read('registry/welfare-external.json')['sources']})
    if kind=='demography':
        nomenclator=read('public/data/nomenclator/index.json')
        editions=nomenclator['editions']
        available.append(dict(
            id='demography:nomenclator',title='Nomenclátor · población por unidad poblacional',
            sourceId='F005',categoryIds=[category],status='integrado',url=nomenclator['source'],
            mapAction='nomenclator',coverage='Municipios, entidades y núcleos de población',
            period={'from':str(editions[0]['year']),'to':str(editions[-1]['year'])},
            unit='personas',license='CC BY 4.0 · INE',
            notes=f"{len(editions)} ediciones nacionales. Series consultables por provincia, año, nombre y código.",
            dataFile='nomenclator/index.json'))
        historical=read('public/data/intercensal/index.json')
        for part in historical['provinces'].values():
            path=ROOT/'public/data/intercensal'/part['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==part['sha256'],path
        available.append(dict(
            id='demography:historical-census',title='Censos históricos y alteraciones de municipios',
            sourceId='F005',categoryIds=[category],status='integrado',url=historical['source'],
            mapAction='historical-census',coverage='52 provincias y ciudades autónomas; municipios históricos y totales publicados',
            period={'from':'1842','to':'2021'},unit='personas y hogares',license='CC BY 4.0 · INE',
            notes=f"{historical['records']:,} fichas censales. Incluye recuentos, símbolos y notas de las alteraciones históricas.",
            dataFile='intercensal/index.json'))
    output={'revision':index['revision'],'available':available,'inventory':list(records.values())}
    (ROOT/f'registry/{kind}-products.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{category}: {len(available)} available products; {len(records)} discovery records')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--kind',default='demography');parser.add_argument('--category',default='F02');args=parser.parse_args();main(args.kind,args.category)
