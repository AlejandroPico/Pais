"""Preserve each published day and population group of MoMo and Kairós."""
from array import array
from collections import Counter
import csv
from datetime import date, timedelta
import gzip
from hashlib import file_digest
import math

from commerce_bde import NATIONAL
from demography_collect import encode, sha
from fiscal_workbooks import area
from funding_collect import COMMUNITY_NAMES
from health_capture import REVISION
from health_collect import OUTPUT, product
from science_collect import PROVINCES

FIRST=date(2015,1,1)
SEX={'all':'Todos','1':'Hombres','6':'Mujeres'}
AGE={'all':'todas las edades','0-14':'0–14 años','15-44':'15–44 años','45-64':'45–64 años',
     '65-74':'65–74 años','75-84':'75–84 años','+65':'65 años o más','+85':'85 años o más'}
MOMO={
    'defunciones_observadas':'Defunciones observadas con corrección de retraso',
    'defunciones_estimadas_base':'Defunciones esperadas en el modelo base',
    'defunciones_estimadas_base_q01':'Defunciones esperadas · percentil 1 del modelo base',
    'defunciones_estimadas_base_q99':'Defunciones esperadas · percentil 99 del modelo base',
    'defunciones_atrib_exc_temp':'Defunciones estimadas atribuibles al calor',
    'defunciones_atrib_def_temp':'Defunciones estimadas atribuibles al frío',
}
KAIROS={
    'prob_exceso_mort_por_defecto_temp':'Probabilidad de exceso de mortalidad por frío',
    'prob_exceso_mort_por_exceso_temp':'Probabilidad de exceso de mortalidad por calor',
    'kairos_defecto_temp':'Índice Kairós por frío',
    'kairos_exceso_temp':'Índice Kairós por calor',
}
UNAVAILABLE='Sin observación para este día y grupo'
MISSING='Dato sin publicar en la distribución'


def area_of(scope, code):
    if scope=='nacional':
        return NATIONAL
    code=code.zfill(2)
    if scope=='ccaa':
        return area(COMMUNITY_NAMES[code],'community',code)
    assert scope=='provincia',scope
    return area(PROVINCES[code],'province',code)


def observation(value):
    if value in {'NA',''}:
        return math.inf
    result=float(value)
    assert math.isfinite(result),value
    return result


def cell(value):
    if math.isnan(value):
        return UNAVAILABLE
    if math.isinf(value):
        return MISSING
    return int(value) if value.is_integer() else value


def surveillance(entry,path):
    momo=path.name=='momo.csv'
    measures=MOMO if momo else KAIROS
    territories=[*([NATIONAL] if momo else []),
                 *(area(name,'community',code) for code,name in COMMUNITY_NAMES.items()),
                 *(area(name,'province',code) for code,name in PROVINCES.items())]
    areas={a['id']:i for i,a in enumerate(territories)}
    days=(date.fromisoformat(REVISION)-FIRST).days+14
    size=days*len(territories)
    by_group={}
    presence={}
    end=-1
    date_field='fecha_defuncion' if momo else 'fecha'
    with path.open(encoding='utf-8-sig',newline='') as stream:
        data=csv.DictReader(stream)
        assert set(measures)<=set(data.fieldnames)
        for row in data:
            group=(row['cod_sexo'],row['cod_gedad'])
            if group not in by_group:
                assert group[0] in SEX and group[1] in AGE,group
                by_group[group]=[array('d',[math.nan])*size for _ in measures]
                presence[group]=bytearray(size)
            territory=area_of(row['ambito'],row['cod_ine_ambito'])
            day=(date.fromisoformat(row[date_field])-FIRST).days
            assert 0<=day<days,row[date_field]
            end=max(end,day)
            index=areas[territory['id']]*days+day
            assert not presence[group][index],(territory,group,row[date_field])
            presence[group][index]=1
            for values,measure in zip(by_group[group],measures,strict=True):
                values[index]=observation(row[measure])
    periods=[dict(id=(FIRST+timedelta(days=i)).isoformat(),label=(FIRST+timedelta(days=i)).isoformat())
             for i in range(end+1)]
    assert len(periods)>3900
    groups=[(s,a) for s in SEX for a in AGE if (s,a) in by_group]
    dimension=dict(name='Sexo y edad',values=[
        'Total' if (s,a)==('all','all') else f'{SEX[s]} · {AGE[a]}' for s,a in groups])
    output=OUTPUT/'isciii'
    output.mkdir(parents=True,exist_ok=True)
    with path.open('rb') as stream:
        digest=file_digest(stream,'sha256').hexdigest()
    products=[]
    for index,(measure,title) in enumerate(measures.items()):
        identifier=(130200 if momo else 130220)+index
        unit=('Defunciones' if momo else 'Probabilidad de 0 a 1' if measure.startswith('prob_') else 'Nivel Kairós publicado')
        table=product({**entry,'title':title},identifier,'ISCIII · '+('MoMo' if momo else 'Kairós'),
            'Instituto de Salud Carlos III',unit,
            ('Cada día, territorio y grupo publicado se conserva. Las cifras observadas incorporan la corrección '
             'por retraso de notificación. Las esperadas y atribuibles son estimaciones revisables del modelo.'
             if momo else 'Probabilidad o nivel publicado por día, territorio y grupo. El suceso modelizado es '
             'un exceso de mortalidad atribuible a calor o frío igual o superior al 10 %.'),b'',
            periods=periods,territories=territories,dimensions=[dimension],partitionDimension=dimension['name'])
        table['sourceTables']=[dict(id=identifier,url=entry['download'],bytes=path.stat().st_size,sha256=digest)]
        missing=Counter()
        shards=[]
        rows=len(territories)*len(periods)
        for part,group in enumerate(groups):
            values=by_group[group][index]
            cells=[cell(values[a*days+d]) for a in range(len(territories)) for d in range(end+1)]
            missing.update(value for value in cells if isinstance(value,str))
            payload=encode(dict(axes=[-2,-1],cells=cells))
            compressed=gzip.compress(payload,compresslevel=6,mtime=0)
            key=f'main-d{part}'
            filename=f'{identifier}-{key}.json.gz'
            (output/filename).write_bytes(compressed)
            shards.append(dict(id=key,file=filename,rows=rows,bytes=len(compressed),sha256=sha(compressed),
                               contentSha256=sha(payload)))
        products.append({**table,'dataFolder':'salud/isciii','shards':shards,'rows':rows*len(groups),
                         'missingTokens':dict(missing)})
    return products
