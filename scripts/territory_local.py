"""Preserve official municipal polygons with their native codes and attributes."""
import argparse
from collections import Counter
import io
import json
import zipfile
import territory_collect as territory

MADRID = 'https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas/information'
BARCELONA = 'https://opendata-ajuntament.barcelona.cat/data/dataset/20170706-districtes-barris'
MADRID_DATA = 'https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas/resource/'
BARCELONA_DATA = 'https://opendata-ajuntament.barcelona.cat/data/dataset/808daafa-d9ce-48c0-925a-fa5afdb1ed41/resource/cd800462-f326-429f-a67a-c69b7fc4c50a/download'

def shapefile_features(raw):
    import sys
    local=territory.CACHE/'python'
    if local.is_dir():
        sys.path.insert(0,str(local))
    import shapefile
    from pyproj import CRS, Transformer
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        def item(extension):
            name=next(name for name in archive.namelist() if name.lower().endswith(extension))
            return archive.read(name)
        crs=CRS.from_wkt(item('.prj').decode('ascii'))
        transform=Transformer.from_crs(crs,4326,always_xy=True)
        encoding=item('.cpg').decode('ascii').strip()
        with shapefile.Reader(shp=io.BytesIO(item('.shp')),shx=io.BytesIO(item('.shx')),
                              dbf=io.BytesIO(item('.dbf')),encoding=encoding) as reader:
            for feature in reader.iterShapeRecords():
                geometry=feature.shape.__geo_interface__
                polygons=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
                coords=[[[[round(v,8) for v in transform.transform(x,y)] for x,y,*_ in ring]
                         for ring in polygon] for polygon in polygons]
                yield dict(type='Feature',properties=feature.record.as_dict(),
                           geometry=dict(type='MultiPolygon',coordinates=coords))


def main(refresh=False):
    products=[]
    def save(id,title,source,url,download,features,code,name,expected,period):
        assert len(features)==expected,(id,len(features),expected)
        seen=set()
        for f in features:
            props=f['properties']
            identifier=str(props[code]).strip()
            if not identifier and source=='F171':
                identifier=str(props[props['TIPUS_UA']]).strip()
            row_id=props['FID'] if source=='F171' else identifier
            assert row_id not in seen,(id,row_id)
            seen.add(row_id)
            f['id']=row_id
            props['atlasName']=str(props.get(name) or '').strip() or identifier
            props['atlasCode']=identifier
        file=id+'.geojson'
        territory.save(territory.OUT/'local'/file,dict(type='FeatureCollection',features=features))
        products.append(dict(id=id,title=title,sourceId=source,url=url,download=download,count=len(features),file='local/'+file,period=period))
    for number,key,title,code,expected,period in [
        (0,'municipio','Término municipal · Madrid',None,1,'16 de mayo de 2024'),
        (6,'barrios','Barrios · Madrid','COD_BAR',131,'Delimitación de 2021; denominaciones actualizadas en 2022'),
        (2,'distritos','Distritos · Madrid','COD_DIS',21,'Delimitación de 2021'),
        (1,'secciones','Secciones censales municipales · Madrid','COD_SECCIO',2462,'Junio de 2022'),
    ]:
        resource=f'900012-{number}-limites-administrativos-mapas'
        url=f'{MADRID_DATA}{resource}/download/{resource}.zip'
        features=list(shapefile_features(territory.fetch('madrid-shp-'+str(number),url,refresh)))
        if code is None:
            features[0]['properties'].update(atlasMunicipality='28079',atlasCity='Madrid')
        save('madrid-'+key,title,'F170',MADRID,url,features,code or 'atlasMunicipality',
             'NOMBRE' if code else 'atlasCity',expected,period)
    with zipfile.ZipFile(io.BytesIO(territory.fetch('barcelona-divisiones',BARCELONA_DATA,refresh))) as archive:
        polygons=next(name for name in archive.namelist() if name.endswith('_POLIGONS.json'))
        features=json.loads(archive.read(polygons))['features']
    specs={
        'TERME':('municipio','Término municipal',1),'DISTRICTE':('distritos','Distritos',10),
        'BARRI':('barrios','Barrios',73),'AEB':('areas','Áreas estadísticas básicas',233),
        'SEC_CENS':('secciones','Secciones censales municipales',1068),'GRANBARRI':('grandes-barrios','Grandes barrios',40),
        'ZUA':('urban-audit','Zonas Urban Audit',74),'AREA_I':('interes','Áreas de interés',2),
    }
    assert Counter(f['properties']['TIPUS_UA'] for f in features)=={key:row[2] for key,row in specs.items()}
    for kind,(id,title,expected) in specs.items():
        selected=[f for f in features if f['properties']['TIPUS_UA']==kind]
        save('barcelona-'+id,title+' · Barcelona','F171',BARCELONA,BARCELONA_DATA,selected,'CODI_UA','NOM',expected,'Distribución GeoJSON actualizada el 1 de diciembre de 2021')
    territory.save(territory.ROOT/'registry/local-territory.json',dict(products=products,provenance=territory.PROVENANCE))
    print('Polígonos municipales:',sum(p['count'] for p in products),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
