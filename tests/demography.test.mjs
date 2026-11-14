import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {defaultDimensions,queryCube,periodOrder,seriesCsv,unitFor,relativeChange} from '../src/demography-data.ts';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const index=read('datos/poblacion/ine/index.json');
const table=id=>index.tables.find(t=>t.id===id);
const cube=(t,part='main')=>JSON.parse(gunzipSync(fs.readFileSync(new URL('datos/poblacion/ine/'+t.shards.find(s=>s.id===part).file,root))));
const digest=b=>createHash('sha256').update(b).digest('hex');

test('every complete demographic table preserves its shard counts, hashes, dictionaries and all observations',()=>{
  const config=read('registry/demography-tables.json');
  assert.deepEqual(index.tables.map(table=>table.id),config.tables.map(table=>table.id));
  assert.equal(new Set(index.tables.map(table=>table.id)).size,index.tables.length);
  let total=0;
  for(const t of index.tables){
    assert.equal(new Set(t.territories.map(a=>a.id)).size,t.territories.length);
    assert.ok(t.periods.every(p=>p.id&&p.label));let count=0;
    for(const shard of t.shards){
      const bytes=fs.readFileSync(new URL('datos/poblacion/ine/'+shard.file,root)),content=gunzipSync(bytes);
      assert.equal(digest(bytes),shard.sha256);assert.equal(digest(content),shard.contentSha256);assert.equal(bytes.length,shard.bytes);
      const rows=JSON.parse(content).rows;assert.equal(rows.length,shard.rows);count+=rows.length;
      for(const r of rows){
        assert.equal(r.length,t.dimensions.length+4);assert.ok(t.territories[r[0]]);assert.ok(t.periods[r[1]]);
        for(let i=0;i<t.dimensions.length;i++)assert.ok(r[i+2]>=0&&r[i+2]<t.dimensions[i].values.length);
        assert.ok(r.at(-2)===null||Number.isFinite(r.at(-2)));assert.equal(typeof r.at(-1),'string');
        if(r.at(-2)===null)assert.ok(r.at(-1));
        if(shard.id!=='main')assert.equal(t.territories[r[0]].provinceCode,shard.id);
      }
    }
    assert.equal(count,t.rows);total+=count;
    for(const a of t.territories)if(a.level==='unlocated')assert.equal(a.name,'No residente','Unresolved official geography: '+t.id);
  }
  assert.equal(total,68090658);
});

test('census filters conserve source totals, sex and nationality; chart and map use the same query',()=>{
  const t=table(68519),c=cube(t),period=t.periods.findIndex(p=>p.id==='2025'),dims=defaultDimensions(t);
  const q={period,dims,level:'national',territory:t.territories.findIndex(a=>a.id==='national:ES')};
  const result=queryCube(t,c,q);assert.equal(result.values[0].value,49128297);
  assert.equal(result.series.length,5);assert.equal(result.pyramid.length,101);
  const sex=t.dimensions.findIndex(d=>d.name==='Sexo'),nationality=t.dimensions.findIndex(d=>d.name==='Nacionalidad');
  const get=(i,v)=>{const selected=[...dims];selected[i]=t.dimensions[i].values.indexOf(v);return queryCube(t,c,{...q,dims:selected}).values[0].value;};
  assert.equal(get(sex,'Hombres')+get(sex,'Mujeres'),49128297);
  assert.equal(get(nationality,'Española')+get(nationality,'Extranjera'),49128297);
  assert.equal(result.pyramid.reduce((s,r)=>s+r.men+r.women,0),49128297);
  const provinceQuery={...q,level:'province'};
  assert.equal(queryCube(t,c,provinceQuery).values.reduce((s,r)=>s+r.value,0),49128297);
  assert.deepEqual(queryCube(t,c,provinceQuery).domain,queryCube(t,c,{...provinceQuery,period:4}).domain,'The scale must stay fixed across the timeline');
});

test('municipal census has all 8132 current INE municipalities and queries Canary provinces with real codes',()=>{
  const t=table(68535),indexTerritory=read('datos/territorio/index.json');
  assert.deepEqual(new Set(t.territories.filter(a=>a.level==='municipal').map(a=>a.code)),new Set(indexTerritory.municipalities.map(a=>a.code)));
  const q={period:t.periods.findIndex(p=>p.id==='2025'),dims:defaultDimensions(t),level:'municipal',territory:t.territories.findIndex(a=>a.id==='municipal:38038')};
  const result=queryCube(t,cube(t,'38'),q);assert.ok(result.values.every(v=>t.territories[v.area].provinceCode==='38'));
  assert.equal(result.pyramid.length,21);assert.equal(result.series.length,5);assert.ok(result.series.every(x=>x.value>0));
});

