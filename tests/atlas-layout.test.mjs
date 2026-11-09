import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {toAtlas,fromAtlas,projectFeature,CANARY_DISPLAY} from '../src/atlas-coordinates.ts';
const read=p=>JSON.parse(fs.readFileSync(new URL('../public/data/territory/'+p,import.meta.url),'utf8'));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);

test('Canary atlas coordinates are reversible and leave mainland, islands and cities elsewhere unchanged',()=>{
  for(const p of [[-16.3,28.5],[-17.9,27.7],[-13.5,29.2]]){
    const displayed=toAtlas(p),original=fromAtlas(displayed);
    assert.ok(displayed[0]<-10&&displayed[0]>-16);assert.ok(displayed[1]>37&&displayed[1]<40);
    close(original[0],p[0]);close(original[1],p[1]);
  }
  for(const p of [[-3.7,40.4],[2.6,39.6],[-5.3,35.9],[-2.94,35.29]])assert.deepEqual(toAtlas(p),p);
});

test('display projection does not mutate canonical geometry, identifiers or statistical properties',()=>{
  const original={type:'Feature',id:'38',properties:{code:'38',areaKm2:2034.1},geometry:{type:'Polygon',coordinates:[[[-16.4,28.3],[-16.3,28.3],[-16.3,28.4],[-16.4,28.3]]]}};
  const before=JSON.stringify(original),display=projectFeature(original);
  assert.equal(JSON.stringify(original),before);assert.equal(display.id,original.id);assert.deepEqual(display.properties,original.properties);
  assert.notDeepEqual(display.geometry,original.geometry);assert.deepEqual(display.geometry.coordinates[0][0],display.geometry.coordinates[0].at(-1));
});

function ringInside([x,y],ring){let b=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [a,c]=ring[i],[d,e]=ring[j];if((c>y)!==(e>y)&&x<(d-a)*(y-c)/(e-c)+a)b=!b;}return b;}
function inside(p,f){return f.geometry.coordinates.some(poly=>ringInside(p,poly[0])&&!poly.slice(1).some(r=>ringInside(p,r)));}
test('the rendered coast and sea follow the displaced islands while canonical geography stays intact',()=>{
  const geographic=read('country.geojson'),displayed=read('country-atlas.geojson'),sea=read('sea-atlas.geojson');
  const tenerife=[-16.6,28.3],moved=toAtlas(tenerife);
  assert.ok(inside(tenerife,geographic));assert.ok(!inside(moved,geographic));
  assert.ok(inside(moved,displayed));assert.ok(!inside(tenerife,displayed));
  assert.ok(!inside(moved,sea));assert.ok(inside(tenerife,sea));
  assert.ok(inside([-3.7,40.4],displayed));assert.ok(CANARY_DISPLAY[2]<-10);
});
