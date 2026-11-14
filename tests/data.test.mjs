import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {valueFor, normalize, safeUrl} from '../src/data.ts';
const read = file => JSON.parse(fs.readFileSync(new URL('../datos/'+file,import.meta.url),'utf8'));
const population=read('poblacion/population.json'), provinces=read('territorio/provinces.geojson'), communities=read('territorio/communities.geojson');

test('every INE territorial code joins to the IGN geometry, including islands and autonomous cities',()=>{
  for(const [level,geo,count] of [['province',provinces,52],['community',communities,19]]){
    const codes=Object.keys(population.data[level]).filter(c=>c!=='00');
    assert.equal(codes.length,count);
    const ids=new Set(geo.features.map(f=>f.properties.code));
    assert.equal(ids.size,geo.features.length);
    for(const code of codes)assert.ok(ids.has(code),level+' '+code);
    for(const f of geo.features){assert.ok(f.properties.areaKm2>0);assert.equal(f.id,f.properties.code);}
  }
  for(const code of ['07','35','38','51','52'])assert.ok(provinces.features.some(f=>f.properties.code===code));
});
test('downloaded sex totals and territorial totals reconcile for every published year',()=>{
  for(const level of ['province','community']){
    const territories=population.data[level];
    for(const [year,national] of Object.entries(territories['00'].series)){
      let sum=0;
      for(const [code,t] of Object.entries(territories)){
        const row=t.series[year];
        assert.equal(row['1']+row['2'],row['0'],`${level} ${code} ${year}`);
        if(code!=='00')sum+=row['0'];
      }
      assert.equal(sum,national['0'],`${level} national ${year}`);
    }
  }
  assert.equal(population.data.province['00'].series['2021']['0'],47385107);
});
test('missing years remain missing; derived percentages do not invent data or infinities',()=>{
  const madrid=population.data.province['28'];
  assert.equal(valueFor(madrid,1997,'population',1),null);
  assert.equal(valueFor(undefined,2021,'density',1),null);
  assert.equal(valueFor(madrid,2021,'density',0),null);
  assert.equal(valueFor(madrid,1996,'change',1),0);
  assert.ok(valueFor(madrid,2021,'women',1)>50);
  assert.equal(valueFor({name:'Missing',series:{2021:{0:100}}},2021,'women',1),null);
  assert.equal(Object.keys(madrid.series).length,25);
});
test('geometries have closed rings, valid axis order and plausible Spain extent',()=>{
  for(const geo of [provinces,communities])for(const f of geo.features)for(const poly of f.geometry.coordinates)for(const ring of poly){
    assert.ok(ring.length>=4);assert.deepEqual(ring[0],ring.at(-1));
    for(const [lng,lat] of ring){assert.ok(lng>=-19&&lng<=5);assert.ok(lat>=27&&lat<=45);}
  }
  const madrid=provinces.features.find(f=>f.properties.code==='28');
  assert.ok(madrid.properties.areaKm2>7900&&madrid.properties.areaKm2<8100);
  const mask=read('territorio/contexto/context-mask.geojson');assert.equal(mask.geometry.type,'MultiPolygon');assert.ok(mask.geometry.coordinates[0].length>1);
});
test('INE catalog is complete for the current retrieval and contains real table metadata',()=>{
  const c=read('catalogo/investigacion/ine-catalog.json');assert.equal(c.errors.length,0);assert.ok(c.operations.length>=160);
  assert.ok(new Set(c.operations.flatMap(o=>o.tables.map(t=>t.Id))).size>=6900);
  for(const o of c.operations){assert.ok(o.Nombre);assert.equal(new Set(o.tables.map(t=>t.Id)).size,o.tables.length);}
  assert.ok(c.operations.some(o=>o.tables.some(t=>t.Id===2852)));
  const provenance=read('catalogo/provenance.json');assert.ok(provenance.length>166);assert.ok(provenance.every(p=>p.sha256.length===64&&p.url.startsWith('https://')));
});
test('search accents and original-source links are handled safely',()=>{
  assert.equal(normalize('Ávila'),normalize('avila'));
  assert.equal(safeUrl('javascript:alert(1)','https://www.ine.es'),'https://www.ine.es');
  assert.equal(safeUrl('/datosabiertos/','https://www.ine.es'),'https://www.ine.es/datosabiertos/');
});
