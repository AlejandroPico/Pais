"""Read Ministry of Health and ONT workbooks and official PDF tables."""
from collections import Counter, defaultdict
from html import unescape
from io import BytesIO
import re
import sys
import json

from affiliation_collect import workbook
from commerce_bde import NATIONAL
from commerce_distributions import publish
from demography_collect import norm
from education_collect import place
from fiscal_workbooks import area, no_geometry
from funding_collect import COMMUNITY_NAMES
from health_capture import CACHE
from health_collect import OUTPUT, origin as source_metadata, product
from science_collect import PROVINCES

MINISTRY='Ministerio de Sanidad'
THOUSANDS='Miles de euros'
PCT='Porcentaje'
DAY='Días'
RATE='Pacientes por 1.000 habitantes'
PATIENTS='Pacientes'
COMMUNITY_ALIASES={'pdo de asturias':'03','p. de asturias':'03','principado de asturias':'03',
    'islas baleares':'04','baleares':'04','illes balears':'04','illes baleares':'04','com. valenciana':'10',
    'valenciana':'10','c. foral de navarra':'15','foral de navarra':'15','region de murcia':'14',
    'c. valenciana':'10','castilla leon':'07','castilla la mancha':'08','rioja':'17',
    'total sns':'national','sistema nacional de salud':'national','sns':'national'}
SPECIALTIES=('Cirugía General y de Digestivo','Ginecología','Oftalmología','ORL','Traumatología',
    'Urología','Cirugía Cardiaca','Angiología / Cirugía Vascular','Cirugía Maxilofacial',
    'Cirugía Pediátrica','Cirugía Plástica','Cirugía Torácica','Neurocirugía','Dermatología','Total')
PROCEDURES=('Catarata','Hernia inguinal / crural','Prótesis de cadera','Artroscopia','Varices MM.II.',
    'Colecistectomía','Hallux valgus','Adenoamigdalectomía','Hipertrofia benigna de próstata',
    'Quiste pilonidal','Túnel carpiano','Prótesis de rodilla','Cirugía cardiaca valvular',
    'By-pass coronario','Histerectomía')
CONSULTATIONS=('Ginecología','Oftalmología','Traumatología','Dermatología','ORL','Neurología',
    'Cirugía General y de Digestivo','Urología','Digestivo','Cardiología','Total')
EQUIPMENT={'P':'TAC','Q':'RMN','R':'GAM','S':'HEM','T':'ASD','U':'LIT','V':'BCO','W':'ALI',
    'X':'SPECT','Y':'PET','Z':'MAMO','AA':'DO','AB':'DIAL'}
YEAR=re.compile(r'((?:19|20)\d{2})(?:\.0|[a-z]|\(\*\))?$')


def clean(value):
    return ' '.join(str(value).split())


