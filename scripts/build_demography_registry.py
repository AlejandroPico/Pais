"""Offline F02 registry. Availability follows preserved, checked cube manifests."""
import argparse
import hashlib
import gzip
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def main(kind="demography",category="F02"):
    folder = {'demography': 'poblacion/ine', 'welfare': 'renta/ine', 'labor': 'trabajo/ine', 'care': 'cuidados/ine', 'housing':'vivienda/ine'}[kind]
    index=read(f'datos/{folder}/index.json');inventory=read(f'datos/{folder}/inventory.json')
    if kind in {'welfare','labor','care','housing'}:
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
                content=gzip.decompress((ROOT/f'datos/{folder}'/s['file']).read_bytes())
                assert hashlib.sha256(content).hexdigest()==s['contentSha256']
                rows=json.loads(content)['rows'];assert len(rows)==s['rows']
                for r in rows:
                    if r[-3] is None:missing[r[-2]]=missing.get(r[-2],0)+1
            t['missingTokens']=missing
            for source in t['sourceTables']:provenance[source['url']]={k:v for k,v in source.items() if k!='id'}
        index['provenance']=sorted(provenance.values(),key=lambda p:p['url'])
        (ROOT/f'datos/{folder}/index.json').write_text(json.dumps(index,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    if kind=='labor':
        index['tables'] += read('datos/trabajo/sepe/sepe.json')['tables']
        index['tables'] += read('datos/trabajo/seguridad-social/index.json')['tables']
    if kind in {'demography','welfare','housing'}:
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
        (ROOT/'datos'/folder/'viewer.json.gz').write_bytes(gzip.compress(payload, compresslevel=6, mtime=0))
    if kind=='welfare':
        index['tables'] += read('datos/renta/aeat/index.json')['tables']
    if kind=='care':
        for name in ('imserso', 'seguridad-social'):
            index['tables'] += read(f'datos/cuidados/{name}/index.json')['tables']
    if kind=='housing':
        index['tables'] += read('datos/vivienda/mivau/index.json')['tables']
    available=[]
    for t in index['tables']:
        table_folder = t.get('dataFolder') or ('trabajo/sepe' if t.get('compactColumns') else folder)
        for s in t['shards']:
            path=ROOT/'datos'/table_folder/s['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==s['sha256'],path
        assert sum(s['rows'] for s in t['shards'])==t['rows']
        periods=sorted(t['periods'],key=lambda p:p['id'])
        filename = ('sepe.json' if t.get('publisher')=='SEPE'
                    else 'viewer.json.gz' if table_folder == folder and kind in {'demography','welfare','housing'}
                    else 'index.json')
        available.append(dict(id=kind+':'+str(t['id']),title=t['label'],sourceId=t.get('sourceId','F005'),categoryIds=[category],status='integrado',url=t['sourceUrl'],mapAction=kind+':'+str(t['id']),coverage=' · '.join({'national':'España','community':'Comunidades','province':'Provincias','municipal':'Municipios','district':'Distritos (series)','section':'Secciones (series)','island':'Islas (series)','unlocated':'Sin localización'}.get(l,l) for l in sorted({a['level'] for a in t['territories']})),period={'from':periods[0]['label'],'to':periods[-1]['label']},unit=t['unit'],license=t['license'],notes=t['note']+f" Tabla completa: {t['rows']:,} observaciones, todas las categorías y periodos de la descarga preservada. Detalle municipal por provincia cuando existe.",dataFile=f'{table_folder}/{filename}'))
    canonical={str(source['id']):p for t,p in zip(index['tables'],available) if p['sourceId']=='F005' for source in t.get('sourceTables',[{'id':t['id']}])}
    for table, product in zip(index['tables'], available, strict=True):
        for alias in table.get('equivalentDownloadIds', []):
            url=f'https://www.ine.es/jaxiT3/files/t/es/csv_bd/{alias}.csv'
            source=next(item for item in index['provenance'] if item['url']==url)
            assert source['sha256']==table['source']['sha256'], (table['id'], alias)
            canonical[str(alias)]=product
    records={}
    for o in inventory['operations']:
        for t in o['tables']:
            key=str(t['Id'])
            if key not in records:
                records[key]=dict(id=kind+'-inventory:'+key,title=t['Nombre'],sourceId='F005',categoryIds=[],suggestedCategoryIds=[category],status='por_revisar',url='https://www.ine.es/jaxiT3/Tabla.htm?t='+key,license=None,operationIds=[],notes='Tabla anunciada en el inventario temático. Puede contener variables de otros fascículos. No implica descarga ni representación de sus observaciones.')
            records[key]['operationIds'].append(o['id'])
            if key in canonical:
                p=canonical[key];records[key].update(url=t.get('sourceUrl',records[key]['url']),status='integrado',categoryIds=[category],license=p['license'],mapAction=p['mapAction'],period=p['period'],coverage=p['coverage'],notes=p['notes'],review={'implementedProductId':p['id'],'updatedAt':index['revision'],'reason':'Todas las observaciones de la descarga se conservan en cubos consultables; sin selección de columnas ni de último periodo.'})
    if kind=='welfare':
        records.update({p['id']:p for p in read('registry/welfare-external.json')['sources']})
        record=records['aeat:anuario-irpf-municipal']
        product=next(p for p in available if p['id']=='welfare:920001')
        record.update(status='integrado',mapAction=product['mapAction'],coverage=product['coverage'],
                      period=product['period'],license=product['license'],notes=product['notes'],
                      review=dict(implementedProductId=product['id'],updatedAt=index['revision'],
                                  reason='Observaciones contrastadas con el diccionario oficial del Anuario.'))
    if kind=='labor':
        for item in read('registry/labor-tables.json').get('emptyDistributions', []):
            key=str(item['id'])
            if key in canonical:
                continue
            reason=f"La API del INE devuelve cero series y la exportación CSV tiene {item['csv']['emptyCells']} celdas vacías."
            records[key].update(status='bloqueado',categoryIds=[category],notes=reason,
                links={'API oficial':item['api']['url'],'CSV oficial':item['csv']['url']},
                review=dict(updatedAt=index['revision'],reason=reason,
                            nextAction='Volver a comprobar la publicación del INE en la próxima actualización.'))
        for t,p in zip(index['tables'],available,strict=True):
            if not t.get('compactColumns'):
                continue
            for edition in t['sourceTables']:
                id=f"labor-{t['publisher'].lower()}:{t['id']}:{edition['id']}"
                records[id]=dict(p,id=id,title=f"{p['title']} · {edition['year']}",url=edition['url'],
                    period=' · '.join(edition['periods']),review=dict(implementedProductId=p['id'],
                    updatedAt=index['revision'],reason=f'Serie de {t['publisher']} preservada con sus desgloses y estados.'))
    if kind=='care':
        for table, product in zip(index['tables'], available, strict=True):
            if table.get('publisher') not in {'IMSERSO', 'INSS'}:
                continue
            for source in table['sourceTables']:
                path = ROOT/'datos'/table['dataFolder']/source['originalFile']
                assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256'], path
                edition = source['edition']
                id = f"{table['publisher'].lower()}:{table['id']}:{edition}"
                records[id] = dict(product, id=id, title=f"{product['title']} · {edition}", url=source['url'],
                    review=dict(implementedProductId=product['id'], updatedAt=index['revision'],
                                reason=f"Original de {table['publisher']} conservado y consultable. Edición {edition}."))
                if table['publisher'] == 'INSS':
                    records[id]['period'] = {'from': edition, 'to': edition}
    if kind=='housing':
        for table, product in zip(index['tables'], available, strict=True):
            if table.get('publisher') != 'MIVAU':
                continue
            source = table['sourceTables'][0]
            id = f"mivau:{table['id']}"
            records[id] = dict(product, id=id,
                links={'CSV oficial':source['url'],'Metodología':table['methodologyUrl']},
                review=dict(implementedProductId=product['id'],updatedAt=index['revision'],
                            reason='Todos los indicadores y ámbitos de esta distribución se pueden consultar.'))
        for tid, reason in read('registry/housing-tables.json').get('excluded', {}).items():
            records[tid].update(status='no_procede',categoryIds=[category],notes=reason,
                                review=dict(updatedAt=index['revision'],reason=reason))
        siu=read('datos/vivienda/siu/layers.json')
        for layer in siu['layers'] + siu['unavailable']:
            provider=layer['provider']
            id='housing:siu:'+layer['id']
            fields={'Capa oficial':provider['layers'],'Consulta de atributos':'GeoJSON' if provider['queryable'] else 'Según el servicio'}
            product=dict(id=id,title=layer['name'],sourceId='F111',categoryIds=[category],url=siu['capabilities'],
                fields=fields,coverage='Ámbitos publicados por el SIU',period=layer['period'],license='Condiciones del SIU · MIVAU',
                mode='remote',notes=f"Cartografía oficial del SIU. Visible desde zoom {layer['minzoom']}.",
                dataFile='vivienda/siu/layers.json')
            record_id='siu:'+layer['id']
            if 'verifiedMap' in layer:
                product.update(status='integrado',mapAction='official-wms:'+layer['id'])
                available.append(product)
                records[record_id]=dict(product,id=record_id,links={'Mapa de comprobación':layer['verifiedMap']},
                    review=dict(implementedProductId=id,updatedAt=siu['revision'],reason='PNG y origen de Pages verificados.'))
            else:
                records[record_id]=dict(product,id=record_id,status='bloqueado',notes=layer['error'],
                    review=dict(updatedAt=siu['revision'],reason=layer['error'],
                                nextAction='Reintentar el mapa a la escala publicada y verificar los datos de la capa.'))
    if kind=='demography':
        nomenclator=read('datos/territorio/nomenclator/index.json')
        editions=nomenclator['editions']
        available.append(dict(
            id='demography:nomenclator',title='Nomenclátor · población por unidad poblacional',
            sourceId='F005',categoryIds=[category],status='integrado',url=nomenclator['source'],
            mapAction='nomenclator',coverage='Municipios, entidades y núcleos de población',
            period={'from':str(editions[0]['year']),'to':str(editions[-1]['year'])},
            unit='personas',license='CC BY 4.0 · INE',
            notes=f"{len(editions)} ediciones nacionales. Series consultables por provincia, año, nombre y código.",
            dataFile='territorio/nomenclator/index.json'))
        historical=read('datos/poblacion/intercensal/index.json')
        for part in historical['provinces'].values():
            path=ROOT/'datos/poblacion/intercensal'/part['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==part['sha256'],path
        available.append(dict(
            id='demography:historical-census',title='Censos históricos y alteraciones de municipios',
            sourceId='F005',categoryIds=[category],status='integrado',url=historical['source'],
            mapAction='historical-census',coverage='52 provincias y ciudades autónomas; municipios históricos y totales publicados',
            period={'from':'1842','to':'2021'},unit='personas y hogares',license='CC BY 4.0 · INE',
            notes=f"{historical['records']:,} fichas censales. Incluye recuentos, símbolos y notas de las alteraciones históricas.",
            dataFile='poblacion/intercensal/index.json'))
    output={'revision':index['revision'],'available':available,'inventory':list(records.values())}
    (ROOT/f'registry/{kind}-products.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{category}: {len(available)} available products; {len(records)} discovery records')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--kind',default='demography');parser.add_argument('--category',default='F02');args=parser.parse_args();main(args.kind,args.category)
