import type {Map as AtlasMap,MapMouseEvent,GeoJSONSource,LayerSpecification,FilterSpecification} from 'maplibre-gl';
import type {Feature,FeatureCollection,Geometry,Position} from 'geojson';
import {normalize} from './data';
import {toAtlas,fromAtlas,projectFeature,projectCollection,displayRegion} from './atlas-coordinates';
import {atlasTileUrl,addShiftedLayer,updateShiftedTiles} from './atlas-geography';
import {municipalCode,coordinatesExtent,validSpanishCoordinate} from './territory-data';
import {territoryLayers,sectionEditions,wmsTile,type WmsProvider} from './territory-config';

const esc=(v:unknown)=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
const dataRoot=import.meta.env.BASE_URL+'data/territory/';
const vectorRoot='https://api-features.ign.es/collections/administrativeunit/items/';
type Municipality={code:string;name:string;provinceCode:string;communityCode:string;ignFeatureId:number;islandId?:string;cartographicName?:string;referenceDate:string};
export type TerritoryIndex={referenceDate:string;municipalities:Municipality[];islands:{id:string;name:string;provinceCode:string}[];supplementalAreas:{code:string;name:string;classification:string}[]};
type LegacyFeature=Feature<Geometry,{code:string;name:string}>;
type Options={active:Set<string>;info:HTMLElement;icons:()=>void;onChange:()=>void;beforeInspect:()=>void;closeDrawer:()=>void;selectLegacy:(f:LegacyFeature,level:'province'|'community')=>void;provinces:FeatureCollection;communities:FeatureCollection};


