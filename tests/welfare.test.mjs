import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {defaultDimensions,queryCube,unitFor,seriesCsv,periodTimestamp} from '../src/demography-data.ts';
const base=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,base),'utf8'));
const index=read('datos/renta/ine/index.json');
const table=id=>index.tables.find(t=>t.id===id);
const bytes=(t,id='main')=>fs.readFileSync(new URL('datos/renta/ine/'+t.shards.find(s=>s.id===id).file,base));
const cube=(t,id='main')=>JSON.parse(gunzipSync(bytes(t,id)));
const sha=b=>createHash('sha256').update(b).digest('hex');
const query=(t,code,year)=>({period:t.periods.findIndex(p=>p.id===year),dims:defaultDimensions(t),level:code.split(':')[0],territory:t.territories.findIndex(a=>a.id===code)});

test('all welfare cubes retain verified content, complete dictionaries, original sources and territorial shards',()=>{
  assert.equal(index.tables.length,51);assert.equal(new Set(index.tables.map(t=>t.id)).size,index.tables.length);
  const configured=read('registry/welfare-tables.json');assert.deepEqual(index.tables.map(t=>t.id),configured.tables.map(t=>t.id));
  let total=0;
  for(const t of index.tables){
    assert.equal(new Set(t.territories.map(a=>a.id)).size,t.territories.length);
    const sources=new Set(t.sourceTables.map(s=>s.id));let count=0;
    for(const shard of t.shards){
      const compressed=bytes(t,shard.id),content=gunzipSync(compressed);assert.equal(sha(compressed),shard.sha256);assert.equal(sha(content),shard.contentSha256);
      const rows=JSON.parse(content).rows;assert.equal(rows.length,shard.rows);count+=rows.length;
      for(const r of rows){
        assert.equal(r.length,t.dimensions.length+5);assert.ok(t.territories[r[0]]);assert.ok(t.periods[r[1]]);assert.ok(sources.has(r.at(-1)));
        for(let d=0;d<t.dimensions.length;d++)assert.ok(r[d+2]>=0&&r[d+2]<t.dimensions[d].values.length);
        assert.ok(r.at(-3)===null||Number.isFinite(r.at(-3)));assert.equal(typeof r.at(-2),'string');
        if(shard.id!=='main')assert.equal(t.territories[r[0]].provinceCode,shard.id);
      }
    }
    assert.equal(count,t.rows);assert.equal(t.rawRows-t.duplicateRows,t.rows);total+=count;
    for(const a of t.territories){if(a.level==='municipal')assert.match(a.code,/^\d{5}$/);if(a.level==='district')assert.match(a.code,/^\d{7}$/);if(a.level==='section')assert.match(a.code,/^\d{10}$/);}
  }
  assert.ok(total>1000000);
});

test('the administrative Atlas reconciles the published national income and keeps its municipal sources distinct',()=>{
  const t=table(53689),q=query(t,'national:ES','2024');
  const indicator=t.dimensions.findIndex(d=>d.name==='Indicador');q.dims[indicator]=t.dimensions[indicator].values.indexOf('Renta neta media por persona');
  const result=queryCube(t,cube(t),q);assert.equal(result.series.find(s=>s.period===q.period).value,15948);
  assert.match(unitFor(t,q.dims),/euro/i);assert.equal(t.sourceTables.length,54);
  const mq=query(t,'municipal:28079','2024');mq.dims=[...q.dims];const local=queryCube(t,cube(t,'28'),mq);
  assert.ok(local.series.some(s=>s.value>0));assert.ok(local.series.every(s=>s.sourceTableId));
  const csv=seriesCsv(t,mq,local.series);assert.ok(csv.includes('28079'));assert.ok(csv.includes('https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/'+local.series[0].sourceTableId));
  assert.equal(t.territories[mq.territory].publicationTableId,31097);assert.ok(t.territories.some(a=>a.level==='district'));assert.ok(t.territories.some(a=>a.level==='section'));
});

