import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {municipalCode,coordinatesExtent,validSpanishCoordinate} from '../src/territory-data.ts';
import {territoryLayers,sectionEditions,orthophotoEditions,canaryEditions,sectionVectorUrl,wmsTile} from '../src/territory-config.ts';
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

test('additional official layers preserve exact verified map endpoints',()=>{
  const checked=read('public/data/territory/official-wms.json').services;
  const available=read('public/data/territory/official-layers.json').layers;
  const verified=checked.flatMap(service=>service.layers.filter(layer=>layer.mapError===null).map(layer=>[service,layer]));
  assert.equal(available.length,verified.length);
  assert.equal(new Set(available.map(layer=>layer.id)).size,available.length);
  const byProvider=new Map(available.map(layer=>[layer.provider.url+'|'+layer.provider.layers,layer.provider]));
  for(const [service,layer] of verified){
    const provider=byProvider.get(service.url+'|'+layer.name);
    assert.ok(provider);
    const tile=new URL(wmsTile(provider));
    assert.equal(tile.searchParams.get('BBOX')||tile.searchParams.get('bbox'),'{bbox-epsg-3857}');
    if(provider.tileEndpoint)assert.equal(tile.searchParams.get('layers'),'show:'+layer.name);
    else{
      assert.equal(tile.searchParams.get('LAYERS'),layer.name);
      assert.equal(tile.searchParams.get(provider.version==='1.1.1'?'SRS':'CRS'),layer.requestCrs||'EPSG:3857');
    }
  }
});

test('municipal layers and local census archives preserve all official polygons',()=>{
  for(const {file,count,id,sha256,geometry,missingFile,missingCount} of [...read('registry/local-territory.json').products,...read('registry/section-archives.json').products]){
    const raw=fs.readFileSync(new URL('../public/data/territory/'+file,import.meta.url));
    if(sha256)assert.equal(createHash('sha256').update(raw).digest('hex'),sha256,id);
    const {features}=JSON.parse(file.endsWith('.gz')?gunzipSync(raw):raw);
    assert.equal(features.length,count,id);
    assert.equal(new Set(features.map(feature=>feature.id)).size,count,id);
    for(const feature of features){
      assert.ok((geometry==='point'?['Point']:['Polygon','MultiPolygon']).includes(feature.geometry.type),id);
      assert.ok(feature.properties.atlasName,id);
    }
    if(missingFile){
      const missing=read('public/data/territory/'+missingFile);
      assert.equal(missing.length,missingCount);
      assert.ok(missing.every(row=>!row.LAT_ETRS89||!row.LON_ETRS89||Number(row.LAT_ETRS89)===0));
    }
  }
  const section=sectionEditions.find(edition=>edition.id==='2025');
  const params=new URL(sectionVectorUrl(section.layer,'2807901001')).searchParams;
  assert.equal(params.get('TYPENAMES'),section.layer);
  assert.equal(params.get('CQL_FILTER'),"CUSEC='2807901001'");
  assert.throws(()=>sectionVectorUrl(section.layer,'2807901001 OR 1=1'));
});

test('both CNIG editions expose every line and polygon table from their GeoPackages',()=>{
  const {products,provenance}=read('registry/cnig-history.json');
  const {inventory}=read('registry/territory-products.json');
  assert.deepEqual(provenance.map(source=>source.year),[2023,2024]);
  assert.equal(products.length,28);
  assert.equal(new Set(products.map(product=>product.id)).size,28);
  for(const [year,count] of [[2023,63626],[2024,64647]]){
    const edition=products.filter(product=>product.period===year+'-01-01');
    assert.equal(edition.length,14);
    assert.equal(new Set(edition.map(product=>product.layer)).size,14);
    assert.equal(edition.reduce((sum,product)=>sum+product.count,0),count);
  }
  for(const {file,count,id,sha256,geometry,layer,period} of products){
    const raw=fs.readFileSync(new URL('../public/data/territory/'+file,import.meta.url));
    assert.equal(createHash('sha256').update(raw).digest('hex'),sha256,id);
    const {features}=JSON.parse(gunzipSync(raw));
    assert.equal(features.length,count,id);
    assert.equal(new Set(features.map(feature=>feature.id)).size,count,id);
    const types=geometry==='line'?['LineString','MultiLineString']:['Polygon','MultiPolygon'];
    for(const feature of features){
      assert.ok(types.includes(feature.geometry.type),id);
      assert.equal(feature.id,feature.properties.fid,id);
      assert.equal(feature.id,feature.properties.atlasId,id);
      assert.ok('INSPIREID' in feature.properties,id);
      assert.ok(feature.properties.atlasName,id);
      if(layer.includes('_histo_'))assert.ok('DATE_HISTO' in feature.properties,id);
    }
    const entry=inventory.find(row=>row.mapAction==='territory:'+id);
    assert.equal(entry?.status,'integrado',id);
    assert.equal(entry?.fields['Tabla GeoPackage'],layer,id);
    assert.equal(entry?.period,period,id);
  }
});
