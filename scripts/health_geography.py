"""Publish Generalitat coordinates and distinguish Madrid registration from service rows."""
from collections import Counter, defaultdict
import csv
import gzip
from io import StringIO
import json

from demography_collect import ROOT, encode, norm, sha
from fiscal_workbooks import area
from health_collect import OUTPUT
from health_distributions import distribute


def catalunya_points(entry,raw,revision):
    features=[]
    counts=Counter()
    fields={'Número registre':'Registro','Nom establiment':'Centro','Tipus establiment':'Tipo',
            'Codi tipus establiment':'Código de tipo','Codi establiment pare':'Establecimiento principal',
            'Telèfon':'Teléfono del centro','Tipus de via':'Tipo de vía','Nom de la via':'Vía',
            'Número de la via':'Número','Codi postal':'Código postal','Codi municipi':'Código de municipio',
            'Municipi':'Municipio','Comarca':'Comarca','Província':'Provincia','ABS':'Área básica de salud',
            'Sector sanitari':'Sector sanitario','Regió sanitària':'Región sanitaria',
            'Servei SPD':'Servicio SPD','Servei FMT nivell 1':'Servicio FMT de nivel 1',
            'Servei FMT nivell 2':'Servicio FMT de nivel 2'}
    reader=csv.DictReader(StringIO(raw.decode('utf-8-sig')))
    assert set(fields)<=set(reader.fieldnames)
    for row in reader:
        counts['registered']+=1
        try:
            point=[float(row[key]) for key in ('Longitud','Latitud')]
        except ValueError:
            continue
        longitude,latitude=point
        if not (.1<=longitude<=3.5 and 40.45<=latitude<=43):
            continue
        properties={label:row[key] for key,label in fields.items() if row[key]}
        identifier=properties['Registro']
        features.append(dict(type='Feature',id=identifier,geometry=dict(type='Point',coordinates=point),
                             properties=dict(atlasId=identifier,atlasName=properties['Centro'],**properties)))
    assert len({f['id'] for f in features})==len(features)>5000
    file='generalitat/centros-autorizados.geojson.gz'
    target=OUTPUT/file
    target.parent.mkdir(parents=True,exist_ok=True)
    payload=gzip.compress(encode(dict(type='FeatureCollection',features=features)),compresslevel=6,mtime=0)
    target.write_bytes(payload)
    return dict(id='health-centros-catalunya',title='Establecimientos autorizados · Cataluña',
                group='Centros y establecimientos sanitarios',directory='salud',geometry='point',file=file,
                coverage='Cataluña',period='Captura '+revision,sourceId=entry['sourceId'],
                url=entry['table'],download=entry['download'],sha256=sha(payload),originalSha256=sha(raw),
                count=len(features),registered=counts['registered'],missingCount=counts['registered']-len(features),
                minzoom=8,center=[1.80,41.72],credit='Generalitat de Catalunya · Departament de Salut · CC BY 4.0',
                note='Posiciones del registro oficial. Las fichas muestran identificador, tipo, dirección y ámbito sanitario.')


def madrid_directory(entry,raw):
    lookup=json.loads((ROOT/'datos/territorio/index.json').read_bytes())['municipalities']
    towns={norm(m['name']):m for m in lookup if m['provinceCode']=='28'}
    region=area('Comunidad de Madrid','community','13')
    reader=csv.DictReader(StringIO(raw.decode('utf-8-sig')),delimiter=';')
    centers=defaultdict(set)
    services=Counter()
    territories={region['id']:region}
    unmatched=set()
    for row in reader:
        name=row['municipio_nombre']
        town=towns.get(norm(name))
        coverage=[region]
        if town:
            coverage.append({**area(town['name'],'municipal',town['code']),'provinceCode':'28'})
        else:
            unmatched.add(name or 'Sin municipio informado')
        clinic=row['centro_nro_registro']
        kind=row['centro_tipo']
        for target in coverage:
            territories[target['id']]=target
            for label in ('Total',kind):
                centers[(target['id'],label)].add(clinic)
                services[(target['id'],label)]+=1
    assert len(centers[(region['id'],'Total')])>10000
    date=entry['period']
    periods=(date,date)
    indicators=('Establecimientos inscritos','Filas de oferta asistencial')
    records=[]
    for (location,kind),codes in centers.items():
        records.extend(((territories[location],*periods,(indicators[0],kind),len(codes),''),
                        (territories[location],*periods,(indicators[1],kind),services[(location,kind)],'')))
    notes=('Registros deduplicados por número de centro dentro de cada ámbito. Una fila de oferta asistencial '
           'corresponde a un servicio publicado, y un centro puede tener varios. Los municipios sin correspondencia '
           'INE comprobada quedan incluidos en el total autonómico. El atlas conserva el acceso al CSV oficial.')
    if unmatched:
        notes+=' Etiquetas sin correspondencia municipal directa: '+', '.join(sorted(unmatched))+'.'
    yield distribute(entry,raw,130340,'comunidad-madrid','Comunidad de Madrid · Registro sanitario','Comunidad de Madrid',
        notes,records,('Indicador','Tipo de centro'),{indicators[0]:'Centros',indicators[1]:'Filas publicadas'})
