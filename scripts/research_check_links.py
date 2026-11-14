"""Read source landing pages once, recording failures rather than hiding them."""
import concurrent.futures
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]/'docs'/'research'
DATA = OUT.parents[1] / 'datos/catalogo/investigacion'
record=json.loads((DATA/'fuentes-tematicas.json').read_text(encoding='utf-8'))
urls=sorted({e['url'] for e in record['sources']}|{l['url'] for e in record['sources'] for l in e.get('links',[])})

def check(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Pais-official-source-research/1.0'})
        with urllib.request.urlopen(req,timeout=18) as response:
            body=response.read(100000)
            charset=response.headers.get_content_charset() or 'utf-8'
            html=body.decode(charset,errors='replace')
            title=re.search('<title[^>]*>(.*?)</title>',html,re.S|re.I)
            return {'url':url,'status':response.status,'resolvedUrl':response.url,'title':re.sub(r'\s+',' ',title.group(1)).strip() if title else '', 'checkedAt':datetime.now(timezone.utc).isoformat()}
    except urllib.error.HTTPError as e:return {'url':url,'status':e.code,'error':str(e),'checkedAt':datetime.now(timezone.utc).isoformat()}
    except Exception as e:return {'url':url,'status':None,'error':str(e),'checkedAt':datetime.now(timezone.utc).isoformat()}

if __name__=='__main__':
    prior_path=DATA/'comprobacion-enlaces.json'
    previous=json.loads(prior_path.read_text(encoding='utf-8')).get('results',[]) if prior_path.exists() else []
    known={r['url']:r for r in previous}
    pending=[url for url in urls if url not in known]
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,result in enumerate(pool.map(check,pending),1):
            results.append(result)
            if i%25==0:print('Checked',i,'of',len(urls),flush=True)
    results.extend(known[url] for url in urls if url in known)
    results.sort(key=lambda r:r['url'])
    summary={'checkedAt':datetime.now(timezone.utc).isoformat(),'scope':'Comprobación HTTP de puertas de entrada. Un 200 no valida el contenido completo, licencia, API, descarga ni todas las familias; un 403 o timeout puede ser protección automatizada y no inexistencia de la fuente.','checked':len(results),'successful':sum(r['status']==200 for r in results),'results':results}
    (DATA/'comprobacion-enlaces.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Summary',summary['checked'],summary['successful'],'HTTP 200',flush=True)
    print(json.dumps([r for r in results if r['status']!=200],ensure_ascii=True,indent=2),flush=True)
