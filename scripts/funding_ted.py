"""Capture and publish TED notices associated with Spain for October 2026."""
import argparse
from collections import Counter, defaultdict
import gzip
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from commerce_distributions import publish
from funding_collect import CACHE, ROOT, TOTAL, aggregate_records, encode, product, sha, source, write_index
from funding_placsp import execution_areas

ENDPOINT = 'https://api.ted.europa.eu/v3/notices/search'
HELP = 'https://ted.europa.eu/en/help/data-reuse'
QUERY = '(buyer-country = ESP OR place-of-performance = ESP) AND publication-date >= 20261001 AND publication-date <= 20261031'
FIELDS = ('publication-number','publication-date','buyer-country','place-of-performance',
          'notice-type','notice-identifier','procedure-identifier','form-type')
PAGE_SIZE = 250


def page(number):
    query = dict(query=QUERY,fields=FIELDS,limit=PAGE_SIZE,page=number,scope='ALL',checkQuerySyntax=False)
    request = Request(ENDPOINT,data=encode(query),headers={'Content-Type':'application/json','Accept':'application/json'})
    for attempt in range(4):
        try:
            with urlopen(request,timeout=60) as response:
                raw = response.read()
            break
        except HTTPError as error:
            if error.code!=429 or attempt==3:
                raise
            wait = error.headers.get('Retry-After','')
            time.sleep(int(wait) if wait.isdigit() else 5*(attempt+1))
    data = json.loads(raw)
    assert not data['timedOut'], number
    notices = [{field:row[field] for field in FIELDS if field in row} for row in data['notices']]
    return dict(query=query,sha256=sha(raw),bytes=len(raw),total=data['totalNoticeCount'],notices=notices)


def capture(path):
    first = page(1)
    print('TED',first['total'],len(first['notices']),flush=True)
    count = (first['total']+PAGE_SIZE-1)//PAGE_SIZE
    assert count*PAGE_SIZE<=10000, 'Use narrower date windows for the paginated API.'
    pages = [first]
    for number in range(2,count+1):
        time.sleep(1.1)
        pages.append(page(number))
    path.write_bytes(encode(pages))


def notices_table(refresh):
    cache = CACHE/'ted-octubre.json'
    if refresh:
        CACHE.mkdir(parents=True,exist_ok=True)
        capture(cache)
    pages = json.loads(cache.read_bytes())
    notices = [notice for page in pages for notice in page['notices']]
    assert {page['total'] for page in pages}=={len(notices)}
    assert len({row['publication-number'] for row in notices})==len(notices)
    path = ROOT/'datos/ayudas/feder/index.json'
    province_names = {a['code']:a['name'] for a in json.loads(path.read_bytes())['tables'][0]['territories']
                      if a['level']=='province'}
    forms = {'planning':'Planificación','competition':'Licitación','result':'Resultado',
             'change':'Cambio','cont-modif':'Modificación de contrato','completion':'Finalización'}
    indicator = 'Anuncios publicados'
    totals, territories = defaultdict(Counter), {}
    for row in notices:
        assert row['publication-date'].startswith('2026-10'),row['publication-number']
        codes = {code for code in row.get('place-of-performance',[]) if len(code) in (4,5) and code.startswith('ES')}
        period = '2026M10'
        form = row.get('form-type') or 'Sin clase de formulario'
        name = forms.get(form,form)
        notice_type = row.get('notice-type') or 'Sin tipo de anuncio'
        for territory in execution_areas(codes,province_names):
            territories[territory['id']] = territory
            for categories in dict.fromkeys(((TOTAL,TOTAL),(name,TOTAL),(name,notice_type),(TOTAL,notice_type))):
                totals[(territory['id'],period,categories)][indicator] += 1
    identifier = 970501
    output = ROOT/'datos/ayudas/ted'
    file = 'anuncios-202610.json.gz'
    original = gzip.compress(encode(pages),compresslevel=6,mtime=0)
    (output/file).write_bytes(original)
    inputs = [source(identifier,HELP,original,originalFile=file)]
    p = product(identifier,'TED · Anuncios con comprador o ejecución en España','Oficina de Publicaciones de la UE · TED',
                'F141',HELP,
                f'{len(notices):,} publicaciones distintas de octubre de 2026. El filtro oficial combina comprador '
                'en España y lugar de ejecución en España. Se conservan las referencias de publicación, anuncio '
                'y procedimiento, incluida la publicación de cambios. Las comunidades y provincias usan únicamente '
                'un lugar español de ejecución declarado. Los anuncios con varios lugares o sin NUTS suficiente '
                'quedan en el total y en los ámbitos de consulta. Una publicación puede actualizar un procedimiento '
                'ya publicado y puede figurar también en PLACSP.',
                inputs,'Condiciones de reutilización de TED')
    p['downloadUrl']='https://ted.europa.eu/es/search/result'
    yield publish('ted',p,aggregate_records(totals,territories,{'2026M10':'2026-10'}),
                  ('Indicador','Formulario','Tipo de anuncio'),{indicator:'Anuncios'},section='ayudas')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true')
    write_index('ted',notices_table(parser.parse_args().refresh))
