import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {matchesProduct} from '../src/registry.ts';
import {territoryLayers} from '../src/territory-config.ts';
import {defaultDimensions,periodTimestamp,queryCube,statisticalParts,unitFor} from '../src/demography-data.ts';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const index=read('datos/catalogo/index.json');
const products=Object.fromEntries(Object.entries(index.files).map(([kind,f])=>[kind,JSON.parse(gunzipSync(fs.readFileSync(new URL('datos/catalogo/'+f.file,root))))]));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');

test('registry inventories retain counts, unique identifiers, references and byte integrity',()=>{
  const sources=new Set(index.sources.map(s=>s.id)),categories=new Set(index.categories.map(c=>c.id));
  assert.equal(sources.size,index.sources.length);assert.equal(categories.size,29);
  assert.equal(index.sources.filter(s=>s.kind==='research').length,183);
  assert.equal(index.sources.filter(s=>s.kind==='publisher').length,238);
  const national=read('datos/catalogo/investigacion/publicadores-catalogo-nacional.json');
  assert.equal(products.national.length,national.datasetCount);
  assert.equal(products.ioe.length,read('datos/catalogo/investigacion/operaciones-ioe-detalladas.json').operations.length);
  const ine=read('datos/catalogo/investigacion/ine-catalog.json');
  assert.equal(products.ine.length,new Set(ine.operations.flatMap(o=>o.tables.map(t=>t.Id))).size);
  for(const [kind,rows] of Object.entries(products)){
    const descriptor=index.files[kind],bytes=fs.readFileSync(new URL('datos/catalogo/'+descriptor.file,root));
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
  actions.add('municipal-changes');
  for(const layer of read('datos/territorio/official-layers.json').layers)actions.add('official-wms:'+layer.id);
  const topicNames=['demography','welfare','labor','care','housing','economy','commerce','fiscal','funding','education','science','health'];
  const topicProducts=topicNames.flatMap(name=>read(`registry/${name}-products.json`).available);
  const expected=read('registry/products.json').products.length+read('registry/territory-products.json').available.length+topicProducts.length;
  for(const p of topicProducts)actions.add(p.mapAction);
  assert.equal(products.available.length,expected);
  for(const p of products.available){assert.equal(p.status,'integrado');assert.ok(actions.has(p.mapAction));assert.ok(p.license);if(p.dataFile)assert.ok(fs.existsSync(new URL('datos/'+p.dataFile,root)));}
  for(const p of [...products.ioe,...products.national,...products.ine])if(!p.review){assert.equal(p.status,'por_revisar');assert.equal(p.categoryIds.length,0);}
  assert.equal(products.ioe.find(p=>p.id==='ioe:01005').fields['Nivel de desagregación'],'Provincial');
  assert.ok(products.ioe.find(p=>p.id==='ioe:01005').responsible.includes('Agricultura'));
  const linked=products.ine.find(p=>p.id==='ine:2852');
  assert.ok(linked.operationIds.length>0);
  assert.equal(linked.mapAction,'demography:2852');
  assert.equal(linked.status,'integrado');
  const nationalPark=products.national.find(p=>p.id.endsWith('/l01281317-parques-y-jardines'));
  assert.ok(nationalPark.suggestedCategoryIds.includes('F15'));
  assert.equal(nationalPark.status,'por_revisar');
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

test('F13 keeps the corrected waiting-list rows, MoMo daily partitions and official center coverage',()=>{
  const table=(folder,id)=>read(`datos/salud/${folder}/index.json`).tables.find(value=>value.id===id);
  const cube=(t,part)=>JSON.parse(gunzipSync(fs.readFileSync(
    new URL(`datos/${t.dataFolder}/${t.shards.find(shard=>shard.id===part).file}`,root))));
  const wait=table('sanidad',130160);
  const territory=wait.territories.findIndex(area=>area.id==='community:08');
  const dims=['Pacientes en espera estructural','Total'].map((label,i)=>wait.dimensions[i].values.indexOf(label));
  const waitValue=queryCube(wait,cube(wait,'main'),{level:'community',period:0,territory,dims}).series[0].value;
  assert.equal(waitValue,36491);
  assert.equal(wait.periods[0].id,'2025-12-31');
  const momo=table('isciii',130200);
  const day=momo.periods.findIndex(period=>period.id==='2026-11-16');
  const national=momo.territories.findIndex(area=>area.level==='national');
  const query={level:'national',period:day,territory:national,dims:defaultDimensions(momo)};
  const [part]=statisticalParts(momo,query,'all');
  const nationalValue=queryCube(momo,cube(momo,part),query).values[0].value;
  assert.equal(part,'main-d0');
  assert.equal(nationalValue,1205.72);
  const [layer]=read('registry/health-geography.json');
  const published=products.available.filter(p=>p.mapAction==='territory:'+layer.id);
  assert.equal(published.length,1);
  assert.deepEqual(published[0].categoryIds,['F13']);
  const features=JSON.parse(gunzipSync(fs.readFileSync(new URL('datos/salud/'+layer.file,root)))).features;
  assert.equal(features.length,5609);
  assert.equal(layer.registered,5680);
  assert.ok(features.every(feature=>feature.properties.Registro&&feature.geometry.type==='Point'));
});

test('F10 preserves published totals, phase units and the FEDER text-formatted territories',()=>{
  const fundingTable=(folder,id)=>read(`datos/ayudas/${folder}/index.json`).tables.find(t=>t.id===id);
  const selectedRow=(table,areaId,periodId,dimensions)=>{
    const geography=table.territories.findIndex(a=>a.id===areaId);
    const period=table.periods.findIndex(p=>p.id===periodId);
    const dims=dimensions.map((v,i)=>table.dimensions[i].values.indexOf(v));
    const shard=table.shards.find(s=>s.id==='main');
    const cube=JSON.parse(gunzipSync(fs.readFileSync(new URL('datos/'+table.dataFolder+'/'+shard.file,root))));
    return cube.rows.find(row=>[geography,period,...dims].every((v,i)=>v===row[i]));
  };
  const awards=fundingTable('bdns',970302);
  assert.equal(selectedRow(awards,'national:ES','2026M10',['Concesiones publicadas','Total','Total'])?.[5],327980);
  const ted=fundingTable('ted',970501);
  assert.equal(selectedRow(ted,'national:ES','2026M10',['Anuncios publicados','Total','Total'])?.[5],5966);
  const contracts=fundingTable('contratos',970001);
  assert.equal(selectedRow(contracts,'community:01','2024',['Contratos registrados','Total'])?.[4],129547);
  assert.equal(selectedRow(contracts,'community:01','2024',['Importe registrado','Total'])?.[4],5395518820);
  assert.equal(contracts.unitsByCategory.values['Peso del procedimiento'],'Porcentaje');
  const feder=fundingTable('feder',970100);
  for(const code of ['18','12']){
    const records=feder.periods.flatMap(({id})=>[selectedRow(feder,'community:'+code,id,['Operaciones con inicio comunicado','Total'])||[]]);
    assert.equal(records.reduce((sum,row)=>sum+(row[4]||0),0),code==='18'?365:9450);
  }
});

test('F11 grids preserve academic courses, territorial axes and the units of expenditure measures',()=>{
  const centers=read('datos/educacion/educabase/index.json').tables.find(table=>
    table.downloadUrl.endsWith('/series/centros/l0/series_01.px'));
  const readGrid=table=>JSON.parse(gunzipSync(fs.readFileSync(new URL(
    'datos/'+table.dataFolder+'/'+table.shards[0].file,root))));
  const country=centers.territories.findIndex(area=>area.id==='national:ES');
  const course=centers.periods.findIndex(entry=>entry.id==='2025M09');
  const centerQuery={territory:country,level:'national',period:course,dims:defaultDimensions(centers)};
  const centerResult=queryCube(centers,readGrid(centers),centerQuery);
  assert.equal(centerResult.values[0].value,28623);
  assert.equal(centerResult.series.length,21);
  assert.ok(centers.periods[course].label.includes('(*)'));
  assert.equal(centers.territories.filter(area=>area.level==='community').length,19);
  const expense=read('datos/educacion/ine/index.json').tables.find(table=>table.downloadUrl.endsWith('/76085.px'));
  const dims=defaultDimensions(expense);
  const indicator=expense.dimensions.findIndex(d=>d.name==='Indicador');
  assert.equal(queryCube(expense,readGrid(expense),{
    territory:0,level:'national',period:0,dims,
  }).values[0].value,27806164);
  dims[indicator]=expense.dimensions[indicator].values.indexOf('Gasto Medio por estudiante');
  assert.equal(unitFor(expense,dims),'Euros');
  assert.equal(queryCube(expense,readGrid(expense),{
    territory:0,level:'national',period:0,dims,
  }).values[0].value,2056);
});

test('F12 preserves distinct patent phases, historical editions and links by grant agreement',()=>{
  const table=(folder,id)=>read(`datos/ciencia/${folder}/index.json`).tables.find(row=>row.id===id);
  const fromDisk=(folder,file)=>JSON.parse(gunzipSync(fs.readFileSync(new URL(`datos/ciencia/${folder}/${file}`,root))));
  const selectedValue=(product,territory,year,measure)=>{
    const area=product.territories.findIndex(row=>row.id===territory);
    const period=product.periods.findIndex(row=>row.id===year);
    const dims=defaultDimensions(product);
    dims[0]=product.dimensions[0].values.indexOf(measure);
    return queryCube(product,fromDisk(product.dataFolder.split('/')[1],product.shards[0].file),{
      territory:area,level:product.territories[area].level,period,dims,
    }).values.find(row=>row.area===area)?.value;
  };
  const patent=table('epo',120250);
  assert.equal(selectedValue(patent,'national:ES','2025','Solicitudes europeas'),2255);
  assert.equal(selectedValue(patent,'community:09','2025','Solicitudes europeas'),754);
  assert.equal(periodTimestamp('2001R01'),periodTimestamp('2001'));
  const horizon=table('cordis',120103);
  assert.ok(horizon.dimensions.find(row=>row.name==='Convocatoria').values.some(value=>value.startsWith('HORIZON-')));
  const snapshot=fromDisk('cordis',horizon.snapshotFile);
  const ids=new Set(snapshot.projects.map(project=>project.id));
  assert.equal(ids.size,7155);
  assert.equal(snapshot.organizations.length,16477);
  assert.ok(snapshot.organizations.every(row=>ids.has(row.projectID)));
  assert.ok(products.available.find(row=>row.id==='science:120103').categoryIds.includes('F10'));
  const cdti=table('cdti',120501);
  assert.equal(cdti.periods.length,13);
  assert.equal(selectedValue(cdti,'national:ES','2026','Registros de ayuda aprobada'),1090);
  assert.ok(products.available.find(row=>row.id==='science:120501').categoryIds.includes('F10'));
});

function insideRing([x,y],ring){let inside=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [xi,yi]=ring[i],[xj,yj]=ring[j];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)inside=!inside;}return inside;}
function inside(point,feature){return feature.geometry.coordinates.some(p=>insideRing(point,p[0])&&!p.slice(1).some(r=>insideRing(point,r)));}
test('coastal masks tint foreign land without greying the sea or covering Spanish territory',()=>{
  const sea=read('datos/territorio/contexto/sea.geojson'),neighbors=read('datos/territorio/contexto/neighbor-land.geojson');
  for(const point of [[-10,40],[0,38],[-18.6,28.3]]){assert.ok(inside(point,sea));assert.ok(!inside(point,neighbors));}
  for(const point of [[-3.7,40.4],[-16.6,28.3],[-5.3069,35.8875],[-2.94,35.29]]){assert.ok(!inside(point,sea),'Spanish point painted blue '+point);assert.ok(!inside(point,neighbors),'Spanish point muted '+point);}
  assert.ok(inside([-9.14,38.72],neighbors));assert.ok(!inside([-9.14,38.72],sea));
});
