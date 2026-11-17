"""Read the two October 2026 Atom distributions and retain distinct procurements."""
import gzip
import io
from collections import Counter, defaultdict
from decimal import Decimal
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from commerce_distributions import publish
from funding_collect import (CACHE, EUROS, NATIONAL, NUTS_COMMUNITIES, NUTS_PROVINCES, ROOT, TOTAL,
                             aggregate_records, area, community_code, encode, fetch, no_geometry,
                             product, source, write_index)

BASE = 'https://contrataciondelsectorpublico.gob.es/sindicacion/'
OFFICIAL = 'https://www.hacienda.gob.es/es-ES/GobiernoAbierto/Datos%20Abiertos/Paginas/'
FILES = (
    ('perfiles', 'Perfiles de la plataforma', 'sindicacion_643/licitacionesPerfilesContratanteCompleto3',
     'licitacionescontratante.aspx'),
    ('agregadas', 'Plataformas agregadas', 'sindicacion_1044/PlataformasAgregadasSinMenores',
     'licitacionesagregacion.aspx'),
)
MONTH = '2026-10'
STATES = {
    'PRE':'Anuncio previo', 'PUB':'Publicada', 'EV':'En evaluación', 'ADJ':'Adjudicada',
    'RES':'Resuelta', 'ANUL':'Anulada',
}
UNITS = {
    'Expedientes actualizados':'Expedientes', 'Versiones de expedientes':'Versiones',
    'Lotes declarados':'Lotes', 'Presupuesto sin impuestos comunicado':EUROS,
    'Anuncios de licitación del mes':'Publicaciones registradas',
    'Resultados con fecha de adjudicación del mes':'Resultados',
    'Resultados con fecha de formalización del mes':'Resultados',
    'Importe sin impuestos de resultados adjudicados en el mes':EUROS,
}


def tag(name):
    return '{*}'+name


def text(element, *path):
    return (element.findtext('/'.join(map(tag,path))) or '').strip()


def nodes(element, name):
    return element.findall(tag(name))


def amount(element, *path):
    value = element.find('/'.join(map(tag,path)))
    if value is not None and value.get('currencyID')=='EUR' and value.text:
        return value.text.strip()
    return ''


def entry_fields(entry):
    folder = entry.find(tag('ContractFolderStatus'))
    identifier = text(entry,'id')
    updated = text(entry,'updated')
    if folder is None or not identifier or not updated:
        return None
    project = folder.find(tag('ProcurementProject'))
    project = project if project is not None else ET.Element('empty')
    locations = sorted({
        text(location,'CountrySubentityCode')
        for location in nodes(project,'RealizedLocation')
        if text(location,'CountrySubentityCode')
    })
    lots = sorted({text(lot,'ID') for lot in nodes(folder,'ProcurementProjectLot') if text(lot,'ID')})
    results = []
    for result in nodes(folder,'TenderResult'):
        money = ('AwardedTenderedProject','LegalMonetaryTotal')
        results.append([
            text(result,'AwardedTenderedProject','ProcurementProjectLotID'), text(result,'ResultCode'),
            text(result,'AwardDate'), text(result,'Contract','IssueDate'), text(result,'Contract','ID'),
            amount(result,*money,'TaxExclusiveAmount'),
        ])
    notices = []
    for notice in nodes(folder,'ValidNoticeInfo'):
        for publication in nodes(notice,'AdditionalPublicationStatus'):
            for doc in nodes(publication,'AdditionalPublicationDocumentReference'):
                notices.append([text(notice,'NoticeTypeCode'),text(doc,'IssueDate'),
                                text(publication,'PublicationMediaName'),text(doc,'ID')])
    link = entry.find(tag('link'))
    return identifier, dict(updated=updated, reference=text(folder,'ContractFolderID'),
                            url=link.get('href','') if link is not None else '',
                            status=text(folder,'ContractFolderStatusCode'), execution=locations, lots=lots,
                            exclusiveBudget=amount(project,'BudgetAmount','TaxExclusiveAmount'),
                            results=results, notices=notices)


def entries(data):
    with ZipFile(io.BytesIO(data)) as archive:
        for name in sorted(archive.namelist()):
            if not name.endswith('.atom'):
                continue
            with archive.open(name) as file:
                stream = ET.iterparse(file,events=('start','end'))
                _, root = next(stream)
                for event, element in stream:
                    if event=='end' and element.tag=='{http://www.w3.org/2005/Atom}entry':
                        parsed = entry_fields(element)
                        if parsed:
                            yield parsed
                        root.remove(element)


