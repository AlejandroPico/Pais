"""Build the public F13 cubes from the checked source distributions."""
from collections import Counter
from datetime import date
import json
import re

from demography_collect import ROOT, encode, norm, sha
from education_collect import jsonstat_grid, place, px_product, publish_grid, top_geography
from fiscal_workbooks import no_geometry
from health_capture import CACHE, MANIFEST, REVISION
from science_collect import dated_editions

OUTPUT = ROOT/'datos/salud'


def write_index(folder, tables):
    path=OUTPUT/folder
    path.mkdir(parents=True,exist_ok=True)
    (path/'index.json').write_bytes(encode(dict(revision=REVISION,tables=tables)))
    print(folder,len(tables),'productos',sum(t['rows'] for t in tables),'celdas',flush=True)


def health_periods(labels):
    months=('enero','febrero','marzo','abril','mayo','junio','julio','agosto',
            'septiembre','octubre','noviembre','diciembre')
    result=[]
    for label in labels:
        name=norm(label)
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',name):
            result.append(date.fromisoformat(name).isoformat())
        elif short:=re.fullmatch(r'(\d{4})[m-](0?[1-9]|1[0-2])',name):
            result.append(f'{short[1]}M{int(short[2]):02}')
        elif month:=re.fullmatch(r'('+'|'.join(months)+r')(?: de)? (\d{4})',name):
            result.append(f'{month[2]}M{months.index(month[1])+1:02}')
        elif re.fullmatch(r'\d{4}(?:t[1-4]|sm\d{2})?',name):
            result.append(name.upper())
        else:
            return list(dated_editions(labels))
    return [dict(id=key,label=label) for key,label in zip(result,labels,strict=True)]


def health_geography(axes, fields, labels):
    for index,(name,values) in enumerate(zip(axes,labels,strict=True)):
        key=norm(name)
        if key.startswith('provincia, comunidad y ciudad autonoma'):
            places=[place(value,'community' if value.isupper() else 'province') for value in values]
            assert len({location['id'] for location in places})==len(values),name
            return index,places
        if key.startswith(('comunidad y ciudad autonoma','comunidad o ciudad autonoma')):
            return index,[place(value,'community') for value in values]
    return top_geography(axes,fields,labels)


def health_units(table):
    available={
        'altas hospitalarias durante el ano':'Altas hospitalarias',
        'estancias causadas':'Estancias',
        'altas hospitalarias por 100.000 habitantes':'Altas hospitalarias por 100.000 habitantes',
        'estancia media por alta hospitalaria':'Días por alta',
        'edad media':'Años de edad',
        'coeficiente de variacion':'Coeficiente de variación',
    }
    for dimension in table['dimensions']:
        if norm(dimension['name'])=='clase de variable':
            units={value:available[norm(value)] for value in dimension['values'] if norm(value) in available}
            if units:
                table['unitsByCategory']=dict(dimension=dimension['name'],values=units)
            break


def ine_tables(manifest, errors):
    tables, gaps = [],list(manifest['ineListings'])
    for key,entry in manifest['ine'].items():
        number,kind=key.split('-')
        name=f'ine-{key}.px'
        identifier=(1300000 if kind=='tpx' else 1400000)+int(number)
        try:
            raw=(CACHE/name).read_bytes()
            profile=dict(id=identifier,folder='ine',publisher='INE',sourceId='F005',
                         family='INE · '+entry['operation'],license='Condiciones de reutilización del INE',
                         periods=health_periods,geography=health_geography)
            title=entry['title']
            if edition:=entry.get('edition'):
                title+=' · '+edition
            table=px_product(dict(entry,topic='ine',title=title),raw,section='salud',profile=profile)
            table['note']=entry['group']+'. '+table['note']
            if (entry['operation']=='Estadística de defunciones según la causa de muerte'
                and title.split('.',1)[0] in {'Asturias, Principado de','Balears, Illes','Cantabria',
                    'Madrid, Comunidad de','Murcia, Región de','Navarra, Comunidad Foral de','Rioja, La Rioja','Ceuta','Melilla'}
                and not any(t['level'] in {'community','province'} for t in table['territories'])):
                location=title.split('.',1)[0]
                territory=place(location,'community')
                table['territories']=[territory if territory['level']=='community' else no_geometry(location)]
            health_units(table)
            tables.append(table)
        except (OSError,ValueError,KeyError,AssertionError) as error:
            reason=errors.get(name,'Distribución no descargada') if isinstance(error,FileNotFoundError) else str(error)
            gaps.append({**entry,'reason':reason[:300] or type(error).__name__})
    tables.sort(key=lambda t:(norm(t['family']),norm(t['label']),t['id']))
    return tables,gaps