test('survey income retains its reference year, differs from administrative income and reproduces official AROPE',()=>{
  const t=table(49145),q=query(t,'national:ES','2025');
  const dimension=t.dimensions.findIndex(d=>d.values.includes('Renta neta media por persona'));q.dims[dimension]=t.dimensions[dimension].values.indexOf('Renta neta media por persona');
  assert.equal(queryCube(t,cube(t),q).series.find(r=>r.period===q.period).value,15620);
  assert.match(t.periods[q.period].label,/2025.*2024/);assert.notEqual(15620,15948);
  const a=table(76847),aq=query(a,'national:ES','2025'),i=a.dimensions.findIndex(d=>d.values.some(v=>v.includes('indicador AROPE')));
  aq.dims[i]=a.dimensions[i].values.findIndex(v=>v.includes('indicador AROPE'));
  assert.equal(queryCube(a,cube(a),aq).series.find(r=>r.period===aq.period).value,25.7);
  assert.notEqual(table(10011).id,a.id,'The old and new AROPE definitions must remain distinct');
});

test('units follow the selected metric and data type rather than a whole-table euro label',()=>{
  const t=table(73990);assert.ok(t.unitsByConditions.length);
  const kinds=new Set(t.unitsByConditions.map(r=>r.unit));assert.ok(kinds.size>1);
  for(const rule of t.unitsByConditions){const dims=defaultDimensions(t);for(const [name,value] of Object.entries(rule.when)){const i=t.dimensions.findIndex(d=>d.name===name);dims[i]=t.dimensions[i].values.indexOf(value);}assert.equal(unitFor(t,dims),rule.unit);}
  const g=table(53688);assert.ok(g.dimensions.some(d=>d.values.some(v=>v.includes('P80/P20'))));
  const s=table(76846);assert.ok(s.dimensions.some(d=>d.values.some(v=>v.includes('S80/S20'))));
});

test('streaming JSON decoding survives chunk boundaries, UTF-8 and legacy encodings; conflicting unit signatures fail',()=>{
  const code=`import sys,gzip,json,tempfile
from pathlib import Path
sys.path.insert(0,'scripts')
from welfare_collect import iter_series,infer_units
with tempfile.TemporaryDirectory(prefix='pais-f03-test-') as tmp:
 p=Path(tmp)/'utf.gz';data=[{'name':'España '+('ñ'*70000),'Data':[0,None,-2]},{'name':'segundo'}]
 p.write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False).encode('utf-8')));assert list(iter_series(p))==data
 p=Path(tmp)/'legacy.gz';p.write_bytes(gzip.compress(json.dumps([{'name':'Álava'}],ensure_ascii=False).encode('cp1252')));assert list(iter_series(p))[0]['name']=='Álava'
 unit,rules=infer_units([(('Hombres','media'),'euros'),(('Mujeres','media'),'euros'),(('Hombres','tasa'),'%'),(('Mujeres','tasa'),'%')],['Sexo','Indicador']);assert all('Sexo' not in r['when'] for r in rules)
 try:infer_units([(('media',),'euros'),(('media',),'%')],['Indicador']);raise RuntimeError('Conflict accepted')
 except AssertionError:pass
`;
  const run=spawnSync('python',['-c',code],{cwd:base,encoding:'utf8'});assert.equal(run.status,0,run.stderr);
});


test('historical charts use elapsed time rather than equally spacing sparse survey years',()=>{
  assert.equal(periodTimestamp('2024M01'),periodTimestamp('2024-01-01'));assert.equal(periodTimestamp('2024T2'),periodTimestamp('2024-04-01'));
  const a=periodTimestamp('2013'),b=periodTimestamp('2018'),c=periodTimestamp('2022');assert.ok((b-a)/(c-b)>1.24&&(b-a)/(c-b)<1.26);
});
