"""Preserve the official municipal modification tables with their publication links."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

import territory_collect as territory

SOURCE = 'https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177031&idp=1254734710990'

class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.span = 1
    def handle_starttag(self, tag, attributes):
        if tag == 'tr':
            self.row = []
        if tag in {'td','th'} and self.row is not None:
            self.cell = []
            self.span = int(dict(attributes).get('colspan','1'))
        if tag == 'br' and self.cell is not None:
            self.cell.append(' ')
    def handle_data(self, value):
        if self.cell is not None:
            self.cell.append(value)
    def handle_endtag(self, tag):
        if tag in {'td','th'} and self.cell is not None:
            self.row.append((' '.join(''.join(self.cell).split()), self.span))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None

def edition(url, refresh):
    year = '20'+re.search(r'/(\d{2})codmunmod\.htm',url)[1]
    raw = territory.fetch('municipal-changes-'+year,url,refresh)
    try:
        page = raw.decode('utf-8')
    except UnicodeDecodeError:
        page = raw.decode('iso-8859-15')
    parser = Tables()
    parser.feed(page.split('FIN MENU',1)[-1].split('INICIO PIE',1)[0])
    sections = []
    section = None
    for row in parser.rows:
        fields = [text for text,_ in row]
        if len(row)==1 and row[0][1]>2 and fields[0]:
            label = fields[0]
            if re.search('municipios?|denominaci|provincia|cambio|correcci', label, re.I):
                section = {'name':label,'rows':[]}
                sections.append(section)
            continue
        if section and any(fields) and len(fields)>1:
            section['rows'].append(fields)
    assert sections, url
    return {'year':year,'url':url,'sections':sections}

def main(refresh=False):
    body=territory.fetch('municipal-history-index',SOURCE,refresh).decode('utf-8')
    paths=sorted(set(re.findall(r'(?:href|value)="([^"]+/\d{2}codmunmod\.htm)"',body)))
    assert paths, 'El INE no anunció ediciones de cambios'
    urls=[urljoin(SOURCE,path) for path in paths]
    with ThreadPoolExecutor(max_workers=6) as pool:
        editions=list(pool.map(lambda url:edition(url,refresh),urls))
    territory.save(territory.OUT/'municipal-changes.json',{
        'source':SOURCE,'editions':editions,'provenance':sorted(territory.PROVENANCE,key=lambda item:item['url']),
    })
    print('Ediciones de cambios municipales:',len(editions),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
