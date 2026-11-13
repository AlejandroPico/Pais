import fs from 'node:fs';
import clipping from 'polygon-clipping';
import {territoryLayers,sectionEditions,orthophotoEditions,historicOrthophoto,canaryEditions,canaryCartography} from '../src/territory-config.ts';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const manifest=read('public/data/territory/manifest.json');
const comarcaFile='public/data/territory/comarcas.geojson';
const comarcaCollection=read(comarcaFile);
const bierzo=read('public/data/territory/bierzo-boundaries.json');
if(new Set(bierzo.boundaries.map(item=>item.code)).size!==38)throw new Error('Incomplete El Bierzo municipality list');
const geometry=clipping.union(...bierzo.boundaries.map(({geometry})=>geometry.type==='Polygon'?[geometry.coordinates]:geometry.coordinates));
const bierzoCode='07:bierzo';
comarcaCollection.features=comarcaCollection.features.filter(feature=>feature.id!==bierzoCode);
comarcaCollection.features.push({
  type:'Feature',id:bierzoCode,
  properties:{code:bierzoCode,name:'El Bierzo',communityCode:'07',kind:'Comarca administrativa',sourceId:'F161',sourceUrl:bierzo.law,snapshot:'2026-11-13'},
  geometry:{type:'MultiPolygon',coordinates:geometry},
});
fs.writeFileSync(new URL(comarcaFile,root),JSON.stringify(comarcaCollection));
manifest.comarcaCoverage=manifest.comarcaCoverage.filter(entry=>entry.territory!=='El Bierzo');
manifest.comarcaCoverage.push({territory:'El Bierzo',sourceId:'F161',status:'integrado',count:1,kind:'Comarca administrativa',url:bierzo.law});
fs.writeFileSync(new URL('public/data/territory/manifest.json',root),JSON.stringify(manifest));

const available=[];
for(const layer of territoryLayers){
  if(layer.id==='municipal')continue; // Canonical product already registered in F00.
  const providers=layer.id==='historical-orthophoto'?orthophotoEditions.map(edition=>historicOrthophoto(edition.id)):layer.id==='canary-cartography'?canaryEditions.map(edition=>canaryCartography(edition.id)):layer.providers||[];
  for(const provider of providers){
    const service=manifest.services.find(s=>s.url===provider.url);
    if(!service||service.status!=='verificado')throw new Error('Unverified service: '+provider.url);
    for(const name of provider.layers.split(','))if(!service.layers.some(l=>l.name===name))throw new Error('Unknown service layer: '+name);
    if(provider.queryable&&provider.infoFormat&&!service.infoFormats.includes(provider.infoFormat))throw new Error('Unsupported query format: '+provider.id+' '+provider.infoFormat);
  }
  const sourceId=layer.providers?.[0]?.sourceId||(layer.id==='sections'?'F005':layer.id==='comarcas'?'F004':'F006');
  const sourceUrl=layer.providers?.[0]?.url||(layer.id==='sections'?'https://www.ine.es/geoserver/ows':layer.id==='historical-limits'?'https://www.ign.es/wms-inspire/unidades-administrativas':'https://www.ign.es/web/ide-area-nodo-ide-ign');
  available.push({id:'territory:'+layer.id,title:layer.name,sourceId,categoryIds:['F01'],status:'integrado',url:sourceUrl,
    coverage:layer.id==='comarcas'?manifest.comarcaCoverage.filter(c=>c.status==='integrado').map(c=>c.territory+' ('+c.count+')').join(', '):layer.note,
    period:layer.id==='sections'?'Ediciones de 2001, 2007–2026 y Censo 2011':layer.id==='historical-limits'?'2009-07-05 a 2026-07-28':layer.id==='comarcas'?'Capturas de noviembre de 2026; vigencia propia de cada fuente':'Según el servicio de origen',
    license:layer.providers?'Condiciones de cada proveedor oficial; consultar el origen':layer.id==='sections'?'Seccionado cedido por el Instituto Nacional de Estadística':layer.id==='comarcas'?'Condiciones de los organismos cartográficos autonómicos':'CC BY 4.0 · IGN',
    mode:layer.id==='comarcas'?'local':'remote',notes:layer.note,mapAction:'territory:'+layer.id,
    ...(layer.id==='comarcas'?{dataFile:'territory/comarcas.geojson'}:{}),
    fields:{'Detalle visible':'Desde zoom '+layer.minzoom,'Fecha de revisión':'2026-11-13',...(layer.providers?{'Proveedores':layer.providers.map(p=>p.credit).join('; ')}:{})}});
}
available.push({id:'territory:municipal-index',title:'Relación de municipios y correspondencia insular',sourceId:'F005',categoryIds:['F01'],status:'integrado',url:'https://www.ine.es/daco/daco42/codmun/diccionario26.xlsx',coverage:'8.132 municipios de España; provincias, comunidades e islas vinculadas',period:'Relación municipal a 2026-01-01. El fichero insular conserva sus rótulos de origen.',license:'CC BY 4.0 · INE',mode:'local',dataFile:'territory/index.json',mapAction:'search:addresses',notes:'La correspondencia IGN preserva 81 áreas adicionales fuera del catálogo municipal. No se convierten en municipios.'});
available.push({id:'territory:address-search',title:'Búsqueda oficial de direcciones y lugares',sourceId:'F007',categoryIds:['F01'],status:'integrado',url:'https://www.cartociudad.es/',coverage:'España · CartoCiudad',period:'Actualización del servicio',license:'CC BY 4.0 · IGN y colaboradores',mode:'remote',mapAction:'search:addresses',notes:'Búsqueda de candidatos seguida de geolocalización. No se usan coordenadas cero de las sugerencias.'});
const changes=read('public/data/territory/municipal-changes.json');
available.push({id:'territory:municipal-changes',title:'Cambios de municipios y códigos',sourceId:'F005',
  categoryIds:['F01'],status:'integrado',url:changes.source,coverage:'Altas, bajas, denominaciones y cambios territoriales de la relación municipal',
  period:{from:changes.editions[0].year,to:changes.editions.at(-1).year},license:'CC BY 4.0 · INE',mode:'local',
  dataFile:'territory/municipal-changes.json',mapAction:'municipal-changes',
  notes:'Ediciones oficiales consultables por año. Se conserva la estructura de cada publicación.'});
