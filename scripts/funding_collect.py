"""Build F10 statistical distributions from the official snapshots."""
import csv
import gzip
from collections import Counter, defaultdict
from decimal import Decimal
from datetime import date, datetime, timedelta
from html import unescape
import io
import json
import re
from urllib.parse import urljoin

from affiliation_collect import fetch, workbook
from commerce_bde import NATIONAL
from commerce_distributions import publish
from demography_collect import ROOT, encode, norm, sha
from economy_cna import sheets
from fiscal_workbooks import area, community, no_geometry

CACHE = ROOT / '.cache/f10'
REVISION = '2026-11-17'
REGISTRY = ('https://www.hacienda.gob.es/es-ES/Areas%20Tematicas/Contratacion/'
            'Junta%20Consultiva%20de%20Contratacion%20Administrativa/Paginas/Registro%20publico%20de%20contratos.aspx')
FEDER = 'https://www.dgfc.sepg.hacienda.gob.es/sitios/dgfc/es-ES/loFEDER1420/porFEDER/Paginas/FicheroExcel.aspx'
BDNS = 'https://www.infosubvenciones.es/bdnstrans/doc/swagger'
COHESION = 'https://cohesion-data.ec.europa.eu/d/3git-md5z'
EUROS = 'Euros'
TOTAL = 'Total'
REGISTRY_GROUPS = {
    'CCAA': 'Comunidades y ciudades autónomas',
    'Estado': 'Ministerios',
    'EELL': 'Tipos de entidades locales',
    'Universidades': 'Universidades',
    'Mutuas': 'Mutuas colaboradoras',
}


def autonomous(label):
    code = {'castilla-leon': '07', 'rioja': '17', 'la rioja': '17', 'ceuta': '18', 'melilla': '19'}
    return area(label, 'community', code[norm(label)]) if norm(label) in code else community(label)


def source(identifier, url, raw, **metadata):
    return dict(id=identifier, url=url, bytes=len(raw), sha256=sha(raw), **metadata)


def product(identifier, name, publisher, source_id, url, note, inputs, license):
    first = inputs[0]
    return dict(id=identifier, label=name, family=publisher, publisher=publisher,
                sourceId=source_id, sourceUrl=url, downloadUrl=first['url'],
                note=note, license=license, sourceTables=inputs)


def contract_value(text):
    if not text:
        return None, 'Celda vacía en origen'
    return float(text.replace('.', '').replace(',', '.').removesuffix('%')), ''


