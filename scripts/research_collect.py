"""Collect official discovery inventories without downloading statistical observations."""
import concurrent.futures
import hashlib
import json
import re
import urllib.request
import urllib.parse
import csv
import gzip
import html as html_module
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache' / 'research'
OUT = ROOT / 'docs' / 'research'
DATA = ROOT / 'datos/catalogo/investigacion'
CACHE.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
REFRESH=False

def fetch(url):
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest()+'.raw')
    if REFRESH or not path.exists():
        for attempt in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Pais-source-research/1.0'}), timeout=90) as r:
                    path.write_bytes(r.read())
                break
            except Exception:
                if attempt==2:raise
                time.sleep(2**attempt)
    return path.read_bytes()

def inspect():
    url = 'https://datos.gob.es/apidata/catalog/publisher.json?_pageSize=50&_page=0'
    data = json.loads(fetch(url))
    print(json.dumps(data, ensure_ascii=True)[:7000])
    html = fetch('https://www.ine.es/dyngs/IOE/es/busquedaAvan.htm').decode('utf-8',errors='replace')
    print('IOE LINKS:', re.findall(r'''href=["']([^"']+)''', html)[-50:])

def inspect_more():
    for url in ['https://datos.gob.es/apidata/catalog/dataset.json?_pageSize=1&_page=0', 'https://www.ine.es/dyngs/IOE/listadoIoeActualAvan.htm?opc=todas']:
        body=fetch(url)
        if 'dataset.json' in url:
            print('DATASET',body.decode('utf-8')[:9000])
        else:
            html=body.decode('utf-8',errors='replace')
            print('IOE CSV LINKS',[(a,b) for a,b in re.findall(r'''href=["']([^"']+)["'][^>]*>(.*?)</a>''',html,re.S) if 'csv' in a.lower() or 'csv' in b.lower()][:5])
            print('IOE LIST sample',re.sub('<[^>]+>',' ',html)[-14000:-9000])
    query='''PREFIX dcat: <http://www.w3.org/ns/dcat#> PREFIX dct: <http://purl.org/dc/terms/> PREFIX foaf: <http://xmlns.com/foaf/0.1/> SELECT ?publisher ?name (COUNT(DISTINCT ?dataset) AS ?datasets) WHERE { ?dataset a dcat:Dataset ; dct:publisher ?publisher . OPTIONAL { ?publisher foaf:name ?name } } GROUP BY ?publisher ?name ORDER BY DESC(?datasets)'''
    url='https://datos.gob.es/virtuoso/sparql?'+urllib.parse.urlencode({'query':query,'format':'application/sparql-results+json'})
    try:
        data=json.loads(fetch(url)); (DATA/'publishers-sparql.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); print('SPARQL',str(data)[:1200], 'count',len(data.get('results',{}).get('bindings',[])))
    except Exception as e:print('SPARQL error',str(e))

def sparql(query):
    url='https://datos.gob.es/virtuoso/sparql?'+urllib.parse.urlencode({'query':query,'format':'application/sparql-results+json'})
    return json.loads(fetch(url))['results']['bindings']

def collect():
    query='''PREFIX dcat: <http://www.w3.org/ns/dcat#> PREFIX dct: <http://purl.org/dc/terms/> PREFIX foaf: <http://xmlns.com/foaf/0.1/> SELECT ?publisher ?name (COUNT(DISTINCT ?dataset) AS ?datasets) WHERE { ?dataset a dcat:Dataset ; dct:publisher ?publisher . OPTIONAL { ?publisher foaf:name ?name } } GROUP BY ?publisher ?name ORDER BY DESC(?datasets)'''
    raw=sparql(query)
    (DATA/'publishers-sparql.json').write_text(json.dumps({'results':{'bindings':raw}},ensure_ascii=False,indent=2),encoding='utf-8')
    publishers={r['publisher']['value']:{'id':r['publisher']['value'].rsplit('/',1)[-1],'name':r.get('name',{}).get('value','Sin denominación'),'uri':r['publisher']['value'],'datasets':int(r['datasets']['value'])} for r in raw}
    print('Publishers',len(publishers),'dataset total',sum(p['datasets'] for p in publishers.values()),flush=True)
    prefix='PREFIX dcat: <http://www.w3.org/ns/dcat#> PREFIX dct: <http://purl.org/dc/terms/> '
    total=sum(p['datasets'] for p in publishers.values())
    def page(offset):
        q=prefix+f'''SELECT DISTINCT ?dataset ?publisher ?title WHERE {{ ?dataset a dcat:Dataset ; dct:publisher ?publisher ; dct:title ?title . FILTER(lang(?title)="es" || lang(?title)="") }} ORDER BY ?dataset ?title LIMIT 5000 OFFSET {offset}'''
        data=sparql(q)
        print('Catalog offset',offset,'rows',len(data),flush=True)
        return data
    rows=[]
    # A sequential ordered scan avoids overwhelming the shared public endpoint.
    offset=0
    while True:
        chunk=page(offset)
        rows.extend(chunk)
        if len(chunk)<5000:break
        offset+=5000
    datasets={}
    for row in rows:
        uri=row['dataset']['value'];pid=row['publisher']['value'];title=row['title']['value']
        datasets.setdefault(uri,{'uri':uri,'publisher':pid,'title':title})
    export=DATA/'datasets-catalogo-nacional.csv.gz'
    with gzip.open(export,'wt',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['publicador_id','publicador','titulo','url_catalogo'])
        for d in datasets.values():
            p=publishers.get(d['publisher'],{})
            w.writerow([p.get('id',d['publisher']),p.get('name',''),d['title'],d['uri'].replace('http://','https://').replace('/catalogo/','/es/catalogo/')])
    for p in publishers.values():
        p['catalogUrl']='https://datos.gob.es/es/catalogo?publisher_display_name='+urllib.parse.quote(p['name'])
        p['apiUrl']='https://datos.gob.es/apidata/catalog/dataset/publisher/'+p['id']
        p['examples']=[d['title'] for d in datasets.values() if d['publisher']==p['uri']][:12]
    record={'retrievedAt':datetime.now(timezone.utc).isoformat(),'source':'https://datos.gob.es/es/sparql','scope':'Publicadores y títulos federados en datos.gob.es en el momento de la consulta. No incluye necesariamente todos los organismos, portales o datos oficiales españoles. Es un inventario de metadatos; no son observaciones descargadas. El catálogo puede cambiar durante la extracción.','publisherCount':len(publishers),'datasetCount':len(datasets),'aggregateDatasetCount':total,'publishers':list(publishers.values())}
    (DATA/'publicadores-catalogo-nacional.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Publicadores del catálogo nacional','',record['scope'],'',f'Consulta: {record["retrievedAt"]}. {len(publishers)} publicadores; {len(datasets):,} conjuntos con título español o sin idioma recuperados. Recuento agregado: {total:,}. La diferencia puede reflejar idiomas, múltiples publicadores o cambios durante la extracción.','']
    for p in sorted(publishers.values(),key=lambda p:p['name']):
        lines.extend([f'## {p["name"]}', '',f'- Identificador oficial: {p["id"]}. Conjuntos según recuento agregado: {p["datasets"]:,}.',f'- [Catálogo del publicador]({p["apiUrl"]})', '- Títulos de muestra (no resumen exhaustivo):']+['  - '+t.rstrip() for t in p['examples']]+[''])
    (OUT/'PUBLICADORES_NACIONALES.md').write_text('\n'.join(lines),encoding='utf-8')
    source='https://www.ine.es/dyngs/IOE/listadoIoeActualAvan.htm?opc=todas'
    html=fetch(source).decode('utf-8',errors='strict')
    pattern=r'''<a[^>]+href="([^"]*operacion\.htm\?id=[^"]+)"[^>]*>\s*<span class="csvCodigoOper">(.*?)</span>.*?<span class="csvTituloOper">(.*?)</span>'''
    operations=[]
    for href,code,title in re.findall(pattern,html,re.S):
        clean=lambda v: html_module.unescape(re.sub('<[^>]+>',' ',v)).strip()
        title=clean(title);code=clean(code)
        operations.append({'code':code,'title':title,'responsibleCode':title.rsplit('(',1)[-1].rstrip(')'),'url':urllib.parse.urljoin('https://www.ine.es',href)})
    assert len(operations)>700,len(operations)
    (DATA/'operaciones-ioe.json').write_text(json.dumps({'source':source,'retrievedAt':record['retrievedAt'],'operations':operations},ensure_ascii=False,indent=2),encoding='utf-8')
    with (DATA/'operaciones-ioe.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['code','title','responsibleCode','url'],delimiter=';');w.writeheader();w.writerows(operations)
    groups={}
    for op in operations:groups.setdefault(op['responsibleCode'],[]).append(op)
    lines=['# Operaciones estadísticas estatales — IOE actual','',f'Fuente: [Inventario de Operaciones Estadísticas]({source}). Consulta {record["retrievedAt"]}. {len(operations)} operaciones. Inventariar una operación no acredita que todas sus observaciones sean abiertas, gratuitas o cartografiables.','']
    for group,ops in sorted(groups.items()):
        lines.extend([f'## {group} — {len(ops)} operaciones','']+[f'- **{o["code"]}** · [{o["title"]}]({o["url"]})' for o in ops]+[''])
    (OUT/'IOE_COMPLETO.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Completed',len(publishers),'publishers',len(datasets),'catalog datasets',len(operations),'IOE operations',flush=True)

def enrich_ioe():
    record=json.loads((DATA/'operaciones-ioe.json').read_text(encoding='utf-8'))
    clean=lambda v: re.sub(r'\s+',' ',html_module.unescape(re.sub('<[^>]+>',' ',v))).strip()
    def detail(op):
        try:
            html=fetch(op['url']).decode('utf-8')
            fields={clean(k):clean(v) for k,v in re.findall(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>',html,re.S)}
            assert 'Servicio responsable' in fields, 'No responsible organization field'
            links={name:html_module.unescape(url) for url,name in re.findall(r'''<a[^>]+href=["']([^"']+)["'][^>]+name=["'](enlace[^"']+)["']''',html,re.S)}
            return {**op,'fields':fields,'links':links}
        except Exception as e:return {**op,'error':str(e)}
    operations=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,op in enumerate(pool.map(detail,record['operations']),1):
            operations.append(op)
            if i%50==0: print('IOE detailed',i,flush=True)
    record['operations']=operations;record['detailErrors']=[{'code':o['code'],'error':o['error']} for o in operations if 'error' in o]
    (DATA/'operaciones-ioe-detalladas.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    groups={}
    for op in operations:
        fields=op.get('fields',{})
        key=fields.get('Servicio responsable',op['responsibleCode'])+' / '+fields.get('Unidad ejecutora','Unidad no recuperada')
        groups.setdefault(key,[]).append(op)
    lines=['# IOE: entidades y operaciones, con variables y escala territorial','',f'{len(operations)} operaciones; {len(groups)} agrupaciones de servicio responsable / unidad ejecutora; {len(record["detailErrors"])} fichas con error.','',f'Fuente: [{record["source"]}]({record["source"]}). Metadatos recogidos el {datetime.now(timezone.utc).isoformat()}. Son fichas de descubrimiento, no observaciones descargadas; una operación puede no ser cartografiable ni publicar todo su detalle.','']
    for group,ops in sorted(groups.items()):
        lines.extend(['## '+group,''])
        for op in ops:
            lines.extend([f'- **{op["code"]} · [{op["title"]}]({op["url"]})**'])
            for key in ['Sector o tema','Subsector o subtema','Nivel de desagregación','Ámbito territorial','Objetivo general','Variables de estudio','Variables de clasificación','Periodicidad de la difusión']:
                if op.get('fields',{}).get(key):lines.append(f'  - {key}: {op["fields"][key]}')
            if op.get('links',{}).get('enlaceDatos'):lines.append(f'  - [Acceso a los resultados]({op["links"]["enlaceDatos"]})')
            if op.get('error'):lines.append('  - Error de recuperación: '+op['error'])
        lines.append('')
    (OUT/'IOE_POR_ENTIDAD.md').write_text('\n'.join(lines),encoding='utf-8')
    with (DATA/'operaciones-ioe-detalladas.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fieldnames=['codigo','operacion','responsable','ejecutor','sector','desagregacion','ambito','variables','clasificacion','periodicidad','resultados','ficha','error']
        writer=csv.DictWriter(f,fieldnames=fieldnames,delimiter=';');writer.writeheader()
        for o in operations:
            fields=o.get('fields',{})
            writer.writerow(dict(zip(fieldnames,[o['code'],o['title'],fields.get('Servicio responsable',''),fields.get('Unidad ejecutora',''),fields.get('Sector o tema',''),fields.get('Nivel de desagregación',''),fields.get('Ámbito territorial',''),fields.get('Variables de estudio',''),fields.get('Variables de clasificación',''),fields.get('Periodicidad de la difusión',''),o.get('links',{}).get('enlaceDatos',''),o['url'],o.get('error','')])))
    print('IOE details complete',len(operations),'groups',len(groups),'errors',len(record['detailErrors']),flush=True)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--details',action='store_true');parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
    REFRESH=args.refresh
    if args.details:enrich_ioe()
    else:collect()