export class TerritoryController{
  private maps:AtlasMap[]=[];
  private mapLayers=new Map<string,string[]>();
  private indexPromise:Promise<TerritoryIndex>|undefined;
  private comarcaPromise:Promise<FeatureCollection>|undefined;
  private controller:AbortController|undefined;
  private searchController:AbortController|undefined;
  private geometryCache=new Map<number,Feature>();
  private selected:Feature|undefined;
  private sectionEdition='2026';
  private boundaryDate='2026-07-28';
  private tileRevision=0;
  private opacities=new Map<string,number>();
  constructor(private options:Options){
    const params=new URLSearchParams(location.hash.slice(1));
    if(sectionEditions.some(e=>e.id===params.get('sections')))this.sectionEdition=params.get('sections')!;
    const date=params.get('boundaries')||'';
    if(/^\d{4}-\d{2}-\d{2}$/.test(date)&&date>='2009-07-05'&&date<='2026-07-28')this.boundaryDate=date;
  }
  urlState(){return {sections:this.sectionEdition,boundaries:this.boundaryDate};}
  private index():Promise<TerritoryIndex>{return this.indexPromise??=fetch(dataRoot+'index.json').then(r=>{if(!r.ok)throw new Error('No se pudo cargar el catálogo municipal');return r.json();}).catch(e=>{this.indexPromise=undefined;throw e;});}
  private comarcas():Promise<FeatureCollection>{return this.comarcaPromise??=fetch(dataRoot+'comarcas.geojson').then(r=>{if(!r.ok)throw new Error('No se pudo cargar la cartografía comarcal');return r.json();}).catch(e=>{this.comarcaPromise=undefined;throw e;});}
  private add(m:AtlasMap,id:string,layer:LayerSpecification,before?:string){
    m.addLayer(layer,before);
    const shifted=addShiftedLayer(m,layer,before);
    const ids=this.mapLayers.get(id)||[];if(!ids.includes(layer.id))ids.push(layer.id);for(const shiftedId of shifted)if(!ids.includes(shiftedId))ids.push(shiftedId);this.mapLayers.set(id,ids);
  }
  attach(m:AtlasMap){
    this.maps.push(m);
    m.addSource('f01-admin',{type:'vector',tiles:['https://vt-unidades-administrativas.ign.es/1.0.0/uadministrativa/{z}/{x}/{y}.pbf'],maxzoom:17,attribution:'© IGN · Unidades administrativas · CC BY 4.0'});
    m.addSource('f01-country',{type:'geojson',data:dataRoot+'country-atlas.geojson'});
    m.addSource('f01-comarcas',{type:'geojson',data:dataRoot+'comarcas.geojson'});
    m.addSource('f01-places',{type:'vector',tiles:['https://vt-poblaciones.ign.es/api.nuc,api.opob,api.sin_toponimo/{z}/{x}/{y}.pbf'],maxzoom:16,attribution:'© IGN · Poblaciones · CC BY 4.0'});
    m.addSource('f01-btn',{type:'vector',tiles:['https://vt-btn.idee.es/1.0.0/btn/tile/{z}/{y}/{x}.pbf'],maxzoom:16,attribution:'© IGN · Base Topográfica Nacional · CC BY 4.0'});
    m.addSource('f01-selection',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
    const visibility=(id:string)=>this.options.active.has(id)?'visible' as const:'none' as const;
    for(const [id,sourceLayer,color,width,minzoom] of [['country','pais','#e9f3ed',1.4,0],['municipal','municipio','#e1e7e1',.75,7]] as const){
      this.add(m,id,{id:'f01-'+id+'-hit',type:'fill',source:id==='country'?'f01-country':'f01-admin',...(id==='country'?{}:{'source-layer':sourceLayer}),minzoom,layout:{visibility:visibility(id)},paint:{'fill-opacity':0}});
      this.add(m,id,{id:'f01-'+id+'-line',type:'line',source:id==='country'?'f01-country':'f01-admin',...(id==='country'?{}:{'source-layer':sourceLayer}),minzoom,layout:{visibility:visibility(id)},paint:{'line-color':color,'line-width':['interpolate',['linear'],['zoom'],5,width,13,width*1.5]}});
    }
    this.add(m,'comarcas',{id:'f01-comarcas-hit',type:'fill',source:'f01-comarcas',minzoom:6,layout:{visibility:visibility('comarcas')},paint:{'fill-opacity':.05,'fill-color':'#ffd6a3'}});
    this.add(m,'comarcas',{id:'f01-comarcas-line',type:'line',source:'f01-comarcas',minzoom:6,layout:{visibility:visibility('comarcas')},paint:{'line-color':'#f1bc77','line-width':1.5,'line-dasharray':[4,2]}});
    this.add(m,'comarcas',{id:'f01-comarcas-label',type:'symbol',source:'f01-comarcas',minzoom:7,layout:{visibility:visibility('comarcas'),'text-field':['get','name'],'text-font':['Noto Sans Regular'],'text-size':12},paint:{'text-color':'#ffdfb7','text-halo-color':'#483725','text-halo-width':1.2}});
    for(const [id,sourceLayer,minzoom,color] of [['nuclei','api.nuc',9,'#eec887'],['other-places','api.opob',10,'#c8d69e'],['unnamed-places','api.sin_toponimo',12,'#cccae2']] as const){
      this.add(m,id,{id:'f01-'+id+'-fill',type:'fill',source:'f01-places','source-layer':sourceLayer,minzoom,layout:{visibility:visibility(id)},paint:{'fill-color':color,'fill-opacity':.25,'fill-outline-color':color}});
      if(id!=='unnamed-places')this.add(m,id,{id:'f01-'+id+'-labels',type:'symbol',source:'f01-places','source-layer':sourceLayer,minzoom:Math.max(minzoom,11),layout:{visibility:visibility(id),'text-field':['get','nombre'],'text-font':['Noto Sans Regular'],'text-size':11},paint:{'text-color':color,'text-halo-color':'#243c2d','text-halo-width':1}});
    }
    for(const sourceLayer of ['btn0507s_edific','btn0513s_ins_ind','btn0516s_edi_rel','btn0519s_molino','btn0534s_ref_vis'])this.add(m,'topographic-buildings',{id:'f01-building-'+sourceLayer,type:'fill',source:'f01-btn','source-layer':sourceLayer,minzoom:13,layout:{visibility:visibility('topographic-buildings')},paint:{'fill-color':'#d8c5af','fill-opacity':.6,'fill-outline-color':'#57453c'}});
    this.add(m,'contours',{id:'f01-contours',type:'line',source:'f01-btn','source-layer':'btn0201l_cur_niv',minzoom:11,layout:{visibility:visibility('contours')},paint:{'line-color':'#ebc18f','line-width':['match',['get','categ_0201'],'02 MAESTRA',1,.5],'line-opacity':.8}});
    this.add(m,'contours',{id:'f01-elevation',type:'circle',source:'f01-btn','source-layer':'btn0204p_pun_aco',minzoom:14,layout:{visibility:visibility('contours')},paint:{'circle-radius':2,'circle-color':'#ebc18f'}});
    m.addSource('f01-shade-dem',{type:'raster-dem',tiles:[atlasTileUrl('https://xyz-mdt.idee.es/1.0.0/raster-dem/{z}/{x}/{y}.png',{size:512,dem:true})],encoding:'mapbox',tileSize:512,minzoom:5,maxzoom:15,attribution:'Modelo de elevaciones © IGN · CC BY 4.0'});
    this.add(m,'hillshade',{id:'f01-hillshade',type:'hillshade',source:'f01-shade-dem',minzoom:5,layout:{visibility:visibility('hillshade')},paint:{'hillshade-exaggeration':.45}},'province-fill');
    for(const def of territoryLayers)if(def.providers)this.raster(m,def.id,def.providers,def.minzoom);
    this.raster(m,'sections',[this.sectionsProvider()],10);
    this.raster(m,'historical-limits',[this.historyProvider()],7,{TIME:this.boundaryDate+'T23:00:00Z'});
    m.addLayer({id:'f01-selected-fill',type:'fill',source:'f01-selection',paint:{'fill-color':'#f6d584','fill-opacity':.1}});
    m.addLayer({id:'f01-selected-point',type:'circle',source:'f01-selection',filter:['==',['geometry-type'],'Point'],paint:{'circle-radius':6,'circle-color':'#f6d584','circle-stroke-color':'#15201e','circle-stroke-width':2}});
    m.addLayer({id:'f01-selected-line',type:'line',source:'f01-selection',paint:{'line-color':'#f6d584','line-width':2.5}});
  }
  private sectionsProvider():WmsProvider{return {id:'ine',url:'https://www.ine.es/geoserver/ows',layers:sectionEditions.find(e=>e.id===this.sectionEdition)!.layer,sourceId:'F005',credit:'Seccionado cedido por el Instituto Nacional de Estadística',bounds:[-18.5,27.5,4.7,44],queryable:true,infoFormat:'application/json'};}
  private historyProvider():WmsProvider{return {id:'ign-history',url:'https://www.ign.es/wms-inspire/unidades-administrativas',layers:'LimitesTime',styles:'Historicos',sourceId:'F006',credit:'© IGN · CC BY 4.0',bounds:[-18.5,27.5,4.7,44],queryable:true,infoFormat:'application/json'};}
  private raster(m:AtlasMap,id:string,providers:WmsProvider[],minzoom:number,extra:Record<string,string>={}){
    for(const p of providers){const source=`f01-raster-${id}-${p.id}`;m.addSource(source,{type:'raster',tiles:[wmsTile(p,extra)],tileSize:256,bounds:p.bounds,attribution:p.credit});this.add(m,id,{id:source,type:'raster',source,minzoom,layout:{visibility:this.options.active.has(id)?'visible':'none'},paint:{'raster-opacity':this.opacities.get(id)??.85}});}
  }
  update(){for(const m of this.maps)for(const [id,ids] of this.mapLayers)for(const layer of ids)if(m.getLayer(layer))m.setLayoutProperty(layer,'visibility',this.options.active.has(id)?'visible':'none');}
  reset(){this.controller?.abort();this.selected=undefined;for(const m of this.maps)(m.getSource('f01-selection') as GeoJSONSource).setData({type:'FeatureCollection',features:[]});}
  activeLabels(){return territoryLayers.filter(d=>this.options.active.has(d.id)).map(d=>d.id==='sections'?`Secciones · ${sectionEditions.find(e=>e.id===this.sectionEdition)!.name}`:d.id==='historical-limits'?`Límites · ${this.boundaryDate}`:d.name);}
  panel(){
    return [...new Set(territoryLayers.map(d=>d.group))].map(group=>`<details class="submenu" ${group==='Divisiones territoriales'?'open':''}><summary>${esc(group)} <span aria-hidden="true">›</span></summary>${territoryLayers.filter(d=>d.group===group).map(d=>`<div class="territory-option"><label class="check-row"><input type="checkbox" data-territory-layer="${d.id}" ${this.options.active.has(d.id)?'checked':''}><span>${esc(d.name)}</span></label><p class="data-note">${esc(d.note)}${d.minzoom>=7?' Visible desde zoom '+d.minzoom+'.':''}</p>${d.providers?`<label class="opacity-control">Opacidad<input data-territory-opacity="${d.id}" type="range" min="10" max="100" value="${(this.opacities.get(d.id)??.85)*100}" aria-label="Opacidad de ${esc(d.name)}"></label>`:''}${d.id==='sections'?`<label class="field-label">Edición del seccionado<select id="section-edition">${sectionEditions.map(e=>`<option value="${e.id}" ${e.id===this.sectionEdition?'selected':''}>${e.name}</option>`).join('')}</select></label>`:''}${d.id==='historical-limits'?`<label class="field-label">Fecha de los límites<input id="boundary-date" type="date" min="2009-07-05" max="2026-07-28" value="${this.boundaryDate}"></label>`:''}</div>`).join('')}</details>`).join('');
  }
  bind(root:HTMLElement){
    root.querySelectorAll<HTMLInputElement>('[data-territory-layer]').forEach(input=>input.onchange=()=>{const id=input.dataset.territoryLayer!;input.checked?this.options.active.add(id):this.options.active.delete(id);this.update();this.options.onChange();});
    root.querySelectorAll<HTMLInputElement>('[data-territory-opacity]').forEach(input=>input.oninput=()=>{const id=input.dataset.territoryOpacity!,value=Number(input.value)/100;this.opacities.set(id,value);for(const m of this.maps)for(const layer of this.mapLayers.get(id)||[])if(m.getLayer(layer)?.type==='raster')m.setPaintProperty(layer,'raster-opacity',value);});
    root.querySelector<HTMLSelectElement>('#section-edition')?.addEventListener('change',e=>{this.sectionEdition=(e.target as HTMLSelectElement).value;this.replaceTemporal('sections',this.sectionsProvider());});
    root.querySelector<HTMLInputElement>('#boundary-date')?.addEventListener('change',e=>{const el=e.target as HTMLInputElement;if(!el.checkValidity()||!el.value)return;this.boundaryDate=el.value;this.replaceTemporal('historical-limits',this.historyProvider(),{TIME:this.boundaryDate+'T23:00:00Z'});});
  }
  private replaceTemporal(id:string,provider:WmsProvider,extra:Record<string,string>={}){
    this.controller?.abort();const layer=`f01-raster-${id}-${provider.id}`;
    for(const m of this.maps){const source=m.getSource(layer) as {setTiles?:(tiles:string[])=>void};const tiles=[wmsTile(provider,{...extra,REVISION:String(++this.tileRevision)})];source?.setTiles?.(tiles);updateShiftedTiles(m,layer,tiles);}
    this.options.onChange();
  }
  private mapFor(_coordinates:Position){return this.maps[0];}
  private showSelection(feature:Feature){this.selected=feature;for(const m of this.maps)(m.getSource('f01-selection') as GeoJSONSource).setData(projectFeature(feature));}
  private card(title:string,kind:string,content:string,source:string){
    this.options.beforeInspect();const info=this.options.info;info.hidden=false;info.innerHTML=`<div class="info-heading"><span class="eyebrow">${esc(kind)}</span><button class="icon-button" id="geo-close" aria-label="Cerrar información">×</button></div><h3>${esc(title)}</h3>${content}<p class="data-note">${source}</p>`;
    info.querySelector<HTMLButtonElement>('#geo-close')!.onclick=()=>{this.reset();info.hidden=true;};this.options.icons();
  }
  private facts(fields:Record<string,unknown>){return '<dl>'+Object.entries(fields).filter(([,v])=>v!==null&&v!==undefined&&v!=='').map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(typeof v==='object'?JSON.stringify(v):v)}</dd>`).join('')+'</dl>';}
  private async municipality(m:Municipality,zoom:boolean){
    this.controller?.abort();const controller=this.controller=new AbortController();
    this.card(m.name,'Municipio',`<p role="status">Consultando geometría oficial…</p>`,'INE / IGN');
    try{
      const index=await this.index();let feature=this.geometryCache.get(m.ignFeatureId);
      if(!feature){const response=await fetch(vectorRoot+m.ignFeatureId+'?f=json',{signal:controller.signal});if(!response.ok)throw new Error('El servicio IGN no ha respondido');feature=await response.json() as Feature;const code=municipalCode(feature.properties?.nationalcode);if(code!==m.code||!feature.geometry)throw new Error('La geometría no corresponde al municipio seleccionado');if(this.geometryCache.size>=12)this.geometryCache.delete(this.geometryCache.keys().next().value!);this.geometryCache.set(m.ignFeatureId,feature);}
      if(controller.signal.aborted)return;
      this.showSelection(feature);
      const province=this.options.provinces.features.find(f=>f.properties?.code===m.provinceCode)?.properties?.name;
      const community=this.options.communities.features.find(f=>f.properties?.code===m.communityCode)?.properties?.name;
      const island=index.islands.find(i=>i.id===m.islandId)?.name;
      this.card(m.name,'Municipio',this.facts({'Código INE':m.code,'Provincia':province,'Comunidad / ciudad autónoma':community,'Isla':island,'Relación municipal':m.referenceDate,'Nombre cartográfico IGN':m.cartographicName})+'<button id="geo-download" class="text-button">Descargar geometría GeoJSON</button>',`<a href="${vectorRoot+m.ignFeatureId+'?f=json'}" target="_blank" rel="noopener">Geometría IGN ↗</a> · CC BY 4.0. Consulta en línea; la fecha del mapa no se convierte en fecha histórica del municipio.`);
      const complete=feature;this.options.info.querySelector('#geo-download')!.addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(complete)],{type:'application/geo+json'}));const link=document.createElement('a');link.href=url;link.download='municipio-'+m.code+'.geojson';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
      if(zoom){const bounds=coordinatesExtent(projectFeature(feature).geometry),target=this.mapFor(bounds[0]);target.fitBounds(bounds,{padding:45,maxZoom:14,pitch:0,duration:600});}
    }catch(error){if(!controller.signal.aborted)this.card(m.name,'Municipio',`<p>${esc(error instanceof Error?error.message:'No se pudo obtener el contorno')}</p>`,'La relación municipal permanece disponible. <a href="https://api-features.ign.es/collections/administrativeunit?f=html" target="_blank" rel="noopener">Consultar IGN ↗</a>');}
  }
  async inspect(m:AtlasMap,e:MapMouseEvent):Promise<boolean>{
    const layers=[...this.mapLayers.entries()].filter(([id])=>this.options.active.has(id)).flatMap(([,ids])=>ids).filter(id=>m.getLayer(id)&&['fill','line','circle'].includes(m.getLayer(id)!.type));
    const features=layers.length?m.queryRenderedFeatures(e.point,{layers}):[];
    const hit=features.find(f=>f.layer.id.startsWith('f01-municipal-hit'))||features.find(f=>f.layer.id==='f01-comarcas-hit')||features.find(f=>!f.layer.id.includes('country'))||features[0];
    const truePoint=fromAtlas([e.lngLat.lng,e.lngLat.lat]);const wms=this.wmsQueries(m,truePoint[0],truePoint[1]);
    if(wms.length){await this.queryWms(wms,truePoint[0],truePoint[1],m);return true;}
    if(!hit)return false;
    this.reset();const p=hit.properties||{};
    if(hit.layer.id.startsWith('f01-municipal-hit')){
      try{const index=await this.index(),code=municipalCode(p.nationalcode);const municipality=index.municipalities.find(x=>x.code===code);if(municipality){await this.municipality(municipality,false);return true;}}catch{}
      this.card(p.nameunit||'Área cartográfica IGN','Unidad cartográfica',this.facts(p),'Unidad publicada por IGN; sin correspondencia municipal confirmada en el catálogo INE de 2026.');return true;
    }
    if(hit.layer.id==='f01-comarcas-hit'){
      const all=await this.comarcas();const full=all.features.find(f=>f.id===hit.id);
      if(full)this.showSelection(full);
      this.card(p.name,p.kind,this.facts({'Código de origen':p.code,'Captura':p.snapshot,'Fuente':p.sourceId}),`<a href="${esc(p.sourceUrl)}" target="_blank" rel="noopener">Fuente territorial ↗</a>. La tipología no es uniforme entre comunidades.`);return true;
    }
    this.card(p.nombre||p.nameunit||p.name||'Elemento cartográfico','Cartografía IGN',this.facts(p),'© IGN · CC BY 4.0. Atributos publicados por el servicio; no se asignan datos estadísticos de otra escala.');return true;
  }
  private wmsQueries(m:AtlasMap,lng:number,lat:number){
    const result:{name:string;provider:WmsProvider;extra?:Record<string,string>}[]=[];
    for(const d of territoryLayers){if(!this.options.active.has(d.id)||m.getZoom()+Math.log2(displayRegion(toAtlas([lng,lat]))?.scale||1)<d.minzoom)continue;let providers=d.providers,extra:Record<string,string>|undefined;
      if(d.id==='sections')providers=[this.sectionsProvider()];if(d.id==='historical-limits'){providers=[this.historyProvider()];extra={TIME:this.boundaryDate+'T23:00:00Z'};}
      for(const p of providers||[])if(lng>=p.bounds[0]&&lng<=p.bounds[2]&&lat>=p.bounds[1]&&lat<=p.bounds[3])result.push({name:d.name,provider:p,extra});
    }return result;
  }
  private async queryWms(queries:ReturnType<TerritoryController['wmsQueries']>,lng:number,lat:number,m:AtlasMap){
    this.reset();const controller=this.controller=new AbortController();this.card('Elementos del mapa','Consulta cartográfica','<p role="status">Consultando las capas activas…</p>','Datos de los servicios oficiales seleccionados.');
    const x=6378137*lng*Math.PI/180,y=6378137*Math.log(Math.tan(Math.PI/4+lat*Math.PI/360)),r=156543.033928/2**m.getZoom()*7/(displayRegion(toAtlas([lng,lat]))?.scale||1);
    const results:string[]=[];
    // Bound concurrency even when several cadastral families are enabled together.
    for(let start=0;start<queries.length;start+=4){const batch=await Promise.all(queries.slice(start,start+4).map(async({name,provider:p,extra})=>{
      const heading=`<h4>${esc(name)}</h4><p class="data-note">${esc(p.credit)}</p>`;
      if(!p.queryable)return `<article>${heading}<p>El servicio no ofrece consulta de atributos para esta capa.</p></article>`;
      const params=new URLSearchParams({SERVICE:'WMS',VERSION:'1.3.0',REQUEST:'GetFeatureInfo',LAYERS:p.layers,QUERY_LAYERS:p.layers,STYLES:p.styles||'',CRS:'EPSG:3857',BBOX:`${x-r},${y-r},${x+r},${y+r}`,WIDTH:'101',HEIGHT:'101',I:'50',J:'50',INFO_FORMAT:p.infoFormat||'application/json',FEATURE_COUNT:'8',FORMAT:'image/png',...extra});
      try{const response=await fetch(p.url+'?'+params,{signal:AbortSignal.any([controller.signal,AbortSignal.timeout(15000)])});if(!response.ok)throw new Error('HTTP '+response.status);let content='';
        if(p.infoFormat==='application/json'){const json=await response.json();content=(json.features||[]).map((f:Feature)=>this.facts(f.properties||{})).join('');}
        else{const doc=new DOMParser().parseFromString(await response.text(),'text/html');const tables=Array.from(doc.querySelectorAll('table')).map(table=>Array.from(table.querySelectorAll('tr')).map(tr=>Array.from(tr.querySelectorAll('th,td')).map(c=>c.textContent?.trim()).filter(Boolean).join(': ')).filter(Boolean).join('\n')).filter(Boolean);doc.querySelectorAll('script,style,nav,header,footer').forEach(el=>el.remove());content=`<p class="source-response">${esc((tables.join('\n')||doc.body.textContent?.trim()||'').slice(0,12000))}</p>`;}
        return `<article>${heading}${content||'<p>No hay un elemento identificado en este punto.</p>'}<a href="${esc(p.url)}" target="_blank" rel="noopener">Servicio de origen ↗</a></article>`;
      }catch{return `<article>${heading}<p>La consulta no ha respondido. Puedes acercarte al elemento y volver a pulsar. La imagen puede seguir visible.</p></article>`;}
    }));if(controller.signal.aborted)return;results.push(...batch);}
    if(!controller.signal.aborted)this.card('Elementos del mapa','Consulta cartográfica','<div id="object-results">'+results.join('')+'</div>','Atributos de origen. Cada capa mantiene su cobertura y su fecha.');
  }
  async mountSearch(root:HTMLElement){
    root.innerHTML='<p data-geosearch-loading role="status">Cargando municipios y divisiones…</p>';
    let index:TerritoryIndex,comarcas:FeatureCollection;
    try{[index,comarcas]=await Promise.all([this.index(),this.comarcas()]);}catch{root.innerHTML='<p>No se pudo cargar el buscador territorial.</p><button id="territory-retry">Reintentar</button>';root.querySelector('#territory-retry')!.addEventListener('click',()=>this.mountSearch(root));return;}
    // The drawer may have been replaced while its index was loading.
    if(!root.isConnected||!root.querySelector('[data-geosearch-loading]'))return;
    root.innerHTML=`<label class="field-label">Buscar en<select id="geo-search-kind"><option value="territories">Municipios, comarcas y divisiones</option><option value="addresses">Direcciones y lugares · CartoCiudad</option></select></label><input type="search" id="place-search" placeholder="Municipio, código INE o lugar…" aria-label="Buscar territorio o dirección" autocomplete="off"><label class="field-label" id="island-filter-label">Ámbito insular<select id="island-filter"><option value="">Todas las islas y península</option>${index.islands.map(i=>`<option value="${i.id}">${esc(i.name)}</option>`).join('')}</select></label><p class="data-note">${index.municipalities.length.toLocaleString('es-ES')} municipios · relación INE ${index.referenceDate}. La geometría conserva la fecha del servicio IGN.</p><div id="place-results" class="place-results" role="status"></div>`;
    const input=root.querySelector<HTMLInputElement>('#place-search')!,kind=root.querySelector<HTMLSelectElement>('#geo-search-kind')!,island=root.querySelector<HTMLSelectElement>('#island-filter')!,results=root.querySelector<HTMLElement>('#place-results')!;
    let timer:ReturnType<typeof setTimeout>,generation=0;
    const draw=()=>{clearTimeout(timer);this.searchController?.abort();const turn=++generation;const q=normalize(input.value.trim());if(!q){results.innerHTML='';return;}
      if(kind.value==='addresses'){results.innerHTML='<p class="data-note">Consultando CartoCiudad…</p>';if(q.length<3){results.textContent='Escribe al menos tres caracteres.';return;}timer=setTimeout(()=>this.addressSearch(input.value,results,()=>turn===generation&&root.isConnected),400);return;}
      const terms=q.split(/\s+/).filter(Boolean);const matched=index.municipalities.filter(m=>(!island.value||m.islandId===island.value)&&terms.every(t=>normalize([m.name,m.cartographicName,m.code].join(' ')).includes(t))).sort((a,b)=>Number(normalize(b.name)===q)-Number(normalize(a.name)===q)||Number(normalize(b.name).startsWith(q))-Number(normalize(a.name).startsWith(q))||a.name.localeCompare(b.name,'es')).slice(0,25);
      const extras=island.value?[]:[...this.options.provinces.features.map(f=>({f,kind:'province'})),...this.options.communities.features.map(f=>({f,kind:'community'})),...comarcas.features.map(f=>({f,kind:'comarca'}))].filter(({f})=>terms.every(t=>normalize(String(f.properties?.name||'')).includes(t))).slice(0,10);
      results.innerHTML=matched.map((m,i)=>`<button class="search-result" data-municipality="${i}"><span>${esc(m.name)}<small>Municipio · ${m.code} · ${esc(this.options.provinces.features.find(f=>f.properties?.code===m.provinceCode)?.properties?.name)}</small></span></button>`).join('')+extras.map(({f,kind},i)=>`<button class="search-result" data-division="${i}"><span>${esc(f.properties?.name)}<small>${esc(kind==='province'?'Provincia / ciudad autónoma':kind==='community'?'Comunidad / ciudad autónoma':f.properties?.kind)}</small></span></button>`).join('')||'<p class="data-note">Sin coincidencias. Para calles y lugares, selecciona CartoCiudad.</p>';
      results.querySelectorAll<HTMLButtonElement>('[data-municipality]').forEach(b=>b.onclick=()=>{this.options.closeDrawer();void this.municipality(matched[Number(b.dataset.municipality)],true);});
      results.querySelectorAll<HTMLButtonElement>('[data-division]').forEach(b=>b.onclick=()=>{const entry=extras[Number(b.dataset.division)];this.options.closeDrawer();if(entry.kind==='comarca'){this.showSelection(entry.f);const p=entry.f.properties!;this.card(p.name,p.kind,this.facts(p),'Cartografía autonómica; captura de 2026-11-09.');const box=coordinatesExtent(projectFeature(entry.f).geometry);this.mapFor(box[0]).fitBounds(box,{padding:45,pitch:0,duration:600});}else{this.reset();this.options.selectLegacy(entry.f as LegacyFeature,entry.kind as 'province'|'community');}});
    };
    input.oninput=draw;kind.onchange=()=>{root.querySelector<HTMLElement>('#island-filter-label')!.hidden=kind.value==='addresses';draw();};island.onchange=draw;input.onkeydown=e=>{if(e.key==='Enter')results.querySelector<HTMLButtonElement>('button')?.click();if(e.key==='ArrowDown')results.querySelector<HTMLButtonElement>('button')?.focus();};input.focus();
  }
  private async addressSearch(text:string,root:HTMLElement,current:()=>boolean){
    this.searchController?.abort();const controller=this.searchController=new AbortController();
    try{
      const response=await fetch('https://www.cartociudad.es/geocoder/api/geocoder/candidates?'+new URLSearchParams({q:text,limit:'8',countrycodes:'es'}),{signal:AbortSignal.any([controller.signal,AbortSignal.timeout(12000)])});if(!response.ok)throw new Error();const data=await response.json() as {id:string;type:string;address:string;muni?:string}[];if(!current())return;
      root.innerHTML=data.map((c,i)=>`<button class="search-result" data-address="${i}"><span>${esc(c.address)}<small>${esc(c.type)} · ${esc(c.muni)}</small></span></button>`).join('')||'<p class="data-note">CartoCiudad no devuelve candidatos para esta búsqueda.</p>';
      root.querySelectorAll<HTMLButtonElement>('[data-address]').forEach(b=>b.onclick=async()=>{const candidate=data[Number(b.dataset.address)];this.options.closeDrawer();this.reset();this.card(candidate.address,'CartoCiudad','<p role="status">Localizando…</p>','IGN y colaboradores');try{const response=await fetch('https://www.cartociudad.es/geocoder/api/geocoder/find?'+new URLSearchParams({id:candidate.id,type:candidate.type}),{signal:AbortSignal.timeout(12000)});if(!response.ok)throw new Error();const found=await response.json();if(!validSpanishCoordinate(found.lng,found.lat))throw new Error();const feature:Feature={type:'Feature',properties:{name:found.address},geometry:{type:'Point',coordinates:[found.lng,found.lat]}};this.showSelection(feature);this.mapFor([found.lng,found.lat]).flyTo({center:toAtlas([found.lng,found.lat]) as [number,number],zoom:16,pitch:0,duration:650});this.card(found.address||candidate.address,'Dirección / lugar oficial',this.facts({'Municipio':found.muni,'Código municipal':found.muniCode,'Provincia':found.province,'Código postal':found.postalCode,'Tipo':candidate.type,'Longitud':found.lng,'Latitud':found.lat}),'<a href="https://www.cartociudad.es/" target="_blank" rel="noopener">CartoCiudad ↗</a> · IGN y colaboradores · CC BY 4.0.');}catch{this.card(candidate.address,'CartoCiudad','<p>No se pudo obtener una coordenada válida. Puedes repetir la búsqueda.</p>','No se sitúa el resultado en coordenadas cero.');}});
    }catch{if(current()&&!controller.signal.aborted)root.innerHTML='<p class="data-note">CartoCiudad no responde. La búsqueda local de municipios continúa disponible.</p>';}
  }
}