def contract_tables():
    page = fetch(REGISTRY, CACHE/'registro.html', False).decode('utf-8')
    links = sorted({unescape(url) for url in re.findall(r'https?://[^"<> ]+\.txt', page, re.I)})
    units = {'Contratos registrados': 'Contratos', 'Importe registrado': EUROS, 'Peso del procedimiento': 'Porcentaje'}
    for offset, (group, label) in enumerate(REGISTRY_GROUPS.items(), 1):
        records, inputs = [], []
        identifier = 970000 + offset
        editions = {}
        for url in links:
            name = url.rsplit('/', 1)[-1]
            match = re.fullmatch(r'Contratos(\d{4})-' + group + r'-(Numero|Importes-Porcentajes)\.txt', name, re.I)
            if not match:
                continue
            year, kind = match.groups()
            raw = fetch(url, CACHE/name, False)
            original = ROOT/'datos/ayudas/contratos/originales'/name
            original.parent.mkdir(parents=True, exist_ok=True)
            original.write_bytes(raw)
            table = [line.split('\t') for line in raw.decode('cp1252').splitlines() if line.strip()]
            amounts = kind.lower() != 'numero'
            headings, measures = table[0], table[1] if amounts else []
            columns = []
            for index, heading in enumerate(headings[1:], 1):
                if not heading.strip() and (not amounts or not measures[index].strip()):
                    continue
                if heading.strip():
                    procedure = TOTAL if heading.strip().casefold()=='total general' else heading.strip()
                indicator = ('Peso del procedimiento' if measures[index].strip()=='%' else 'Importe registrado') if amounts else 'Contratos registrados'
                columns.append((index, indicator, procedure))
            footnotes = []
            for row in table[2 if amounts else 1:]:
                group_name = row[0].strip()
                recognised_region = group=='CCAA' and autonomous(group_name.split(' (')[0])['level']=='community'
                if not any(cell.strip() for cell in row[1:]) and not recognised_region:
                    if group_name:
                        footnotes.append(group_name)
                    continue
                assert group_name, (name, row)
                total = group_name.casefold()=='total general'
                geography = NATIONAL if total else autonomous(group_name.split(' (')[0]) if group=='CCAA' else no_geometry(group_name)
                for index, measure, procedure in columns:
                    raw_value = row[index].strip() if index < len(row) else ''
                    records.append((geography, year, year, (measure,procedure), *contract_value(raw_value)))
            input_id = 971000 + offset*100 + (int(year)-2013)*2 + int(amounts)
            editions[(year,amounts)] = input_id
            inputs.append(source(input_id, url, raw, year=int(year), notes=footnotes,
                                 originalFile='originales/'+name))
        inputs.sort(key=lambda item: (item['year'],item['id']))
        geography_note = ('La ubicación indica la comunidad de la administración contratante.' if group=='CCAA'
                          else 'El total corresponde a España. Los desgloses institucionales se consultan como ámbitos sin geometría.')
        p = product(identifier, 'Contratos registrados · '+label, 'Registro de Contratos del Sector Público',
                    'F046', REGISTRY, geography_note + ' El Registro clasifica contratos comunicados y publica'
                    ' sus importes, recuentos y porcentajes. Se conservan las celdas vacías y las notas de cada edición.',
                    inputs, 'Condiciones de reutilización de Hacienda')
        yield publish('contratos', p, records, ('Indicador','Procedimiento'), units, section='ayudas',
                      source_for_record=lambda year, categories: editions[(year,categories[0]!='Contratos registrados')])


NUTS_PROVINCES = dict(zip(
    'ES111 ES112 ES113 ES114 ES120 ES130 ES211 ES212 ES213 ES220 ES230 ES241 ES242 ES243 ES300 '
    'ES411 ES412 ES413 ES414 ES415 ES416 ES417 ES418 ES419 ES421 ES422 ES423 ES424 ES425 '
    'ES431 ES432 ES511 ES512 ES513 ES514 ES521 ES522 ES523 ES531 ES532 ES533 '
    'ES611 ES612 ES613 ES614 ES615 ES616 ES617 ES618 ES620 ES630 ES640 ES703 ES704 ES705 ES706 ES707 ES708 ES709'.split(),
    '15 27 32 36 33 39 01 20 48 31 26 22 44 50 28 05 09 24 34 37 40 42 47 49 02 13 16 19 45 '
    '06 10 08 17 25 43 03 12 46 07 07 07 04 11 14 18 21 23 29 41 30 51 52 38 35 35 38 38 35 38'.split(),
    strict=True))
NUTS_COMMUNITIES = dict(zip(
    'ES11 ES12 ES13 ES21 ES22 ES23 ES24 ES30 ES41 ES42 ES43 ES51 ES52 ES53 ES61 ES62 ES63 ES64 ES70'.split(),
    '12 03 06 16 15 17 02 13 07 08 11 09 10 04 01 14 18 19 05'.split(), strict=True))
PROGRAMMES = dict(zip(
    'AN AR AS BB IC CN CE CL CM CT EX GA LR MD ME MU NA EU CV'.split(),
    '01 02 03 04 05 06 18 07 08 09 11 12 17 13 19 14 15 16 10'.split(), strict=True))
COMMUNITY_NAMES = dict(zip(
    '01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19'.split(),
    ('Andalucía','Aragón','Asturias','Illes Balears','Canarias','Cantabria','Castilla y León','Castilla-La Mancha',
     'Cataluña','Comunitat Valenciana','Extremadura','Galicia','Comunidad de Madrid','Región de Murcia',
     'Navarra','País Vasco','La Rioja','Ceuta','Melilla'), strict=True))


def community_code(code):
    return area(COMMUNITY_NAMES[code], 'community', code)


def aggregate_records(totals, territories, labels):
    for (territory, period, categories), values in totals.items():
        for indicator, value in values.items():
            yield territories[territory], period, labels.get(period,period), (indicator,*categories), float(value), ''


