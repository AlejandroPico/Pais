"""Preserve every cell of the EDUCAbase and UNIVbase distributions captured for F11."""
from collections import Counter, defaultdict
import argparse
import gzip
import json
import math
from pathlib import Path
import re

from commerce_bde import GEO, NATIONAL
from demography_collect import ROOT, encode, norm, sha
from fiscal_workbooks import area, no_geometry
from funding_collect import COMMUNITY_NAMES, NUTS_COMMUNITIES

CACHE = ROOT / '.cache/f11'
OUTPUT = ROOT / 'datos/educacion'
REVISION = '2026-11-17'
FAMILIES = {
    'edcentre':'EDUCAbase · Centros y unidades',
    'edcentres':'EDUCAbase · Centros y servicios',
    'edprof':'EDUCAbase · Profesorado y personal',
    'edseries':'EDUCAbase · Matrícula y escolarización',
    'edresult':'EDUCAbase · Graduación y resultados académicos',
    'edtic':'EDUCAbase · Tecnologías en los centros',
    'edbibliotecas':'EDUCAbase · Bibliotecas escolares',
    'edfpactual':'EDUCAbase · Formación Profesional 2024–2025',
    'edfprend':'EDUCAbase · Seguimiento de cohortes de FP',
    'edfpinsercion':'EDUCAbase · Inserción laboral de titulados de FP',
    'edbecas':'EDUCAbase · Becas y ayudas 2024–2025',
    'edfin':'EDUCAbase · Gasto público en educación',
    'edabandono':'EDUCAbase · Indicadores de la encuesta de fuerza de trabajo',
    'uesiiu':'SIIU · Universidades, centros y titulaciones',
    'uepersonal':'SIIU · Personal de las universidades',
    'uebecas':'SIIU · Becas y ayudas',
    'uerendimiento':'SIIU · Rendimiento académico',
    'uefinanciacion':'SIIU · Financiación y gasto',
    'ueinternacionalizacion':'SIIU · Internacionalización',
    'ine':'INE · Encuesta de Gasto de los Hogares en Educación',
}
STUDENT_GROUPS = ('Matrícula de Grado y Ciclos', 'Egreso de Grado y Ciclos', 'Nuevo ingreso en Grado',
                  'Matrícula de Máster', 'Egreso de Máster', 'Matrícula de Doctorado', 'Egreso de Doctorado',
                  'Histórico del sistema universitario', 'Histórico de Grado y Ciclos', 'Histórico de Máster')
COURSE_FALLBACK = {'edfpactual':'2024-2025','edbibliotecas':'2023-2024','edbecas':'2024-2025'}
PLACE_ALIASES = {
    'asturias':'03','principado de asturias':'03','asturias, principado de':'03',
    'baleares':'04','balears':'04','balears, illes':'04',
    'castilla y leon':'07','castilla leon':'07','castilla la mancha':'08','castilla.la mancha':'08','catalunya':'09',
    'valencia':'10','valenciana, comunidad':'10','madrid, comunidad de':'13','madrid':'13',
    'murcia, region de':'14','murcia':'14','navarra, comunidad foral de':'15','navarra':'15',
    'euskadi':'16','rioja, la':'17','rioja':'17','ciudad de ceuta':'18','ciudad de melilla':'19',
}
QUOTED = re.compile(r'"((?:""|[^"])*)"')
FIELD = re.compile(r'(?m)^([A-Z][A-Z0-9-]*)(?:\("((?:""|[^"])*)"\))?(?:\[[^\]]+\])?\s*=\s*((?:"(?:""|[^"])*"|[^";])*);')
DATA_START = re.compile(rb'(?m)^DATA\s*=')


def clean_label(name):
    return ' '.join(name.split())


def capture_id(source_url):
    return 110000000 + int(sha(source_url.encode())[:8],16)%800000000


def period(value, *, course=False):
    label = clean_label(value)
    matched = re.match(r'^(?:curso\s+)?(\d{4})\s*[-–/]\s*(\d{2}|\d{4})(?!\d)',label,re.I)
    if matched:
        start, end = matched.groups()
        assert int(end[-2:])==(int(start)+1)%100, label
        return dict(id=start+'M09',label=label)
    if matched := re.match(r'^(\d{4})(?!\d)(.*)$',label):
        return dict(id=matched[1]+('M09' if course else ''),label=label)
    raise ValueError('Periodo no reconocido: '+label)


def academic_axis(labels):
    return all(re.match(r'^(?:curso\s+)?\d{4}\s*[-–/]\s*\d{2}',label,re.I) for label in labels)