def origin(entry, identifier, raw):
    return dict(id=identifier,url=entry['download'],bytes=len(raw),sha256=sha(raw))


def product(entry, identifier, family, publisher, unit, note, raw, **spec):
    return dict(id=identifier,title=entry['title'],label=entry['title'],family=family,
                publisher=publisher,sourceId=entry['sourceId'],sourceUrl=entry['table'],
                downloadUrl=entry['download'],unit=unit,note=note,
                license='Condiciones de reutilización de '+publisher,sourceTables=[origin(entry,identifier,raw)],**spec)


def eurostat(entry, raw):
    spec,cells,axes,flags=jsonstat_grid(json.loads(raw),
        {'freq':'Frecuencia','unit':'Unidad','facility':'Tipo de establecimiento','bedtype':'Tipo de cama'})
    assert any(t['level']=='community' for t in spec['territories'])
    dimension=next(d for d in spec['dimensions'] if d['name']=='Unidad')
    table=product(entry,130001,'Eurostat · Recursos asistenciales','Eurostat','Según la unidad seleccionada',
        'Ámbitos de España publicados por Eurostat. Conserva por separado los recuentos, las tasas '
        'y las marcas de calidad. Consulta los metadatos de Eurostat para los cambios nacionales de comparabilidad.',
        raw,**spec,unitsByCategory=dict(dimension='Unidad',values={v:v for v in dimension['values']}))
    return [publish_grid('eurostat',table,cells,axes,flags,section='salud')]


def main():
    manifest=json.loads(MANIFEST.read_bytes())
    errors=json.loads((CACHE/'errors.json').read_bytes())
    ine,gaps=ine_tables(manifest,errors)
    tables={'ine':ine,'sanidad':[],'eurostat':[],'isciii':[],'ont':[],'oms':[],'aesan':[],'oeda':[],'comunidad-madrid':[]}
    geography=[]
    from health_distributions import aladino, hospital, expenditure, waiting, transplant, primary_care, pharmacy, who, oeda
    from health_geography import catalunya_points, madrid_directory
    from health_surveillance import surveillance
    connectors = {
        'cnh-2025.xlsx':('sanidad',hospital),
        'egsp.xls':('sanidad',expenditure),
        'egsp-1988-2005.xls':('sanidad',expenditure),
        'sisle-2025.pdf':('sanidad',waiting),
        'ont-2025.pdf':('ont',transplant),
        'hospitales-beds.json':('eurostat',eurostat),
        'momo.csv':('isciii',surveillance),
        'kairos.csv':('isciii',surveillance),
        'siap-2026.xlsx':('sanidad',primary_care),
        'urgencias-2026.xlsx':('sanidad',primary_care),
        'sanidad-madrid.csv':('comunidad-madrid',madrid_directory),
        'oms-WHOSIS_000001.json':('oms',who),
        'oms-WHOSIS_000002.json':('oms',who),
        'aladino-resumen.html':('aesan',aladino),
        'oeda-2025.pdf':('oeda',oeda),
    }
    for name,entry in manifest['external'].items():
        path=CACHE/name
        try:
            if name=='sanidad-catalunya.csv':
                geography.append(catalunya_points(entry,path.read_bytes(),REVISION))
                continue
            folder,parse=connectors[name]
            products=parse(entry,path) if parse is surveillance else list(parse(entry,path.read_bytes()))
            assert products,name
            tables[folder].extend(products)
        except (OSError,ValueError,KeyError,AssertionError) as error:
            reason=errors.get(name,'Distribución no descargada') if isinstance(error,FileNotFoundError) else str(error)
            gaps.append({**entry,'reason':reason[:300] or type(error).__name__})
    if manifest.get('pharmacy'):
        tables['sanidad'].append(pharmacy(manifest['pharmacy']))
    for folder,products in tables.items():
        write_index(folder,products)
    (ROOT/'registry/health-geography.json').write_bytes(encode(geography))
    (ROOT/'registry/health-capture.json').write_bytes(encode(dict(
        revision=REVISION, operations=manifest['operations'],ineTableCount=len(manifest['ine']),
        ineProducts=len(ine),productCount=sum(map(len,tables.values()))+len(geography),
        coverage=dict(Counter(table['sourceId'] for group in tables.values() for table in group)),
        gaps=list({gap['download']:gap for gap in gaps}.values()))))


if __name__=='__main__':
    main()
