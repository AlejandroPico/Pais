import * as maplibregl from 'maplibre-gl';
import {type Map as AtlasMap,type ExpressionSpecification,type StyleSpecification} from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import {createIcons,Search,ChevronDown,ChevronRight,X,ArrowUpRight,MapPin,Mountain,Map,Play,Pause,Info,Download,Users,Waves,TrainFront,Route,Footprints,LocateFixed,SlidersHorizontal,ExternalLink,Database,ChartNoAxesCombined,Github,Wallet,BriefcaseBusiness,HeartHandshake,House,Factory,Landmark,FileCheck,GraduationCap,FlaskConical,HeartPulse,Wheat,Trees,CloudSun,Sailboat,Recycle,Zap,Wifi,Luggage,LibraryBig,Vote,Building2,Shield,Palette,Maximize,Minimize,Ellipsis,Check} from 'lucide';
import packageInfo from '../package.json';
import {formatValue,labels,normalize,scales,units,valueFor,type Metric,type Population,type Properties} from './data';
import {overlays} from './sources';
import {categories} from './categories';
import {TerritoryController} from './territory';
import {DemographyController,type StatisticsKind} from './demography';
import {territoryLayers} from './territory-config';
import {toAtlas,fromAtlas,projectFeature,projectCollection,ATLAS_BOUNDS,shiftedIds,displayRegion} from './atlas-coordinates';
import {registerAtlasProtocol,atlasTileUrl,addShiftedLayer,addAtlasSeparation} from './atlas-geography';
import './style.css';
import type {Feature,FeatureCollection,MultiPolygon} from 'geojson';

registerAtlasProtocol();maplibregl.setWorkerUrl(workerUrl);maplibregl.setWorkerCount(2);
const $=<T extends HTMLElement=HTMLElement>(q:string)=>document.querySelector<T>(q)!;
const icon=(name:string,cls='')=>`<i data-lucide="${name}" class="${cls}" aria-hidden="true"></i>`;
const icons=()=>createIcons({icons:{Search,ChevronDown,ChevronRight,X,ArrowUpRight,MapPin,Mountain,Map,Play,Pause,Info,Download,Users,Waves,TrainFront,Route,Footprints,LocateFixed,SlidersHorizontal,ExternalLink,Database,ChartNoAxesCombined,Github,Wallet,BriefcaseBusiness,HeartHandshake,House,Factory,Landmark,FileCheck,GraduationCap,FlaskConical,HeartPulse,Wheat,Trees,CloudSun,Sailboat,Recycle,Zap,Wifi,Luggage,LibraryBig,Vote,Building2,Shield,Palette,Maximize,Minimize,Ellipsis,Check}});
const esc=(s:unknown)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
type Geo=FeatureCollection<MultiPolygon,Properties>;
let map:AtlasMap,maps:AtlasMap[]=[],geography:TerritoryController;
const statistics={} as Record<StatisticsKind,DemographyController>;
const statisticCategories={demography:'F02',welfare:'F03',labor:'F04'} as const;
const statisticControllers=()=>Object.values(statistics);
function disableStatistics(except?:StatisticsKind){
  for(const [kind,controller] of Object.entries(statistics)){
    if(kind!==except)controller.disable();
  }
}
let provinces:Geo,communities:Geo,population:Population;
let ready=false,years:number[]=[],drawerTab='',expanded=false;
const hash=new URLSearchParams(location.hash.slice(1));const compatibleLayout=hash.get('atlas')==='2';let overviewInitialized=false;
let year=Number(hash.get('year'))||2021;
let metric:Metric=(['population','density','women','change'].includes(hash.get('metric')||'')?hash.get('metric'):'density') as Metric;
let thematic=hash.get('data')==='1',level:'province'|'community'=hash.get('level')==='community'?'community':'province';
let base=['terrain','satellite','street'].includes(hash.get('base')||'')?hash.get('base')!:'satellite';
let tilted=hash.get('flat')!=='1',opacity=.73;
let selected:Feature<MultiPolygon,Properties>|undefined;
const active=new Set((hash.get('layers')||'').split(',').filter(id=>overlays.some(o=>o.id===id)||territoryLayers.some(o=>o.id===id)));
const overlayOpacity:Record<string,number>={};
let showCommunities=hash.get('ccaa')==='1',showProvinces=hash.get('provinces')==='1';
let playing:ReturnType<typeof setInterval>|undefined,modalController:AbortController|undefined;
let priorFocus:HTMLElement|null=null,featureQuery:AbortController|undefined;
const sourceErrors=new Set<string>();
const railButton=(id:string,name:string,glyph:string)=>`<button class="rail-btn" id="${id}" title="${name}" aria-label="${name}">${icon(glyph)}<span class="rail-label">${name}</span></button>`;
$('#app').innerHTML=`<div class="workspace"><nav class="rail" aria-label="Menú principal">
<button id="brand-menu" class="rail-brand" aria-label="El país · Ampliar menú" aria-expanded="false"><img src="${import.meta.env.BASE_URL}favicon.svg" alt="" width="36" height="36"><span class="rail-label">El país</span></button>
${railButton('filters-open','Filtros','sliders-horizontal')}${railButton('search-open','Buscar','search')}
<div class="category-nav" aria-label="Categorías de capas">${categories.map(c=>`<button class="rail-btn category-btn" data-category="${c.id}" aria-label="${esc(c.name)}" title="${esc(c.name)}" aria-expanded="false" aria-controls="drawer">${icon(c.icon)}<span class="rail-label">${esc(c.name)}</span><span class="compact-label">${c.short}</span>${icon('chevron-right','category-arrow')}</button>`).join('')}</div>
<button id="more-categories" class="rail-btn" title="Todas las categorías" aria-label="Todas las categorías">${icon('ellipsis')}</button><div class="rail-bottom">
${railButton('home-map','Vista general','locate-fixed')}${railButton('appearance-open','Tema y mapa','palette')}<button class="rail-btn" id="terrain-toggle" title="Terreno 3D" aria-label="Terreno 3D" aria-pressed="true"><b>3D</b><span class="rail-label">Terreno 3D</span></button>${railButton('fullscreen','Pantalla completa','maximize')}${railButton('sources-open','Fuentes','database')}${railButton('about-open','Acerca de','info')}</div></nav>
<main class="map-area" aria-label="Mapa de España"><div id="map" aria-label="Mapa interactivo. Arrastra para desplazarte. Rueda o pellizco para ampliar. Doble clic derecho para orientar al norte."></div><section id="info-panel" class="info-panel" aria-label="Información del territorio" hidden></section><div id="legend" class="legend" hidden></div><div id="overlay-legend" class="overlay-legend" hidden></div><div id="map-status" class="map-status" role="status">Preparando cartografía…</div>
<section id="timeline" class="timeline" aria-label="Evolución temporal" hidden><button id="play" aria-label="Reproducir evolución">${icon('play')}</button><div class="timeline-label"><small>PADRÓN · INE</small><strong id="year-value">2021</strong></div><div class="timeline-track"><input id="year" type="range" min="0" max="24" step="1" aria-label="Año de los datos"><div class="timeline-ticks"><span>1996</span><span>2005</span><span>2013</span><span>2021</span></div></div><button id="timeline-info" class="icon-button" aria-label="Información de la serie">${icon('info')}</button></section></main>
<aside id="drawer" class="drawer" aria-labelledby="drawer-title" hidden><header class="drawer-head"><h1 id="drawer-title"></h1><button id="drawer-close" class="icon-button" aria-label="Cerrar panel">${icon('x')}</button></header><div id="drawer-content" class="drawer-content"></div></aside></div><div id="toast" class="toast" role="status" hidden></div><dialog id="modal" aria-labelledby="modal-title"><header class="modal-top"><span>EL PAÍS</span><button id="modal-close" class="icon-button" aria-label="Cerrar ventana">${icon('x')}</button></header><div id="modal-body"></div></dialog>`;