def geographical_axis(label):
    candidate = norm(label)
    if re.match(r'^comunidad(?:es)? autonomas?\s*/\s*provincias?',candidate):
        return 'mixed'
    if re.match(r'^(comunidad(?:es)?(?: y ciudades)? autonomas?|cc\.?aa\.?|ccaa|comunidad de residencia)\b',candidate):
        return 'community'
    if re.match(r'^provincias?\b',candidate):
        return 'province'
    return None


def place(label, level, published_code=''):
    if level=='mixed':
        level='community' if re.match(r'^\s*\d{2}\s',label) else 'province'
    key = norm(re.sub(r'(?:\s*\([^()]*\))+\s*$', '', label))
    key = re.sub(r'\s*-\s*','-',key)
    key = re.sub(r'\s+,',',',key)
    key = re.sub(r'^\d{2}\s*[-.:]?\s+', '', key)
    if re.fullmatch(r'(?:total(?: nacional| espana)?|espana|nacional|todas? las comunidades autonomas)',key):
        return NATIONAL
    if level=='community':
        published = re.fullmatch(r'CA(\d{2})',published_code)
        code = PLACE_ALIASES.get(key) or GEO.get((level,key))
        if published and published[1] in COMMUNITY_NAMES:
            if code and code!=published[1]:
                raise ValueError(f'Código territorial en conflicto: {label} {published_code}')
            code=published[1]
        if code:
            return area(COMMUNITY_NAMES[code],level,code)
    else:
        code=GEO.get((level,key))
        for alternative in key.split('/'):
            code=code or GEO.get((level,alternative.strip()))
        if code:
            return area(clean_label(label),level,code)
    return no_geometry(label)


def strings(body):
    return [match.replace('""','"') for match in QUOTED.findall(body)]


def metadata(raw):
    marker = DATA_START.search(raw)
    if not marker:
        raise ValueError('Fichero servido sin bloque PC-Axis DATA')
    head = raw[:marker.start()]
    encoding = re.search(rb'(?im)^CODEPAGE="([^"]+)"',head)
    codec = encoding[1].decode('ascii') if encoding else 'cp1252'
    fields = {(name,axis or ''):strings(value) for name,axis,value in FIELD.findall(head.decode(codec))}
    return fields,raw[marker.end():].strip().removesuffix(b';').strip()


def data_values(body):
    missing = Counter()
    cells = []
    for match in re.finditer(rb'"([^"]*)"|(\S+)',body):
        raw_flag, raw_number = match.groups()
        if raw_flag is not None:
            flag = raw_flag.decode('ascii',errors='replace') or 'Celda vacía'
            missing[flag]+=1
            cells.append(flag)
            continue
        value = float(raw_number)
        if not math.isfinite(value):
            raise ValueError('La fuente contiene un número no finito')
        cells.append(int(value) if value.is_integer() else value)
    return cells,dict(missing)


def top_geography(axes, fields, labels):
    for index,name in enumerate(axes):
        level=geographical_axis(name)
        if not level:
            continue
        codes=fields.get(('CODES',name),['']*len(labels[index]))
        territories=[place(value,level,code) for value,code in zip(labels[index],codes,strict=True)]
        repeat=Counter(a['id'] for a in territories)
        return index,[a if repeat[a['id']]==1 else no_geometry(f'{labels[index][i]} · categoría {i+1}')
                      for i,a in enumerate(territories)]
    institutional=any(norm(name) in {'universidad','universidades','centro universitario','centro'} for name in axes)
    return -1,[no_geometry('Consulta de instituciones') if institutional else NATIONAL]


def publish_grid(folder, table, cells, axes, flags=None):
    output = OUTPUT/folder
    output.mkdir(parents=True,exist_ok=True)
    rows = len(cells)
    shape = {-2:len(table['territories']),-1:len(table['periods']),
             **{i:len(d['values']) for i,d in enumerate(table['dimensions'])}}
    assert set(shape)==set(axes) and len(axes)==len(shape)
    assert math.prod(shape[axis] for axis in axes)==rows,(table['sourceUrl'],rows,shape)
    payload = dict(axes=axes,cells=cells)
    if flags:
        payload['flags']=flags
    uncompressed = encode(payload)
    raw = gzip.compress(uncompressed,compresslevel=6,mtime=0)
    name = str(table['id'])+'-main.json.gz'
    (output/name).write_bytes(raw)
    return {**table,'dataFolder':f'educacion/{folder}','rows':rows,'shards':[
        dict(id='main',file=name,rows=rows,bytes=len(raw),sha256=sha(raw),contentSha256=sha(uncompressed))]}


