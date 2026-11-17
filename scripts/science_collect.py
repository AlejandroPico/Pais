"""Import official research, innovation and European framework programme data."""
from collections import Counter, defaultdict
import csv
from decimal import Decimal
import gzip
import io
import json
import re
from zipfile import ZipFile

from affiliation_collect import fetch
from commerce_bde import NATIONAL
from commerce_distributions import publish
from demography_collect import ROOT, encode, norm
from education_collect import px_product
from fiscal_workbooks import area, no_geometry
from funding_collect import NUTS_COMMUNITIES, NUTS_PROVINCES, aggregate_records, community_code, product, source

CACHE = ROOT/'.cache/f12'
OUTPUT = ROOT/'datos/ciencia'
REVISION = '2026-11-17'
CORDIS = 'https://cordis.europa.eu/projects'
PROGRAMMES = {'fp7':'Séptimo Programa Marco','h2020':'Horizonte 2020','HORIZON':'Horizonte Europa'}
ROLES = {'participant':'Participante','coordinator':'Coordinador','thirdParty':'Tercero',
         'partner':'Socio','associatedPartner':'Socio asociado'}
PROVINCES = {
    '01':'Álava','02':'Albacete','03':'Alicante','04':'Almería','05':'Ávila','06':'Badajoz','07':'Illes Balears',
    '08':'Barcelona','09':'Burgos','10':'Cáceres','11':'Cádiz','12':'Castellón','13':'Ciudad Real','14':'Córdoba',
    '15':'A Coruña','16':'Cuenca','17':'Girona','18':'Granada','19':'Guadalajara','20':'Gipuzkoa','21':'Huelva',
    '22':'Huesca','23':'Jaén','24':'León','25':'Lleida','26':'La Rioja','27':'Lugo','28':'Madrid','29':'Málaga',
    '30':'Murcia','31':'Navarra','32':'Ourense','33':'Asturias','34':'Palencia','35':'Las Palmas','36':'Pontevedra',
    '37':'Salamanca','38':'Santa Cruz de Tenerife','39':'Cantabria','40':'Segovia','41':'Sevilla','42':'Soria',
    '43':'Tarragona','44':'Teruel','45':'Toledo','46':'Valencia','47':'Valladolid','48':'Bizkaia','49':'Zamora',
    '50':'Zaragoza','51':'Ceuta','52':'Melilla',
}
PROVINCE_COMMUNITY = {code:NUTS_COMMUNITIES[nuts[:4]] for nuts,code in NUTS_PROVINCES.items()}
CORDIS_FIELDS = {
    'ecContribution':'Aportación UE publicada',
    'netEcContribution':'Aportación neta UE publicada',
    'totalCost':'Coste del participante publicado',
}


def write_index(folder, tables):
    path=OUTPUT/folder
    path.mkdir(parents=True,exist_ok=True)
    tables=list(tables)
    assert tables,folder
    (path/'index.json').write_bytes(encode(dict(revision=REVISION,tables=tables)))
    print(folder,len(tables),sum(t['rows'] for t in tables),flush=True)


def dated_editions(labels):
    seen=Counter()
    for label in labels:
        years=re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',label)
        if not years:
            raise ValueError('En la tabla figura un periodo sin año reconocible: '+label)
        year=years[-1]
        suffix=f'R{seen[year]:02}' if seen[year] else ''
        seen[year]+=1
        yield dict(id=year+suffix,label=label)


def ine_tables():
    manifest=json.loads((CACHE/'ine-tables.json').read_bytes())
    errors=json.loads((CACHE/'ine-errors.json').read_bytes())
    products,gaps=[],[]
    for key,entry in manifest.items():
        number,kind=key.split('-')
        path='ine-'+key+'.px'
        identifier=(1200000 if kind=='tpx' else 1300000)+int(number)
        try:
            raw=(CACHE/path).read_bytes()
            profile=dict(id=identifier,folder='ine',publisher='INE',sourceId='F005',
                         family='INE · '+entry['operation'],license='Condiciones de reutilización del INE',
                         periods=lambda labels: list(dated_editions(labels)))
            title=entry['title']
            if entry.get('edition'):
                title+=' · '+entry['edition']
            table=px_product(dict(entry,topic='science',title=title),raw,section='ciencia',profile=profile)
            table['note']=entry['group']+'. '+table['note']
            if any('R' in period['id'] for period in table['periods']):
                table['note']+=' Mantiene por separado las variantes del mismo año que ofrece la fuente.'
            if number in {'76791','76794'}:
                dimension=table['dimensions'][0]
                units={}
                for label in dimension['values']:
                    key=norm(label)
                    units[label]=('Tanto por mil' if 'tanto por mil' in key else
                                  'Porcentaje' if '%' in key or 'tasa de crecimiento' in key else
                                  'Personas' if 'numero de personas' in key else
                                  'Personas en equivalencia a jornada completa')
                table['unitsByCategory']=dict(dimension=dimension['name'],values=units)
            products.append(table)
        except (OSError,ValueError,KeyError,AssertionError) as error:
            reason = errors.get(path,'Distribución no descargada') if isinstance(error,FileNotFoundError) else str(error)
            gaps.append({**entry,'reason':reason[:250]})
    products.sort(key=lambda t:(t['family'],norm(t['label']),t['id']))
    registered=ROOT/'registry/science-inputs.json'
    if registered.exists():
        gaps.extend(json.loads(registered.read_bytes())['blocked'])
    (ROOT/'registry/science-capture.json').write_bytes(encode(dict(
        revision=REVISION,ineTableCount=len(manifest),ineProducts=len(products),gaps=gaps)))
    return products


