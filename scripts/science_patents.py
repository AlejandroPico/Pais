"""Read the Spain slices of the EPO's published Technology Dashboard workbooks."""
import json
import re
from decimal import Decimal

from affiliation_collect import workbook
from commerce_bde import NATIONAL
from commerce_distributions import publish
from economy_cna import sheets
from funding_collect import community_code, product, source
from fiscal_workbooks import no_geometry
from science_collect import CACHE, OUTPUT, write_index

EPO = 'https://www.epo.org/en/about-us/statistics/data-download'
REGIONS = dict(zip(
    ['Andalusia','Aragon','Asturias','Balearic Islands','Canary Islands','Cantabria','Castille and Leon',
     'Castille-La Mancha','Catalonia','Valencia','Extramadura','Galicia','Madrid','Murcia','Navarre','Basque Country',
     'La Rioja','Ceuta','Melilla'],
    [f'{i:02}' for i in range(1,20)],strict=True))


def parse_book(manifest, prefix, identifier):
    filename=next(name for name in manifest if name.startswith(prefix))
    raw=(CACHE/filename).read_bytes()
    url=manifest[filename]['url']
    file=OUTPUT/'epo'/'originales'/filename
    file.parent.mkdir(parents=True,exist_ok=True)
    file.write_bytes(raw)
    return raw,source(identifier,url,raw,originalFile='originales/'+filename)


def cell(value, multiplier=1):
    if value:
        return float(Decimal(value)*multiplier),''
    return None,'Celda vacía en origen'


def summary(raw, indicator):
    sheet=next(iter(sheets(raw)))[1]
    rows=list(workbook(raw,sheet))
    header=next(row for row in rows if row.get('A')=='Country')
    spain=next(row for row in rows if row.get('A')=='ES')
    for column,yr in header.items():
        if re.fullmatch(r'20\d{2}',yr):
            yield (NATIONAL,yr,yr,(indicator,),*cell(spain[column]))


def technology(raw, indicator):
    for year, sheet in sheets(raw):
        if not re.fullmatch(r'20\d{2}',year):
            continue
        rows=list(workbook(raw,sheet))
        header=next(row for row in rows if row.get('A')=='Field of technology')
        spain=next(column for column,label in header.items() if label=='Spain')
        for row in rows:
            name=row.get('B','').strip() or row.get('A','').strip()
            if row.get(spain,'').strip() and name and row[spain].strip().isdigit():
                yield (NATIONAL,year,year,(indicator,name),*cell(row[spain]))


def communities(raw):
    sheets_by_name=dict(sheets(raw))
    units={'Solicitudes europeas':'Solicitudes','Peso en España':'Porcentaje','Variación anual':'Porcentaje'}
    indicators=list(units)
    rows=[]
    for row in workbook(raw,sheets_by_name['Communities']):
        name=row.get('B','').strip() or row.get('A','').strip()
        if name in REGIONS:
            territory=community_code(REGIONS[name])
        elif name=='Total':
            territory=NATIONAL
        elif name=='Unclassified':
            territory=no_geometry('Residencia sin comunidad clasificada')
        else:
            continue
        for year,column,percent in (('2024','E','F'),('2025','C','D')):
            rows.append((territory,year,year,(indicators[0],),*cell(row.get(column))))
            rows.append((territory,year,year,(indicators[1],),*cell(row.get(percent),100)))
        rows.append((territory,'2025','2025',(indicators[2],),*cell(row.get('G'),100)))
    assert len(rows)==105,len(rows)
    return rows,units


def products():
    folder='epo'
    manifest=json.loads((CACHE/'epo-books.json').read_bytes())
    group='Oficina Europea de Patentes'
    notes='El país se asigna por la residencia del primer solicitante listado. Las series preservan la fase publicada.'
    for i,(kind,indicator,unit) in enumerate([
        ('european-patent-applications','Solicitudes europeas','Solicitudes'),
        ('granted-patents','Patentes europeas concedidas','Concesiones'),
    ],1):
        identifier=120200+i
        raw,origin=parse_book(manifest,kind+'-2016-2025-per-country',identifier)
        matrix,additional=parse_book(manifest,kind+'-per-field-of-technology',identifier+20)
        totals=list(summary(raw,indicator))
        details=[row for row in technology(matrix,indicator) if row[3][1]!='Total']
        assert len(totals)==10 and len({row[1] for row in details})==10
        metadata=product(identifier,indicator+' · solicitantes de España',group,'F183',EPO,notes,[origin],
                         'Condiciones de reutilización de las estadísticas de la EPO')
        yield publish(folder,metadata,totals,('Indicador',),{indicator:unit},section='ciencia')
        details=[(a,date,label,(measure,'Total'),value,status) for a,date,label,(measure,),value,status in totals]+details
        metadata=product(identifier+20,indicator+' · campos tecnológicos',group,'F183',EPO,
                         notes+' Los totales provienen de la serie por país.',
                         [additional,origin],'Condiciones de reutilización de las estadísticas de la EPO')
        yield publish(folder,metadata,details,('Indicador','Campo tecnológico'),{indicator:unit},section='ciencia')
    raw,origin=parse_book(manifest,'spain-epo-',120250)
    records,units=communities(raw)
    metadata=product(120250,'Solicitudes europeas · comunidades del solicitante',group,'F183',EPO,
                     notes+' España y 19 comunidades o ciudades autónomas. El expediente sin clasificación territorial se conserva.',
                     [origin],'Condiciones de reutilización de las estadísticas de la EPO')
    yield publish(folder,metadata,records,('Indicador',),units,section='ciencia')
    raw,origin=parse_book(manifest,'national-applications-in-epc-',120251)
    sheet=next(iter(sheets(raw)))[1]
    es=next(row for row in workbook(raw,sheet) if row.get('B')=='ES')
    units={'Solicitudes presentadas':'Solicitudes','Variación anual':'Porcentaje'}
    records=[(NATIONAL,'2024','2024',(indicator,),*cell(es.get(column),scale))
             for indicator,column,scale in zip(units,'CD',(1,100),strict=True)]
    metadata=product(120251,'Solicitudes ante la oficina española · referencia EPO',group,'F183',EPO,
                     'Solicitudes presentadas ante la oficina española en 2024 según la serie de oficinas nacionales de la EPO.',
                     [origin],'Condiciones de reutilización de las estadísticas de la EPO')
    yield publish(folder,metadata,records,('Indicador',),units,section='ciencia')


if __name__=='__main__':
    write_index('epo',products())