def px_product(info, raw):
    fields, data = metadata(raw)
    axes = fields.get(('STUB',''),[])+fields.get(('HEADING',''),[])
    labels = [fields[('VALUES',name)] for name in axes]
    start = info['topic'].split('-')
    group = start[0]
    family = ('SIIU · '+STUDENT_GROUPS[int(start[1])-1] if group=='uedirectory' else FAMILIES[group])
    geo_index, territories = top_geography(axes,fields,labels)
    timed = [i for i,name in enumerate(axes)
             if norm(name) in {'periodo','curso academico','ano','ano academico','anio','ano de referencia','time'}
             or academic_axis(labels[i])]
    time_index = timed[0] if timed else -1
    if time_index>=0:
        periods = [period(entry,course='curso' in norm(axes[time_index])) for entry in labels[time_index]]
    else:
        edition = info.get('edition') or COURSE_FALLBACK.get(group)
        periods = [period(edition) if edition else dict(id='0000',label='Periodo no indicado en la tabla')]
    assert len({entry['id'] for entry in periods})==len(periods),periods
    dimensions, grid_axes = [], []
    for i,name in enumerate(axes):
        if i==geo_index:
            grid_axes.append(-2)
        elif i==time_index:
            grid_axes.append(-1)
        else:
            grid_axes.append(len(dimensions))
            dimensions.append(dict(name=name,values=labels[i]))
    if geo_index<0:
        grid_axes.append(-2)
    if time_index<0:
        grid_axes.append(-1)
    cells, missing = data_values(data)
    code = capture_id(info['download'])
    note = ('Dimensión territorial original: '+axes[geo_index]+'. ' if geo_index>=0 else 'Ámbito según las dimensiones de la tabla. ')
    label = info['title']
    details = clean_label(''.join(fields.get(('NOTE',''),[])))
    publisher,source_id,folder = ('INE','F005','ine') if group=='ine' else (
        ('Sistema Integrado de Información Universitaria','F074','siiu') if group.startswith('ue') else ('EDUCAbase','F073','educabase'))
    public_fields = dict(id=code,label=label,title=label,family=family,sourceId=source_id,publisher=publisher,
                         note=note+(details[:1200] if details else 'Conserva las categorías y los estados de la edición original.'),
                         unit=clean_label(' / '.join(fields.get(('UNITS',''),[]))) or 'Consultar la unidad en origen',
                         license='Condiciones de reutilización del ministerio editor',sourceUrl=info['table'],downloadUrl=info['download'],
                         territories=territories,periods=periods,dimensions=dimensions,missingTokens=missing,
                         sourceTables=[dict(id=code,url=info['download'],sha256=sha(raw),bytes=len(raw),
                                            notes=[details] if details else [])])
    unit_key=norm(public_fields['unit'])
    if 'importe' in unit_key and ('miles de euros' in unit_key or 'miles de euro' in unit_key):
        for dimension in dimensions:
            if not any('importe' in norm(value) for value in dimension['values']):
                continue
            units={}
            for value in dimension['values']:
                name=norm(value)
                if 'importe' in name:
                    units[value]='Miles de euros'
                elif 'becario' in name or 'beneficiario' in name:
                    units[value]='Beneficiarios'
                elif 'beca' in name or 'ayuda' in name:
                    units[value]='Becas y ayudas'
            public_fields['unitsByCategory']=dict(dimension=dimension['name'],values=units)
            break
    if group=='ine':
        public_fields['license']='Condiciones de reutilización del INE'
        indicator=next((d for d in dimensions if norm(d['name'])=='indicador'),None)
        if indicator and 'miles de euros' in unit_key:
            units={}
            for value in indicator['values']:
                measure=norm(value)
                if measure=='gasto total':
                    units[value]='Miles de euros'
                elif measure.startswith('gasto medio'):
                    units[value]='Euros'
                elif measure.startswith('numero de estudiantes'):
                    units[value]='Estudiantes'
            if units:
                public_fields['unitsByCategory']=dict(dimension=indicator['name'],values=units)
    return publish_grid(folder,public_fields,cells,grid_axes)


EUROSTAT_TITLES = {
    'edat_lfse_16':'Abandono temprano de la educación y la formación',
    'edat_lfse_04':'Nivel educativo de la población en hogares privados',
    'trng_lfse_04':'Participación en educación y formación durante las últimas cuatro semanas',
}
EUROSTAT_DIMENSIONS = {'freq':'Frecuencia','unit':'Unidad','sex':'Sexo','age':'Edad','isced11':'Nivel CINE 2011'}


