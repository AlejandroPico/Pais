"""Convert the aggregate and per-entity sheets in both live CONPREL advances."""
import argparse
from collections import Counter
from urllib.parse import urlencode

from affiliation_collect import fetch, workbook
from commerce_bde import NATIONAL
from commerce_distributions import number, publish
from demography_collect import ROOT, encode, norm, sha
from economy_cna import sheets
from fiscal_bde import CITY_CODES, REVISION
from fiscal_workbooks import CACHE, area, coded, community, no_geometry

PAGE='https://serviciostelematicosext.hacienda.gob.es/SGFAL/CONPREL'
OUTPUT=ROOT/'datos/hacienda/conprel'
PROFILES=((2025,'Liquidaciones','Liquidación local 2025'),(2026,'Presupuestos','Presupuesto local 2026'))
MONEY='Miles de euros'
CITY_LABELS={'madrid_ciudad':'Madrid','barcelona':'Barcelona','valencia':'Valencia','sevilla':'Sevilla','zaragoza':'Zaragoza','malaga':'Málaga'}


def municipal(name,code):
    return {**area(name,'municipal',code),'provinceCode':code[:2]}


def region(name):
    explicit={'rioja (la)':'17','com. valenciana':'10','castilla la mancha':'08'}
    code=explicit.get(norm(name))
    return area(name,'community',code) if code else community(name)


def tidy(label):
    return ' '.join(label.split())


def individual(rows,year):
    units={}
    group_row={}
    for row in rows:
        if row.get('A')=='Pr' and row.get('B')=='Cor':
            header=row
            break
        if row.get('G') and row.get('Q'):
            group_row=row
    else:
        return [],{}
    headings={}
    category=''
    for column,label in header.items():
        if column in {'A','B','C','D','F'} or not label:
            continue
        category=tidy(group_row.get(column) or category)
        indicator=tidy(label) if column=='E' else f'{category} · {tidy(label)}'
        if column.startswith('A') and len(column)==2:
            indicator='Funcional · '+indicator
        headings[column]=indicator
        units[indicator]='Personas' if column=='E' else 'Euros'
    if 'E' in headings:
        headings['E']=headings.pop('E')
    output=[]
    for row in rows:
        province,entity_type,name=(row.get(c,'') for c in 'ACD')
        corp=row.get('B','')
        province=coded(province,2)
        if not province or not entity_type or not name:
            continue
        town=coded(corp,3)
        if entity_type=='A00' and town:
            place=municipal(name,province+town)
        else:
            place=area(name,'unlocated',f'{province}:{corp}:{entity_type}')
        state='Avance'+(' · '+row['F'] if row.get('F') else '')
        for col,indicator in headings.items():
            value,missing=number(row.get(col))
            output.append((place,str(year),str(year),(indicator,),value,missing or state))
    return output,units


def aggregate(sheet,rows,year):
    place=NATIONAL if sheet=='Nacional' else region(sheet)
    label=CITY_LABELS.get(norm(sheet))
    if label:
        place=municipal(label,CITY_CODES[norm(label)])
    headings={}
    seen=Counter()
    context=[]
    direction=''
    for row in rows:
        if row.get('C','').startswith(('Liquidación de los Presupuestos','Presupuestos de las Entidades')):
            context=[]
            headings={}
            continue
        candidate=row.get('C','')
        if not headings and candidate and not row.get('D') and not candidate.startswith('('):
            context.append(tidy(candidate))
        if norm(candidate)=='cap.' and row.get('D'):
            direction=tidy(row['D'])
            headings={col:tidy(text) for col,text in row.items() if col not in {'C','D'} and text}
            continue
        label=tidy(row.get('D',''))
        if not headings or not label or not any(number(row.get(col))[0] is not None for col in headings):
            continue
        if year==2025 and not sheet=='6GC':
            scope=context[1] if len(context)>1 else 'Total de entidades'
            if scope.startswith('Ayuntamientos') and len(scope)>len('Ayuntamientos'):
                scope='Total de entidades'
        else:
            scope=''
        for column,heading in headings.items():
            current=municipal(heading,CITY_CODES[norm(heading)]) if sheet=='6GC' else place
            code=tidy(row.get('C',''))
            measure=heading if sheet!='6GC' else 'Presupuesto inicial'
            indicator=' · '.join(filter(None,(direction,scope,code,label,measure)))
            seen[(current['id'],indicator)]+=1
            ordinal=seen[(current['id'],indicator)]
            if ordinal>1:
                indicator+=f' · fila {ordinal}'
            value,missing=number(row.get(column))
            yield current,str(year),str(year),(indicator,),value,missing or 'Avance'


def capture(year,kind,title,refresh):
    file='conprel-'+str(year)+'.bin'
    url=PAGE+'/Consulta/DescargaFichero?'+urlencode(dict(CCAA='',TipoDato=kind,Ejercicio=year,TipoPublicacion='Avance'))
    raw=fetch(url,CACHE/file,refresh)
    entities, totals, units=[],[],{}
    for sheet,path in sheets(raw):
        if sheet=='Inicio':
            continue
        rows=workbook(raw,path)
        if sheet.endswith('-Entidades'):
            records, measures=individual(rows,year)
            assert records, sheet
            entities.extend(records)
            units.update(measures)
        else:
            records=list(aggregate(sheet,rows,year))
            assert records, sheet
            totals.extend(records)
    for offset, records, measures, scale in [(0,entities,units,'por entidad'), (1,totals,{r[3][0]:MONEY for r in totals},'cuadros agregados')]:
        identifier=965000+(year-2025)*10+offset
        note='Avance publicado el 30/10/2026. Distingue el ejercicio, la clasificación, la fase y el tipo de entidad. El código de estado se conserva tal como figura en el Excel.'
        if year==2026 and not offset:
            note+=' La columna de población conserva el encabezado literal «Pobla 2021» de la publicación de 2026.'
        product=dict(id=identifier,label=f'{title} · {scale}',family='Presupuestos y liquidaciones locales · CONPREL',
            publisher='Ministerio de Hacienda',sourceId='F043',sourceUrl=PAGE,downloadUrl=url,
            sourceTables=[dict(id=identifier,url=url,year=year,bytes=len(raw),sha256=sha(raw))],
            license='Condiciones de reutilización del Ministerio de Hacienda',note=note)
        yield publish('conprel',product,records,('Indicador',),measures,section='hacienda')


def main(refresh):
    OUTPUT.mkdir(parents=True,exist_ok=True)
    CACHE.mkdir(parents=True,exist_ok=True)
    tables=[t for y,k,n in PROFILES for t in capture(y,k,n,refresh)]
    (OUTPUT/'index.json').write_bytes(encode(dict(schemaVersion=1,revision=REVISION,tables=tables)))
    print(f'CONPREL: {len(tables)} productos, {sum(t["rows"] for t in tables)} observaciones')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
