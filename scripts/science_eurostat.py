"""Publish Eurostat science statistics with original dimensions and quality flags."""
import json

from demography_collect import sha
from education_collect import jsonstat_grid, publish_grid
from science_collect import CACHE, write_index

PROFILES = (
    ('rd_e_gerdreg',120401,'Gasto interno en I+D por sector ejecutor',
     'Gasto interno en I+D por sector ejecutor. España y comunidades NUTS 2.'),
    ('gba_nabsfin07',120402,'Presupuesto público de I+D por objetivo socioeconómico',
     'Créditos presupuestarios públicos de I+D para España por objetivo NABS 2007. Son asignaciones, distintas del gasto ejecutado.'),
)
DIMENSIONS={'freq':'Frecuencia','unit':'Unidad','sectperf':'Sector ejecutor','nabs07':'Objetivo socioeconómico'}
UNITS={
    'Million euro':'Millones de euros',
    'Euro per inhabitant':'Euros por habitante',
    'Million units of national currency':'Millones en moneda nacional',
    'Million purchasing power standards (PPS)':'Millones en paridad de poder adquisitivo',
    'Million purchasing power standards (PPS) at 2005 prices':'Millones en paridad de poder adquisitivo a precios de 2005',
    'Purchasing power standard (PPS) per inhabitant at constant 2005 prices':'Paridad de poder adquisitivo por habitante a precios de 2005',
    'Percentage of gross domestic product (GDP)':'Porcentaje del PIB',
    'Percentage of total GBARD':'Porcentaje del presupuesto público de I+D',
}


def products():
    for dataset,identifier,title,note in PROFILES:
        raw=(CACHE/(dataset+'.json')).read_bytes()
        url=(CACHE/(dataset+'.url')).read_text(encoding='utf-8')
        structure,cells,axes,flags=jsonstat_grid(json.loads(raw),DIMENSIONS)
        units=next(d for d in structure['dimensions'] if d['name']=='Unidad')
        units['values']=[UNITS.get(name,name) for name in units['values']]
        table=dict(id=identifier,label=title,title=title,family='Eurostat · I+D y presupuestos',publisher='Eurostat',
                   sourceId='F130',unit='Según el selector de unidad',
                   unitsByCategory={'dimension':'Unidad','values':dict(zip(units['values'],units['values']))},
                   note=note+' La tabla conserva los estados y marcas de calidad de la fuente.',
                   sourceUrl='https://ec.europa.eu/eurostat/databrowser/view/'+dataset+'/default/table',
                   downloadUrl=url,license='Política de reutilización de Eurostat',**structure,
                   sourceTables=[dict(id=identifier,url=url,bytes=len(raw),sha256=sha(raw))])
        yield publish_grid('eurostat',table,cells,axes,flags,section='ciencia')


if __name__=='__main__':
    write_index('eurostat',products())
