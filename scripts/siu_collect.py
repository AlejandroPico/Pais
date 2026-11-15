"""Capture and verify the official SIU map and feature-query endpoints."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'datos/vivienda/siu'
URL='https://mapas.fomento.gob.es/arcgis/services/SIU/Servicios_OGC/MapServer/WMSServer'
ORIGIN='https://alejandropico.github.io'
NAMES={'OGC_Areas_Urbanas':'Áreas urbanas','OGC_Clases_Suelo':'Clases de suelo',
       'OGC_Recintos':'Recintos de planeamiento','OGC_Sectores':'Sectores urbanísticos'}


def retrieve(parameters):
    url=URL+'?'+urlencode({'SERVICE':'WMS','VERSION':'1.3.0',**parameters})
    with urlopen(Request(url,headers={'Origin':ORIGIN}),timeout=35) as response:
        if response.headers.get('Access-Control-Allow-Origin') not in {ORIGIN,'*'}:
            raise ValueError('El servicio no admite el origen público')
        return url,response.read()


def collect(layer):
    name=layer.findtext('{*}Name')
    year=None
    if name in NAMES:
        title=NAMES[name]
        group='Planeamiento y áreas urbanas'
        zoom=7 if name.endswith('Urbanas') else 10
    else:
        prefix,subject,*years=name.split('_')
        assert prefix=='OGC' and subject in {'CORINE','SIOSE'},name
        if years[0]=='Variacion':
            years=years[1:]
            title='Cambios CORINE '+ '–'.join(years)
        else:
            title=subject+' '+years[0]
        year={'from':years[0],'to':years[-1]}
        group='Ocupación del suelo'
        zoom=8 if subject=='CORINE' else 10
    bbox=layer.find("{*}BoundingBox[@CRS='CRS:84']")
    bounds=[float(bbox.get(k)) for k in ('minx','miny','maxx','maxy')]
    provider=dict(id='siu',url=URL,layers=name,version='1.3.0',requestCrs='EPSG:3857',
                  sourceId='F111',credit='Sistema de Información Urbana · MIVAU',bounds=bounds,queryable=False)
    parameters=dict(LAYERS=name,STYLES='',CRS='EPSG:3857',BBOX='-417000,4918000,-405000,4930000',
                    WIDTH='256',HEIGHT='256',FORMAT='image/png',TRANSPARENT='TRUE')
    record=dict(id='siu-'+name[4:].lower().replace('_','-'),name=title,group=group,minzoom=zoom,provider=provider,
                period=year or 'Según la publicación vigente del SIU')
    try:
        url,image=retrieve(dict(REQUEST='GetMap',**parameters))
        assert image.startswith(b'\x89PNG\r\n\x1a\n'), 'El servicio no devolvió PNG'
        record['verifiedMap']=url
    except (OSError,ValueError,AssertionError) as error:
        record['error']=str(error)
        return record
    try:
        url,body=retrieve(dict(REQUEST='GetFeatureInfo',QUERY_LAYERS=name,INFO_FORMAT='application/geo+json',
                               I=128,J=128,FEATURE_COUNT=5,**parameters))
        assert json.loads(body).get('type')=='FeatureCollection'
        provider.update(queryable=True,infoFormat='application/geo+json')
        record['verifiedInfo']=url
    except (OSError,ValueError,AssertionError):
        pass
    return record


def main():
    url,raw=retrieve({'REQUEST':'GetCapabilities'})
    xml=ET.fromstring(raw)
    layers=[layer for layer in xml.findall('.//{*}Layer') if layer.findtext('{*}Name')]
    with ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(collect,layers))
    for i, record in enumerate(records):
        if 'error' in record:
            records[i]=collect(layers[i])
    OUT.mkdir(parents=True,exist_ok=True)
    result=dict(revision='2026-11-15',capabilities=url,layers=[r for r in records if 'verifiedMap' in r],
                unavailable=[r for r in records if 'error' in r])
    (OUT/'layers.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(len(records), len(result['layers']), sum(r['provider']['queryable'] for r in records))
    for row in result['unavailable']:
        print(row['id'],row['error'])


if __name__=='__main__':
    main()
