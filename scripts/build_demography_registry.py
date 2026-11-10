"""Offline F02 registry. Availability follows preserved, checked cube manifests."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def main():
    index=read('public/data/demography/index.json');inventory=read('public/data/demography/inventory.json')
    available=[]
    for t in index['tables']:
        for s in t['shards']:
            path=ROOT/'public/data/demography'/s['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==s['sha256'],path
        assert sum(s['rows'] for s in t['shards'])==t['rows']
        periods=sorted(t['periods'],key=lambda p:p['id'])
        available.append(dict(id='demography:'+str(t['id']),title=t['label'],sourceId='F005',categoryIds=['F02'],status='integrado',url=t['sourceUrl'],mapAction='demography:'+str(t['id']),coverage=' · '.join(sorted({a['level'] for a in t['territories']})),period={'from':periods[0]['label'],'to':periods[-1]['label']},unit=t['unit'],license=t['license'],notes=t['note']+f" Tabla completa: {t['rows']:,} observaciones, todas las categorías y periodos de la descarga preservada. Detalle municipal por provincia cuando existe.",dataFile='demography/index.json'))
    canonical={p['id'].split(':')[1]:p for p in available}
    records={}
    for o in inventory['operations']:
        for t in o['tables']:
            key=str(t['Id'])
            if key not in records:
                records[key]=dict(id='demographic-inventory:'+key,title=t['Nombre'],sourceId='F005',categoryIds=[],suggestedCategoryIds=['F02'],status='por_revisar',url='https://www.ine.es/jaxiT3/Tabla.htm?t='+key,license=None,operationIds=[],notes='Tabla anunciada en una operación demográfica. Puede contener variables de otros fascículos. No implica descarga ni representación de sus observaciones.')
            records[key]['operationIds'].append(o['id'])
            if key in canonical:
                p=canonical[key];records[key].update(status='integrado',categoryIds=['F02'],license=p['license'],mapAction=p['mapAction'],period=p['period'],coverage=p['coverage'],notes=p['notes'],review={'implementedProductId':p['id'],'updatedAt':index['revision'],'reason':'Todas las observaciones de la descarga se conservan en cubos consultables; sin selección de columnas ni de último periodo.'})
    output={'revision':index['revision'],'available':available,'inventory':list(records.values())}
    (ROOT/'registry/demography-products.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'F02: {len(available)} complete tables; {len(records)} discovery records')

if __name__=='__main__':main()
