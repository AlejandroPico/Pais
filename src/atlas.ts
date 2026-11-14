import * as maplibregl from 'maplibre-gl';
import {type Map as AtlasMap,type ExpressionSpecification,type StyleSpecification} from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import {createIcons,Search,ChevronDown,ChevronRight,X,ArrowUpRight,MapPin,Mountain,Map,Play,Pause,Info,Download,Users,Waves,TrainFront,Route,Footprints,LocateFixed,Eye,SlidersHorizontal,ExternalLink,Database,ChartNoAxesCombined,Github,Wallet,BriefcaseBusiness,HeartHandshake,House,Factory,Landmark,FileCheck,GraduationCap,FlaskConical,HeartPulse,Wheat,Trees,CloudSun,Sailboat,Recycle,Zap,Wifi,Luggage,LibraryBig,Vote,Building2,Shield,Palette,Maximize,Minimize,Ellipsis,Check} from 'lucide';
import packageInfo from '../package.json';
import {formatValue,labels,normalize,scales,units,valueFor,type Metric,type Population,type Properties} from './data';
import {overlays} from './sources';
import {categories} from './categories';
import {TerritoryController} from './territory';
import {DemographyController,type StatisticsKind} from './demography';
import {territoryLayers,orthophotoEditions,historicOrthophoto,wmsTile} from './territory-config';
import {toAtlas,fromAtlas,projectFeature,projectCollection,ATLAS_BOUNDS,shiftedIds,displayRegion} from './atlas-coordinates';
import {registerAtlasProtocol,atlasTileUrl,addShiftedLayer,addAtlasSeparation} from './atlas-geography';
import {readTheme,solarTheme,themeOptions,type Theme} from './theme';
import {appearanceFields,bindAppearance,layerAppearance,paintLayer,paletteFor} from './layer-appearance';
import {bindLayerMenu} from './layer-menu';
import './style.css';
import type {Feature,FeatureCollection,MultiPolygon} from 'geojson';

