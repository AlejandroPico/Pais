"""Import the four annual INE section editions absent from its WMS."""
import argparse
import gzip
import hashlib
import io
import json
import sys
import zipfile
from collections import Counter

import territory_collect as territory
from ingest import simplify


def capture(year,refresh):
    import shapefile
    from pyproj import CRS, Transformer
    url=f'https://www.ine.es/prodyser/cartografia/seccionado_{year}.zip'
    raw=territory.fetch('seccionado-shp-'+str(year),url,refresh)
    features=[]
    counts=Counter()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members={name.lower():name for name in archive.namelist()}
        for name in sorted(name for name in members if name.endswith('.shp')):
            stem=name[:-4]
            def content(extension):
                return archive.read(members[stem+extension])
            transform=Transformer.from_crs(CRS.from_wkt(content('.prj').decode('ascii')),4326,always_xy=True)
            with shapefile.Reader(shp=io.BytesIO(content('.shp')),dbf=io.BytesIO(content('.dbf')),encoding='latin-1') as reader:
                for item in reader.iterShapeRecords():
                    props=item.record.as_dict()
                    code=props['PROVMUN']+props['DISTRITO']+props['SECCION']
                    standard=len(code)==10 and code.isdecimal() and '01'<=code[:2]<='52'
                    label='Sección '+code if standard else 'Recinto '+(code or 'sin código publicado')
                    geometry=item.shape.__geo_interface__
                    polygons=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
                    result=[]
                    for polygon in polygons:
                        rings=[]
                        for ring in polygon:
                            xs,ys=transform.transform([v[0] for v in ring],[v[1] for v in ring])
                            coordinates=list(zip(xs,ys))
                            reduced=simplify(coordinates,0.00008)
                            if len(reduced)<4:
                                reduced=coordinates
                            rings.append([[round(x,6),round(y,6)] for x,y in reduced])
                        result.append(rings)
                    if standard:counts[code[:2]]+=1
                    features.append(dict(type='Feature',id=len(features),properties={**props,'atlasName':label,'atlasCode':code,'atlasId':len(features)},
                                         geometry=dict(type='MultiPolygon',coordinates=result)))
    assert len(counts)>=50,(year,counts)
    assert len(features)>30000,(year,len(features))
    name=f'local/secciones-{year}.geojson.gz'
    body=json.dumps(dict(type='FeatureCollection',features=features),ensure_ascii=False,separators=(',',':')).encode()
    path=territory.OUT/name
    path.parent.mkdir(parents=True,exist_ok=True)
    archive=gzip.compress(body,compresslevel=5,mtime=0)
    temporary=path.with_suffix('.tmp')
    temporary.write_bytes(archive)
    temporary.replace(path)
    print(year,len(features),flush=True)
    return dict(id=f'archive-sections-{year}',title=f'Secciones censales · {year}',sourceId='F005',url='https://www.ine.es/dyngs/DAB/es/index.htm?cid=1389',
                download=url,count=len(features),file=name,period=str(year),sha256=hashlib.sha256(archive).hexdigest())


def main(refresh):
    local=territory.CACHE/'python'
    if local.is_dir():
        sys.path.insert(0,str(local))
    products=[capture(year,refresh) for year in range(2003,2007)]
    territory.save(territory.ROOT/'registry/section-archives.json',dict(products=products,provenance=territory.PROVENANCE))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
