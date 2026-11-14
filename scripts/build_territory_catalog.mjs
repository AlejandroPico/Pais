import fs from 'node:fs';
import {createHash} from 'node:crypto';
import clipping from 'polygon-clipping';
import {territoryLayers,sectionEditions,orthophotoEditions,historicOrthophoto,canaryEditions,canaryCartography,localCredit} from '../src/territory-config.ts';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const revision='2026-11-14';
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
  properties:{code:bierzoCode,name:'El Bierzo',communityCode:'07',kind:'Comarca administrativa',sourceId:'F157',sourceUrl:bierzo.law,snapshot:'2026-11-13'},
  geometry:{type:'MultiPolygon',coordinates:geometry},
});
fs.writeFileSync(new URL(comarcaFile,root),JSON.stringify(comarcaCollection));
manifest.comarcaCoverage=manifest.comarcaCoverage.filter(entry=>entry.territory!=='El Bierzo');
manifest.comarcaCoverage.push({territory:'El Bierzo',sourceId:'F157',status:'integrado',count:1,kind:'Comarca administrativa',url:bierzo.law});
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
  const sourceId=layer.local?.sourceId||layer.providers?.[0]?.sourceId||(layer.id==='sections'?'F005':layer.id==='comarcas'?'F004':'F006');
  const sourceUrl=layer.local?.url||layer.providers?.[0]?.url||(layer.id==='sections'?'https://www.ine.es/geoserver/ows':layer.id==='historical-limits'?'https://www.ign.es/wms-inspire/unidades-administrativas':'https://www.ign.es/web/ide-area-nodo-ide-ign');
  available.push({id:'territory:'+layer.id,title:layer.name,sourceId,categoryIds:['F01'],status:'integrado',url:sourceUrl,
    coverage:layer.id==='comarcas'?manifest.comarcaCoverage.filter(c=>c.status==='integrado').map(c=>c.territory+' ('+c.count+')').join(', '):layer.local?.coverage||layer.local?.group||layer.note,
    period:layer.local?.period||(layer.id==='sections'?'Ediciones de 2001, 2007–2026 y Censo 2011':layer.id==='historical-limits'?'2009-07-05 a 2026-07-28':layer.id==='comarcas'?'Capturas de noviembre de 2026; vigencia propia de cada fuente':'Según el servicio de origen'),
    license:layer.local?(localCredit(layer.local)+(layer.local.credit&&!layer.local.credit.includes('4.0')?' · Condiciones del organismo publicador':''))
      :layer.providers?'Condiciones de cada proveedor oficial; consultar el origen':layer.id==='sections'?'Seccionado cedido por el Instituto Nacional de Estadística':layer.id==='comarcas'?'Condiciones de los organismos cartográficos autonómicos':'CC BY 4.0 · IGN',
    mode:layer.local||layer.id==='comarcas'?'local':'remote',notes:layer.note,mapAction:'territory:'+layer.id,
    ...(layer.local?{dataFile:'territory/'+layer.local.file,links:{'Descarga original':layer.local.download}}:layer.id==='comarcas'?{dataFile:'territory/comarcas.geojson'}:{}),
    fields:{'Detalle visible':'Desde zoom '+layer.minzoom,'Fecha de revisión':revision,
      ...(layer.local?.layer?{'Tabla GeoPackage':layer.local.layer,'Registros':String(layer.local.count)}:{}),
      ...(layer.local?.missingCount?{'Registros sin coordenadas':String(layer.local.missingCount)}:{}),
      ...(layer.providers?{'Proveedores':layer.providers.map(p=>p.credit).join('; ')}:{})}});
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
const sectionVectors=read('public/data/territory/section-vectors.json');
for(const download of sectionVectors.downloads||[]){
  const edition=sectionEditions.find(item=>item.id===download.year||(download.year==='2001'&&item.id==='C2001'));
  if(!edition){
    const product=available.find(row=>row.id==='territory:archive-sections-'+download.year);
    if(!product)throw new Error('Edición sin representación en el visor: '+download.year);
    inventory.push({...product,id:'f01-section-archive:'+download.year,url:download.url,
      review:{implementedProductId:product.id,updatedAt:revision,reason:'Se preservan todos los recintos de la edición descargada.'}});
    continue;
  }
  const item=inventory.find(row=>row.mapAction==='territory:sections:'+edition.layer);
  if(item)item.links={'Archivo SHP nacional':download.url};
}
for(const edition of read('registry/cnig-history.json').products){
  const product=available.find(row=>row.id==='territory:'+edition.id);
  if(!product)throw new Error('Tabla del CNIG sin representación en el visor: '+edition.layer);
  inventory.push({...product,id:'f01-cnig:'+edition.id,
    review:{implementedProductId:product.id,updatedAt:revision,reason:'Recuento completo de la tabla oficial. Geometría simplificada para el visor.'}});
}
const directory=read('public/data/territory/official-wms.json');
const labels={imagen:'Ortofotos y fotografía aérea',divisiones:'Divisiones territoriales',relieve:'Relieve y elevaciones',catastro:'Catastro',base:'Cartografía base y toponimia'};
const officialLayers=[];
for(const service of directory.services){
  const sourceUrl=service.capabilities||service.url;
  const classified=service.layers.filter(layer=>layer.group&&!layer.container);
  if(!classified.length){
    inventory.push({id:'f01-directory:'+service.id,title:service.title,sourceId:service.sourceId,categoryIds:['F01'],
      status:'bloqueado',url:sourceUrl,coverage:service.region,license:null,
      notes:service.error||'El servicio carece de capas individuales clasificadas para F01.',
      fields:{'Servicio':service.title,'Familia':labels[service.group]}});
  }
  for(const layer of classified){
    const id=service.id+'-'+createHash('sha256').update(layer.name).digest('hex').slice(0,12);
    const productId='territory:directory:'+id;
    const label=labels[layer.group];
    const title=classified.length===1?service.title:layer.title;
    const mapAction='official-wms:'+id;
    const time=layer.dimensions.find(d=>d.name?.toLowerCase()==='time');
    const periods=time?.values.split(',').map(value=>value.trim()).filter(value=>/^\d{4}(-\d{2}-\d{2})?$/.test(value))||[];
    const period=periods.length?{from:periods[0],to:periods.at(-1)}:time?.values||'Según el producto original';
    const fields={'Servicio':service.title,'Familia':label,'Nombre de capa':layer.name,
      'Consulta de atributos':layer.tileEndpoint?'Ver servicio WMS original':layer.queryable?'Anunciada por el servicio':'Sin consulta anunciada'};
    const record={title,sourceId:service.sourceId,categoryIds:['F01'],url:sourceUrl,coverage:service.region,period,fields};
    if(service.url==='https://wms-satelites-historicos.idee.es/satelites-historicos'&&layer.name==='fondo'){
      inventory.push({...record,id:'f01-directory:'+id,status:'no_procede',license:null,
        notes:'Fondo auxiliar del servicio de mosaicos. Las imágenes y huellas se ofrecen en sus capas propias.'});
    }else if(layer.mapError===null){
      const infoFormat=['application/json','application/geo+json','text/html'].find(format=>service.infoFormats.includes(format));
      const minzoom=layer.name==='CAL_PORTALES'?15:layer.name==='CAL_CALLES'?11:layer.name.startsWith('DANA.')?9:layer.group==='catastro'?13:layer.group==='divisiones'?7:6;
      officialLayers.push({id,name:title,group:layer.group,minzoom,...(periods.length?{periods,defaultPeriod:time.default}:{}),provider:{
        id:service.id,url:service.url,layers:layer.name,version:service.version,tileEndpoint:layer.tileEndpoint,requestCrs:layer.requestCrs,bounds:layer.bounds,sourceId:service.sourceId,
        credit:service.url.endsWith('/WMS_KARTOGRAFIA')?'Eusko Jaurlaritza / Gobierno Vasco':service.region+' · '+service.title,queryable:Boolean(!layer.tileEndpoint&&layer.queryable&&infoFormat),infoFormat,
      }});
      available.push({...record,id:productId,status:'integrado',mapAction,mode:'remote',license:'Condiciones del organismo publicador',
        notes:label+' · imagen oficial. Disponible a partir de zoom '+minzoom+'.'});
      inventory.push({...record,id:'f01-directory:'+id,status:'integrado',mapAction,license:'Condiciones del organismo publicador',
        notes:label+' · capa verificada mediante petición de mapa.',
        review:{implementedProductId:productId,updatedAt:revision,reason:'Petición GetMap verificada para esta capa y origen.'}});
    }else{
      inventory.push({...record,id:'f01-directory:'+id,status:'bloqueado',license:null,
        notes:layer.mapError||service.error||'La capa no anuncia PNG en EPSG:3857 con una extensión utilizable.'});
    }
  }
}
fs.writeFileSync(new URL('public/data/territory/official-layers.json',root),JSON.stringify({revision,layers:officialLayers}));
const activeCount=inventory.filter(product=>product.status==='integrado').length;
const unresolved=inventory.filter(product=>!['integrado','no_procede'].includes(product.status)).length;
console.log(`Inventario F01: ${activeCount} entradas disponibles; ${unresolved} requieren resolución.`);
const result={schemaVersion:1,revision,available,inventory};
fs.writeFileSync(new URL('registry/territory-products.json',root),JSON.stringify(result,null,2)+'\n');
console.log(`F01: ${available.length} products; ${inventory.length} service layers inventoried.`);