registerAtlasProtocol();maplibregl.setWorkerUrl(workerUrl);maplibregl.setWorkerCount(2);
const $=<T extends HTMLElement=HTMLElement>(q:string)=>document.querySelector<T>(q)!;
const icon=(name:string,cls='')=>`<i data-lucide="${name}" class="${cls}" aria-hidden="true"></i>`;
const icons=()=>createIcons({icons:{Search,ChevronDown,ChevronRight,X,ArrowUpRight,MapPin,Mountain,Map,Play,Pause,Info,Download,Users,Waves,TrainFront,Route,Footprints,LocateFixed,Eye,SlidersHorizontal,ExternalLink,Database,ChartNoAxesCombined,Github,Wallet,BriefcaseBusiness,HeartHandshake,House,Factory,Landmark,FileCheck,GraduationCap,FlaskConical,HeartPulse,Wheat,Trees,CloudSun,Sailboat,Recycle,Zap,Wifi,Luggage,LibraryBig,Vote,Building2,Shield,Palette,Maximize,Minimize,Ellipsis,Check}});
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
const hash=new URLSearchParams(location.hash.slice(1));
const compatibleLayout=hash.get('atlas')==='2';
if(compatibleLayout)history.replaceState(history.state,'',location.pathname+location.search);
let overviewInitialized=false;
let year=Number(hash.get('year'))||2021;
let metric:Metric=(['population','density','women','change'].includes(hash.get('metric')||'')?hash.get('metric'):'density') as Metric;
let thematic=hash.get('data')==='1',level:'province'|'community'=hash.get('level')==='community'?'community':'province';
const ignCredit='© IGN y colaboradores · CC BY 4.0';
function wmts(path:string,layer:string,format:string){
  return path+'?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER='+layer+'&STYLE=default&FORMAT=image/'+format+'&TILEMATRIXSET=GoogleMapsCompatible&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}';
}
type BaseMap={id:string;name:string;group:string;url?:string;maxzoom?:number;credit?:string;scheme?:'xyz'|'tms';madrid?:boolean};
const streetService='https://www.ign.es/wmts/ign-base';
const rasterService='https://www.ign.es/wmts/mapa-raster';
const historicalService='https://www.ign.es/wmts/primera-edicion-mtn';
const landService='https://servicios.idee.es/wmts/ocupacion-suelo';
const baseMaps:BaseMap[]=[
  {id:'satellite',name:'Ortofoto',group:'Imagen',url:wmts('https://www.ign.es/wmts/pnoa-ma','OI.OrthoimageCoverage','jpeg'),credit:'PNOA © IGN y colaboradores · CC BY 4.0',maxzoom:19},
  {id:'terrain',name:'Relieve',group:'Terreno',url:'https://tms-relieve.idee.es/1.0.0/relieve/{z}/{x}/{y}.jpeg',scheme:'tms',maxzoom:16},
  {id:'elevation',name:'Modelo digital del terreno',group:'Terreno',url:wmts('https://servicios.idee.es/wmts/mdt','EL.ElevationGridCoverage','png')},
  {id:'lidar',name:'Superficies LiDAR',group:'Terreno',url:wmts('https://wmts-mapa-lidar.idee.es/lidar','EL.GridCoverageDSM','png')},
  {id:'street',name:'Callejero',group:'Callejero',url:wmts(streetService,'IGNBaseTodo','jpeg')},
  {id:'street-gray',name:'Callejero gris',group:'Callejero',url:wmts(streetService,'IGNBase-gris','jpeg')},
  {id:'street-simple',name:'Callejero simplificado',group:'Callejero',url:wmts(streetService,'IGNBaseSimplificado','png')},
  {id:'street-cut',name:'Callejero recortado',group:'Callejero',url:wmts(streetService,'IGNBaseTodo-nofondo','png')},
  {id:'street-labels',name:'Rotulación sobre ortofoto',group:'Imagen',url:wmts(streetService,'IGNBaseOrto','png')},
  {id:'topographic',name:'Topográfico IGN',group:'Topografía',url:wmts(rasterService,'MTN','jpeg')},
  {id:'topographic-background',name:'Fondo topográfico',group:'Topografía',url:wmts(rasterService,'MTN_Fondo','jpeg')},
  {id:'land-cover',name:'Cubierta terrestre',group:'Ocupación del suelo',url:wmts(landService,'LC.LandCoverSurfaces','png')},
  {id:'land-use',name:'Usos del suelo',group:'Ocupación del suelo',url:wmts(landService,'LU.ExistingLandUse','png')},
  {id:'neutral',name:'Silueta neutra',group:'Fondos del atlas'},
  {id:'outline',name:'Contorno',group:'Fondos del atlas'},
  {id:'mtn50-history',name:'Primera edición MTN50',group:'Cartografía histórica',url:wmts(historicalService,'mtn50-edicion1','jpeg')},
  {id:'mtn25-history',name:'Primera edición MTN25',group:'Cartografía histórica',url:wmts(historicalService,'mtn25-edicion1','jpeg')},
  {id:'mtn50-drafts',name:'Minutas del MTN50',group:'Cartografía histórica',url:wmts(historicalService,'catastrones','jpeg')},
  {id:'historical-plans',name:'Planimetrías (1870–1950)',group:'Cartografía histórica',url:wmts('https://www.ign.es/wmts/minutas-cartograficas','Minutas','png')},
  ...orthophotoEditions.map(edition=>({
    id:'flight-'+edition.id,name:edition.name,group:'Ortofotos históricas y vuelos',
    url:wmsTile(historicOrthophoto(edition.id)),credit:historicOrthophoto(edition.id).credit,maxzoom:18,
  })),
  ...[
    ['MancelliMadrid','1622 · Mancelli'],
    ['Texeira','1656 · Texeira'],
    ['ChalmadrierMadrid','1761 · Chalmandrier'],
    ['EspinosaMadrid','1769 · Espinosa de los Monteros'],
    ['GeometricoMadrid','1785 · López'],
    ['MadozMadrid','1848 · Madoz y Coello'],
    ['IbanezMadrid','1875 · Ibáñez Íbero'],
    ['FacundoMadrid','1900 · Cañada'],
    ['NunezMadrid','1910 · Núñez Granés'],
    ['AyuntamientoMadrid','1929 · Plano municipal'],
    ['ParcelarioMadrid','1940–1960 · Parcelario']
  ].map(([id,name])=>({id:'madrid-'+id,name,group:'Planos históricos de Madrid',url:wmts('https://www.ign.es/wmts/planos',id,'png'),madrid:true})),
];
const rasterBases=baseMaps.filter(item=>item.url);
let base=baseMaps.some(({id})=>id===hash.get('base'))?hash.get('base')!:'satellite';
let tilted=hash.get('flat')!=='1';
let selected:Feature<MultiPolygon,Properties>|undefined;
const active=new Set((hash.get('layers')||'').split(',').filter(id=>overlays.some(o=>o.id===id)||territoryLayers.some(o=>o.id===id)));
let layerMenu:ReturnType<typeof bindLayerMenu>|undefined;
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
${railButton('appearance-open','Visualización','eye')}${railButton('sources-open','Fuentes','database')}${railButton('about-open','Acerca de','info')}</div></nav>
<main class="map-area" aria-label="Mapa de España"><div id="map" aria-label="Mapa interactivo. Arrastra para desplazarte. Rueda o pellizco para ampliar. Doble clic derecho para orientar al norte."></div><section id="info-panel" class="info-panel" aria-label="Información del territorio" hidden></section><div id="legend" class="legend" hidden></div><div id="overlay-legend" class="overlay-legend" hidden></div><div id="map-status" class="map-status" role="status">Preparando cartografía…</div>
<section id="timeline" class="timeline" aria-label="Evolución temporal" hidden><button id="play" aria-label="Reproducir evolución">${icon('play')}</button><div class="timeline-label"><small>PADRÓN · INE</small><strong id="year-value">2021</strong></div><div class="timeline-track"><input id="year" type="range" min="0" max="24" step="1" aria-label="Año de los datos"><div class="timeline-ticks"><span>1996</span><span>2005</span><span>2013</span><span>2021</span></div></div><button id="timeline-info" class="icon-button" aria-label="Información de la serie">${icon('info')}</button></section></main>
<aside id="drawer" class="drawer" aria-labelledby="drawer-title" hidden><header class="drawer-head"><h1 id="drawer-title"></h1><button id="drawer-close" class="icon-button" aria-label="Cerrar panel">${icon('x')}</button></header><div id="base-dock"></div><div id="drawer-content" class="drawer-content"></div><div id="layer-dock" data-depth="0"></div></aside></div><div id="toast" class="toast" role="status" hidden></div><dialog id="modal" aria-labelledby="modal-heading"><header class="modal-top"><span id="modal-heading">El país</span><button id="modal-close" class="icon-button" aria-label="Cerrar ventana">${icon('x')}</button></header><div id="modal-body"></div></dialog>`;

let toastTimeout:ReturnType<typeof setTimeout>;
function toast(message:string){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>$('#toast').hidden=true,6000);}
function extent(f:Feature<MultiPolygon,Properties>):[[number,number],[number,number]]{const p=f.geometry.coordinates.flat(2);return [[Math.min(...p.map(p=>p[0])),Math.min(...p.map(p=>p[1]))],[Math.max(...p.map(p=>p[0])),Math.max(...p.map(p=>p[1]))]];}
function home(duration=500){if(!ready)return;map.fitBounds(ATLAS_BOUNDS,{padding:{top:24,right:24,bottom:35,left:24},pitch:0,bearing:0,duration});}
function fitOverview(){const camera=map.cameraForBounds(ATLAS_BOUNDS,{padding:{top:24,right:24,bottom:35,left:24}});if(!camera)return;const wasHome=map.getZoom()<=map.getMinZoom()+.05;map.setMinZoom(camera.zoom||3);if(wasHome||!overviewInitialized)map.jumpTo({...camera,bearing:0,pitch:0});overviewInitialized=true;}
function selectedGeo(){return level==='province'?provinces:communities;}
function openModal(html:string,view='',title='El país'){
  const modal=$<HTMLDialogElement>('#modal');
  if(!modal.open)priorFocus=document.activeElement as HTMLElement;
  modalController?.abort();
  modalController=new AbortController();
  modal.dataset.view=view;
  $('#modal-heading').textContent=title;
  $('#modal-body').innerHTML=html;
  if(!modal.open)modal.showModal();
  icons();
}
function closeModal(){$<HTMLDialogElement>('#modal').close();}
async function showCatalog(category?:string,inventory?:string){
  closeDrawer();
  openModal('<p role="status">Cargando fuentes…</p>','catalog','El país · Fuentes');
  const signal=modalController!.signal;
  try{
    const {mountCatalog}=await import('./catalog');
    if(!signal.aborted)await mountCatalog($('#modal-body'),{
      category,inventory,signal,icons,activate:action=>{activateProduct(action);closeModal();},
      setTitle:title=>{$('#modal-heading').textContent=title;},
    });
  }catch{
    if(signal.aborted)return;
    $('#modal-body').innerHTML='<p>No se pudo cargar el registro de fuentes.</p><button id="registry-retry">Reintentar</button>';
    $('#registry-retry').onclick=()=>showCatalog(category,inventory);
  }
}
function about(){
  closeDrawer();
  openModal(`
    <div class="about-body">
      <div class="about-brand">
        <img src="${import.meta.env.BASE_URL}favicon.svg" alt="" width="72" height="72">
        <div><h2 id="modal-title">El país</h2><span>Atlas abierto de España · versión ${packageInfo.version}</span></div>
      </div>
      <p class="about-intro">Explora España a través de su territorio y sus datos públicos.</p>
      <div class="about-features">
        <section><h3>Explora el territorio</h3><p>Recorre la península, Baleares, Canarias, Ceuta, Melilla y otros territorios. Alterna mapas base y busca municipios, comarcas y direcciones.</p></section>
        <section><h3>Consulta y compara</h3><p>Combina capas, abre fichas territoriales y recorre los periodos disponibles. Descarga las series que te interesen y consulta su unidad y procedencia.</p></section>
      </div>
      <p class="about-credit">Un proyecto de <strong>Alejandro Pico</strong> en desarrollo, basado en datos oficiales.</p>
    </div>
    <footer class="about-links">
      <a href="https://alejandropico.github.io/Portfolio/" target="_blank" rel="noopener">Porfolio ${icon('arrow-up-right')}</a>
      <a href="https://github.com/AlejandroPico/Pais" target="_blank" rel="noopener">${icon('github')} Repositorio ${icon('arrow-up-right')}</a>
    </footer>`,'about','Acerca de');
}
function seriesInfo(){openModal(`<h2 id="modal-title">Serie histórica</h2><p>${esc(population?.note||'Padrón municipal del INE.')}</p><ul><li>Tablas INE 2852 y 2853. Datos a 1 de enero, 1996–2021; no hay observación de 1997.</li><li>Los límites actuales no reconstruyen las fronteras históricas. La superficie y la densidad son aproximadas.</li><li>El cronograma modifica la estadística seleccionada. Cada mapa base o red conserva su propia fecha.</li></ul><a href="https://www.ine.es/jaxiT3/Tabla.htm?t=2852" target="_blank" rel="noopener">Consultar el origen ↗</a>`);}
function download(name:string,content:string,type:string){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function expandRail(next=!expanded){expanded=next;$('.workspace').classList.toggle('expanded',expanded);$('#brand-menu').setAttribute('aria-expanded',String(expanded));$('#brand-menu').setAttribute('aria-label',`El país · ${expanded?'Contraer':'Ampliar'} menú`);fitRail();setTimeout(()=>maps.forEach(m=>m.resize()),200);}
function closeDrawer(){layerMenu?.close();layerMenu=undefined;drawerTab='';$('#drawer').hidden=true;document.querySelectorAll<HTMLElement>('[data-category]').forEach(b=>{b.setAttribute('aria-expanded','false');b.classList.remove('active');});}
function openDrawer(tab:string,title:string,html:string){if(drawerTab===tab){closeDrawer();return;}closeDrawer();if(innerWidth<760&&expanded)expandRail(false);drawerTab=tab;$('#drawer-title').textContent=title;$('#base-dock').innerHTML=baseOptions();$('#drawer-content').innerHTML=html;$('#drawer').hidden=false;$('#drawer-content').scrollTop=0;document.querySelector(`[data-category="${tab}"]`)?.setAttribute('aria-expanded','true');document.querySelector(`[data-category="${tab}"]`)?.classList.add('active');icons();bindControls();layerMenu=bindLayerMenu($('#drawer-content'),$('#layer-dock'));}
function layerMenuRow(title:string,controls:string){
  return `<details class="submenu layer-option"><summary><span class="submenu-label">${esc(title)}</span>${icon('chevron-right')}</summary>${controls}</details>`;
}
function overlayRow(o:typeof overlays[number]){
  return layerMenuRow(o.name,`<label class="check-row"><input type="checkbox" data-overlay="${o.id}" ${active.has(o.id)?'checked':''}>Mostrar capa</label><p class="data-note">${esc(o.note)}</p>${appearanceFields(o.id,'#ffce75',.85,true)}`);
}
function backgroundOptions(){
  return layerMenuRow('Fondo del mapa',`<h2 class="settings-label">Mar</h2>${appearanceFields('base-sea','#0b2842')}
    <h2 class="settings-label">Tierra</h2>${appearanceFields('base-land','#a4b4bb')}
    <h2 class="settings-label">Cartografía del mapa base</h2>${appearanceFields('base-image','#c7cbba',1,true)}
    <p class="data-note">La cobertura varía según la edición del vuelo o del mapa histórico.</p>
    <p class="data-note">Reduce la opacidad de la cartografía para ver el color de tierra debajo.</p>`);
}
function baseOptions(){
  const groups=[...new Set(baseMaps.map(item=>item.group))];
  return `<label class="base-picker">Mapa base<select id="base-select">${groups.map(group=>
    `<optgroup label="${group}">${baseMaps.filter(item=>item.group===group).map(({id,name})=>
      `<option value="${id}" ${base===id?'selected':''}>${name}</option>`).join('')}</optgroup>`).join('')}</select></label>`;
}
function categoryPanel(id:string){const c=categories.find(c=>c.id===id)!;let html='';
  if(id==='F01')html=`<details class="submenu"><summary>Comunidades y provincias ${icon('chevron-right')}</summary>${
    layerMenuRow('Comunidades autónomas',`<label class="check-row"><input id="communities-toggle" type="checkbox" ${showCommunities?'checked':''}>Mostrar capa</label>${appearanceFields('community-lines','#fff8d2')}`)
    + layerMenuRow('Provincias',`<label class="check-row"><input id="provinces-toggle" type="checkbox" ${showProvinces?'checked':''}>Mostrar capa</label>${appearanceFields('province-lines','#e9e5d5')}`)
  }</details>${geography?.panel()||'<p>Preparando cartografía…</p>'}`;
  else if(id==='F03'||id==='F04')html=layerMenuRow(id==='F04'?'Indicadores de trabajo':'Indicadores de renta y condiciones de vida','<div id="statistics-panel"></div>');
  else if(id==='F02')html=`<details class="submenu" id="nomenclator"><summary>Nomenclátor · entidades y núcleos ${icon('chevron-right')}</summary><div id="nomenclator-panel"></div></details><details class="submenu" id="historical-census"><summary>Censos históricos · 1842–2021 ${icon('chevron-right')}</summary><div id="historical-census-panel"></div></details>${layerMenuRow('Indicadores de población','<div id="demography-panel"></div>')}<details class="submenu"><summary>Padrón histórico · INE ${icon('chevron-right')}</summary>${(['population','density','women','change'] as Metric[]).map(m=>layerMenuRow(labels[m],`<label class="check-row"><input type="radio" name="metric" value="${m}" ${thematic&&metric===m?'checked':''}>Mostrar capa</label>${appearanceFields('metric-'+m,scales[m].colors[3],.73)}`)).join('')}<button id="clear-metric" class="text-button">Desactivar población</button><label class="field-label">División territorial<select id="level"><option value="province" ${level==='province'?'selected':''}>Provincias</option><option value="community" ${level==='community'?'selected':''}>Comunidades</option></select></label><p class="data-note">1996–2021, sin 1997. No es la población más reciente.</p></details>`;
  const ids=id==='F16'?['rivers']:id==='F22'?['rail','roads','camino']:['F24','F26'].includes(id)?['camino']:[];
  if(ids.length)html+=`<details class="submenu" open><summary>Capas disponibles ${icon('chevron-right')}</summary>${overlays.filter(o=>ids.includes(o.id)).map(overlayRow).join('')}</details>`;
  if(!html)html='<p class="panel-note">Las capas de esta categoría están pendientes de integración. Puedes consultar los productos y fuentes inventariados.</p>';
  html+=`<button class="catalog-category" data-open-catalog="${id}">${icon('database')} Productos y cobertura ${icon('chevron-right')}</button>`;openDrawer(id,c.name,html);
}
function filtersPanel(){openDrawer('filters','Filtros',`<p class="panel-note" id="filter-summary">${active.size+Number(thematic)+statisticControllers().filter(controller=>controller.active).length+Number(showCommunities)+Number(showProvinces)} capas activas</p><button id="clear-all" class="wide-button">Desactivar todas las capas</button><details class="submenu" open><summary>Buscar una capa ${icon('chevron-right')}</summary><input id="layer-search" type="search" placeholder="Nombre o categoría…" aria-label="Buscar capas"><div id="layer-matches"></div></details><p class="data-note">Las opciones de cada indicador están dentro de su categoría.</p>`);if(!$('#clear-all'))return;$('#clear-all').onclick=()=>{active.clear();disableStatistics();thematic=false;showCommunities=false;showProvinces=false;stopPlaying();updateData();$('#filter-summary').textContent='0 capas activas';};$('#layer-search').oninput=()=>{const q=normalize($<HTMLInputElement>('#layer-search').value);$('#layer-matches').innerHTML=q?categories.filter(c=>normalize(c.name).includes(q)).map(c=>`<button data-match="${c.id}" class="search-result">${esc(c.name)} ${icon('chevron-right')}</button>`).join(''):'';document.querySelectorAll<HTMLButtonElement>('[data-match]').forEach(b=>b.onclick=()=>categoryPanel(b.dataset.match!));icons();};}
function appearancePanel(){
  const modes=themeOptions.map(([id,label])=>
    `<button data-theme="${id}" aria-pressed="${theme===id}">${label}</button>`).join('');
  openDrawer('appearance','Visualización',`
    <div class="view-actions">
      ${railButton('home-map','Vista general','locate-fixed')}
      <button id="terrain-toggle" aria-pressed="${tilted}">${icon('mountain')} Terreno 3D</button>
      <button id="fullscreen">${icon(document.fullscreenElement?'minimize':'maximize')} ${document.fullscreenElement?'Salir de pantalla completa':'Pantalla completa'}</button>
    </div>
    ${backgroundOptions()}
    <details class="submenu" open><summary>Tema ${icon('chevron-right')}</summary>
      <div class="theme-options">${modes}</div>
      <p class="data-note">Automático sigue el amanecer, el mediodía solar y la puesta de sol de Madrid.</p>
    </details>`);
}

function fitRail(){
  const nav=$('.category-nav');
  const buttons=Array.from(nav.querySelectorAll<HTMLElement>('.category-btn'));
  const row=buttons[0]?.getBoundingClientRect().height;
  if(!row)return;
  const styles=getComputedStyle(nav);
  const available=nav.clientHeight-parseFloat(styles.paddingTop)-parseFloat(styles.paddingBottom);
  const count=Math.max(1,Math.floor(available/row));
  buttons.forEach((button,i)=>{button.hidden=!expanded&&i>=count;});
}
function syncLayerScales(){geography?.zoomStatus($('#drawer'));}
function applyLayerAppearance(id:string){
  geography?.applyAppearance(id);
  for(const m of maps)for(const layer of [id,...shiftedIds(id)])paintLayer(m,layer,layerAppearance(id));
  if(id.startsWith('base-'))for(const m of maps)if(m.getLayer('atlas-opaque-sea')&&m.isSourceLoaded('atlas-visible-sea'))showBase(m);
  if(id==='metric-'+metric)updateData();
}
function bindControls(){
  geography?.bind($('#drawer-content'));
  syncLayerScales();
  geography?.syncIndicators($('#drawer'));
  bindAppearance($('#drawer-content'),applyLayerAppearance);
  if($('#demography-panel')&&statistics.demography)void statistics.demography.mount($('#demography-panel'));
  const nomenclator=$<HTMLDetailsElement>('#nomenclator');
  if(nomenclator)nomenclator.ontoggle=()=>{
    const target=$('#nomenclator-panel');
    if(nomenclator.open&&target&&!target.hasChildNodes()){
      void import('./nomenclator').then(({mountNomenclator})=>{
        if(target.isConnected)void mountNomenclator(target,provinces.features.map(feature=>feature.properties));
      });
    }
  };
  const historical=$<HTMLDetailsElement>('#historical-census');
  if(historical)historical.ontoggle=()=>{
    const target=$('#historical-census-panel');
    if(historical.open&&target&&!target.hasChildNodes()){
      void import('./intercensal').then(({mountHistoricalCensus})=>{
        if(target.isConnected)void mountHistoricalCensus(target,provinces.features.map(feature=>feature.properties));
      });
    }
  };
  const panel=$('#statistics-panel');
  if(panel)void statistics[drawerTab==='F04'?'labor':'welfare']?.mount(panel);
  $<HTMLSelectElement>('#base-select').onchange=e=>setBase((e.target as HTMLSelectElement).value);
  document.querySelectorAll<HTMLButtonElement>('button[data-theme]').forEach(button=>{
    button.onclick=()=>setTheme(readTheme(button.dataset.theme||null));
  });
  $('#home-map')?.addEventListener('click',()=>{closeDrawer();home();});
  $('#terrain-toggle')?.addEventListener('click',()=>{tilted=!tilted;terrain();});
  $('#fullscreen')?.addEventListener('click',toggleFullscreen);
  $('[data-open-cartography]')?.addEventListener('click',()=>showCatalog('F01','territory'));
  document.querySelectorAll<HTMLButtonElement>('[data-open-catalog]').forEach(b=>b.onclick=()=>showCatalog(b.dataset.openCatalog));
  $('#communities-toggle')?.addEventListener('change',e=>{showCommunities=(e.target as HTMLInputElement).checked;updateData();});$('#provinces-toggle')?.addEventListener('change',e=>{showProvinces=(e.target as HTMLInputElement).checked;updateData();});
  document.querySelectorAll<HTMLInputElement>('[name="metric"]').forEach(i=>i.onchange=()=>{disableStatistics();metric=i.value as Metric;thematic=true;updateData();});$('#clear-metric')?.addEventListener('click',()=>{thematic=false;stopPlaying();updateData();document.querySelectorAll<HTMLInputElement>('[name="metric"]').forEach(i=>i.checked=false);});
  $('#level')?.addEventListener('change',e=>{level=(e.target as HTMLSelectElement).value as typeof level;selected=undefined;$('#info-panel').hidden=true;updateData();});
  document.querySelectorAll<HTMLInputElement>('[data-overlay]').forEach(i=>i.onchange=()=>{i.checked?active.add(i.dataset.overlay!):active.delete(i.dataset.overlay!);updateData();if(i.dataset.overlay==='municipal'&&i.checked&&ready&&map.getZoom()<8)toast('Los límites municipales aparecen al acercar el mapa.');});
}
function updateBackground(map:AtlasMap){
  const sea=layerAppearance('base-sea'),land=layerAppearance('base-land'),image=layerAppearance('base-image');
  const seaColor=sea.color??'#0b2842',alpha=sea.opacity??1;
  const channels=[0,2,4].map(i=>Math.round(parseInt(seaColor.slice(i+1,i+3),16)*alpha+parseInt('0b2842'.slice(i,i+2),16)*(1-alpha)));
  const water=`rgb(${channels.join(',')})`;
  map.setPaintProperty('background','background-color',water);
  map.setPaintProperty('atlas-opaque-sea','fill-color',water);
  map.setPaintProperty('atlas-separation-label','text-halo-color',water);
  if(map.getLayer('atlas-islets-shape')){
    map.setPaintProperty('base-neutral','fill-color',land.color??'#a4b4bb');
    map.setPaintProperty('base-neutral','fill-opacity',land.opacity??1);
    map.setPaintProperty('base-outline','line-color',land.color??'#c2d4dc');
    map.setPaintProperty('base-outline','line-opacity',land.opacity??1);
    map.setLayoutProperty('atlas-islets-shape','visibility',base==='outline'?'none':'visible');
    map.setPaintProperty('atlas-islets-shape','fill-opacity',(land.opacity??1)*.35);
    map.setPaintProperty('atlas-islets-shape','fill-color',land.color??'#9aa98d');
  }
  for(const id of [base,...(base==='street-labels'?['satellite']:[])])if(map.getLayer('base-'+id))paintLayer(map,'base-'+id,image);
}
function showBase(map:AtlasMap){
  for(const {id} of baseMaps){
    const layer='base-'+id;
    if(!map.getLayer(layer))continue;
    const visible=id===base||id==='satellite'&&base==='street-labels'||id==='neutral'&&base!=='outline'
      &&(layerAppearance('base-land').color!==undefined||layerAppearance('base-land').opacity!==undefined||layerAppearance('base-image').opacity!==undefined);
    map.setLayoutProperty(layer,'visibility',visible?'visible':'none');
  }
  updateBackground(map);
}
function setBase(next:string){
  const item=baseMaps.find(({id})=>id===next);
  if(!item)return;
  sourceErrors.clear();
  if(ready)$('#map-status').hidden=true;
  base=next;
  for(const m of maps)if(m.getLayer('atlas-opaque-sea')&&m.isSourceLoaded('atlas-visible-sea'))showBase(m);
  const selector=$<HTMLSelectElement>('#base-select');
  if(selector)selector.value=base;
  if(item.madrid&&ready)map.easeTo({center:[-3.7038,40.419],zoom:13,pitch:0,duration:500});
}
function terrain(){for(const m of maps)if(m.getSource('dem'))m.setTerrain(tilted?{source:'dem',exaggeration:1.3}:null);$('#terrain-toggle')?.setAttribute('aria-pressed',String(tilted));}
function activateProduct(action:string){const [kind,id,...parameters]=action.split(':');
  if(Object.hasOwn(statisticCategories,kind)){
    const statisticKind=kind as StatisticsKind;
    thematic=false;
    stopPlaying();
    void statistics[statisticKind].useTable(Number(id));
    const category=statisticCategories[statisticKind];
    if(drawerTab===category)closeDrawer();
    categoryPanel(category);
    const details=($('#statistics-panel')||$('#demography-panel'))?.closest('details');
    if(details)layerMenu?.open(details);
    return;
  }
  if(kind==='official-wms'){
    void geography?.toggleOfficial(id,true).then(()=>{
      if(drawerTab==='F01')closeDrawer();
      categoryPanel('F01');
      const details=$<HTMLDetailsElement>('#official-active');
      if(details)layerMenu?.open(details);
    }).catch(()=>toast('No se pudo abrir la capa cartográfica.'));
    return;
  }
  if(kind==='territory'){
    active.add(id);
    if(parameters.length)geography?.selectEdition(id,parameters.join(':'));
    geography?.update();
    geography?.focusLayer(id);
    updateData();
    return;
  }
  const consultation={
    'nomenclator':['F02','nomenclator'],
    'historical-census':['F02','historical-census'],
    'municipal-changes':['F01','municipal-changes'],
  }[action];
  if(consultation){
    closeDrawer();
    categoryPanel(consultation[0]);
    const details=$<HTMLDetailsElement>('#'+consultation[1]);
    if(details)layerMenu?.open(details);
    return;
  }
  if(action==='search:addresses'){closeModal();searchPanel();return;}if(action.startsWith('base:'))setBase(action.slice(5));else if(action.startsWith('metric:')){disableStatistics();metric=action.slice(7) as Metric;thematic=true;}else if(action.startsWith('overlay:'))active.add(action.slice(8));else if(action==='communities')showCommunities=true;else if(action==='provinces')showProvinces=true;else if(action==='terrain'){tilted=true;terrain();}updateData();}
function updateData(){if(!ready)return;
  for(const m of maps){if(!m.getLayer('province-fill'))continue;for(const l of ['province','community'] as const){const geo=l==='province'?provinces:communities;if(thematic&&l===level)for(const f of geo.features){const value=valueFor(population.data[l][f.properties.code],year,metric,f.properties.areaKm2);m.setFeatureState({source:l,id:f.id!},{value:value??-999999,missing:value===null});}const scale=scales[metric];const palette=paletteFor(scale.colors,layerAppearance('metric-'+metric).color);const color=['interpolate',['linear'],['feature-state','value'],...scale.stops.flatMap((stop,i)=>[stop,palette[i]])] as ExpressionSpecification;m.setPaintProperty(`${l}-fill`,'fill-color',['case',['boolean',['feature-state','missing'],true],'#b8b6aa',color]);m.setPaintProperty(`${l}-fill`,'fill-opacity',thematic&&l===level?layerAppearance('metric-'+metric).opacity??.73:0);}m.setLayoutProperty('province-lines','visibility',showProvinces?'visible':'none');m.setLayoutProperty('community-lines','visibility',showCommunities?'visible':'none');for(const o of overlays){m.setLayoutProperty(o.id,'visibility',active.has(o.id)?'visible':'none');for(const id of shiftedIds(o.id))if(m.getLayer(id))m.setLayoutProperty(id,'visibility',active.has(o.id)?'visible':'none');}(m.getSource('selection') as maplibregl.GeoJSONSource).setData(selected?projectFeature(selected):{type:'FeatureCollection',features:[]});}
  geography?.update();
  geography?.syncIndicators($('#drawer'));
  $('#timeline').hidden=!thematic;$('#legend').hidden=!thematic;
  if(thematic){const s=scales[metric];const appearance=layerAppearance('metric-'+metric);$('#legend').innerHTML=`<div class="legend-title"><strong>${labels[metric]}</strong><span>${year}</span></div><p>${units[metric]} · ${level==='province'?'provincias':'comunidades'}</p><div class="color-scale" style="background:linear-gradient(90deg,${paletteFor(s.colors,appearance.color).join(',')})"></div><div class="scale-labels"><span>${formatValue(s.stops[0],metric)}</span><span>≥ ${formatValue(s.stops[6],metric)}</span></div><p class="legend-credit">Sin datos: gris · INE / IGN</p>`;}
  $('#year-value').textContent=String(year);const slider=$<HTMLInputElement>('#year');slider.max=String(years.length-1);slider.value=String(years.indexOf(year));slider.setAttribute('aria-valuetext',String(year));const enabled=[...overlays.filter(o=>active.has(o.id)).map(o=>o.name),...geography.activeLabels()];$('#overlay-legend').hidden=!enabled.length;$('#overlay-legend').textContent=enabled.join(' · ');if(selected)renderInfo();
}
function selectTerritory(f:Feature<MultiPolygon,Properties>,zoom=false){selected=f;for(const m of maps)if(m.getSource('selection'))(m.getSource('selection') as maplibregl.GeoJSONSource).setData(projectFeature(f));renderInfo();if(zoom){const target=map;target.fitBounds(extent(projectFeature(f)),{padding:40,maxZoom:10,pitch:0,duration:600});}}
function searchPanel(){openDrawer('search','Buscar','<div id="territory-search"></div>');const target=$('#territory-search');if(!target)return;if(ready)void geography.mountSearch(target);else target.innerHTML='<p>La búsqueda estará disponible al terminar de cargar el mapa.</p>';}


function style():StyleSpecification{return {version:8,glyphs:'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',sources:{
  ...Object.fromEntries(rasterBases.map(({id,url,maxzoom=19,scheme,credit,madrid})=>[id,{
    type:'raster',tiles:[madrid?url!:atlasTileUrl(url!,{scheme,maxzoom})],tileSize:256,maxzoom,attribution:credit??ignCredit,
    ...(madrid?{bounds:[-3.91,40.29,-3.48,40.58]}:{})
  }])),
  dem:{type:'raster-dem',tiles:[atlasTileUrl('https://xyz-mdt.idee.es/1.0.0/raster-dem/{z}/{x}/{y}.png',{size:512,dem:true})],encoding:'mapbox',tileSize:512,minzoom:5,maxzoom:15,attribution:'Modelo de elevaciones © IGN · CC BY 4.0'}
},layers:[{id:'background',type:'background',paint:{'background-color':'#0b2842'}},...rasterBases.map(({id})=>({id:`base-${id}`,type:'raster' as const,source:id,layout:{visibility:'none' as const},paint:{'raster-fade-duration':150}}))]};}
function setupMap(m:AtlasMap){
  m.addSource('base-spain',{type:'geojson',data:import.meta.env.BASE_URL+'data/territory/country-atlas.geojson',attribution:'Límites © IGN · CC BY 4.0'});
  m.addLayer({id:'base-neutral',type:'fill',source:'base-spain',layout:{visibility:'none'},paint:{'fill-color':'#a4b4bb'}},'base-'+rasterBases[0].id);
  m.addLayer({id:'base-outline',type:'line',source:'base-spain',layout:{visibility:'none'},paint:{'line-color':'#a9c0cd','line-width':1.5}});
  for(const l of ['province','community'] as const){m.addSource(l,{type:'geojson',data:projectCollection(l==='province'?provinces:communities)});m.addLayer({id:`${l}-fill`,type:'fill',source:l,paint:{'fill-opacity':0,'fill-color':'#78a18a'}});}
  for(const o of overlays){const tile=`${o.url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=${encodeURIComponent(o.layers)}&STYLES=${encodeURIComponent('styles' in o?o.styles!:'')}&FORMAT=image/png&TRANSPARENT=TRUE&SRS=EPSG:3857&WIDTH=256&HEIGHT=256&BBOX={bbox-epsg-3857}`;m.addSource(o.id,{type:'raster',tiles:[tile],tileSize:256,bounds:[-18.5,27,4.7,44],attribution:'© IGN · CC BY 4.0'});m.addLayer({id:o.id,type:'raster',source:o.id,minzoom:o.minzoom||0,layout:{visibility:active.has(o.id)?'visible':'none'},paint:{'raster-opacity':.85}});const original=m.getStyle().layers.find(l=>l.id===o.id)!;
    const ids=[o.id,...addShiftedLayer(m,original)];
    const specs=m.getStyle().layers;
    for(const id of ids)paintLayer(m,id,layerAppearance(o.id),specs.find(l=>l.id===id)!);
  }
  const revealBase=()=>{if(m.getSource('atlas-visible-sea')&&m.isSourceLoaded('atlas-visible-sea')){showBase(m);m.off('sourcedata',revealBase);}};m.on('sourcedata',revealBase);revealBase();
  geography.attach(m);
  m.addLayer({id:'province-lines',type:'line',source:'province',layout:{visibility:showProvinces?'visible':'none'},paint:{'line-color':'#e9e5d5','line-width':['interpolate',['linear'],['zoom'],4,.6,8,1.2,13,2],'line-opacity':.8}});m.addLayer({id:'community-lines',type:'line',source:'community',layout:{visibility:showCommunities?'visible':'none'},paint:{'line-color':'#fff8d2','line-width':['interpolate',['linear'],['zoom'],4,1.5,8,2.5,13,3.5],'line-opacity':.95}});
  for(const id of ['province-lines','community-lines']){
    const original=m.getStyle().layers.find(layer=>layer.id===id)!;
    paintLayer(m,id,layerAppearance(id),original);
  }
  m.addSource('selection',{type:'geojson',data:{type:'FeatureCollection',features:[]}});m.addLayer({id:'selected-outline',type:'line',source:'selection',paint:{'line-color':'#efd68c','line-width':2.5}});if(tilted)m.setTerrain({source:'dem',exaggeration:1.3});
  m.on('click',async e=>{if(!ready)return;if(m.queryRenderedFeatures(e.point,{layers:['atlas-opaque-sea']}).length)return;featureQuery?.abort();if(statisticControllers().some(controller=>controller.inspect(m,e)))return;delete $('#info-panel').dataset.demography;if(await geography.inspect(m,e))return;geography.reset();const features=m.queryRenderedFeatures(e.point,{layers:[`${level}-fill`]});if(features[0]){const f=selectedGeo().features.find(f=>f.properties.code===features[0].properties.code);if(f)selectTerritory(f);}else{selected=undefined;$('#info-panel').hidden=true;for(const target of maps)(target.getSource('selection') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features:[]});}const truePoint=fromAtlas([e.lngLat.lng,e.lngLat.lat]);queryObjects(truePoint[0],truePoint[1]);});
  for(const controller of statisticControllers())controller.attach(m,provinces,communities);
  addAtlasSeparation(m);
  m.moveLayer('base-outline','atlas-islets-shape');
  m.setLayoutProperty('atlas-islets-shape','visibility',base==='outline'?'none':'visible');
  const specs=m.getStyle().layers;
  for(const {id} of rasterBases){
    const layer='base-'+id;
    paintLayer(m,layer,{},specs.find(spec=>spec.id===layer)!);
  }
  geography.restoreOfficial();
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
      closeDrawer,
      clearSelection:clearStatisticsSelection,
    },kind,hash);
  }
  geography=new TerritoryController({active,info:$('#info-panel'),icons,onChange:updateData,beforeInspect:()=>{featureQuery?.abort();selected=undefined;for(const m of maps)if(m.getSource('selection'))(m.getSource('selection') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features:[]});},closeDrawer,selectLegacy:(f,l)=>{level=l;updateData();selectTerritory(f as Feature<MultiPolygon,Properties>,true);},provinces,communities},hash);let loaded=0;
  for(const m of maps){m.on('error',e=>{sourceErrors.add((e as unknown as {sourceId?:string}).sourceId||'map');$('#map-status').hidden=false;$('#map-status').textContent='Un servicio cartográfico no ha respondido.';console.warn('Cartographic service error',e.error?.message);});m.on('load',()=>{setupMap(m);if(++loaded===1){ready=true;fitOverview();const lng=Number(hash.get('lng')),lat=Number(hash.get('lat')),z=Number(hash.get('z'));if(compatibleLayout&&hash.has('lng')&&Number.isFinite(lng)&&Number.isFinite(lat)&&Number.isFinite(z)&&lng>=-20&&lng<=7&&lat>=25.5&&lat<=46.5&&z>=3&&z<=18)map.jumpTo({center:[lng,lat],zoom:z,pitch:0});terrain();updateData();syncLayerScales();if(!sourceErrors.size)$('#map-status').hidden=true;}});}
  map.touchZoomRotate.disableRotation();map.on('zoomend',syncLayerScales);map.on('moveend',()=>{const c=map.getCenter(),lng=Math.max(ATLAS_BOUNDS[0][0],Math.min(ATLAS_BOUNDS[1][0],c.lng)),lat=Math.max(ATLAS_BOUNDS[0][1],Math.min(ATLAS_BOUNDS[1][1],c.lat));if(c.lng!==lng||c.lat!==lat)map.jumpTo({center:[lng,lat],bearing:0,pitch:0});});new ResizeObserver(()=>{maps.forEach(m=>m.resize());if(ready)fitOverview();}).observe($('.map-area'));
}catch(error){console.error(error);$('#map-status').hidden=false;$('#map-status').innerHTML='No se pudo iniciar el mapa. <button id="retry">Reintentar</button>';$('#retry').onclick=()=>location.reload();}}

let theme:Theme='auto';
try{theme=readTheme(localStorage.getItem('pais-theme'));}catch{}
function applyTheme(){
  document.documentElement.dataset.theme=theme==='auto'?solarTheme(new Date()):theme;
  document.querySelectorAll<HTMLButtonElement>('button[data-theme]').forEach(button=>{
    button.setAttribute('aria-pressed',String(button.dataset.theme===theme));
  });
}
function setTheme(next:Theme){
  theme=next;
  try{localStorage.setItem('pais-theme',next);}catch{}
  applyTheme();
}
async function toggleFullscreen(){
  try{
    if(document.fullscreenElement)await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  }catch{toast('La pantalla completa no está disponible en este navegador.');}
}
applyTheme();
setInterval(()=>{if(theme==='auto')applyTheme();},30_000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)applyTheme();});
new ResizeObserver(fitRail).observe($('.category-nav'));
document.fonts.ready.then(fitRail);
$('#brand-menu').onclick=()=>expandRail();$('#more-categories').onclick=()=>expandRail(true);document.querySelectorAll<HTMLButtonElement>('[data-category]').forEach(b=>b.onclick=()=>categoryPanel(b.dataset.category!));
$('#drawer-close').onclick=closeDrawer;$('#filters-open').onclick=filtersPanel;$('#search-open').onclick=searchPanel;$('#appearance-open').onclick=appearancePanel;$('#sources-open').onclick=()=>showCatalog();$('#about-open').onclick=about;$('#timeline-info').onclick=seriesInfo;
document.addEventListener('fullscreenchange',()=>{
  const button=$('#fullscreen');
  if(button){
    const full=Boolean(document.fullscreenElement);
    button.innerHTML=icon(full?'minimize':'maximize')+(full?' Salir de pantalla completa':' Pantalla completa');
    icons();
  }
  maps.forEach(m=>m.resize());
});
$('#modal-close').onclick=closeModal;$('#modal').addEventListener('close',()=>{modalController?.abort();priorFocus?.focus();});$('#modal').addEventListener('click',e=>{if(e.target===$('#modal')){const r=$('#modal').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeModal();}});
function stopPlaying(){clearInterval(playing);playing=undefined;$('#play').innerHTML=icon('play');$('#play').setAttribute('aria-label','Reproducir evolución');icons();}
$('#year').oninput=e=>{stopPlaying();year=years[Number((e.target as HTMLInputElement).value)];updateData();};$('#play').onclick=()=>{if(!ready)return;if(playing){stopPlaying();return;}$('#play').innerHTML=icon('pause');$('#play').setAttribute('aria-label','Pausar evolución');icons();playing=setInterval(()=>{year=years[(years.indexOf(year)+1)%years.length];updateData();},1100);};
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$<HTMLDialogElement>('#modal').open&&!layerMenu?.back())closeDrawer();if(e.key==='/'&&!(e.target as HTMLElement).matches('input,textarea,select')&&!$<HTMLDialogElement>('#modal').open){e.preventDefault();if(drawerTab==='search')$<HTMLInputElement>('#place-search').focus();else searchPanel();}});window.addEventListener('pagehide',()=>{stopPlaying();featureQuery?.abort();});
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