def feder_year(value):
    if re.fullmatch(r'\d{4,5}(\.0+)?',value):
        return str((date(1899,12,30)+timedelta(days=int(Decimal(value)))).year)
    if re.fullmatch(r'\d{1,2}/\d{1,2}/\d{4}',value):
        return str(datetime.strptime(value,'%d/%m/%Y').year)
    return None


def feder_decimal(value):
    normalized = value.replace('.','').replace(',','.') if ',' in value else value
    return Decimal(normalized) if re.fullmatch(r'-?\d+(\.\d+)?',normalized) else None


def feder_tables():
    page = fetch(FEDER, CACHE/'feder.html', False).decode('utf-8')
    links = sorted({urljoin(FEDER, path) for path in re.findall(r'href="([^"]*/LO-[A-Z]+\.xlsx)"',page)})
    assert {url.rsplit('/',1)[-1][3:-5] for url in links}==set(PROGRAMMES)
    units = {'Operaciones con inicio comunicado': 'Operaciones', 'Coste subvencionable publicado': EUROS,
             'Cofinanciación UE estimada (coste × tasa)': EUROS}
    totals, territories = defaultdict(Counter), {}
    original_records, duplicates, no_year, missing_geo, missing_cost, missing_rate = 0, 0, 0, 0, 0, 0
    labels, inputs, seen = {}, [], set()
    for offset, url in enumerate(links, 1):
        name = url.rsplit('/',1)[-1]
        raw = fetch(url,CACHE/name,False)
        inputs.append(source(970100+offset,url,raw))
        for _, sheet in sheets(raw):
            for row in workbook(raw,sheet):
                cci, operation, start, cost, rate, location, municipality, field = (row.get(col,'').strip() for col in 'CGKMNOPS')
                if not re.fullmatch(r'2014ES\w+', cci) or not operation:
                    continue
                signature = tuple(row.get(key,'').strip() for key in 'CDEFGKLMNOPRSTUV')
                if signature in seen:
                    duplicates += 1
                    continue
                seen.add(signature)
                original_records += 1
                year = feder_year(start)
                if year is None:
                    no_year += 1
                    year = '0000'
                    labels[year] = 'Fecha de inicio sin asignar'
                locations = [NATIONAL]
                nuts = location.split(maxsplit=1)[0] if location else ''
                if code := NUTS_COMMUNITIES.get(nuts[:4]):
                    locations.append(community_code(code))
                else:
                    missing_geo += 1
                    locations.append(no_geometry('Sin comunidad de ejecución identificada'))
                province = NUTS_PROVINCES.get(nuts)
                if province:
                    name = {'07':'Illes Balears','35':'Las Palmas','38':'Santa Cruz de Tenerife'}.get(
                        province,location.partition(' ')[2] or nuts)
                    locations.append(area(name, 'province',province))
                    if re.match(r'\d{5}\s',municipality) and municipality[:2]==province and municipality[2:5]!='000':
                        locations.append({**area(municipality[6:],'municipal',municipality[:5]),'provinceCode':province})
                values = {next(iter(units)): 1}
                amount = feder_decimal(cost)
                if amount is not None:
                    values['Coste subvencionable publicado'] = amount
                    ratio = feder_decimal(rate)
                    if ratio is not None and ',' in rate:
                        ratio /= 100
                    if ratio is not None and 0<=ratio<=1:
                        values['Cofinanciación UE estimada (coste × tasa)'] = (amount*ratio).quantize(Decimal('.01'))
                    else:
                        missing_rate += 1
                else:
                    missing_cost += 1
                field = field or 'Campo de intervención sin dato'
                for territory in locations:
                    territories[territory['id']] = territory
                    for category in (TOTAL,field):
                        totals[(territory['id'],year,(category,))].update(values)
    note = (f'19 listas de operaciones de los programas regionales 2014–2020, versión de marzo de 2024. '
            f'{original_records:,} filas de operación, con {duplicates:,} duplicados exactos retirados, '
            f'{no_year:,} sin año interpretable, {missing_geo:,} sin comunidad identificada, '
            f'{missing_cost:,} sin coste interpretable y {missing_rate:,} con coste pero sin tasa utilizable. '
            'Localización declarada en la operación según NUTS y código municipal explícito. '
            'Los totales incluyen filas con geografía incompleta. El coste es subvencionable. La cofinanciación '
            'se estima solo en filas con coste y tasa válidos. Ambos indicadores son distintos de los pagos.')
    p = product(970100,'FEDER 2014–2020 · Operaciones de programas regionales','Dirección General de Fondos Europeos',
                'F043',FEDER,note,inputs,'Condiciones de reutilización de Hacienda')
    yield publish('feder',p,aggregate_records(totals,territories,labels),('Indicador','Campo de intervención'),
                  units,section='ayudas')


