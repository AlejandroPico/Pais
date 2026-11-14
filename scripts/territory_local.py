"""Preserve official municipal polygons with their native codes and attributes."""
import argparse
from collections import Counter
import io
import json
import zipfile
from urllib.parse import urlencode
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
    def save(id,title,source,url,download,features,code,name,expected,period,*,group=None,center=None,credit=None):
        assert len(features)==expected,(id,len(features),expected)
        seen=set()
        for f in features:
            props=f['properties']
            identifier=str(props[code]).strip()
            if not identifier and source=='F171':
                identifier=str(props[props['TIPUS_UA']]).strip()
            row_id=props['FID'] if source=='F171' else props['objectid'] if source=='F172' else identifier
            assert row_id not in seen,(id,row_id)
            seen.add(row_id)
            f['id']=row_id
            props['atlasName']=str(props.get(name) or '').strip() or identifier
            props['atlasCode']=identifier
            if source=='F172':props['atlasId']=row_id
        file=id+'.geojson'
        territory.save(territory.OUT/'local'/file,dict(type='FeatureCollection',features=features))
        product=dict(id=id,title=title,sourceId=source,url=url,download=download,count=len(features),file='local/'+file,period=period)
        if group:product.update(group=group,center=center,credit=credit)
        products.append(product)
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
    def fetch_collection(id,url):
        collection=json.loads(territory.fetch(id,url,refresh))
        assert collection['type']=='FeatureCollection' and not collection.get('exceededTransferLimit'),id
        features=collection['features']
        assert collection.get('numberMatched',len(features))==len(features),id
        for item in features:
            if item['geometry'] is None:
                assert id in {'zaragoza-juntas','zaragoza-unidades'},id
                continue
            assert item['geometry']['type'] in {'Polygon','MultiPolygon'},id
            polygons=item['geometry']['coordinates']
            if item['geometry']['type']=='Polygon':polygons=[polygons]
            for polygon in polygons:
                for ring in polygon:
                    assert len(ring)>=4 and ring[0]==ring[-1],(id,item.get('id'))
                    assert all(-10<=x<=5 and 35<=y<=44 for x,y,*_ in ring),id
        return features

    for kind,layer,code,expected in [('barrios',224,'coddistbar',88),('distritos',225,'coddistrit',22)]:
        id='valencia-'+kind
        source='https://datos.gob.es/es/catalogo/l01462508-'+kind
        url=f'https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/{layer}/query?where=1%3D1&outFields=%2A&f=geojson'
        save(id,kind.capitalize()+' · València','F172',source,url,fetch_collection(id,url),code,'nombre',
             expected,'Catálogo de marzo de 2026',group='València',center=[-0.376,39.459],credit='Ayuntamiento de València')

    for kind,filename,code,name,expected in [('barrios','Barrio','ID_BARRIO','NOMBARRIO',419),
                                        ('distritos','DistritoMunicipal','ID_DISMUNI','NOMBRE',11)]:
        id='malaga-'+kind
        source='https://datosabiertos.malaga.eu/dataset/sistema-de-informacion-cartografica-'+('barrio' if kind=='barrios' else 'distrito-municipal')
        url='https://datosabiertos.malaga.eu/recursos/urbanismoEInfraestructura/planimetria/callejero/da_cartografia'+filename+'-4326.geojson'
        save(id,kind.capitalize()+' · Málaga','F174',source,url,fetch_collection(id,url),code,name,
             expected,'Captura del 14/11/2026',group='Málaga',center=[-4.432,36.72],credit='Ayuntamiento de Málaga')

    def zaragoza_url(group,layer):
        return f'https://idezar-sig.zaragoza.es/servicios/geoserver/{group}/wfs?'+urlencode(dict(
            REQUEST='GetFeature',SERVICE='WFS',VERSION='2.0.0',outputFormat='application/json',typeName=layer,srsName='EPSG:4326'))

    municipal={}
    for kind,title,layer,record,expected in [
        ('distritos','Distritos municipales','Distritos_Municipales','3962',16),
        ('juntas','Juntas municipales y vecinales','Juntas_Municipales_Vecinales','3964',29),
    ]:
        id='zaragoza-'+kind
        url=zaragoza_url('urbanismo','urbanismo:'+layer)
        features=fetch_collection(id,url)
        if kind=='juntas':
            excluded=[item for item in features if item['geometry'] is None]
            assert len(excluded)==1 and excluded[0]['properties']['estado']=='BAJA'
            features=[item for item in features if item['geometry'] is not None]
        municipal.update({item['properties']['referencia']:item['properties']['nombre'] for item in features})
        save(id,title+' · Zaragoza','F173','https://www.zaragoza.es/web/espacio-de-datos/servicio/catalogo/'+record,url,
             features,'referencia','nombre',expected,'Captura del 14/11/2026',
             group='Zaragoza',center=[-0.889,41.657],credit='Ayuntamiento de Zaragoza')
    url=zaragoza_url('au','au:AdministrativeUnit')
    units=fetch_collection('zaragoza-unidades',url)
    omitted=[item for item in units if item['geometry'] is None]
    assert len(omitted)==1 and omitted[0]['properties']['nationalCode'] is None
    units=[item for item in units if item['geometry'] is not None]
    for item in units:
        props=item['properties']
        code=props['nationalCode']
        props['atlasName']=municipal.get(code) or ('Zaragoza' if code=='50900' else code)
        for field in ('inspireId','nationalLevel','upperLevelUnit'):
            if field in props:props[field]=json.dumps(props[field],ensure_ascii=False)
    assert Counter(len(f['properties']['nationalCode']) for f in units)=={5:1,8:16,11:29}
    save('zaragoza-unidades','Unidades administrativas INSPIRE · Zaragoza','F173',
         'https://www.zaragoza.es/web/espacio-de-datos/servicio/catalogo/6042',url,
         units,'nationalCode','atlasName',46,'12 de junio de 2026',
         group='Zaragoza',center=[-0.889,41.657],credit='Ayuntamiento de Zaragoza')

    base='https://sig.asturias.es/servicios/rest/services/Visor/CartografiaBase/MapServer/18'
    url=base+'/query?where=1%3D1&outFields=%2A&outSR=4326&f=geojson'
    count=json.loads(territory.fetch('asturias-parroquias-count',base+'/query?where=1%3D1&returnCountOnly=true&f=json',refresh))['count']
    save('asturias-parroquias','Parroquias y recintos sin parroquia · Asturias','F153',base,url,
         fetch_collection('asturias-parroquias',url),'objectid','topo_ofi',count,'Captura del 14/11/2026',
         group='Asturias',center=[-5.85,43.33],credit='Administración del Principado de Asturias · CC BY 4.0')

    territory.save(territory.ROOT/'registry/local-territory.json',dict(products=products,provenance=territory.PROVENANCE))
    print('Polígonos municipales:',sum(p['count'] for p in products),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
