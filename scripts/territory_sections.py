"""Verify the INE WFS counterparts of every published census-map edition."""
import argparse
import re
from concurrent.futures import ThreadPoolExecutor
import json
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import territory_collect as territory

WFS = 'https://www.ine.es/geoserver/ows'
DOWNLOAD = 'https://www.ine.es/dyngs/DAB/es/index.htm?cid=1389'


def query(**options):
    return WFS+'?'+urlencode(dict(SERVICE='WFS',VERSION='2.0.0',**options))


def capture(layer,refresh):
    key=layer.rsplit(':',1)[-1].replace('.','-')
    sample=query(REQUEST='GetFeature',TYPENAMES=layer,COUNT='1',OUTPUTFORMAT='application/json',SRSNAME='EPSG:4326')
    try:
        data=json.loads(territory.fetch('section-vector-'+key,sample,refresh))
        feature=data['features'][0]
        assert feature['geometry']['type'] in {'Polygon','MultiPolygon'},feature['geometry']['type']
        assert data['numberMatched']>0
        code=next((key for key,value in feature['properties'].items() if key.upper()=='CUSEC' and value),None)
        assert code, list(feature['properties'])
        return dict(layer=layer,status='verificado',sample=sample,codeField=code)
    except Exception as error:
        return dict(layer=layer,status='bloqueado',sample=sample,error=str(error))


def main(refresh=False):
    raw=territory.fetch('ine-wfs',query(REQUEST='GetCapabilities'),refresh)
    root=ET.fromstring(raw)
    names=[name.text for name in root.findall('.//{*}FeatureType/{*}Name')]
    expected={'SU.VectorStatisticalUnit',*(f'Secciones_{year}' for year in range(2007,2026)),
              'Secciones_Censo_Poblacion_Viviendas_2001','Secciones_Censo_Poblacion_Viviendas_2011'}
    assert {name.rsplit(':',1)[1] for name in names}==expected,names
    page=territory.fetch('ine-sections-download',DOWNLOAD,refresh).decode('utf-8')
    editions=[dict(year=year,url=url) for url,year in re.findall(r'<option value="(https://www\.ine\.es/prodyser/cartografia/[^"]+\.zip)"[^>]*>(\d{4})<',page)]
    assert {'2001','2003','2004','2005','2006',*(str(year) for year in range(2007,2027))}=={e['year'] for e in editions}
    with ThreadPoolExecutor(max_workers=5) as pool:
        records=list(pool.map(lambda layer:capture(layer,refresh),names))
    territory.save(territory.OUT/'section-vectors.json',dict(source=WFS,downloads=editions,downloadPage=DOWNLOAD,records=records,provenance=sorted(territory.PROVENANCE,key=lambda row:row['url'])))
    print([(item['layer'].split(':')[-1],item.get('matched',item.get('error'))) for item in records],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    main(parser.parse_args().refresh)