let toastTimeout:ReturnType<typeof setTimeout>;
function toast(message:string){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>$('#toast').hidden=true,6000);}
function syncUrl(){if(!ready)return;const c=map.getCenter();history.replaceState(null,'','#'+new URLSearchParams({atlas:'2',base,metric,year:String(year),level,data:thematic?'1':'0',flat:tilted?'0':'1',lng:c.lng.toFixed(4),lat:c.lat.toFixed(4),z:map.getZoom().toFixed(2),layers:[...active].join(','),ccaa:showCommunities?'1':'0',provinces:showProvinces?'1':'0',...geography?.urlState(),...Object.assign({},...statisticControllers().map(controller=>controller.urlState()))}));}
function extent(f:Feature<MultiPolygon,Properties>):[[number,number],[number,number]]{const p=f.geometry.coordinates.flat(2);return [[Math.min(...p.map(p=>p[0])),Math.min(...p.map(p=>p[1]))],[Math.max(...p.map(p=>p[0])),Math.max(...p.map(p=>p[1]))]];}
function home(duration=500){if(!ready)return;map.fitBounds(ATLAS_BOUNDS,{padding:{top:24,right:24,bottom:35,left:24},pitch:0,bearing:0,duration});}
function fitOverview(){const camera=map.cameraForBounds(ATLAS_BOUNDS,{padding:{top:24,right:24,bottom:35,left:24}});if(!camera)return;const wasHome=map.getZoom()<=map.getMinZoom()+.05;map.setMinZoom(camera.zoom||3);if(wasHome||!overviewInitialized)map.jumpTo({...camera,bearing:0,pitch:0});overviewInitialized=true;}
function selectedGeo(){return level==='province'?provinces:communities;}
function openModal(html:string){priorFocus=document.activeElement as HTMLElement;modalController?.abort();modalController=new AbortController();$('#modal-body').innerHTML=html;const d=$<HTMLDialogElement>('#modal');if(!d.open)d.showModal();icons();}
function closeModal(){$<HTMLDialogElement>('#modal').close();}
async function showCatalog(category?:string){closeDrawer();openModal('<h2 id="modal-title">Fuentes</h2><p role="status">Cargando registro…</p>');const signal=modalController!.signal;try{const {mountCatalog}=await import('./catalog');if(!signal.aborted)await mountCatalog($('#modal-body'),{category,signal,icons,activate:action=>{activateProduct(action);closeModal();}});}catch{if(!signal.aborted){$('#modal-body').innerHTML='<h2 id="modal-title">Fuentes</h2><p>No se pudo cargar el registro.</p><button id="registry-retry">Reintentar</button>';$('#registry-retry').onclick=()=>showCatalog(category);}}}
function about(){closeDrawer();openModal(`<div class="about-brand"><img src="${import.meta.env.BASE_URL}favicon.svg" alt="" width="72" height="72"><div><h2 id="modal-title">El país</h2><span>Versión ${packageInfo.version}</span></div></div><p class="modal-lead">Atlas de España basado en datos públicos.</p><p>Reunir y organizar la información de organismos estatales, autonómicos y locales para consultarla sobre un mismo mapa, combinar capas y recorrer sus series históricas.</p><h3>Esta versión</h3><p>Ortofoto, relieve elevado, callejero y cartografía oficial. Búsqueda de los 8.132 municipios de 2026 y direcciones oficiales. Municipios, poblaciones, comarcas con cobertura identificada, secciones censales, límites históricos, edificios y catastro estatal y foral. Vista general compacta de España sin países vecinos, con marcos para Canarias, Ceuta, Melilla y otros territorios. Las ampliaciones de escala se indican en cada marco; consultas y descargas conservan su localización real. F02: censos anuales con edad, sexo, nacionalidad y nacimiento; hogares, movimiento natural, migraciones e indicadores demográficos. Series y pirámides consultables, detalle municipal por provincia y descargas con procedencia. F03: renta del Atlas y encuestas, pobreza y desigualdad, carencias, gasto familiar y bienestar subjetivo, conservando unidades y definiciones. F04: empleo y paro de la EPA, distribución salarial, costes, jornada y vacantes. Padrón histórico conservado por separado, hidrografía y transporte. Catálogo común de fuentes, productos y cobertura.</p><h3>El proyecto</h3><p>Una base común y 29 fascículos temáticos: territorio, población, salud, vivienda, naturaleza, energía, cultura y organización pública, entre otros. Cada producto conserva su procedencia, cobertura, fechas y estado de integración.</p><p>Los catálogos describen lo encontrado; solo los productos disponibles se pueden activar en el mapa. Las nuevas familias se incorporarán progresivamente.</p><div class="about-author"><span>Creado por</span><strong>Alejandro Pico</strong></div><div class="about-links"><a href="https://alejandropico.github.io/Portfolio/" target="_blank" rel="noopener">Portfolio ${icon('arrow-up-right')}</a><a href="https://github.com/AlejandroPico/Pais" target="_blank" rel="noopener">${icon('github')} Repositorio ${icon('arrow-up-right')}</a></div>`);}
function seriesInfo(){openModal(`<h2 id="modal-title">Serie histórica</h2><p>${esc(population?.note||'Padrón municipal del INE.')}</p><ul><li>Tablas INE 2852 y 2853. Datos a 1 de enero, 1996–2021; no hay observación de 1997.</li><li>Los límites actuales no reconstruyen las fronteras históricas. La superficie y la densidad son aproximadas.</li><li>El cronograma modifica la estadística seleccionada. Cada mapa base o red conserva su propia fecha.</li></ul><a href="https://www.ine.es/jaxiT3/Tabla.htm?t=2852" target="_blank" rel="noopener">Consultar el origen ↗</a>`);}
function download(name:string,content:string,type:string){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function expandRail(next=!expanded){expanded=next;$('.workspace').classList.toggle('expanded',expanded);$('#brand-menu').setAttribute('aria-expanded',String(expanded));$('#brand-menu').setAttribute('aria-label',`El país · ${expanded?'Contraer':'Ampliar'} menú`);setTimeout(()=>maps.forEach(m=>m.resize()),200);}
function closeDrawer(){drawerTab='';$('#drawer').hidden=true;document.querySelectorAll<HTMLElement>('[data-category]').forEach(b=>{b.setAttribute('aria-expanded','false');b.classList.remove('active');});}
function openDrawer(tab:string,title:string,html:string){if(drawerTab===tab){closeDrawer();return;}closeDrawer();if(innerWidth<760&&expanded)expandRail(false);drawerTab=tab;$('#drawer-title').textContent=title;$('#drawer-content').innerHTML=html;$('#drawer').hidden=false;$('#drawer-content').scrollTop=0;document.querySelector(`[data-category="${tab}"]`)?.setAttribute('aria-expanded','true');document.querySelector(`[data-category="${tab}"]`)?.classList.add('active');icons();bindControls();}
function overlayRow(o:typeof overlays[number]){return `<div class="overlay-entry"><label class="check-row"><input type="checkbox" data-overlay="${o.id}" ${active.has(o.id)?'checked':''}><span>${esc(o.name)}</span></label><p class="data-note">${esc(o.note)}</p><label class="opacity-control">Opacidad<input type="range" min="10" max="100" value="${100*(overlayOpacity[o.id]??.85)}" data-opacity="${o.id}" aria-label="Opacidad de ${esc(o.name)}"></label></div>`;}
function baseOptions(){return `<div class="base-options">${[['satellite','Ortofoto'],['terrain','Relieve'],['street','Callejero']].map(([id,name])=>`<button data-base="${id}" aria-pressed="${base===id}">${name}</button>`).join('')}</div>`;}
function categoryPanel(id:string){const c=categories.find(c=>c.id===id)!;let html='';
  if(id==='F01')html=`<details class="submenu" open><summary>Mapa base <span aria-hidden="true">›</span></summary>${baseOptions()}<p class="data-note">Terreno 3D: modelo oficial IGN. La cámara puede mantenerse vertical.</p></details><details class="submenu" open><summary>Comunidades y provincias <span aria-hidden="true">›</span></summary><label class="check-row"><input id="communities-toggle" type="checkbox" ${showCommunities?'checked':''}><span>Comunidades autónomas</span><span class="line-sample community-line"></span></label><label class="check-row"><input id="provinces-toggle" type="checkbox" ${showProvinces?'checked':''}><span>Provincias</span><span class="line-sample province-line"></span></label></details>${geography?.panel()||'<p>Preparando cartografía…</p>'}`;
  else if(id==='F03'||id==='F04')html='<div id="statistics-panel"></div>';
  else if(id==='F02')html=`<div id="demography-panel"></div><details class="submenu"><summary>Padrón histórico · INE ${icon('chevron-right')}</summary>${(['population','density','women','change'] as Metric[]).map(m=>`<label class="check-row"><input type="radio" name="metric" value="${m}" ${thematic&&metric===m?'checked':''}><span>${labels[m]}</span></label>`).join('')}<button id="clear-metric" class="text-button">Desactivar población</button><label class="field-label">División territorial<select id="level"><option value="province" ${level==='province'?'selected':''}>Provincias</option><option value="community" ${level==='community'?'selected':''}>Comunidades</option></select></label><p class="data-note">1996–2021, sin 1997. No es la población más reciente.</p></details>`;
  const ids=id==='F16'?['rivers']:id==='F22'?['rail','roads','camino']:['F24','F26'].includes(id)?['camino']:[];
  if(ids.length)html+=`<details class="submenu" open><summary>Capas disponibles ${icon('chevron-right')}</summary>${overlays.filter(o=>ids.includes(o.id)).map(overlayRow).join('')}</details>`;
  if(!html)html='<p class="panel-note">Las capas de esta categoría están pendientes de integración. Puedes consultar los productos y fuentes inventariados.</p>';
  html+=`<button class="catalog-category" data-open-catalog="${id}">${icon('database')} Productos y cobertura ${icon('chevron-right')}</button>`;openDrawer(id,c.name,html);
}
function filtersPanel(){openDrawer('filters','Filtros',`<p class="panel-note" id="filter-summary">${active.size+Number(thematic)+statisticControllers().filter(controller=>controller.active).length+Number(showCommunities)+Number(showProvinces)} capas activas</p><button id="clear-all" class="wide-button">Desactivar todas las capas</button><details class="submenu" open><summary>Buscar una capa ${icon('chevron-right')}</summary><input id="layer-search" type="search" placeholder="Nombre o categoría…" aria-label="Buscar capas"><div id="layer-matches"></div></details><p class="data-note">Las opciones de cada indicador están dentro de su categoría.</p>`);if(!$('#clear-all'))return;$('#clear-all').onclick=()=>{active.clear();disableStatistics();thematic=false;showCommunities=false;showProvinces=false;stopPlaying();updateData();$('#filter-summary').textContent='0 capas activas';};$('#layer-search').oninput=()=>{const q=normalize($<HTMLInputElement>('#layer-search').value);$('#layer-matches').innerHTML=q?categories.filter(c=>normalize(c.name).includes(q)).map(c=>`<button data-match="${c.id}" class="search-result">${esc(c.name)} ${icon('chevron-right')}</button>`).join(''):'';document.querySelectorAll<HTMLButtonElement>('[data-match]').forEach(b=>b.onclick=()=>categoryPanel(b.dataset.match!));icons();};}
function appearancePanel(){openDrawer('appearance','Tema y mapa',`<details class="submenu" open><summary>Mapa base ${icon('chevron-right')}</summary>${baseOptions()}</details><details class="submenu" open><summary>Interfaz ${icon('chevron-right')}</summary><div class="base-options">${[['auto','Automático'],['dark','Oscuro'],['light','Claro']].map(([id,name])=>`<button data-theme="${id}" aria-pressed="${theme===id}">${name}</button>`).join('')}</div></details><p class="data-note">Arrastra para desplazarte. Usa la rueda o pellizca para ampliar. Doble clic derecho para orientar al norte.</p>`);}
function bindControls(){
  geography?.bind($('#drawer-content'));
  if($('#demography-panel')&&statistics.demography)void statistics.demography.mount($('#demography-panel'));
  const panel=$('#statistics-panel');
  if(panel)void statistics[drawerTab==='F04'?'labor':'welfare']?.mount(panel);
  document.querySelectorAll<HTMLButtonElement>('[data-base]').forEach(b=>b.onclick=()=>setBase(b.dataset.base!));document.querySelectorAll<HTMLButtonElement>('[data-theme]').forEach(b=>b.onclick=()=>{theme=b.dataset.theme!;try{localStorage.setItem('pais-theme',theme);}catch{}applyTheme();});
  document.querySelectorAll<HTMLButtonElement>('[data-open-catalog]').forEach(b=>b.onclick=()=>showCatalog(b.dataset.openCatalog));
  $('#communities-toggle')?.addEventListener('change',e=>{showCommunities=(e.target as HTMLInputElement).checked;updateData();});$('#provinces-toggle')?.addEventListener('change',e=>{showProvinces=(e.target as HTMLInputElement).checked;updateData();});
  document.querySelectorAll<HTMLInputElement>('[name="metric"]').forEach(i=>i.onchange=()=>{disableStatistics();metric=i.value as Metric;thematic=true;updateData();});$('#clear-metric')?.addEventListener('click',()=>{thematic=false;stopPlaying();updateData();document.querySelectorAll<HTMLInputElement>('[name="metric"]').forEach(i=>i.checked=false);});
  $('#level')?.addEventListener('change',e=>{level=(e.target as HTMLSelectElement).value as typeof level;selected=undefined;$('#info-panel').hidden=true;updateData();});
  document.querySelectorAll<HTMLInputElement>('[data-overlay]').forEach(i=>i.onchange=()=>{i.checked?active.add(i.dataset.overlay!):active.delete(i.dataset.overlay!);updateData();if(i.dataset.overlay==='municipal'&&i.checked&&ready&&map.getZoom()<8)toast('Los límites municipales aparecen al acercar el mapa.');});
  document.querySelectorAll<HTMLInputElement>('[data-opacity]').forEach(i=>i.oninput=()=>{overlayOpacity[i.dataset.opacity!]=Number(i.value)/100;for(const m of maps)for(const id of [i.dataset.opacity!,...shiftedIds(i.dataset.opacity!)])if(m.getLayer(id))m.setPaintProperty(id,'raster-opacity',overlayOpacity[i.dataset.opacity!]);});
}
function setBase(next:string){base=next;for(const m of maps)for(const b of ['terrain','satellite','street'])if(m.getLayer(`base-${b}`))m.setLayoutProperty(`base-${b}`,'visibility',b===base?'visible':'none');document.querySelectorAll<HTMLElement>('[data-base]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.base===base)));syncUrl();}
function terrain(){for(const m of maps)if(m.getSource('dem'))m.setTerrain(tilted?{source:'dem',exaggeration:1.3}:null);$('#terrain-toggle').setAttribute('aria-pressed',String(tilted));syncUrl();}
function activateProduct(action:string){const [kind,id]=action.split(':');
  if(Object.hasOwn(statisticCategories,kind)){
    const statisticKind=kind as StatisticsKind;
    thematic=false;
    stopPlaying();
    void statistics[statisticKind].useTable(Number(id));
    categoryPanel(statisticCategories[statisticKind]);
    return;
  }
  if(action.startsWith('territory:')){active.add(action.slice(10));geography?.update();updateData();return;}if(action==='search:addresses'){closeModal();searchPanel();return;}if(action.startsWith('base:'))setBase(action.slice(5));else if(action.startsWith('metric:')){disableStatistics();metric=action.slice(7) as Metric;thematic=true;}else if(action.startsWith('overlay:'))active.add(action.slice(8));else if(action==='communities')showCommunities=true;else if(action==='provinces')showProvinces=true;else if(action==='terrain'){tilted=true;terrain();}updateData();}
function updateData(){if(!ready)return;
  for(const m of maps){if(!m.getLayer('province-fill'))continue;for(const l of ['province','community'] as const){const geo=l==='province'?provinces:communities;if(thematic&&l===level)for(const f of geo.features){const value=valueFor(population.data[l][f.properties.code],year,metric,f.properties.areaKm2);m.setFeatureState({source:l,id:f.id!},{value:value??-999999,missing:value===null});}const scale=scales[metric];const color=['interpolate',['linear'],['feature-state','value'],...scale.stops.flatMap((stop,i)=>[stop,scale.colors[i]])] as ExpressionSpecification;m.setPaintProperty(`${l}-fill`,'fill-color',['case',['boolean',['feature-state','missing'],true],'#b8b6aa',color]);m.setPaintProperty(`${l}-fill`,'fill-opacity',thematic&&l===level?opacity:0);}m.setLayoutProperty('province-lines','visibility',showProvinces?'visible':'none');m.setLayoutProperty('community-lines','visibility',showCommunities?'visible':'none');for(const o of overlays){m.setLayoutProperty(o.id,'visibility',active.has(o.id)?'visible':'none');for(const id of shiftedIds(o.id))if(m.getLayer(id))m.setLayoutProperty(id,'visibility',active.has(o.id)?'visible':'none');}(m.getSource('selection') as maplibregl.GeoJSONSource).setData(selected?projectFeature(selected):{type:'FeatureCollection',features:[]});}
  geography?.update();
  $('#timeline').hidden=!thematic;$('#legend').hidden=!thematic;
  if(thematic){const s=scales[metric];$('#legend').innerHTML=`<div class="legend-title"><strong>${labels[metric]}</strong><span>${year}</span></div><p>${units[metric]} · ${level==='province'?'provincias':'comunidades'}</p><div class="color-scale" style="background:linear-gradient(90deg,${s.colors.join(',')})"></div><div class="scale-labels"><span>${formatValue(s.stops[0],metric)}</span><span>≥ ${formatValue(s.stops[6],metric)}</span></div><label class="opacity-control">Opacidad<input id="thematic-opacity" type="range" min="10" max="100" value="${opacity*100}" aria-label="Opacidad estadística"></label><p class="legend-credit">Sin datos: gris · INE / IGN</p>`;$('#thematic-opacity').oninput=e=>{opacity=Number((e.target as HTMLInputElement).value)/100;for(const m of maps)if(m.getLayer(`${level}-fill`))m.setPaintProperty(`${level}-fill`,'fill-opacity',opacity);};}
  $('#year-value').textContent=String(year);const slider=$<HTMLInputElement>('#year');slider.max=String(years.length-1);slider.value=String(years.indexOf(year));slider.setAttribute('aria-valuetext',String(year));const enabled=[...overlays.filter(o=>active.has(o.id)).map(o=>o.name),...geography.activeLabels()];$('#overlay-legend').hidden=!enabled.length;$('#overlay-legend').textContent=enabled.join(' · ');if(selected)renderInfo();syncUrl();
}
function selectTerritory(f:Feature<MultiPolygon,Properties>,zoom=false){selected=f;for(const m of maps)if(m.getSource('selection'))(m.getSource('selection') as maplibregl.GeoJSONSource).setData(projectFeature(f));renderInfo();if(zoom){const target=map;target.fitBounds(extent(projectFeature(f)),{padding:40,maxZoom:10,pitch:0,duration:600});}}
function searchPanel(){openDrawer('search','Buscar','<div id="territory-search"></div>');const target=$('#territory-search');if(!target)return;if(ready)void geography.mountSearch(target);else target.innerHTML='<p>La búsqueda estará disponible al terminar de cargar el mapa.</p>';}


function style():StyleSpecification{return {version:8,glyphs:'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',sources:{
  terrain:{type:'raster',tiles:[atlasTileUrl('https://tms-relieve.idee.es/1.0.0/relieve/{z}/{x}/{y}.jpeg',{scheme:'tms'})],scheme:'xyz',tileSize:256,maxzoom:16,attribution:'© IGN · CC BY 4.0'},
  satellite:{type:'raster',tiles:[atlasTileUrl('https://www.ign.es/wmts/pnoa-ma?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=OI.OrthoimageCoverage&STYLE=default&FORMAT=image/jpeg&TILEMATRIXSET=GoogleMapsCompatible&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}')],tileSize:256,maxzoom:19,attribution:'PNOA © IGN y colaboradores · CC BY 4.0'},
  street:{type:'raster',tiles:[atlasTileUrl('https://www.ign.es/wmts/ign-base?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=IGNBaseTodo&STYLE=default&FORMAT=image/png&TILEMATRIXSET=GoogleMapsCompatible&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}')],tileSize:256,maxzoom:19,attribution:'© IGN y colaboradores · CC BY 4.0'},
  dem:{type:'raster-dem',tiles:[atlasTileUrl('https://xyz-mdt.idee.es/1.0.0/raster-dem/{z}/{x}/{y}.png',{size:512,dem:true})],encoding:'mapbox',tileSize:512,minzoom:5,maxzoom:15,attribution:'Modelo de elevaciones © IGN · CC BY 4.0'}
},layers:[{id:'background',type:'background',paint:{'background-color':'#0b2842'}},...['terrain','satellite','street'].map(b=>({id:`base-${b}`,type:'raster' as const,source:b,layout:{visibility:'none' as const},paint:{'raster-fade-duration':150}}))]};}
function setupMap(m:AtlasMap){
  for(const name of ['sea'])m.addSource(name,{type:'geojson',data:`${import.meta.env.BASE_URL}data/${name==='sea'?'territory/sea-atlas.geojson':name+'.geojson'}`});
  m.addLayer({id:'blue-sea',type:'fill',source:'sea',paint:{'fill-color':'#0b2842','fill-opacity':1}});
  for(const l of ['province','community'] as const){m.addSource(l,{type:'geojson',data:projectCollection(l==='province'?provinces:communities)});m.addLayer({id:`${l}-fill`,type:'fill',source:l,paint:{'fill-opacity':0,'fill-color':'#78a18a'}});}
  for(const o of overlays){const tile=`${o.url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=${encodeURIComponent(o.layers)}&STYLES=${encodeURIComponent('styles' in o?o.styles!:'')}&FORMAT=image/png&TRANSPARENT=TRUE&SRS=EPSG:3857&WIDTH=256&HEIGHT=256&BBOX={bbox-epsg-3857}`;m.addSource(o.id,{type:'raster',tiles:[tile],tileSize:256,bounds:[-18.5,27,4.7,44],attribution:'© IGN · CC BY 4.0'});m.addLayer({id:o.id,type:'raster',source:o.id,minzoom:o.minzoom||0,layout:{visibility:active.has(o.id)?'visible':'none'},paint:{'raster-opacity':overlayOpacity[o.id]??.85}});addShiftedLayer(m,m.getStyle().layers.find(l=>l.id===o.id)!);}
  const revealBase=()=>{if(m.getSource('atlas-visible-sea')&&m.isSourceLoaded('atlas-visible-sea')){for(const b of ['terrain','satellite','street'])m.setLayoutProperty('base-'+b,'visibility',b===base?'visible':'none');m.off('sourcedata',revealBase);}};m.on('sourcedata',revealBase);revealBase();
  geography.attach(m);
  m.addLayer({id:'province-lines',type:'line',source:'province',layout:{visibility:showProvinces?'visible':'none'},paint:{'line-color':'#e9e5d5','line-width':['interpolate',['linear'],['zoom'],4,.6,8,1.2,13,2],'line-opacity':.8}});m.addLayer({id:'community-lines',type:'line',source:'community',layout:{visibility:showCommunities?'visible':'none'},paint:{'line-color':'#fff8d2','line-width':['interpolate',['linear'],['zoom'],4,1.5,8,2.5,13,3.5],'line-opacity':.95}});
  m.addSource('selection',{type:'geojson',data:{type:'FeatureCollection',features:[]}});m.addLayer({id:'selected-outline',type:'line',source:'selection',paint:{'line-color':'#efd68c','line-width':2.5}});if(tilted)m.setTerrain({source:'dem',exaggeration:1.3});
  m.on('click',async e=>{if(!ready)return;if(m.queryRenderedFeatures(e.point,{layers:['atlas-opaque-sea']}).length)return;featureQuery?.abort();if(statisticControllers().some(controller=>controller.inspect(m,e)))return;delete $('#info-panel').dataset.demography;if(await geography.inspect(m,e))return;geography.reset();const features=m.queryRenderedFeatures(e.point,{layers:[`${level}-fill`]});if(features[0]){const f=selectedGeo().features.find(f=>f.properties.code===features[0].properties.code);if(f)selectTerritory(f);}else{selected=undefined;$('#info-panel').hidden=true;for(const target of maps)(target.getSource('selection') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features:[]});}const truePoint=fromAtlas([e.lngLat.lng,e.lngLat.lat]);queryObjects(truePoint[0],truePoint[1]);});
  for(const controller of statisticControllers())controller.attach(m,provinces,communities);
  addAtlasSeparation(m);
  let rightClick=0;m.getCanvas().addEventListener('contextmenu',e=>{e.preventDefault();const now=performance.now();if(now-rightClick<350){m.easeTo({bearing:0,pitch:0,duration:350});rightClick=0;}else rightClick=now;});
}
async function load<T>(file:string):Promise<T>{const r=await fetch(`${import.meta.env.BASE_URL}data/${file}`);if(!r.ok)throw new Error(`${file}: ${r.status}`);return r.json();}
async function init(){try{
  [provinces,communities,population]=await Promise.all([load<Geo>('provinces.geojson'),load<Geo>('communities.geojson'),load<Population>('population.json')]);years=Object.keys(population.data.province['00'].series).map(Number).sort((a,b)=>a-b);if(!years.includes(year))year=years.at(-1)!;
  const common={maxZoom:18,minZoom:3,dragPan:true,dragRotate:false,touchPitch:false,renderWorldCopies:false,pitch:0,attributionControl:{compact:true},maxTileCacheSize:100,fadeDuration:150};
  map=new maplibregl.Map({...common,container:'map',center:[-2.7,39.6],zoom:5.4,style:style()});maps=[map];
  const clearStatisticsSelection=()=>{
    selected=undefined;
    geography?.reset();
    for(const m of maps){
      const source=m.getSource<maplibregl.GeoJSONSource>('selection');
      source?.setData({type:'FeatureCollection',features:[]});
    }
  };
  for(const kind of Object.keys(statisticCategories) as StatisticsKind[]){
    statistics[kind]=new DemographyController({
      info:$('#info-panel'),
      onActivate:()=>{
        disableStatistics(kind);
        thematic=false;
        stopPlaying();
        document.querySelectorAll<HTMLInputElement>('[name="metric"]').forEach(input=>input.checked=false);
        selected=undefined;
        geography?.reset();
        updateData();
      },
      onChange:syncUrl,
      closeDrawer,
      clearSelection:clearStatisticsSelection,
    },kind);
  }
  geography=new TerritoryController({active,info:$('#info-panel'),icons,onChange:updateData,beforeInspect:()=>{featureQuery?.abort();selected=undefined;for(const m of maps)if(m.getSource('selection'))(m.getSource('selection') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features:[]});},closeDrawer,selectLegacy:(f,l)=>{level=l;updateData();selectTerritory(f as Feature<MultiPolygon,Properties>,true);},provinces,communities});let loaded=0;
  for(const m of maps){m.on('error',e=>{sourceErrors.add((e as unknown as {sourceId?:string}).sourceId||'map');$('#map-status').hidden=false;$('#map-status').textContent='Un servicio cartográfico no responde. Puedes cambiar el mapa base.';console.warn('Cartographic service error',e.error?.message);});m.on('load',()=>{setupMap(m);if(++loaded===1){ready=true;fitOverview();const lng=Number(hash.get('lng')),lat=Number(hash.get('lat')),z=Number(hash.get('z'));if(compatibleLayout&&hash.has('lng')&&Number.isFinite(lng)&&Number.isFinite(lat)&&Number.isFinite(z)&&lng>=-20&&lng<=7&&lat>=25.5&&lat<=46.5&&z>=3&&z<=18)map.jumpTo({center:[lng,lat],zoom:z,pitch:0});terrain();updateData();if(!sourceErrors.size)$('#map-status').hidden=true;}});}
  map.touchZoomRotate.disableRotation();map.on('moveend',()=>{const c=map.getCenter(),lng=Math.max(ATLAS_BOUNDS[0][0],Math.min(ATLAS_BOUNDS[1][0],c.lng)),lat=Math.max(ATLAS_BOUNDS[0][1],Math.min(ATLAS_BOUNDS[1][1],c.lat));if(c.lng!==lng||c.lat!==lat)map.jumpTo({center:[lng,lat],bearing:0,pitch:0});syncUrl();});new ResizeObserver(()=>{maps.forEach(m=>m.resize());if(ready)fitOverview();}).observe($('.map-area'));
}catch(error){console.error(error);$('#map-status').hidden=false;$('#map-status').innerHTML='No se pudo iniciar el mapa. <button id="retry">Reintentar</button>';$('#retry').onclick=()=>location.reload();}}

let theme='auto';try{theme=localStorage.getItem('pais-theme')||'auto';}catch{}const scheme=matchMedia('(prefers-color-scheme:dark)');
function applyTheme(){document.documentElement.dataset.theme=theme==='auto'?(scheme.matches?'dark':'light'):theme;document.querySelectorAll<HTMLElement>('[data-theme]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.theme===theme)));}
applyTheme();scheme.addEventListener('change',applyTheme);
$('#brand-menu').onclick=()=>expandRail();$('#more-categories').onclick=()=>expandRail(true);document.querySelectorAll<HTMLButtonElement>('[data-category]').forEach(b=>b.onclick=()=>categoryPanel(b.dataset.category!));
$('#drawer-close').onclick=closeDrawer;$('#filters-open').onclick=filtersPanel;$('#search-open').onclick=searchPanel;$('#appearance-open').onclick=appearancePanel;$('#sources-open').onclick=()=>showCatalog();$('#about-open').onclick=about;$('#home-map').onclick=()=>home();$('#terrain-toggle').onclick=()=>{tilted=!tilted;terrain();};$('#timeline-info').onclick=seriesInfo;
$('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{toast('La pantalla completa no está disponible en este navegador.');}};document.addEventListener('fullscreenchange',()=>{$('#fullscreen').innerHTML=icon(document.fullscreenElement?'minimize':'maximize')+'<span class="rail-label">Pantalla completa</span>';icons();maps.forEach(m=>m.resize());});
$('#modal-close').onclick=closeModal;$('#modal').addEventListener('close',()=>{modalController?.abort();priorFocus?.focus();});$('#modal').addEventListener('click',e=>{if(e.target===$('#modal')){const r=$('#modal').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeModal();}});
function stopPlaying(){clearInterval(playing);playing=undefined;$('#play').innerHTML=icon('play');$('#play').setAttribute('aria-label','Reproducir evolución');icons();}
$('#year').oninput=e=>{stopPlaying();year=years[Number((e.target as HTMLInputElement).value)];updateData();};$('#play').onclick=()=>{if(!ready)return;if(playing){stopPlaying();return;}$('#play').innerHTML=icon('pause');$('#play').setAttribute('aria-label','Pausar evolución');icons();playing=setInterval(()=>{year=years[(years.indexOf(year)+1)%years.length];updateData();},1100);};
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDrawer();if(e.key==='/'&&!(e.target as HTMLElement).matches('input,textarea,select')&&!$<HTMLDialogElement>('#modal').open){e.preventDefault();if(drawerTab==='search')$<HTMLInputElement>('#place-search').focus();else searchPanel();}});window.addEventListener('pagehide',()=>{stopPlaying();featureQuery?.abort();});
icons();init();

async function queryObjects(lng:number,lat:number){
  featureQuery?.abort();featureQuery=new AbortController();const controller=featureQuery;
  const enabled=overlays.filter(o=>active.has(o.id)&&map.getZoom()+Math.log2(displayRegion(toAtlas([lng,lat]))?.scale||1)>=(o.minzoom||0));
  if(!enabled.length)return;
  if(!selected){$('#info-panel').hidden=false;$('#info-panel').innerHTML=`<div class="info-heading"><span class="eyebrow">CONSULTA DEL MAPA</span><button id="info-close" class="icon-button" aria-label="Cerrar información">${icon('x')}</button></div><h3>En este lugar</h3><p class="data-note">${lat.toFixed(5)}, ${lng.toFixed(5)} · coordenadas del punto consultado</p>`;$('#info-close').onclick=()=>{controller.abort();$('#info-panel').hidden=true;};}
  let panel=$('#object-results');if(!panel){panel=document.createElement('div');panel.id='object-results';$('#info-panel').append(panel);}panel.innerHTML='<p class="data-note" role="status">Consultando las capas activas…</p>';
  const x=6378137*lng*Math.PI/180,y=6378137*Math.log(Math.tan(Math.PI/4+lat*Math.PI/360));
  const radius=156543.033928/2**map.getZoom()*7/(displayRegion(toAtlas([lng,lat]))?.scale||1);
  const results=await Promise.all(enabled.map(async o=>{
    const params=new URLSearchParams({SERVICE:'WMS',VERSION:'1.1.1',REQUEST:'GetFeatureInfo',LAYERS:o.layers,QUERY_LAYERS:o.layers,STYLES:'styles' in o?o.styles!:'',SRS:'EPSG:3857',BBOX:`${x-radius},${y-radius},${x+radius},${y+radius}`,WIDTH:'101',HEIGHT:'101',X:'50',Y:'50',INFO_FORMAT:'application/json',FEATURE_COUNT:'4',FORMAT:'image/png'});
    try{
      const response=await fetch(`${o.url}?${params}`,{signal:AbortSignal.any([controller.signal,AbortSignal.timeout(12000)])});if(!response.ok)throw new Error('Service response');
      const data=await response.json();
      const features=Array.isArray(data.features)?data.features:[];
      return `<article><h4>${icon(o.icon)}${o.name}</h4>${features.length?features.map((f:{properties?:Record<string,unknown>})=>{const pairs=Object.entries(f.properties||{}).filter(([,v])=>v!==null&&typeof v!=='object');return `<details><summary>Ver atributos del elemento</summary><dl>${pairs.slice(0,18).map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(String(v).slice(0,250))}</dd>`).join('')}</dl></details>`;}).join(''):'<p>No se ha identificado un elemento en este punto. Acerca el mapa y pulsa sobre la línea o superficie.</p>'}</article>`;
    }catch{return `<article><h4>${icon(o.icon)}${o.name}</h4><p>La consulta de objetos no está disponible en este servicio o no ha respondido. La capa de imagen puede seguir visible.</p></article>`;}
  }));
  if(controller.signal.aborted)return;
  const target=$('#object-results');if(target){target.innerHTML=`<p class="eyebrow">ELEMENTOS DE LAS CAPAS · IGN</p>${results.join('')}`;icons();}
}
function renderInfo() {
  if(!selected)return;
  const p=selected.properties;const t=population.data[level][p.code];
  const val=valueFor(t,year,metric,p.areaKm2);
  const points=years.map((y)=>({y,v:valueFor(t,y,metric,p.areaKm2)})).filter(d=>d.v!==null) as {y:number;v:number}[];
  const vals=points.map(d=>d.v); const low=Math.min(...vals),high=Math.max(...vals); const diff=high-low||1;
  const path=points.map((d,i)=>`${i?'L':'M'}${8+(d.y-years[0])/(years.at(-1)!-years[0])*264},${56-(d.v-low)/diff*44}`).join(' ');
  const cca=communities.features.find(f=>f.properties.code===p.communityCode)?.properties.name;
  const total=valueFor(t,year,'population',p.areaKm2), density=valueFor(t,year,'density',p.areaKm2);
  const originalUrl=`https://www.ine.es/jaxiT3/Tabla.htm?t=${level==='province'?2852:2853}`;
  $('#info-panel').hidden=false;
  $('#info-panel').innerHTML=`<div class="info-heading"><span class="eyebrow">${level==='province'?'PROVINCIA / CIUDAD AUTÓNOMA':'COMUNIDAD / CIUDAD AUTÓNOMA'}</span><button id="info-close" class="icon-button" aria-label="Cerrar información">${icon('x')}</button></div><h3>${esc(p.name)}</h3><p class="info-region">${esc(level==='province'?cca:'España')} <span>· Código INE ${esc(p.code)}</span></p><div class="info-main"><span>${thematic?labels[metric]:'Población'}</span><strong>${formatValue(thematic?val:total,thematic?metric:'population')}</strong><small>${thematic?units[metric]:'habitantes'} · 1 de enero de ${year}</small></div>${thematic&&points.length?`<svg class="sparkline" viewBox="0 0 280 68" role="img" aria-label="Evolución de ${esc(labels[metric])} entre ${years[0]} y ${years.at(-1)}"><path d="${path} L272,68 L8,68 Z" fill="#e7eddb"/><path d="${path}" fill="none" stroke="#4c7760" stroke-width="2"/></svg><div class="sparkline-labels"><span>${years[0]}</span><span>${years.at(-1)}</span></div>`:''}<div class="info-facts"><div><span>Superficie aprox.</span><strong>${new Intl.NumberFormat('es-ES',{maximumFractionDigits:0}).format(p.areaKm2)} km²</strong></div><div><span>Densidad aprox.</span><strong>${formatValue(density,'density')} hab./km²</strong></div></div><p class="data-note">Padrón histórico 1996–2021. Superficie calculada sobre límites IGN actuales. No representa los datos más recientes.</p><div class="info-footer"><a href="${population.sourceUrl}" target="_blank" rel="noopener">INE · fuente original ${icon('arrow-up-right')}</a><button id="download-territory" title="Descargar serie del territorio" aria-label="Descargar serie del territorio">${icon('download')}</button></div>`;
  $('#info-panel .info-footer a').setAttribute('href',originalUrl);
  $('#info-close').onclick=()=>{featureQuery?.abort();selected=undefined;$('#info-panel').hidden=true;for(const m of maps)(m.getSource('selection') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features:[]});};
  $('#download-territory').onclick=()=>{
    if(!t){toast('Este territorio no tiene observaciones en la serie del INE.');return;}
    const lines=['codigo;territorio;anio;poblacion;hombres;mujeres;superficie_aprox_km2;fuente',...years.map(y=>`${p.code};"${p.name.replace(/"/g,'""')}";${y};${t.series[y]?.['0']??''};${t.series[y]?.['1']??''};${t.series[y]?.['2']??''};${p.areaKm2};INE tablas 2852 y 2853`)].join('\r\n');
    download(`poblacion-${p.code}.csv`,'\uFEFF'+lines,'text/csv;charset=utf-8');
  };icons();
}
