import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {matchesProduct} from '../src/registry.ts';
import {territoryLayers} from '../src/territory-config.ts';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const index=read('public/data/registry/index.json');
const products=Object.fromEntries(Object.entries(index.files).map(([kind,f])=>[kind,JSON.parse(gunzipSync(fs.readFileSync(new URL('public/data/registry/'+f.file,root))))]));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');

test('registry inventories retain counts, unique identifiers, references and byte integrity',()=>{
  const sources=new Set(index.sources.map(s=>s.id)),categories=new Set(index.categories.map(c=>c.id));
  assert.equal(sources.size,index.sources.length);assert.equal(categories.size,29);
  assert.equal(index.sources.filter(s=>s.kind==='research').length,182);
  assert.equal(index.sources.filter(s=>s.kind==='publisher').length,238);
  const national=read('docs/research/publicadores-catalogo-nacional.json');
  assert.equal(products.national.length,national.datasetCount);
  assert.equal(products.ioe.length,read('docs/research/operaciones-ioe-detalladas.json').operations.length);
  const ine=read('public/data/ine-catalog.json');
  assert.equal(products.ine.length,new Set(ine.operations.flatMap(o=>o.tables.map(t=>t.Id))).size);
  for(const [kind,rows] of Object.entries(products)){
    const descriptor=index.files[kind],bytes=fs.readFileSync(new URL('public/data/registry/'+descriptor.file,root));
    assert.equal(bytes.length,descriptor.bytes);assert.equal(sha(bytes),descriptor.sha256);assert.equal(sha(gunzipSync(bytes)),descriptor.contentSha256);
    assert.equal(rows.length,descriptor.count);assert.equal(new Set(rows.map(r=>r.id)).size,rows.length);
    for(const r of rows){
      assert.ok(sources.has(r.sourceId),r.id);assert.ok(index.statusLabels[r.status],r.id);
      for(const c of [...r.categoryIds,...r.suggestedCategoryIds||[]])assert.ok(categories.has(c),r.id+' '+c);
      if(r.status==='integrado')assert.ok(kind==='available'||r.review?.implementedProductId);
    }
  }
  for(const input of index.provenance)assert.equal(sha(fs.readFileSync(new URL(input.path,root))),input.sha256,'Stale registry: '+input.path);
});

test('available products link to real map actions and preserved observations; discovery is separate',()=>{
  const actions=new Set(['base:satellite','base:terrain','base:street','terrain','communities','provinces','metric:population','metric:density','metric:women','metric:change','overlay:municipal','overlay:rivers','overlay:rail','overlay:roads','overlay:camino']);
  for(const layer of territoryLayers)actions.add('territory:'+layer.id);
  actions.add('search:addresses');
  const expected=read('registry/products.json').products.length+read('registry/territory-products.json').available.length+read('registry/demography-products.json').available.length+read('registry/welfare-products.json').available.length+read('registry/labor-products.json').available.length;
  for(const file of ['registry/demography-products.json','registry/welfare-products.json','registry/labor-products.json'])for(const p of read(file).available)actions.add(p.mapAction);
  assert.equal(products.available.length,expected);
  for(const p of products.available){assert.equal(p.status,'integrado');assert.ok(actions.has(p.mapAction));assert.ok(p.license);if(p.dataFile)assert.ok(fs.existsSync(new URL('public/data/'+p.dataFile,root)));}
  for(const p of [...products.ioe,...products.national,...products.ine])if(!p.review){assert.equal(p.status,'por_revisar');assert.equal(p.categoryIds.length,0);assert.equal(p.license,null);}
  assert.equal(products.ioe.find(p=>p.id==='ioe:01005').fields['Nivel de desagregación'],'Provincial');
  assert.ok(products.ioe.find(p=>p.id==='ioe:01005').responsible.includes('Agricultura'));
  assert.ok(products.ine.find(p=>p.id==='ine:2852').operationIds.length>0);
});

test('catalog search combines accents, multiple terms, source, state and explicit or candidate topics',()=>{
  const p={id:'demo',title:'Población de Ávila',sourceId:'F005',status:'por_revisar',categoryIds:[],suggestedCategoryIds:['F02']};
  const q={kind:'ioe',q:'AVILA poblacion',source:'',status:'',category:'',page:0};
  assert.equal(matchesProduct(p,q),true);
  assert.equal(matchesProduct(p,{...q,category:'F02'}),true);
  assert.equal(matchesProduct(p,{...q,category:'F03'}),false);
  assert.equal(matchesProduct(p,{...q,status:'integrado'}),false);
  assert.equal(matchesProduct(p,{...q,source:'F006'}),false);
  assert.equal(matchesProduct(p,{...q,q:'poblacion inexistente'}),false);
  assert.equal(matchesProduct({...p,suggestedCategoryIds:[]},{...q,category:'F02'}),false);
});

function insideRing([x,y],ring){let inside=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [xi,yi]=ring[i],[xj,yj]=ring[j];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)inside=!inside;}return inside;}
function inside(point,feature){return feature.geometry.coordinates.some(p=>insideRing(point,p[0])&&!p.slice(1).some(r=>insideRing(point,r)));}
test('coastal masks tint foreign land without greying the sea or covering Spanish territory',()=>{
  const sea=read('public/data/sea.geojson'),neighbors=read('public/data/neighbor-land.geojson');
  for(const point of [[-10,40],[0,38],[-18.6,28.3]]){assert.ok(inside(point,sea));assert.ok(!inside(point,neighbors));}
  for(const point of [[-3.7,40.4],[-16.6,28.3],[-5.3069,35.8875],[-2.94,35.29]]){assert.ok(!inside(point,sea),'Spanish point painted blue '+point);assert.ok(!inside(point,neighbors),'Spanish point muted '+point);}
  assert.ok(inside([-9.14,38.72],neighbors));assert.ok(!inside([-9.14,38.72],sea));
});
