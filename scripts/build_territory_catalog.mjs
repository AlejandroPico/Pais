import fs from 'node:fs';
import {territoryLayers,sectionEditions} from '../src/territory-config.ts';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const manifest=read('public/data/territory/manifest.json');
const available=[];
for(const layer of territoryLayers){
  if(layer.id==='municipal')continue; // Canonical product already registered in F00.
  for(const provider of layer.providers||[]){
    const service=manifest.services.find(s=>s.url===provider.url);
    if(!service||service.status!=='verificado')throw new Error('Unverified service: '+provider.url);
    for(const name of provider.layers.split(','))if(!service.layers.some(l=>l.name===name))throw new Error('Unknown service layer: '+name);
    if(provider.queryable&&provider.infoFormat&&!service.infoFormats.includes(provider.infoFormat))throw new Error('Unsupported query format: '+provider.id+' '+provider.infoFormat);
  }
  const sourceId=layer.providers?.[0]?.sourceId||(layer.id==='sections'?'F005':layer.id==='comarcas'?'F004':'F006');
  const sourceUrl=layer.providers?.[0]?.url||(layer.id==='sections'?'https://www.ine.es/geoserver/ows':layer.id==='historical-limits'?'https://www.ign.es/wms-inspire/unidades-administrativas':'https://www.ign.es/web/ide-area-nodo-ide-ign');
  available.push({id:'territory:'+layer.id,title:layer.name,sourceId,categoryIds:['F01'],status:'integrado',url:sourceUrl,
    coverage:layer.id==='comarcas'?manifest.comarcaCoverage.filter(c=>c.status==='integrado').map(c=>c.territory+' ('+c.count+')').join(', '):layer.note,
    period:layer.id==='sections'?'Ediciones de 2001, 2007–2026 y Censo 2011':layer.id==='historical-limits'?'2009-07-05 a 2026-07-28':layer.id==='comarcas'?'Captura 2026-11-09; vigencia propia de cada fuente':'Según el servicio de origen',
    license:layer.providers?'Condiciones de cada proveedor oficial; consultar el origen':layer.id==='sections'?'Seccionado cedido por el Instituto Nacional de Estadística':layer.id==='comarcas'?'Condiciones de los organismos cartográficos autonómicos':'CC BY 4.0 · IGN',
    mode:layer.id==='comarcas'?'local':'remote',notes:layer.note,mapAction:'territory:'+layer.id,
    ...(layer.id==='comarcas'?{dataFile:'territory/comarcas.geojson'}:{}),
    fields:{'Detalle visible':'Desde zoom '+layer.minzoom,'Fecha de revisión':'2026-11-09',...(layer.providers?{'Proveedores':layer.providers.map(p=>p.credit).join('; ')}:{})}});
}
available.push({id:'territory:municipal-index',title:'Relación de municipios y correspondencia insular',sourceId:'F005',categoryIds:['F01'],status:'integrado',url:'https://www.ine.es/daco/daco42/codmun/diccionario26.xlsx',coverage:'8.132 municipios de España; provincias, comunidades e islas vinculadas',period:'Relación municipal a 2026-01-01. El fichero insular conserva sus rótulos de origen.',license:'CC BY 4.0 · INE',mode:'local',dataFile:'territory/index.json',mapAction:'search:addresses',notes:'La correspondencia IGN preserva 81 áreas adicionales fuera del catálogo municipal. No se convierten en municipios.'});
available.push({id:'territory:address-search',title:'Búsqueda oficial de direcciones y lugares',sourceId:'F007',categoryIds:['F01'],status:'integrado',url:'https://www.cartociudad.es/',coverage:'España · CartoCiudad',period:'Actualización del servicio',license:'CC BY 4.0 · IGN y colaboradores',mode:'remote',mapAction:'search:addresses',notes:'Búsqueda de candidatos seguida de geolocalización. No se usan coordenadas cero de las sugerencias.'});
const inventory=[];
for(const service of manifest.services)for(const layer of service.layers||[]){
  inventory.push({id:'f01-wms:'+service.id+':'+layer.name,title:layer.title,sourceId:service.sourceId,categoryIds:['F01'],suggestedCategoryIds:[],status:'por_revisar',url:service.url+'?SERVICE=WMS&REQUEST=GetCapabilities',coverage:service.coverage,period:layer.dimensions.map(d=>d.values).join('; ')||'Según el producto original',license:null,notes:'Inventario técnico completo de las capas anunciadas por este servicio. No equivale a una capa nueva ni a tener todas sus variantes adaptadas.',fields:{'Servicio':service.name,'Nombre de capa':layer.name,'Estilos':layer.styles.join(', '),'Consulta de atributos':layer.queryable?'Disponible en el servicio':'No anunciada'}});
}
for(const edition of sectionEditions)if(!manifest.services.find(s=>s.id==='ine-wms').layers.some(l=>l.name===edition.layer))throw new Error('Missing census edition '+edition.id);
const result={schemaVersion:1,revision:'2026-11-09',available,inventory};
fs.writeFileSync(new URL('registry/territory-products.json',root),JSON.stringify(result,null,2)+'\n');
console.log(`F01: ${available.length} products; ${inventory.length} service layers inventoried.`);