def eurostat_products():
    for offset,(dataset,title) in enumerate(EUROSTAT_TITLES.items(),1):
        raw = (CACHE/(dataset+'.json')).read_bytes()
        url = (CACHE/(dataset+'.url')).read_text(encoding='utf-8')
        source_url = 'https://ec.europa.eu/eurostat/databrowser/view/'+dataset+'/default/table'
        original = json.loads(raw)
        assert original['id'] and len(original['id'])==len(original['size'])
        dimensions, axes = [], []
        for code in original['id']:
            category = original['dimension'][code]['category']
            codes = sorted(category['index'],key=category['index'].get)
            labels = [category.get('label',{}).get(k,k) for k in codes]
            if code=='geo':
                territories=[]
                for k,label in zip(codes,labels,strict=True):
                    community=NUTS_COMMUNITIES.get(k)
                    territories.append(NATIONAL if k=='ES' else area(COMMUNITY_NAMES[community],'community',community)
                                       if community else no_geometry(label+' ('+k+')'))
                axes.append(-2)
            elif code=='time':
                periods = [period(k) for k in codes]
                axes.append(-1)
            else:
                if code=='sex':
                    labels = [dict(T='Total',M='Hombres',F='Mujeres').get(k,v) for k,v in zip(codes,labels,strict=True)]
                dimensions.append(dict(name=EUROSTAT_DIMENSIONS.get(code,original['dimension'][code]['label']),
                                       values=labels))
                axes.append(len(dimensions)-1)
        values=original.get('value',{})
        flags=original.get('status',{})
        count=math.prod(original['size'])
        missing='Sin dato en la respuesta'
        cells=[values.get(str(i),missing) for i in range(count)]
        metadata=dict(id=990110+offset,label=title,title=title,family='Eurostat · Educación y formación',sourceId='F130',
                      publisher='Eurostat',note='España y territorios NUTS 2 consultados con la API. '
                      'Conserva los indicadores, las categorías y las marcas de calidad de la encuesta.',
                      unit='Porcentaje',license='Política de reutilización de Eurostat',
                      sourceUrl=source_url,downloadUrl=url,territories=territories,periods=periods,
                      dimensions=dimensions,missingTokens={missing:cells.count(missing)},
                      sourceTables=[dict(id=990110+offset,url=url,bytes=len(raw),sha256=sha(raw))])
        yield publish_grid('eurostat',metadata,cells,axes,flags)


def main(resume):
    manifest = {}
    errors = {}
    for name in ('tables.json','extra-tables.json'):
        path=CACHE/name
        if path.exists():
            manifest.update(json.loads(path.read_bytes()))
    for name in ('download-errors.json','extra-errors.json'):
        path=CACHE/name
        if path.exists():
            errors.update(json.loads(path.read_bytes()))
    tables = defaultdict(list)
    gaps = []
    identifiers = set()
    known = {}
    if resume:
        for folder in ('educabase','siiu'):
            path=OUTPUT/folder/'index.json'
            if path.exists():
                tables[folder]=json.loads(path.read_bytes())['tables']
                identifiers.update(t['id'] for t in tables[folder])
                known.update({t['downloadUrl']:t for t in tables[folder]})
    for position,(filename,info) in enumerate(sorted(manifest.items()),1):
        if info['download'] in known:
            table=known[info['download']]
            raw=(CACHE/filename).read_bytes()
            assert sha(raw)==table['sourceTables'][0]['sha256'], info['download']
            fields,_=metadata(raw)
            axes=fields.get(('STUB',''),[])+fields.get(('HEADING',''),[])
            _,places=top_geography(axes,fields,[fields[('VALUES',name)] for name in axes])
            assert len(places)==len(table['territories'])
            table['territories']=places
            continue
        try:
            table = px_product(info,(CACHE/filename).read_bytes())
        except (ValueError, AssertionError, KeyError, OSError) as error:
            reason=errors.get(filename,'Distribución PC-Axis sin descargar') if isinstance(error,FileNotFoundError) else str(error)
            gaps.append({**info,'reason':reason[:220]})
        else:
            assert table['id'] not in identifiers,table['sourceUrl']
            identifiers.add(table['id'])
            tables[Path(table['dataFolder']).name].append(table)
        if position%100==0:
            print('Revisadas',position,'de',len(manifest),flush=True)
    tables['eurostat'] = list(eurostat_products())
    for folder,products in tables.items():
        products.sort(key=lambda t:(t['family'],norm(t['label']),t['id']))
        (OUTPUT/folder/'index.json').write_bytes(encode(dict(revision=REVISION,tables=products)))
        print(folder,len(products),sum(t['rows'] for t in products),flush=True)
    manifest_out = ROOT/'registry/education-capture.json'
    counters = dict(reviewed=len(manifest),available=len(identifiers),gaps=gaps)
    ine_capture=CACHE/'ine-summary.json'
    if ine_capture.exists():
        ine=json.loads(ine_capture.read_bytes())
        for key in counters:
            counters[key]+=ine[key]
    manifest_out.write_bytes(encode(dict(revision=REVISION,**counters)))
    print('Incidencias de captura:',len(gaps),flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume',action='store_true',help='Incorporar tablas nuevas a los índices de EDUCAbase y SIIU existentes.')
    main(parser.parse_args().resume)
