"""Join CORDIS project publication metadata by grant agreement and publication identifiers."""
from collections import defaultdict
import gzip
import io
import json
import re
from zipfile import ZipFile

from affiliation_collect import fetch
from commerce_distributions import publish
from funding_collect import product, source
from science_collect import CACHE, CORDIS, OUTPUT, PROGRAMMES, csv_table, encode, spanish_areas, write_index


def corpus():
    for offset,code in enumerate(('h2020','HORIZON'),1):
        url='https://cordis.europa.eu/data/cordis-'+code+'projectPublications-csv.zip'
        raw=fetch(url,CACHE/(code+'-publications.zip'),False)
        snapshot=json.loads(gzip.decompress((OUTPUT/'cordis'/(code+'-proyectos.json.gz')).read_bytes()))
        ids={item['id'] for item in snapshot['projects']}
        project_geographies=defaultdict(set)
        territories={}
        for row in snapshot['organizations']:
            for geography in spanish_areas(row):
                key=geography['id']
                territories[key]=geography
                project_geographies[row['projectID']].add(key)
        counts=defaultdict(set)
        retained=[]
        with ZipFile(io.BytesIO(raw)) as archive:
            for row in csv_table(archive,'projectPublications.csv'):
                if row['projectID'] not in ids:
                    continue
                published=row['publishedYear'].strip()
                date=published if re.fullmatch(r'\d{4}',published) else '0000'
                doi=row['doi'].strip()
                kind=row['isPublishedAs'].strip() or 'Tipo sin dato'
                key=doi.lower().removeprefix('https://doi.org/') if doi else 'cordis:'+row['id']
                for geography in project_geographies[row['projectID']]:
                    for category in dict.fromkeys(('Total',kind)):
                        counts[(geography,date,category)].add(key)
                retained.append({field:row[field] for field in ('id','title','journalTitle','publishedYear','doi',
                                                                'projectID','projectAcronym','isPublishedAs','issn','isbn')})
        label='Publicaciones enlazadas'
        records=[(territories[key],date,date if date!='0000' else 'Año de publicación sin dato',
                  (label,category),len(items),'') for (key,date,category),items in counts.items()]
        identifier=120300+offset
        original=source(identifier,url,raw)
        payload=gzip.compress(encode(dict(source=original,publications=retained)),compresslevel=6,mtime=0)
        file=code+'-publicaciones.json.gz'
        (OUTPUT/'resultados'/file).write_bytes(payload)
        note=(f'{len(retained):,} relaciones publicadas entre proyecto y publicación con participación de organizaciones españolas. '
              'El recuento se deduplica por DOI o identificador CORDIS dentro de cada grupo. El territorio '
              'corresponde a las organizaciones españolas del proyecto. Puede estar repetido en varias regiones. '
              'La reutilización de metadatos se distingue de la licencia de cada publicación, consultable desde su DOI.')
        p=product(identifier,'CORDIS · Publicaciones de '+PROGRAMMES[code],'Comisión Europea · CORDIS','F140',CORDIS,note,
                  [original,source(identifier+20,url,payload,originalFile=file)],
                  'Reutilización de los metadatos de la Comisión Europea')
        p.update(snapshotFile=file,snapshotLabel='Metadatos de publicaciones y proyectos (JSON comprimido)')
        yield publish('resultados',p,records,('Indicador','Tipo de publicación'),{label:'Publicaciones'},section='ciencia')


if __name__=='__main__':
    write_index('resultados',corpus())
