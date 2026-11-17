"""Import the annual CDTI open data exports and their published breakdowns."""
from collections import Counter, defaultdict
from decimal import Decimal
import gzip
from itertools import product as combinations
import json
import re

from affiliation_collect import fetch
from commerce_bde import GEO, NATIONAL
from commerce_distributions import publish
from demography_collect import norm
from fiscal_workbooks import area, no_geometry
from funding_collect import aggregate_records, product, source
from education_collect import place
from science_collect import CACHE, OUTPUT, PROVINCES, PROVINCE_COMMUNITY, encode, write_index

LISTING='https://www.cdti.es/datos-abiertos-creditos-subvenciones-y-lineas'
API='https://sede.cdti.gob.es/AreaPrivada/Servicios/DatosAbiertos/api/datos/proyectosidi/JSON/'
YEARS=range(2000,2027)
MEASURES={
    'Registros de ayuda aprobada':'Registros',
    'Presupuesto publicado':'Euros',
    'Aportación CDTI publicada':'Euros',
}
PROVINCE_NAMES={**{norm(name):code for code,name in PROVINCES.items()},
                'baleares':'07','sta. c. de tenerife':'38'}


def get_number(value):
    if value is None or not str(value).strip():
        return None
    assert isinstance(value,str),repr(value)
    value=value.removesuffix('€').strip().replace('.','').replace(',','.')
    assert re.fullmatch(r'-?\d+(\.\d+)?',value),value
    return Decimal(value)


def distribution():
    records,territories=defaultdict(Counter),{}
    metadata,archived,dates,editions,missing=[],[],set(),{},Counter()
    years=[]
    for year in YEARS:
        url=API+str(year)+'/ALL'
        path=CACHE/f'cdti-{year}.json'
        if not path.exists():
            continue
        raw=fetch(url,path,False)
        downloaded=json.loads(raw)
        assert isinstance(downloaded,list) and downloaded,year
        editions[str(year)]=120600+year-2000
        metadata.append(source(editions[str(year)],url,raw,year=year))
        years.append(year)
        for row in downloaded:
            approval=row['FechaAprobacionResolucion']
            assert re.fullmatch(r'\d{2}/\d{2}/'+str(year),approval),(year,approval)
            geo=[NATIONAL]
            community=place(row['CCAA'] or 'Comunidad sin dato','community')
            if community['level']!='national':
                geo.append(community)
            province=row['Provincia'] or ''
            key=norm(province)
            province_code=PROVINCE_NAMES.get(key) or GEO.get(('province',key))
            if province_code and community['level']=='community' and PROVINCE_COMMUNITY[province_code]!=community['code']:
                missing['Conflicto entre provincia y comunidad']+=1
                geo=[NATIONAL,no_geometry('Conflicto entre provincia y comunidad')]
            elif province_code:
                geo.append(area(PROVINCES[province_code],'province',province_code))
            elif province:
                missing['Provincia sin equivalencia']+=1
            values={'Registros de ayuda aprobada':1}
            amounts={'Presupuesto publicado':get_number(row['Presupuesto']),
                     'Aportación CDTI publicada':get_number(row['AportacionCDTI'])}
            for measure,value in amounts.items():
                if value is None:
                    missing[measure]+=1
                else:
                    values[measure]=value
            filters=[(row.get(field) or fallback).strip() for field,fallback in zip(
                ('TipoAyuda','InstrumentoFinanciero','OrigenFondos'),('Tipo sin dato','Instrumento sin dato','Origen sin dato'),strict=True)]
            for territory in geo:
                territories[territory['id']]=territory
                for selected in combinations(*(dict.fromkeys(('Total',value)) for value in filters)):
                    records[(territory['id'],str(year),selected)].update(values)
            if row.get('UltimaFechaActualizacion'):
                dates.add(row['UltimaFechaActualizacion'])
            archived.append({key:row[key] for key in ('FechaAprobacionResolucion','CCAA','Provincia','Localidad','TipoEntidad',
                'PYME','TipoAyuda','InstrumentoFinanciero','AreaSectorial','CNAE','OrigenFondos','Presupuesto','AportacionCDTI')})
    assert years
    snapshot='proyectos-cdti.json.gz'
    data=gzip.compress(encode(dict(pages=metadata,records=archived)),compresslevel=6,mtime=0)
    (OUTPUT/'cdti'/snapshot).write_bytes(data)
    end_date=', '.join(sorted(dates))
    note=(f'{len(archived):,} registros en {len(years)} cortes anuales. Última actualización en la descarga: {end_date}. '
          'La geografía sigue las columnas del CDTI. Año según la aprobación o resolución. '
          'Presupuesto y aportación publicada son importes diferentes. El recuento es de filas de ayuda. '
          f'{missing["Conflicto entre provincia y comunidad"]} registro con clasificación territorial contradictoria. '
          'El extracto conservado omite beneficiarios e identificadores fiscales.')
    metadata.append(source(120650,LISTING,data,originalFile=snapshot,notes=[
        'Captura minimizada de los cortes anuales.', 'Ausencias en origen: '+json.dumps(dict(missing),ensure_ascii=False)]))
    item=product(120501,'Ayudas, presupuestos y aportaciones aprobadas','CDTI · Datos abiertos','F077',LISTING,
                 note,metadata,'Aviso de reutilización de datos abiertos del CDTI')
    item.update(snapshotFile=snapshot,snapshotLabel='Registros de ayudas y cuantías (JSON comprimido)')
    yield publish('cdti',item,aggregate_records(records,territories,{}),('Indicador','Tipo de ayuda',
                  'Instrumento','Origen de los fondos'),MEASURES,section='ciencia',source_by_period=editions)


if __name__=='__main__':
    write_index('cdti',distribution())