test('missing, suppressed and zero values stay distinct; negative migration balances survive export',()=>{
  const t=table(69767),c=cube(t,'28'),q={period:0,dims:defaultDimensions(t),level:'municipal',territory:0};
  const negative=queryCube(t,c,q).values.find(v=>v.value<0);assert.ok(negative);
  const r=queryCube(t,c,{...q,territory:negative.area}),csv=seriesCsv(t,{...q,territory:negative.area},r.series);
  assert.ok(csv.includes('saldo de movimientos'));assert.ok(csv.includes(String(negative.value)));
  const tiny={...table(6528),dimensions:[],territories:[{id:'province:28',code:'28',name:'Una "prueba"; territorial',level:'province'}],periods:[{id:'2020',label:'2020'},{id:'2021',label:'2021'},{id:'2022',label:'2022'}]};
  const rows={rows:[[0,0,0,''],[0,1,null,'..'],[0,2,-2,'']]},selection={period:1,dims:[],level:'province',territory:0};
  const result=queryCube(tiny,rows,selection);assert.equal(result.values[0].value,null);assert.equal(result.series[0].value,0);assert.equal(result.series[1].status,'..');
  assert.ok(seriesCsv(tiny,selection,result.series).includes('Una ""prueba""; territorial'));
});

test('projected mean household size has its own unit and Spanish INE numbers and reference dates parse exactly',()=>{
  const t=table(54562),dims=defaultDimensions(t);assert.equal(unitFor(t,dims),'hogares proyectados');
  dims[0]=t.dimensions[0].values.indexOf('Tamaño medio');assert.equal(unitFor(t,dims),'personas por hogar proyectadas');
  assert.equal(t.periods[periodOrder(t).at(-1)].id,'2041');
  const code="import sys;sys.path.insert(0,'scripts');from demography_collect import number,period_key;assert number('1.234')==1234;assert number('-2,49')==-2.49;assert number('0')==0;assert number('..') is None;assert period_key('1 de julio de 2026')=='2026-07-01';assert period_key('2024M12')=='2024M12'";
  const run=spawnSync('python',['-c',code],{cwd:new URL('../',import.meta.url),encoding:'utf8'});assert.equal(run.status,0,run.stderr);
});

test('population change retains direction and never invents percentages from a zero or missing baseline',()=>{
  assert.equal(relativeChange(80,100),-19.999999999999996);
  assert.equal(relativeChange(0,100),-100);
  assert.equal(relativeChange(120,0),null);assert.equal(relativeChange(120,undefined),null);assert.equal(relativeChange(null,100),null);
});

test('section 2807901001 returns the official Madrid census value and annual series',()=>{
  const t=table(65031),c=cube(t,'28');
  const territory=t.territories.findIndex(a=>a.id==='section:2807901001');
  assert.equal(t.territories[territory].municipalityCode,'28079');
  const query={period:t.periods.findIndex(p=>p.id==='2025'),dims:defaultDimensions(t),level:'section',territory};
  const result=queryCube(t,c,query);
  assert.equal(result.series.length,5);
  assert.equal(result.values.find(row=>row.area===territory).value,1192);
});

test('municipal census histories preserve all declared records, including dissolved municipalities',()=>{
  const historical=read('datos/poblacion/intercensal/index.json');
  assert.equal(Object.keys(historical.provinces).length,52);
  let total=0;
  for(const part of Object.values(historical.provinces)){
    const bytes=fs.readFileSync(new URL('datos/poblacion/intercensal/'+part.file,root));
    assert.equal(digest(bytes),part.sha256);
    const {entries}=JSON.parse(bytes);
    assert.equal(entries.length,part.count);
    for(const entry of entries){
      const [heading,,years,...lines]=entry.split('\n').filter(line=>line.trim());
      assert.match(heading,/^Provincia: /);
      assert.match(years,/^;(18|19|20)\d{2}/);
      assert.ok(lines.slice(0,3).every(line=>line.split(';').length===years.split(';').length),heading);
    }
    total+=entries.length;
  }
  assert.equal(total,11977);
});