def cohesion_tables():
    fields = {
        'total_amount':'Presupuesto planificado',
        'eu_amount':'Aportación UE planificada',
        'total_eligiblecost_of_selectedoperations':'Coste elegible de operaciones seleccionadas',
        'totalspendeligibleexpenditure_declared':'Gasto elegible declarado',
        'eueligible_costs_decided_selectednotional':'Componente UE estimado de operaciones seleccionadas',
        'euspendshare_eligexpendituredeclarednotional':'Componente UE estimado del gasto declarado',
    }
    raw = (CACHE/'cohesion.csv').read_bytes()
    url = (CACHE/'cohesion.url').read_text(encoding='utf-8')
    inputs = [source(970200,url,raw)]
    programme_regions = {}
    for prefix,start,sequence in [
        ('2021ES16RFPR',2,'01 02 03 04 05 06 07 08 09 18 10 11 12 17 13 19 14 15 16'),
        ('2021ES05SFPR',5,'01 02 03 04 05 06 09 08 07 18 10 11 12 17 13 19 14 15 16'),
    ]:
        programme_regions.update({f'{prefix}{i:03}':code for i,code in enumerate(sequence.split(),start)})
    territories, labels, totals = {}, {}, defaultdict(Counter)
    count = 0
    for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        raw_cycle = row['tod_cycle']
        cycle = raw_cycle[:4]+'M'+raw_cycle[4:]
        labels[cycle] = raw_cycle[:4]+'-'+raw_cycle[4:]
        code = programme_regions.get(row['cci'])
        programme = row['programme_short_title']+' · '+row['cci']
        locations = [NATIONAL,community_code(code) if code else no_geometry(programme)]
        values = {name: Decimal(row[key]) for key,name in fields.items() if row[key]}
        count += 1
        for territory in locations:
            territories[territory['id']] = territory
            for categories in ((row['fund'],programme),(row['fund'],TOTAL)):
                totals[(territory['id'],cycle,categories)].update(values)
            if row['fund'] in {'ERDF','ESF+','JTF'}:
                totals[(territory['id'],cycle,(TOTAL,TOTAL))].update(values)
    p = product(970200,'Cohesión 2021–2027 · Financiación planificada, seleccionada y declarada',
                'Comisión Europea · Cohesion Open Data','F142',COHESION,
                f'{count:,} filas de la dimensión campo de intervención para España. Ciclos de declaración '
                'acumulados. Cada ciclo se suma por separado siguiendo el gráfico oficial. '
                'El mapa autonómico representa el ámbito de los programas regionales. Los programas de '
                'ámbito nacional o plurirregional se consultan por nombre y en el total nacional. '
                'El total de cohesión comprende FEDER, FSE+ y FTJ. AMIF, BMVI e ISF pueden consultarse por fondo. '
                'El gasto declarado se distingue de los pagos. Los componentes UE de ejecución son estimaciones de la fuente.',
                inputs,'Reuse of Commission documents · Decision 2011/833/EU')
    units = dict.fromkeys(fields.values(),EUROS)
    yield publish('cohesion',p,aggregate_records(totals,territories,labels),('Indicador','Fondo','Programa'),
                  units,section='ayudas')


