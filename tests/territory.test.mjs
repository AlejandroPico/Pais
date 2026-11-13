import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {municipalCode,coordinatesExtent,validSpanishCoordinate} from '../src/territory-data.ts';
import {territoryLayers,sectionEditions,orthophotoEditions,canaryEditions,wmsTile} from '../src/territory-config.ts';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const index=read('public/data/territory/index.json'),manifest=read('public/data/territory/manifest.json');

test('every INE municipality joins to an IGN geometry and a real provincial and regional parent',()=>{
  const provinces=read('public/data/provinces.geojson').features,communities=read('public/data/communities.geojson').features;
  const codes=new Set(index.municipalities.map(m=>m.code));
  assert.equal(codes.size,index.municipalities.length);assert.equal(codes.size,8132);assert.equal(codes.size,manifest.municipalCount);
  assert.equal(index.missingGeometryCodes.length,0);
  for(const m of index.municipalities){
    assert.match(m.code,/^\d{5}$/);assert.ok(m.name);assert.equal(m.code.slice(0,2),m.provinceCode);assert.ok(Number.isInteger(m.ignFeatureId));
    const province=provinces.find(f=>f.properties.code===m.provinceCode);assert.ok(province,m.code);assert.equal(province.properties.communityCode,m.communityCode);
    assert.ok(communities.some(f=>f.properties.code===m.communityCode),m.code);
    if(['07','35','38'].includes(m.provinceCode))assert.ok(index.islands.some(i=>i.id===m.islandId),m.code);
  }
  for(const area of index.supplementalAreas){assert.ok(!codes.has(area.code));assert.ok(area.classification.includes('sin correspondencia'));}
  for(const code of ['28005','08019','35016','38038','51001','52001'])assert.ok(codes.has(code),code);
});

test('all imported comarca geometries retain their regional type, code, source and closed rings',()=>{
  const features=read('public/data/territory/comarcas.geojson').features;
  assert.ok(features.length>=190);assert.equal(new Set(features.map(f=>f.id)).size,features.length);
  for(const region of manifest.comarcaCoverage.filter(c=>c.status==='integrado'))assert.equal(features.filter(f=>f.properties.sourceId===region.sourceId).length,region.count,region.territory);
  assert.ok(features.some(f=>f.properties.name==='Lluçanès'));
  assert.ok(features.some(f=>f.properties.name.includes('Aran')&&f.properties.kind==='Entidad territorial singular'));
  for(const f of features){
    assert.ok(f.properties.kind);assert.ok(f.properties.sourceUrl.startsWith('https://'));assert.match(f.properties.snapshot,/^2026-11-(09|13)$/);
    for(const polygon of f.geometry.coordinates)for(const ring of polygon){assert.ok(ring.length>=4);assert.deepEqual(ring[0],ring.at(-1));for(const [x,y] of ring){assert.ok(x>=-10&&x<=5);assert.ok(y>=35&&y<=44);}}
  }
});

test('census editions and cadastral providers correspond to advertised official layers and formats',()=>{
  const census=manifest.services.find(s=>s.id==='ine-wms');assert.equal(sectionEditions.length,22);
  assert.equal(new Set(sectionEditions.map(e=>e.id)).size,22);
  for(const edition of sectionEditions)assert.ok(census.layers.some(l=>l.name===edition.layer));
  for(const layer of territoryLayers)for(const provider of layer.providers||[]){
    const service=manifest.services.find(s=>s.url===provider.url);assert.ok(service,provider.id);assert.equal(service.status,'verificado');
    for(const name of provider.layers.split(','))assert.ok(service.layers.some(l=>l.name===name),name);
    if(provider.queryable)assert.ok(service.infoFormats.includes(provider.infoFormat));
    const tile=wmsTile(provider,{TIME:'2016-01-01T23:00:00Z'});const params=new URL(tile).searchParams;
    assert.equal(params.get('CRS'),'EPSG:3857');assert.equal(params.get('LAYERS'),provider.layers);assert.equal(params.get('TIME'),'2016-01-01T23:00:00Z');assert.equal(params.get('BBOX'),'{bbox-epsg-3857}');
  }
  const parcels=territoryLayers.find(l=>l.id==='parcels');assert.deepEqual(new Set(parcels.providers.map(p=>p.sourceId)),new Set(['F008','F165','F177','F178','F179']));
});

test('large real-world geometries can be fitted without spreading coordinates onto the call stack',()=>{
  const coordinates=Array.from({length:150000},(_,i)=>[-8+i/100000,38+i/150000]);
  const extent=coordinatesExtent({type:'LineString',coordinates});
  assert.deepEqual(extent[0],[-8,38]);assert.deepEqual(extent[1],coordinates.at(-1));
  assert.equal(municipalCode('34010404001'),'04001');assert.equal(municipalCode('28005'),'28005');assert.equal(municipalCode('ES300'),null);
  assert.equal(validSpanishCoordinate(0,0),false);assert.equal(validSpanishCoordinate(-16.3,28.5),true);assert.equal(validSpanishCoordinate(NaN,40),false);assert.equal(validSpanishCoordinate(-3.7,40.4),true);
});

test('orthophoto and Canary selectors use all relevant advertised WMS editions',()=>{
  const orthophoto=manifest.services.find(s=>s.id==='pnoa-historico').layers;
  const canary=manifest.services.find(s=>s.id==='comarca-canarias').layers;
  assert.deepEqual(orthophotoEditions.map(e=>e.id),orthophoto.map(layer=>layer.name));
  assert.deepEqual(canaryEditions.map(e=>e.id),canary.filter(layer=>!['WMS_CARTO_EST','ALJTUR2015','CME1','CME2'].includes(layer.name)).map(layer=>layer.name));
  const bierzo=read('public/data/territory/bierzo-boundaries.json');
  assert.equal(new Set(bierzo.boundaries.map(row=>row.code)).size,38);
});