def execution_areas(codes, province_names):
    places = [NATIONAL]
    regions = {NUTS_COMMUNITIES.get(code[:4]) for code in codes}
    provinces = {NUTS_PROVINCES.get(code) for code in codes}
    if len(regions)==1 and None not in regions:
        places.append(community_code(next(iter(regions))))
    else:
        places.append(no_geometry('Sin comunidad única de ejecución declarada'))
    if len(provinces)==1 and None not in provinces:
        province = next(iter(provinces))
        places.append(area(province_names[province],'province',province))
    return places


def distributions():
    feder = ROOT/'datos/ayudas/feder/index.json'
    import json
    province_names = {a['code']:a['name'] for a in json.loads(feder.read_bytes())['tables'][0]['territories']
                      if a['level']=='province'}
    output = ROOT/'datos/ayudas/placsp'
    for offset,(name,label,archive,listing) in enumerate(FILES,1):
        identifier = 970400+offset
        url = BASE+archive+'_202610.zip'
        raw = fetch(url,CACHE/f'placsp-{name}.zip',False)
        histories = defaultdict(dict)
        for key,record in entries(raw):
            # When the same Atom entry is repeated in adjacent files, its content and time identify the version.
            histories[key][(record['updated'],encode(record))] = record
        totals, territories = defaultdict(Counter), {}
        records = []
        for key,history in sorted(histories.items()):
            ordered = [history[version] for version in sorted(history)]
            latest = ordered[-1]
            notices = {tuple(item) for record in ordered for item in record['notices']
                       if item[0]=='DOC_CN' and item[1].startswith(MONTH)}
            awarded = [result for result in latest['results'] if result[2].startswith(MONTH)]
            formalized = [result for result in latest['results'] if result[3].startswith(MONTH)]
            values = {
                'Expedientes actualizados':1,'Versiones de expedientes':len(ordered),
                'Lotes declarados':len(latest['lots']),'Anuncios de licitación del mes':len(notices),
                'Resultados con fecha de adjudicación del mes':len(awarded),
                'Resultados con fecha de formalización del mes':len(formalized),
            }
            if latest['exclusiveBudget']:
                values['Presupuesto sin impuestos comunicado'] = Decimal(latest['exclusiveBudget'])
            amounts = [Decimal(result[5]) for result in awarded if result[5]]
            if amounts:
                values['Importe sin impuestos de resultados adjudicados en el mes'] = sum(amounts)
            code = latest['status']
            status = STATES.get(code,code or 'Sin estado comunicado')
            for territory in execution_areas(latest['execution'],province_names):
                territories[territory['id']] = territory
                for state in (TOTAL,status):
                    totals[(territory['id'],'2026M10',(state,))].update(values)
            records.append([key,ordered])
        inputs = [source(identifier,url,raw)]
        payload = gzip.compress(encode(dict(source=url,sha256=inputs[0]['sha256'],expedientes=records)),
                                compresslevel=6,mtime=0)
        file = f'{name}-expedientes-202610.json.gz'
        (output/file).write_bytes(payload)
        inputs.append(source(identifier+50,url,payload,originalFile=file,
                             notes=['Captura normalizada del paquete de sindicación.']))
        note = (f'{len(histories):,} expedientes distintos y {sum(map(len,histories.values())):,} versiones '
                'en el paquete de octubre de 2026, sin contratos menores. Se conserva la referencia al '
                'expediente, su enlace, versiones, códigos, lotes, fechas y cuantías seleccionadas. '
                'Los estados, lotes y resultados usan la versión más reciente del expediente en este '
                'paquete. Los anuncios, adjudicaciones y formalizaciones cuentan observaciones fechadas en octubre. '
                'La geografía usa el NUTS de ejecución, con un ámbito sin asignar para registros '
                'sin código suficiente o con varios ámbitos. Cada canal se consulta por separado.')
        p = product(identifier,'PLACSP · '+label,'Plataforma de Contratación del Sector Público','F046',
                    OFFICIAL+listing,note,inputs,'Condiciones de reutilización de PLACSP')
        yield publish('placsp',p,aggregate_records(totals,territories,{'2026M10':MONTH}),('Indicador','Estado'),
                      UNITS,section='ayudas')


if __name__=='__main__':
    write_index('placsp',distributions())