def number(value, *, decimal_comma=False):
    text=clean(value)
    if decimal_comma:
        text=text.replace('.','').replace(',','.')
    if re.fullmatch(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?',text):
        n=float(text)
        return (int(n) if n.is_integer() else n),''
    return None,clean(value) or 'Celda vacía en origen'


def community(label):
    normalized=re.sub(r'\s*[-–]\s*','-',norm(label))
    key=re.sub(r'^(?:comunidad (?:autonoma )?(?:de |del )?|ciudad autonoma de )','',normalized)
    key=re.sub(r'^(?:la|las) (?=illes|region)','',key)
    code=COMMUNITY_ALIASES.get(norm(label)) or COMMUNITY_ALIASES.get(key)
    if code=='national':
        return NATIONAL
    if code:
        return area(COMMUNITY_NAMES[code],'community',code)
    return place(key,'community')


def distribute(entry, raw, identifier, folder, family, publisher, note, records, dimensions, units, original=None):
    output=OUTPUT/folder
    output.mkdir(parents=True,exist_ok=True)
    table=product(entry,identifier,family,publisher,'Según indicador',note,raw)
    if original:
        target=output/'originales'/original
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
        relative='originales/'+original
        table['sourceTables'][0]['originalFile']=relative
        table.update(snapshotFile=relative,snapshotLabel='Descarga de la edición consultada')
    return publish(folder,table,records,dimensions,units,section='salud')


def hospital(entry,raw):
    directory=list(workbook(raw))[1:]
    structure={row['B']:row for row in list(workbook(raw,'xl/worksheets/sheet2.xml'))[1:] if row.get('B')}
    directory=[row for row in directory if row.get('B')]
    assert len({row['B'] for row in directory})==len(directory)>700
    period='2025'
    tag='Edición 2025 · fecha de referencia 31/12/2024'
    coverage={}
    totals=Counter()
    beds_missing=set()
    details=[]
    equipment=[]
    centers={}
    bed_title='Camas publicadas'
    center_title='Registros del directorio hospitalario'
    for row in directory:
        code=row['F'][:5]
        assert len(row['F'])==6 and code[:2]==row['H'],row['B']
        province=area(PROVINCES[row['H']],'province',row['H'])
        region=area(COMMUNITY_NAMES[row['J']],'community',row['J'])
        town={**area(row['G'],'municipal',code),'provinceCode':row['H']}
        bed,status=number(row.get('M',''))
        classification=row['O']
        dependence=row['Q']
        for territory in (NATIONAL,region,province,town):
            coverage[territory['id']]=territory
            for selector in (('Total','Total'),('Clase de centro',classification),('Dependencia funcional',dependence)):
                key=(territory['id'],*selector)
                totals[(*key,center_title)]+=1
                totals[(*key,bed_title)]+=bed or 0
                if bed is None:
                    beds_missing.add(key)
        center=no_geometry(f'{row["C"]} · {row["G"]} · CNH {row["B"]}')
        centers[row['B']]=center
        details.append((center,period,tag,(bed_title,),bed,status))
    for identifier,equipment_row in structure.items():
        center=centers.get(identifier) or no_geometry(
            f'{equipment_row["C"]} · {equipment_row["E"]} · CNH {identifier}')
        for col,measure in EQUIPMENT.items():
            equipment.append((center,period,tag,(measure,),*number(equipment_row.get(col,''))))
    records=[(coverage[key],period,tag,(measure,classification,selection),
              None if (key,classification,selection) in beds_missing and measure==bed_title else value,
              'Algún registro sin dato de camas' if (key,classification,selection) in beds_missing and measure==bed_title else '')
             for (key,classification,selection,measure),value in totals.items()]
    origin='cnh-2025.xlsx'
    family='Sanidad · Catálogo Nacional de Hospitales'
    notes=('Edición 2025 con datos a 31/12/2024. El directorio identifica centros, sedes y complejos. '
           'Conserva los registros que figuran en la hoja y las camas publicadas. '
           'La descarga contiene las fichas originales, altas, bajas, estructura funcional y diccionarios.')
    yield distribute(entry,raw,130100,'sanidad',family,MINISTRY,notes,records,
        ('Indicador','Clasificación','Categoría'),{bed_title:'Camas',center_title:'Registros'},origin)
    yield distribute({**entry,'title':'Camas por centro del catálogo de hospitales'},raw,130101,'sanidad',family,MINISTRY,
        notes+' Consulta individual por código CNH. El fichero indica el municipio y la dirección.',
        details,('Indicador',),{bed_title:'Camas'},origin)
    yield distribute({**entry,'title':'Equipamiento por centro del catálogo de hospitales'},raw,130102,'sanidad',family,MINISTRY,
        notes+' Las siglas son las de la hoja de estructura funcional. DC se conserva como estado de origen.',
        equipment,('Indicador',),dict.fromkeys(EQUIPMENT.values(),'Equipos publicados'),origin)


def primary_care(entry,raw):
    emergency='Urgencias' in entry['title']
    origin='urgencias-2026.xlsx' if emergency else 'siap-2026.xlsx'
    indicators=({'B':('Dispositivos de urgencias extrahospitalarias','Dispositivos')} if emergency else {
        'B':('Áreas de salud','Áreas'),'C':('Zonas básicas de salud','Zonas'),
        'D':('Centros de atención primaria','Centros'),'E':('Centros de salud','Centros'),
        'F':('Consultorios locales','Consultorios')})
    records=[]
    for row in workbook(raw):
        label=row.get('A','')
        territory=community(label)
        if norm(label)=='ceuta y melilla':
            territory=no_geometry('Ceuta y Melilla · agregado publicado por INGESA')
        if territory['level']=='unlocated':
            if norm(label)!='ceuta y melilla':
                continue
        for col,(label,_) in indicators.items():
            value=row.get(col,'')
            if col=='B' and not emergency:
                value=sum(int(n) for n in re.findall(r'(?:^|/\s*)(\d+)',value))
            records.append((territory,'2025-12-31','31/12/2025 · edición 2026',(label,),*number(value)))
    assert len({r[0]['id'] for r in records})==19
    family='Sanidad · Oferta de atención primaria y urgencias'
    yield distribute(entry,raw,130181 if emergency else 130180,'sanidad',family,MINISTRY,
        'Hoja Datos generales del catálogo. Conserva las cifras publicadas y las definiciones del SIAP. '
        'El fichero original incluye el directorio de centros y ámbitos sanitarios de la edición. '
        'INGESA publica Ceuta y Melilla como un agregado en esta hoja.',
        records,('Indicador',),dict(indicators.values()),origin)


def pharmacy(entries):
    categories={'Envases facturados':'Envases','Gasto farmacéutico de receta oficial':'Euros',
                'Gasto medio por envase facturado':'Euros por envase'}
    records, sources, source_by_period=[],[],{}
    titles=('Dato mensual','Dato mensual del mismo mes del año anterior','Variación mensual interanual',
            'Acumulado del año hasta el mes','Acumulado equivalente del año anterior','Variación interanual del acumulado',
            'Acumulado móvil de doce meses','Acumulado móvil equivalente del año anterior',
            'Variación interanual del acumulado móvil')
    units={}
    for period,url in entries.items():
        path=CACHE/f'farmacia-{period}.html'
        raw=path.read_bytes()
        identifier=int(period.replace('M',''))
        source_by_period[period]=identifier
        sources.append(source_metadata({'download':url},identifier,raw))
        html=raw.decode('utf-8')
        tables=re.findall(r'<table\b.*?</table>',html,re.I|re.S)
        found=0
        for table in tables:
            matrix=[]
            for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',table,re.I|re.S):
                matrix.append([clean(unescape(re.sub(r'<[^>]*>','',value))) for value in
                    re.findall(r'<(?:th|td)\b[^>]*>(.*?)</(?:th|td)>',row,re.I|re.S)])
            if not matrix or len(matrix[0])!=2:
                continue
            heading=norm(matrix[0][1])
            kind=('Gasto medio por envase facturado' if heading.startswith('gasto medio') else
                  'Gasto farmacéutico de receta oficial' if heading.startswith('gasto farmaceutico') else
                  'Envases facturados' if 'envases facturados' in heading else None)
            if not kind:
                continue
            found+=1
            assert matrix[2][:2]==[period[:4],str(int(period[:4])-1)],matrix[2]
            size=len(matrix[2])
            assert size in {6,9},(period,matrix[2])
            observed=set()
            for fields in matrix[3:]:
                if len(fields)!=size+1:
                    continue
                territory=community(fields[0])
                assert territory['level']!='unlocated',fields[0]
                observed.add(territory['code'])
                for i,(value,tag) in enumerate(zip(fields[1:],titles[:size],strict=True)):
                    label=f'{kind} · {tag}'
                    units[label]=PCT if i%3==2 else categories[kind]
                    records.append((territory,period,f'{period[5:]}/{period[:4]}',(label,),*number(value,decimal_comma=True)))
            assert observed=={*COMMUNITY_NAMES,'ES'},(period,observed)
        assert found==3,(period,found)
    label='Facturación de recetas médicas del SNS'
    start=next(iter(entries.values()))
    table=dict(id=130190,label=label,family='Sanidad · Prestación farmacéutica',publisher=MINISTRY,
        sourceId='F067',sourceUrl=start.rsplit('/',1)[0].rsplit('/',1)[0]+'/home.htm',downloadUrl=start,
        license='Condiciones de reutilización del Ministerio de Sanidad',sourceTables=sources,
        note='Facturación en farmacias de recetas oficiales del SNS. Distingue mes de publicación, acumulado anual, '
             'acumulado móvil de doce meses, periodo equivalente del año anterior y variación publicada. '
             'Conserva el enlace de cada corte.')
    return publish('sanidad',table,records,('Indicador',),units,section='salud',source_by_period=source_by_period)


def who(entry,raw):
    response=json.loads(raw)
    assert not response.get('@odata.nextLink'),'La OMS ha paginado esta distribución.'
    records=[]
    sex={'SEX_BTSX':'Total','SEX_MLE':'Hombres','SEX_FMLE':'Mujeres'}
    measures={'NumericValue':'Estimación','Low':'Límite inferior','High':'Límite superior'}
    for row in response['value']:
        assert row['SpatialDim']=='ESP' and row['TimeDimType']=='YEAR' and row['Dim1Type']=='SEX'
        year=row['TimeDimensionValue']
        for field,name in measures.items():
            value=row[field]
            records.append((NATIONAL,year,year,(name,sex[row['Dim1']]),value,
                            '' if value is not None else 'Sin valor publicado'))
    identifier=130350+int(entry['indicator'].split('_')[1])
    dates=sorted({r['Date'][:10] for r in response['value']})
    yield distribute(entry,raw,identifier,'oms','OMS · Estimaciones de esperanza de vida','Organización Mundial de la Salud',
        f'Estimaciones nacionales de la OMS, por sexo. Fecha de actualización en esta captura: {dates[-1]}. '
        'Distingue la estimación y los límites de incertidumbre de la distribución de origen.',
        records,('Indicador','Sexo'),dict.fromkeys(measures.values(),'Años'))


def aladino(entry,raw):
    body=clean(unescape(re.sub(r'<[^>]+>', ' ',raw.decode('utf-8'))))
    match=re.search(r'tasa de exceso de peso infantil en España se situó en el (\d+,\d+)% en (\d{4})'
                    r' ante al (\d+,\d+)% que hubo en (\d{4})',body)
    assert match and {match[2],match[4]}=={'2019','2023'},'No se ha localizado el indicador en el resumen oficial.'
    measure='Prevalencia estimada de exceso de peso'
    records=[(NATIONAL,year,year,(measure,),*number(pct,decimal_comma=True))
             for pct,year in ((match[1],match[2]),(match[3],match[4]))]
    yield distribute(entry,raw,130370,'aesan','AESAN · Alimentación y obesidad infantil','AESAN',
        'Resumen oficial de avance publicado el 25/09/2024. Población escolar de 6 a 9 años en España. '
        'El exceso de peso reúne sobrepeso y obesidad según el estudio ALADINO.',
        records,('Indicador',),{measure:PCT})


def oeda(entry,raw):
    doc=pdf_pages(raw)
    family='OEDA · EDADES'
    publisher='Observatorio Español de las Drogas y las Adicciones'
    measures=('Alguna vez en la vida','Últimos 12 meses','Últimos 30 días','Consumo diario')
    numeric=re.compile(r'\d+(?:,\d+)|[-–]')
    for i,(page,number_in_report,measure) in enumerate(zip(
            (31,32,33,33),(11,12,13,14),measures,strict=True)):
        report=doc[page-1].extract_text(extraction_mode='layout').split(f'Tabla 1.1.{number_in_report}.',1)[1]
        report=re.split(r'(?m)^(?:Tabla|Figura|Fuente|FUENTE)',report,maxsplit=1)[0]
        lines=[line.strip() for line in report.splitlines() if line.strip()]
        row=next(j for j,line in enumerate(lines) if re.fullmatch(r'\d{4}(?:\s+\d{4}){10,}',line))
        years=lines[row].split()
        assert len(years) in {14,15} and years[-1]=='2024',years
        records=[]
        wrapped=[]
        for line in lines[row+1:]:
            values=list(numeric.finditer(line))
            if len(values)<len(years):
                if values and any(',' in value.group() for value in values):
                    assert line.startswith(('*','Nota')),line
                if not values:
                    wrapped.append(line)
                continue
            cells=values[-len(years):]
            label=clean(' '.join([*wrapped,line[:cells[0].start()]]))
            wrapped.clear()
            assert label
            records.extend((NATIONAL,year,year,(label,),*number(cell.group(),decimal_comma=True))
                           for year,cell in zip(years,cells,strict=True))
        assert len(records)==(270,270,252,70)[i],(measure,len(records))
        title='Consumo de sustancias psicoactivas · '+measure
        units=dict.fromkeys((r[3][0] for r in records),PCT)
        yield distribute({**entry,'title':title},raw,130380+i,'oeda',family,publisher,
            f'Tabla 1.1.{number_in_report} de las estadísticas OEDA 2025. Prevalencias estimadas de EDADES. '
            'Población de 15 a 64 años residente en hogares. Cada año conserva las categorías y los guiones publicados.',
            records,('Indicador',),units)
    for page,cols in ((39,9),(40,6)):
        text=doc[page-1].extract_text(extraction_mode='layout').split(f'Tabla 1.1.{25 if cols==9 else 26}.',1)[1]
        text=re.split(r'(?m)^(?:Tabla|Figura|Fuente|FUENTE)',text,maxsplit=1)[0]
        rows=[]
        variants=('Prevalencia','IC95 % inferior','IC95 % superior') if cols==9 else ('Hombres','Mujeres')
        for line in text.splitlines():
            fields=re.split(r'  +',line.strip())
            territory=community(fields[0])
            if territory['level']=='unlocated' or len(fields)!=cols+1:
                continue
            axis=[(measure,variant) for measure in measures[:3] for variant in variants]
            rows.extend((territory,'2024','2024',group,*number(cell,decimal_comma=True))
                        for group,cell in zip(axis,fields[1:],strict=True))
        assert len({row[0]['id'] for row in rows})>=19,(page,len(rows))
        title='Consumo de alcohol por comunidad · '+('prevalencia e intervalo' if cols==9 else 'por sexo')
        yield distribute({**entry,'title':title},raw,130384 if cols==9 else 130385,'oeda',family,publisher,
            'EDADES 2024. Población de 15 a 64 años residente en hogares. Mantiene cada ventana de consumo del informe.',
            rows,('Indicador','Estimación' if cols==9 else 'Sexo'),dict.fromkeys(measures[:3],PCT))


def expenditure(entry,raw):
    sys.path.insert(0,str(CACHE/'vendor'))
    import xlrd
    book=xlrd.open_workbook(file_contents=raw,on_demand=True)
    historical='1988' in entry['title']
    origin='egsp-1988-2005.xls' if historical else 'egsp.xls'
    years='1988–2005' if historical else '2002–2024'
    family='Sanidad · Gasto sanitario público '+years
    notes=('Serie histórica por clasificación original. Los años coincidentes con la edición posterior conservan la edición de origen.'
           if historical else 'Serie de cuentas satélite del Ministerio, en la edición de cierre de 2024. '
           'Los años con asterisco se publican como provisionales.')
    sheet_groups=(('tabla 5','tabla 6','tabla 7','tabla 8') if historical else ('Anexo I.1','Anexo I.2'))
    measure_titles=(('Gasto territorial consolidado','Gasto de comunidades autónomas','Gasto de corporaciones locales',
        'Transferencias de comunidades a corporaciones locales') if historical else
        ('Aportación al gasto sanitario público en relación al PIB','Aportación al gasto sanitario público por habitante'))
    annex_units=(PCT,'Euros por habitante')
    for i,(sheet_name,title) in enumerate(zip(sheet_groups,measure_titles,strict=True)):
        sheet=book.sheet_by_name(sheet_name)
        unit=THOUSANDS if historical else annex_units[i]
        header=7 if historical else 6
        periods=[(j,m[1],clean(v).removesuffix('.0')) for j,v in enumerate(sheet.row_values(header)) if (m:=YEAR.fullmatch(clean(v)))]
        assert len(periods)>10
        records=[]
        for ri in range(header+1,sheet.nrows):
            row=sheet.row_values(ri)
            region=community(clean(row[1]))
            if region['level']=='unlocated' or not any(isinstance(row[j],float) for j,_,_ in periods):
                continue
            records.extend((region,year,label,(title,),*number(row[j])) for j,year,label in periods)
        assert len({row[0]['id'] for row in records})>=17,(sheet_name,len(records))
        yield distribute({**entry,'title':title+' · '+years},raw,(130140 if historical else 130110)+i,
            'sanidad',family,MINISTRY,notes+' Hoja '+sheet_name+'.',records,('Indicador',),{title:unit},origin)
    sheet=book.sheet_by_name('tabla 1' if historical else 'Tabla 1.1')
    header=7 if historical else 6
    first,last=(3,38) if historical else (4,27)
    periods=[(j,m[1],clean(sheet.cell_value(header,j)).removesuffix('.0')) for j in range(first,last)
             if (m:=YEAR.fullmatch(clean(sheet.cell_value(header,j))))]
    records,units=[],{}
    assert len(periods)>=18
    for i in range(header+1,sheet.nrows):
        row=sheet.row_values(i)
        label=clean(row[2] if not historical else row[1]) or clean(row[1] if not historical else row[0])
        if not label or not any(isinstance(row[j],float) for j,_,_ in periods):
            continue
        category=label if label not in units else f'{label} · fila {i+1}'
        units[category]=THOUSANDS
        records.extend((NATIONAL,year,period,(category,),*number(row[j])) for j,year,period in periods)
    title='Gasto público en sanidad · conceptos de la cuenta satélite · '+years
    yield distribute({**entry,'title':title},raw,130149 if historical else 130119,'sanidad',family,MINISTRY,
        notes+' Los conceptos con nombre repetido llevan el número de fila de la hoja.',records,('Indicador',),units,origin)
    if not historical:
        yield from expenditure_by_community(entry,raw,book,family,notes,origin)


def expenditure_by_community(entry,raw,book,family,notes,original):
    specifications=(('económico-presupuestaria',6),('funcional',7),('agregados de contabilidad nacional',4))
    for i,(classification,components) in enumerate(specifications):
        records=[]
        units={}
        for code,name in COMMUNITY_NAMES.items():
            sheet_name=f'Tabla 3.4.{code}' if code<'18' else f'Tabla 3.5.{int(code)-17}'
            sheet=book.sheet_by_name(sheet_name)
            value_rows=[j for j in range(sheet.nrows)
                if norm(clean(sheet.cell_value(j,4)))=='miles de euros / porcentaje sobre el total']
            assert len(value_rows)==3,(sheet_name,value_rows)
            start=value_rows[i]+1
            years=[(j,m[1],clean(sheet.cell_value(start,j)).removesuffix('.0')) for j in range(4,27)
                   if (m:=YEAR.fullmatch(clean(sheet.cell_value(start,j))))]
            assert len(years)==23,sheet_name
            territory=area(name,'community',code)
            first=start+2
            for j in range(first,first+2*components,2):
                item=clean(sheet.cell_value(j,2))
                assert item and not clean(sheet.cell_value(j+1,2)),(sheet_name,j)
                for row,prefix,unit in ((j,'Importe',THOUSANDS),(j+1,'Peso',PCT)):
                    indicator=f'{prefix} · {item}'
                    units[indicator]=unit
                    records.extend((territory,year,label,(indicator,),*number(sheet.cell_value(row,col)))
                                   for col,year,label in years)
            for j in range(first+2*components,first+2*components+(3 if i==0 else 1)):
                description=clean(sheet.cell_value(j,2)) or clean(sheet.cell_value(j,1))
                assert description,sheet_name
                units[description]=THOUSANDS
                records.extend((territory,year,label,(description,),*number(sheet.cell_value(j,col)))
                               for col,year,label in years)
        title='Gasto sanitario por comunidad · '+classification
        yield distribute({**entry,'title':title},raw,130115+i,'sanidad',family,MINISTRY,
            notes+' Hojas 3.4 y 3.5. Distingue el importe y el peso de cada componente. '
            'Ceuta y Melilla se refieren a la liquidación del INGESA.',
            records,('Indicador',),units,original)


def pdf_pages(raw):
    sys.path.insert(0,str(CACHE/'vendor'))
    from pypdf import PdfReader
    return PdfReader(BytesIO(raw)).pages


def waiting(entry,raw):
    pages=pdf_pages(raw)
    family='Sanidad · Listas de espera del SNS'
    base_note=('Corte de 31/12/2025. Edición territorial rectificada en septiembre de 2026. '
               'La población de referencia y el cómputo siguen los publicados en el SISLE-SNS.')
    period='2025-12-31'
    label='31/12/2025'
    origin='sisle-2025.pdf'
    measures=(('Pacientes en espera estructural',PATIENTS),('Tasa por 1.000 habitantes',RATE),
              ('Tiempo medio de espera',DAY),('Pacientes con más de seis meses',PCT))
    clinic_measures=(('Pacientes en espera estructural',PATIENTS),('Tasa por 1.000 habitantes',RATE),
                    ('Tiempo medio de espera',DAY),('Citas a más de 60 días',PCT))
    blocks=((130160,(9,10),SPECIALTIES,'Especialidad','Espera quirúrgica por especialidad',measures),
            (130161,(12,13),PROCEDURES,'Proceso','Espera quirúrgica por proceso',measures),
            (130163,(16,17),CONSULTATIONS,'Especialidad','Primeras consultas externas por especialidad',clinic_measures))
    for identifier,group,columns,dimension,title,definitions in blocks:
        records=[]
        for section,page in enumerate(group):
            lines=pages[page-1].extract_text(extraction_mode='layout').splitlines()
            body=[]
            for line in lines:
                fields=re.split(r'  +',line.strip())
                territory=community(fields[0])
                if territory['level']=='community' and len(fields)==len(columns)+1:
                    body.append((territory,fields[1:]))
            assert len(body)==38,(page,len(body))
            for position,(territory,values) in enumerate(body):
                measure=definitions[section*2+position//19][0]
                records.extend((territory,period,label,(measure,key),*number(cell,decimal_comma=True))
                               for key,cell in zip(columns,values,strict=True))
        yield distribute({**entry,'title':title},raw,identifier,'sanidad',family,MINISTRY,
            base_note+' El guion conserva el estado de la tabla publicada.',
            records,('Indicador',dimension),dict(definitions),origin)
    measures=(('Tasa de primeras consultas por 1.000 habitantes',RATE),
              ('Tiempo medio de espera',DAY),('Citas a más de 60 días',PCT))
    lines=pages[13].extract_text(extraction_mode='layout').splitlines()
    records=[]
    for line in lines:
        fields=re.split(r'  +',line.strip())
        territory=community(fields[0])
        if territory['level']=='community' and len(fields)>=4:
            assert all(re.fullmatch(r'[\d,]+|-',v) for v in fields[1:4]),fields
            records.extend((territory,period,label,(title,),*number(v,decimal_comma=True))
                           for (title,_),v in zip(measures,fields[1:4],strict=True))
    assert len(records)==19*3,len(records)
    yield distribute({**entry,'title':'Espera para primeras consultas externas'},raw,130162,'sanidad',family,MINISTRY,
        base_note,records,('Indicador',),dict(measures),origin)


def transplant(entry,raw):
    doc=pdf_pages(raw)
    lines=doc[14].extract_text(extraction_mode='layout').splitlines()
    pattern=re.compile(r'(\d+)\s*/\s*(\d+)\s*\((\d+)%\)|(?<=\s)-(?=\s|$)')
    aliases={'C. Foral de':'Navarra','Castilla la':'Castilla-La Mancha','Com.':'Comunidad Valenciana','Región de':'Murcia'}
    donor_types=('Muerte encefálica','Asistolia tipo III','Asistolia tipo V',
                 'Muerte encefálica y asistolia tipos III y V','Asistolia tipo II','Total')
    measures=('Donantes eficaces','Donantes efectivos','Efectividad publicada')
    records=[]
    for line in lines:
        if len(line)<150:
            continue
        label=re.split(r'  +',line.strip())[0]
        territory=community(aliases.get(label,label))
        if territory['level']=='unlocated':
            continue
        matches=list(pattern.finditer(line[20:]))
        assert len(matches) in {5,6},(label,line)
        if len(matches)==5:
            assert label=='Ceuta'
            matches.insert(3,None)
        for donor,match in zip(donor_types,matches,strict=True):
            for quantity,group in zip(measures,range(1,4),strict=True):
                data=match.group(group) if match else None
                records.append((territory,'2025','2025',(quantity,donor),int(data) if data is not None else None,
                                '' if data is not None else 'Guion o blanco en la tabla oficial'))
    assert len(records)==20*6*3,len(records)
    assert any(r[0]==NATIONAL and r[3]==('Donantes eficaces','Total') and r[4]==2274 for r in records)
    yield distribute({**entry,'title':'Efectividad de la donación por tipo de donante'},raw,130300,'ont',
        'ONT · Donación y trasplante','Organización Nacional de Trasplantes',
        'Tabla 1 de la memoria 2025. Conserva por separado los donantes eficaces y efectivos y el porcentaje oficial. '
        'El área corresponde al ámbito donde se registra la donación.',
        records,('Indicador','Tipo de donante'),{measures[0]:'Donantes',measures[1]:'Donantes',measures[2]:PCT},'ont-2025.pdf')
    organs=('Renal','Hepático','Cardiaco','Pulmonar','Pancreático','Intestinal')
    activity=[]
    hospitals=[]
    for page in (71,72):
        text=doc[page].extract_text(extraction_mode='layout')
        header=next(line for line in text.splitlines() if 'HEPÁTICO' in line and 'INTESTINAL' in line)
        boundaries=[header.index(key) for key in ('RENAL','HEPÁTICO','CARDÍACO','PULMONAR','PANCREÁTICO','INTESTINAL')]
        for line_number,line in enumerate(text.splitlines(),1):
            fields=re.split(r'  +',line.strip(),maxsplit=2)
            if len(fields)<3 or 'Página' in fields[0]:
                continue
            territory=community(fields[0])
            if territory['level']=='unlocated':
                continue
            location=(territory if fields[1].lower()=='total' else
                      no_geometry(f'{fields[1]} · {territory["name"]} · p. {page+1}, línea {line_number}'))
            records=activity if fields[1].lower()=='total' else hospitals
            positions={}
            for value in re.finditer(r'\d+',line[boundaries[0]:]):
                column=value.start()+boundaries[0]
                index=min(range(len(boundaries)),key=lambda i:abs(boundaries[i]+3-column))
                assert abs(boundaries[index]+3-column)<=5 and index not in positions,line
                positions[index]=int(value.group())
            records.extend((location,'2025','2025',(organ,),positions.get(i),
                            '' if i in positions else 'Blanco en la memoria de la ONT')
                           for i,organ in enumerate(organs))
    for i,raw_rows in enumerate((activity,hospitals),1):
        title='Trasplantes por órgano y '+('comunidad del centro' if i==1 else 'centro')
        assert raw_rows
        if i==1:
            assert sum(r[4] for r in raw_rows if r[0]==NATIONAL)==6336
        yield distribute({**entry,'title':title},raw,130300+i,'ont',
            'ONT · Donación y trasplante','Organización Nacional de Trasplantes',
            'Anexo 4.2 de la memoria 2025. La comunidad corresponde a la ubicación del centro trasplantador. '
            'El blanco conserva la ausencia de una cifra en las celdas de la memoria.',
            raw_rows,('Indicador',),dict.fromkeys(organs,'Trasplantes'),'ont-2025.pdf')
