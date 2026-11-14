"""Convert dated CNIG GeoPackages into individually loadable layers, preserving all rows."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import territory_collect as territory

SOURCES = {
    2023: 'https://centrodedescargas.cnig.es/CentroDescargas/detalleArchivo?sec=12969663',
    2024: 'https://centrodedescargas.cnig.es/CentroDescargas/detalleArchivo?sec=12969664',
}
FAMILIES = {
    'll_municipales_histo': 'Trazados históricos municipales',
    'll_municipales': 'Líneas municipales',
    'll_provinciales': 'Líneas provinciales',
    'll_autonomicas': 'Líneas autonómicas',
    'recintos_municipales': 'Recintos municipales',
    'recintos_provinciales': 'Recintos provinciales',
    'recintos_autonomicas': 'Recintos autonómicos',
}
CREDIT = 'Obra derivada de BDLJE CC-BY 4.0 ign.es'


def sha256(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def export(path, year):
    import shapely
    source = SOURCES[year]
    products = []
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True) as connection:
        assert connection.execute('PRAGMA quick_check').fetchall() == [('ok',)]
        metadata = connection.execute('SELECT table_name, column_name, geometry_type_name, srs_id FROM gpkg_geometry_columns').fetchall()
        by_name = {name:(column,geometry,srid) for name,column,geometry,srid in metadata}
        assert len(by_name)==14
        connection.row_factory = sqlite3.Row
        for family,title in FAMILIES.items():
            for zone,suffix,name in [('peninbal','peninbal_etrs89','Península, Baleares y plazas españolas'),('canarias','canarias_wgs84','Canarias')]:
                table = family+'_inspire_'+suffix
                column, geometry_type, srid = by_name[table]
                is_line = family.startswith('ll_')
                assert column=='geom' and geometry_type==('MULTILINESTRING' if is_line else 'MULTIPOLYGON')
                assert srid==(4326 if zone=='canarias' else 4258)
                rows = connection.execute(f'SELECT * FROM "{table}" ORDER BY fid').fetchall()
                encoded = []
                for row in rows:
                    geometry = row[column]
                    assert geometry[:2]==b'GP'
                    envelope=(geometry[3]>>1)&7
                    original=shapely.from_wkb(geometry[8+(0,32,48,48,64)[envelope]:])
                    assert not original.is_empty
                    x1,y1,x2,y2=original.bounds
                    assert -20<=x1<=x2<=5 and 26<=y1<=y2<=45,(table,original.bounds)
                    reduced=shapely.simplify(original,0.00004,preserve_topology=True)
                    assert not reduced.is_empty
                    attrs={key:row[key] for key in row.keys() if key!=column}
                    code=attrs.get('NATCODE') or attrs.get('NATIONALCO') or attrs['INSPIREID']
                    attrs.update(atlasId=row['fid'],atlasCode=code,atlasName=attrs.get('NAMEUNIT') or attrs.get('NAME_BOUND') or code)
                    encoded.append(dict(type='Feature',id=row['fid'],properties=attrs,geometry=json.loads(shapely.to_geojson(reduced))))
                id=f'cnig-{year}-{family.replace("_","-")}-{zone}'
                file=f'local/{id}.geojson.gz'
                target=territory.OUT/file
                target.parent.mkdir(parents=True, exist_ok=True)
                payload=json.dumps(dict(type='FeatureCollection',features=encoded),ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
                temporary=target.with_suffix('.tmp')
                temporary.write_bytes(gzip.compress(payload,compresslevel=5,mtime=0))
                temporary.replace(target)
                products.append(dict(id=id,title=f'{title} · {name} · {year}',sourceId='F006',url=source,
                    download=source,count=len(rows),file=file,period=f'{year}-01-01',group=f'Límites vectoriales · {year}',
                    credit=CREDIT,geometry='line' if is_line else 'polygon',coverage=name,
                    layer=table,sha256=sha256(target)))
    print(year,len(products),sum(row['count'] for row in products),flush=True)
    return products,dict(url=source,sha256=sha256(path),bytes=path.stat().st_size,filename=path.name,year=year)


def main(files):
    local=territory.CACHE/'python'
    if local.is_dir():
        sys.path.insert(0,str(local))
    products,provenance=[],[]
    for year,path in zip(SOURCES, files, strict=True):
        edition,origin=export(path,year)
        products.extend(edition)
        provenance.append(origin)
    territory.save(territory.ROOT/'registry/cnig-history.json',dict(products=products,provenance=provenance))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('files',nargs=2,type=Path,metavar='GPKG',help='GeoPackage 2023 seguido del GeoPackage 2024')
    main(parser.parse_args().files)
