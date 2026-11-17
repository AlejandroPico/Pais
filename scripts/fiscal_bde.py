"""Capture public-sector chapters 11–14 of the Boletín Estadístico."""
import argparse
import io
import re
from zipfile import ZipFile

from affiliation_collect import fetch
from commerce_bde import BASE, GEO, NATIONAL, PUBLIC_SOURCES, capture
from demography_collect import ROOT, encode, norm, sha

REVISION = '2026-11-17'
CHAPTERS = {
    11: 'Administraciones públicas',
    12: 'Administración central y Seguridad Social',
    13: 'Comunidades autónomas',
    14: 'Corporaciones locales',
}
TITLES = {
    '1104':'Pasivos y deuda según el PDE',
    '1306':'Deuda autonómica por instrumento y comunidad',
    '1309':'Deuda PDE por comunidad autónoma',
    '1310':'Deuda PDE por comunidad autónoma en porcentaje del PIB',
    '13a':'Capacidad o necesidad de financiación por comunidad autónoma',
    '1406':'Deuda de las corporaciones locales por entidad e instrumento',
    '1409':'Deuda de los ayuntamientos de más de 300.000 habitantes',
}
PUBLICATIONS = PUBLIC_SOURCES + ('secretaria general del tesoro', 'dgtpf', 'ministerio de economia y hacienda')
CITY_CODES = {
    'alicante':'03014','barcelona':'08019','bilbao':'48020','cordoba':'14021','comunidad de madrid':'28079',
    'madrid':'28079','malaga':'29067','region de murcia':'30030','murcia':'30030','palma':'07040',
    'las palmas':'35016','sevilla':'41091','valencia':'46250','valladolid':'47186','zaragoza':'50297',
}


def geography(key, description, chapter):
    fields = description.split('. ')
    if chapter == 13:
        for i, field in enumerate(fields):
            code = GEO.get(('community', norm(field)))
            if code:
                area = dict(level='community', id='community:'+code, code=code, name=field)
                return area, '. '.join(fields[:i]+fields[i+1:])
    if chapter == 14:
        match=re.search(r'(?:^|\.)\s*(ayuntamiento de (?P<city>[^.]+)|diputaci[oó]n [^.]+|cabildo [^.]+|consell [^.]+)',
                        description,re.I)
        if match:
            name=match[1].strip()
            code=CITY_CODES.get(norm(match['city'] or ''))
            if code:
                area=dict(level='municipal',id='municipal:'+code,code=code,name=name,provinceCode=code[:2])
            else:
                key=norm(name)
                area=dict(level='unlocated',id='unlocated:'+key,code=key,name=name)
            measure=(description[:match.start()]+description[match.end():]).strip(' .')
            return area,measure
    return NATIONAL, description


def main(refresh=False):
    cache = ROOT / '.cache/f09'
    output = ROOT / 'datos/hacienda/bde'
    cache.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    tables, sources, omitted = [], [], []
    for chapter in CHAPTERS:
        name = f'be{chapter}.zip'
        url = BASE + 'compartido/datos/zip/' + name
        data = fetch(url, cache / name, refresh)
        archive = dict(chapter=chapter, url=url, sha256=sha(data), bytes=len(data))
        sources.append(archive)
        with ZipFile(io.BytesIO(data)) as zipped:
            for file in sorted(zipped.namelist()):
                table, excluded = capture(chapter, file, zipped.read(file), archive, section='hacienda',
                    chapters=CHAPTERS, titles=TITLES, resolve_area=geography, public_sources=PUBLICATIONS)
                if table:
                    tables.append(table)
                if excluded:
                    omitted.append(dict(file=file, series=excluded))
    (output/'index.json').write_bytes(encode(dict(schemaVersion=1, revision=REVISION, tables=tables,
        provenance=sources, excludedSeries=omitted)))
    print(f'BdE: {len(tables)} cuadros, {sum(t["rows"] for t in tables)} observaciones')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    main(parser.parse_args().refresh)
