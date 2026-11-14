import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {toAtlas,fromAtlas,projectFeature,CANARY_DISPLAY,ATLAS_REGIONS,ATLAS_FRAMES,WORLD,mercY,vectorTileAddress} from '../src/atlas-coordinates.ts';
const read=p=>JSON.parse(fs.readFileSync(new URL('../datos/territorio/'+p,import.meta.url),'utf8'));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);

test('all atlas frames preserve real coordinates and leave mainland and Balearic coordinates unchanged',()=>{
  for(const p of [[-16.3,28.5],[-17.9,27.7],[-13.5,29.2]]){
    const displayed=toAtlas(p),original=fromAtlas(displayed);
    assert.ok(displayed[0]<-10&&displayed[0]>-16);assert.ok(displayed[1]>41&&displayed[1]<44);
    close(original[0],p[0]);close(original[1],p[1]);
  }
  for(const p of [[-3.7,40.4],[2.6,39.6]])assert.deepEqual(toAtlas(p),p);
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


test('all seven affine transforms are invertible, disjoint and contained by their four map frames',()=>{
  assert.equal(ATLAS_FRAMES.length,4);
  for(const r of ATLAS_REGIONS){
    const p=[(r.original[0]+r.original[2])/2,(r.original[1]+r.original[3])/2],d=toAtlas(p),back=fromAtlas(d);
    close(back[0],p[0]);close(back[1],p[1]);
    const f=ATLAS_FRAMES.find(f=>f.id===r.id)||ATLAS_FRAMES.at(-1);
    assert.ok(r.display[0]>=f.bounds[0]&&r.display[1]>=f.bounds[1]&&r.display[2]<=f.bounds[2]&&r.display[3]<=f.bounds[3],r.id);
    for(const other of ATLAS_REGIONS)if(other!==r)assert.ok(r.display[0]>=other.display[2]||r.display[2]<=other.display[0]||r.display[1]>=other.display[3]||r.display[3]<=other.display[1]);
  }
});

test('one opaque sea mask removes foreign land and original copies while preserving every displayed territory',()=>{
  const displayed=read('country-atlas.geojson'),sea=read('sea-atlas.geojson');
  const samples=[[-16.6,28.3],[-5.31,35.89],[-2.95,35.29],[-4.299,35.172],[-3.9008355518,35.2175730805],[-2.43,35.181],[-3.034,35.94],[-3.7,40.4],[2.7,39.6]];
  for(const p of samples){const d=toAtlas(p);assert.ok(inside(d,displayed),'Missing displayed land '+p);assert.ok(!inside(d,sea),'Masked displayed land '+p);}
  for(const p of [[-9.14,38.72],[2.35,48.86],[-5.8,35.76],[-16.9,32.65],[-5.35,36.14],[-1.765,43.343],[-5.42,35.914],[-5.31,35.89],[-2.95,35.29]])assert.ok(inside(p,sea),'Foreign or relocated original remains visible '+p);
});

test('vector tile addressing matches affine geometry exactly at the minimum supported zoom',()=>{
  for(const r of ATLAS_REGIONS){const z=r.vectorMinzoom,x=400,y=400,s=WORLD/2**z,t=vectorTileAddress(r,z,x,y),ss=WORLD/2**t.z;
    assert.ok(Math.abs((t.x*ss-WORLD/2)*r.scale+r.dx-(x*s-WORLD/2))<1e-5);
    assert.ok(Math.abs((WORLD/2-t.y*ss)*r.scale+r.dy-(WORLD/2-y*s))<1e-5);
  }
});