def bdns_tables():
    for identifier, kind, date_label in [
        (970301,'convocatorias','recepción'),
        (970302,'concesiones','concesión'),
    ]:
        paths = sorted(CACHE.glob(kind+'-??-??-????.jsonl'))
        if not paths:
            continue
        totals, territories, labels, inputs, editions = defaultdict(Counter), {}, {}, [], {}
        systems = {'ESTADO':'Estatal','AUTONOMICA':'Autonómica','LOCAL':'Local',
                   'OTROS':'Otros','OTRAS':'Otros'}
        titles = {'convocatorias':'Convocatorias publicadas','concesiones':'Concesiones publicadas'}
        units = {titles[kind]: 'Convocatorias' if kind=='convocatorias' else 'Concesiones'}
        if kind=='concesiones':
            units.update({'Importe concedido':EUROS,'Ayuda equivalente comunicada':EUROS})
        seen = set()
        for file in paths:
            pages = [json.loads(line) for line in file.read_text(encoding='utf-8').splitlines()]
            first = pages[0]
            source_id = identifier*100 + int(file.stem[-4:])-2000
            count = sum(len(page['rows']) for page in pages)
            assert count==first['total']
            snapshot = gzip.compress(encode(pages), compresslevel=6, mtime=0)
            snapshot_name = file.stem+'.json.gz'
            (ROOT/'datos/ayudas/bdns'/snapshot_name).write_bytes(snapshot)
            inputs.append(source(source_id,first['url'],snapshot,originalFile=snapshot_name,
                                 notes=[f'{count:,} filas. La huella de cada respuesta oficial está en la captura minimizada.']))
            for page in pages:
                for row_id, reported_date, administration, authority, *payload in page['rows']:
                    period = reported_date[:4]+('M'+reported_date[5:7] if kind=='concesiones' else '')
                    labels[period] = reported_date[:7] if kind=='concesiones' else period
                    editions[period] = source_id
                    assert row_id not in seen, row_id
                    seen.add(row_id)
                    administration = systems.get(administration,administration or 'Sin administración identificada')
                    locations = [NATIONAL]
                    if administration=='Autonómica' and authority:
                        locations.append(autonomous(authority))
                    values = {titles[kind]:1}
                    if kind=='convocatorias':
                        breakdown = ('Mecanismo de Recuperación y Resiliencia' if payload[0] is True
                                     else 'Sin marca MRR' if payload[0] is False else 'Marca MRR sin dato')
                    else:
                        amount, aid, instrument = payload
                        if amount is not None:
                            values['Importe concedido'] = Decimal(str(amount))
                        if aid is not None:
                            values['Ayuda equivalente comunicada'] = Decimal(str(aid))
                        breakdown = (instrument or '').strip() or 'Instrumento sin dato'
                    for territory in locations:
                        territories[territory['id']] = territory
                        for categories in dict.fromkeys(((TOTAL,TOTAL),(administration,TOTAL),(administration,breakdown),(TOTAL,breakdown))):
                            totals[(territory['id'],period,categories)].update(values)
        note = (f'{len(seen):,} registros públicos con la fecha de {date_label} dentro de los cortes '
                'indicados. Cada corte se ha cotejado con el total de la API y se ha comprobado la '
                'unicidad de los registros. Las comunidades corresponden a la administración que convoca '
                'o concede. El total nacional incluye todos los ámbitos. Las cuantías de concesión se '
                'distinguen de los pagos. Los archivos conservan los campos de las series y omiten la identidad del beneficiario.')
        p = product(identifier,'BDNS · '+titles[kind],'IGAE · BDNS','F045',BDNS,note,inputs,
                    'Condiciones de reutilización del SNPSAP')
        yield publish('bdns',p,aggregate_records(totals,territories,labels),
                      ('Indicador','Administración','Marca MRR' if kind=='convocatorias' else 'Instrumento'),
                      units,section='ayudas',source_by_period=editions)


def write_index(folder, tables):
    path = ROOT/'datos/ayudas'/folder
    path.mkdir(parents=True, exist_ok=True)
    tables = list(tables)
    assert tables, folder
    (path/'index.json').write_bytes(encode(dict(revision=REVISION,tables=tables)))
    print(folder, len(tables), sum(table['rows'] for table in tables), flush=True)


if __name__=='__main__':
    write_index('contratos',contract_tables())
    write_index('feder',feder_tables())
    write_index('cohesion',cohesion_tables())
    write_index('bdns',bdns_tables())