def csv_table(archive, name):
    with archive.open(name) as buffer:
        yield from csv.DictReader(io.TextIOWrapper(buffer,encoding='utf-8-sig',newline=''),delimiter=';')


def spanish_areas(record):
    code=record['nutsCode'].strip().upper()
    province=NUTS_PROVINCES.get(code)
    community=NUTS_COMMUNITIES.get(code[:4])
    postal=record['postCode'].strip()
    postal_province=postal[:2] if re.fullmatch(r'\d{5}',postal) and postal[:2] in PROVINCES else None
    if not province and postal_province and (not community or community==PROVINCE_COMMUNITY.get(postal_province)):
        province=postal_province
        community=community or PROVINCE_COMMUNITY.get(postal_province)
    places=[NATIONAL]
    if community:
        places.append(community_code(community))
    else:
        places.append(no_geometry('Organización española sin comunidad asignable'))
    if province:
        places.append(area(PROVINCES[province],'province',province))
    return places


def cordis_data():
    name_count,branch_count='Participaciones de organizaciones españolas','Proyectos distintos con participación'
    for offset,(code,label) in enumerate(PROGRAMMES.items(),1):
        url='https://cordis.europa.eu/data/cordis-'+code+'projects-csv.zip'
        raw=fetch(url,CACHE/(code+'.zip'),False)
        with ZipFile(io.BytesIO(raw)) as archive:
            organizations=[o for o in csv_table(archive,'organization.csv') if o['country']=='ES']
            ids={row['projectID'] for row in organizations}
            projects={row['id']:row for row in csv_table(archive,'project.csv') if row['id'] in ids}
        assert set(projects)==ids,(code,sorted(ids-set(projects))[:10])
        counts,territories,project_per_group=defaultdict(Counter),{},defaultdict(set)
        preserved=[]
        missing_geo=0
        for record in organizations:
            project_id=record['projectID']
            project_row=projects[project_id]
            date=project_row['startDate']
            period=date[:4] if re.match(r'^\d{4}-',date) else '0000'
            role=ROLES.get(record['role'],record['role'] or 'Rol sin dato')
            status={'SIGNED':'Firmado','CLOSED':'Cerrado','TERMINATED':'Terminado'}.get(
                project_row['status'],project_row['status'] or 'Estado sin dato')
            call=(project_row.get('subCall') or project_row.get('masterCall') or 'Convocatoria sin dato').strip()
            values={name_count:1}
            for field,indicator in CORDIS_FIELDS.items():
                value=record[field].strip()
                if value:
                    values[indicator]=Decimal(value.replace(',','.'))
            places=spanish_areas(record)
            missing_geo+=int(places[-1]['level']=='unlocated')
            for place in places:
                territories[place['id']]=place
                for call_scope in dict.fromkeys(('Total',call)):
                    for role_scope,state_scope in dict.fromkeys((('Total','Total'),(role,'Total'),('Total',status),(role,status))):
                        key=(place['id'],period,(role_scope,state_scope,call_scope))
                        counts[key].update(values)
                        project_per_group[key].add(project_id)
            preserved.append({field:record[field] for field in (
                'projectID','organisationID','name','activityType','SME','city','postCode','nutsCode','role','order',
                'ecContribution','netEcContribution','totalCost','endOfParticipation','active')})
        for key,projects_in_group in project_per_group.items():
            counts[key][branch_count]=len(projects_in_group)
        identifier=120100+offset
        original=source(identifier,url,raw)
        fields=('id','acronym','title','status','startDate','endDate','ecSignatureDate','frameworkProgramme',
                'masterCall','subCall','fundingScheme','topics','legalBasis','totalCost','ecMaxContribution','grantDoi')
        project_rows=[{**{key:p.get(key,'') for key in fields},
                       'url':'https://cordis.europa.eu/project/id/'+p['id']}
                      for p in projects.values()]
        snapshot=gzip.compress(encode(dict(source=original,projects=project_rows,organizations=preserved)),compresslevel=6,mtime=0)
        name=code+'-proyectos.json.gz'
        (OUTPUT/'cordis'/name).write_bytes(snapshot)
        note=(f'{len(organizations):,} filas de participación y {len(projects):,} proyectos distintos con '
              f'organizaciones de España. {missing_geo:,} participaciones sin comunidad asignable. El año '
              'corresponde al inicio del proyecto. El mapa sitúa el domicilio publicado de la organización y '
              'emplea NUTS o un código postal español cuando es compatible; el lugar de ejecución puede ser distinto. '
              'Las aportaciones y los costes son campos del participante. Su suma se limita a campos con valor. '
              'Un proyecto puede estar presente en varias comunidades o roles. La convocatoria sigue el código publicado en CORDIS.')
        metadata=product(identifier,'CORDIS · '+label,'Comisión Europea · CORDIS','F140',CORDIS,note,
                         [original,source(identifier+20,url,snapshot,originalFile=name)],
                         'Reutilización de la Comisión Europea con reconocimiento de la fuente')
        metadata['snapshotFile']=name
        metadata['snapshotLabel']='Proyectos y participaciones de España (JSON comprimido)'
        units={name_count:'Participaciones',branch_count:'Proyectos',**dict.fromkeys(CORDIS_FIELDS.values(),'Euros')}
        yield publish('cordis',metadata,aggregate_records(counts,territories,{'0000':'Inicio sin fecha'}),
                      ('Indicador','Rol','Estado del proyecto','Convocatoria'),units,section='ciencia')


if __name__=='__main__':
    write_index('ine',ine_tables())
    write_index('cordis',cordis_data())