const inventory=[];
const implementedLayers=new Map();
for(const layer of territoryLayers){
  const providers=layer.id==='historical-orthophoto'?orthophotoEditions.map(edition=>historicOrthophoto(edition.id)):layer.id==='canary-cartography'?canaryEditions.map(edition=>canaryCartography(edition.id)):layer.providers||[];
  for(const provider of providers)for(const name of provider.layers.split(',')){
    implementedLayers.set(provider.url+'|'+name,'territory:'+layer.id);
  }
}
for(const edition of sectionEditions)implementedLayers.set('https://www.ine.es/geoserver/ows|'+edition.layer,'territory:sections');
implementedLayers.set('https://www.ign.es/wms-inspire/unidades-administrativas|LimitesTime','territory:historical-limits');

for(const service of manifest.services)for(const layer of service.layers||[]){
  const productId=implementedLayers.get(service.url+'|'+layer.name);
  const rootLayer=['WMS_CARTO_EST','gipuzkoa_wms'].includes(layer.name);
  const tourism=layer.name==='ALJTUR2015';
  inventory.push({id:'f01-wms:'+service.id+':'+layer.name,title:layer.title,sourceId:service.sourceId,categoryIds:['F01'],suggestedCategoryIds:tourism?['F24']:[],status:productId?'integrado':rootLayer||tourism?'no_procede':'por_revisar',...(productId?{mapAction:['territory:historical-orthophoto','territory:canary-cartography','territory:sections'].includes(productId)?productId+':'+layer.name:productId,review:{implementedProductId:productId,updatedAt:'2026-11-13',reason:'Capa representada en el producto indicado.'}}:{}),url:service.url+'?SERVICE=WMS&REQUEST=GetCapabilities',coverage:service.coverage,period:layer.dimensions.map(d=>d.values).join('; ')||'Según el producto original',license:null,notes:productId?'Capa consultable en el producto indicado.':rootLayer?'Raíz del servicio WMS que agrupa las capas temáticas.':tourism?'Capa de alojamientos turísticos asignada a F24.':'Pendiente de comprobar su integración en el visor.',fields:{'Servicio':service.name,'Nombre de capa':layer.name,'Estilos':layer.styles.join(', '),'Consulta de atributos':layer.queryable?'Disponible en el servicio':'No anunciada'}});
}
for(const edition of sectionEditions)if(!manifest.services.find(s=>s.id==='ine-wms').layers.some(l=>l.name===edition.layer))throw new Error('Missing census edition '+edition.id);
const result={schemaVersion:1,revision:'2026-11-13',available,inventory};
fs.writeFileSync(new URL('registry/territory-products.json',root),JSON.stringify(result,null,2)+'\n');
console.log(`F01: ${available.length} products; ${inventory.length} service layers inventoried.`);
