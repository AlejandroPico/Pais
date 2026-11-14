"""Relate discovery catalogues by official identifiers without conflating datasets."""
import re
from collections import defaultdict
from urllib.parse import unquote, urlsplit

THEMES = {
    'ciencia-tecnologia': ['F12', 'F23'], 'comercio': ['F08'], 'cultura-ocio': ['F25', 'F26'],
    'demografia': ['F02'], 'deporte': ['F26'], 'economia': ['F03', 'F07', 'F08', 'F09'],
    'educacion': ['F11'], 'empleo': ['F04'], 'energia': ['F21'], 'hacienda': ['F09'],
    'industria': ['F07', 'F18', 'F21'], 'legislacion-justicia': ['F28', 'F29'],
    'medio-ambiente': ['F15', 'F16', 'F17', 'F18', 'F19', 'F20'], 'medio-rural-pesca': ['F14', 'F15'],
    'salud': ['F13'], 'sector-publico': ['F09', 'F10', 'F27', 'F28'], 'seguridad': ['F29'],
    'sociedad-bienestar': ['F03', 'F05'], 'transporte': ['F22'], 'turismo': ['F24'],
    'urbanismo-infraestructuras': ['F01', 'F06', 'F22', 'F28'], 'vivienda': ['F06'],
    'AGRI': ['F14', 'F15'], 'ECON': ['F03', 'F07', 'F08', 'F09'], 'EDUC': ['F11', 'F12', 'F25'],
    'ENER': ['F21'], 'ENVI': ['F15', 'F16', 'F17', 'F18', 'F19', 'F20'],
    'GOVE': ['F09', 'F10', 'F27', 'F28'], 'HEAL': ['F13'], 'INTR': ['F28'],
    'JUST': ['F28', 'F29'], 'REGI': ['F01', 'F06', 'F28'], 'SOCI': ['F02', 'F03', 'F04', 'F05'],
    'TECH': ['F12', 'F23'], 'TRAN': ['F22'],
}
INSPIRE = {
    'ad': ['F01'], 'au': ['F01', 'F28'], 'bu': ['F01'], 'cp': ['F01'],
    'el': ['F01'], 'gn': ['F01'], 'oi': ['F01'], 'pd': ['F02'],
    'af': ['F14'], 'br': ['F15'], 'hb': ['F15'], 'ps': ['F15'], 'sd': ['F15'],
    'hy': ['F16'], 'ac': ['F17', 'F20'], 'mf': ['F17'], 'ge': ['F18'], 'nz': ['F18'],
    'so': ['F18'], 'of': ['F19'], 'sr': ['F19'], 'ef': ['F15', 'F20'],
    'er': ['F21'], 'tn': ['F22'], 'lc': ['F15'], 'lu': ['F06', 'F15'],
}


def theme_candidates(uris):
    candidates = set()
    for uri in uris:
        parsed = urlsplit(uri)
        if parsed.hostname == 'datos.gob.es' and '/kos/sector-publico/sector/' in parsed.path:
            candidates.update(THEMES.get(parsed.path.rsplit('/', 1)[-1], []))
        elif parsed.hostname == 'publications.europa.eu' and '/authority/data-theme/' in parsed.path:
            candidates.update(THEMES.get(parsed.path.rsplit('/', 1)[-1], []))
        elif parsed.hostname == 'inspire.ec.europa.eu' and parsed.path.startswith('/theme/'):
            candidates.update(INSPIRE.get(parsed.path.rsplit('/', 1)[-1], []))
    return sorted(candidates)


def enrich_national(products, metadata):
    shared = defaultdict(list)
    for product in products:
        record = metadata.get(product['id'], {})
        fields = {}
        if themes := record.get('themes'):
            fields['Temas declarados por el publicador'] = ' · '.join(themes)
            product['suggestedCategoryIds'] = theme_candidates(themes)
        if areas := record.get('areas'):
            product['coverage'] = ' · '.join(unquote(urlsplit(area).path.rsplit('/', 1)[-1]) or area for area in areas)
            fields['Cobertura declarada'] = ' · '.join(areas)
        if licenses := record.get('licenses'):
            product['license'] = ' · '.join(licenses)
        for identifier in record.get('identifiers', []):
            parsed = urlsplit(identifier)
            if parsed.scheme in {'http', 'https'} and parsed.netloc and parsed.path not in {'','/'}:
                shared[(product['sourceId'], identifier)].append(product)
        if fields:
            product['fields'] = fields
    for (_, identifier), records in shared.items():
        if len(records) < 2:
            continue
        for product in records:
            product.setdefault('fields', {})['Coincidencia de identificador publicado'] = identifier
            product.setdefault('links', {}).update({
                'Mismo identificador declarado · '+peer['id'].rsplit('/', 1)[-1]: peer['url']
                for peer in records if peer is not product
            })


def link_ine(products, ine_operations):
    ioe = {row['id'].removeprefix('ioe:'): row for row in products['ioe']}
    operations = {op['Id']: ioe.get(str(op.get('Cod_IOE'))) for op in ine_operations}
    equivalents = defaultdict(list)
    for kind in ('demography', 'welfare', 'labor'):
        for row in products.get(kind, []):
            match = re.fullmatch(r'https://www\.ine\.es/jaxiT3/Tabla\.htm\?t=(\d+)',row['url'])
            if match:
                equivalents['ine:'+match[1]].append(row)
    for row in products['ine']:
        official_ops = [operations[op] for op in row['operationIds'] if operations.get(op)]
        same = equivalents[row['id']]
        row['suggestedCategoryIds'] = sorted(set(row['suggestedCategoryIds']) | {
            category for product in [*official_ops, *same] for category in product.get('suggestedCategoryIds', [])
        })
        if official_ops:
            row.setdefault('links', {}).update({'Operación '+op['id']: op['url'] for op in official_ops})
        # Use an existing verified map action only when the exact edition and table ID match.
        target = next((item for item in same if item['status']=='integrado'), None)
        if target and 'review' not in row:
            for field in ('status', 'categoryIds', 'license', 'coverage', 'period', 'mapAction', 'notes', 'review'):
                if field in target:
                    row[field] = target[field]
