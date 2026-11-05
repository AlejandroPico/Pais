import * as maplibregl from 'maplibre-gl';
import { type Map as AtlasMap, type ExpressionSpecification } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import {createIcons, Layers3, Search, ChevronDown, ChevronRight, X, ArrowUpRight, MapPin, Mountain, Globe2, Map, PanelLeftClose, PanelLeftOpen, Plus, Minus, Compass, RotateCcw, Play, Pause, Info, Download, Link, Check, Users, Waves, TrainFront, Route, Footprints, Scan, SlidersHorizontal, ExternalLink, ArrowLeft, BookOpen, Database, MoveUpRight, LocateFixed, ChartNoAxesCombined, Github} from 'lucide';
import packageInfo from '../package.json';
import {formatValue, labels, normalize, scales, units, valueFor, safeUrl, type Metric, type Population, type Properties} from './data';
import {sources, overlays} from './sources';
import './style.css';
import type {Feature, FeatureCollection, MultiPolygon} from 'geojson';
maplibregl.setWorkerUrl(workerUrl);

const $ = <T extends HTMLElement = HTMLElement>(q: string) => document.querySelector<T>(q)!;
const icon = (name: string, cls = '') => `<i data-lucide="${name}" class="${cls}" aria-hidden="true"></i>`;
const icons = () => createIcons({icons:{Layers3,Search,ChevronDown,ChevronRight,X,ArrowUpRight,MapPin,Mountain,Globe2,Map,PanelLeftClose,PanelLeftOpen,Plus,Minus,Compass,RotateCcw,Play,Pause,Info,Download,Link,Check,Users,Waves,TrainFront,Route,Footprints,Scan,SlidersHorizontal,ExternalLink,ArrowLeft,BookOpen,Database,MoveUpRight,LocateFixed,ChartNoAxesCombined,Github}});
const esc = (s: unknown) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
type Geo = FeatureCollection<MultiPolygon, Properties>;
type Catalog = {generatedAt:string;scope:string;errors:unknown[];operations:{Id:number;Nombre:string;Url?:string;Codigo:string;geographic:boolean;error?:string;tables:{Id:number;Nombre:string;Codigo?:string;Anyo_Periodo_ini?:string;Anyo_Periodo_fin?:string}[]}[]};
let map: AtlasMap;
let provinces: Geo, communities: Geo, population: Population;
let catalog: Catalog | undefined;
let ready = false;
let years: number[] = [];
const hash = new URLSearchParams(location.hash.slice(1));
let year = Number(hash.get('year')) || 2021;
let metric: Metric = (['population','density','women','change'].includes(hash.get('metric') || '') ? hash.get('metric') : 'density') as Metric;
let thematic = hash.get('data') === '1';
let level: 'province' | 'community' = hash.get('level') === 'community' ? 'community' : 'province';
let base = ['terrain','satellite','street'].includes(hash.get('base') || '') ? hash.get('base')! : 'terrain';
let tilted = hash.get('flat') !== '1';
let opacity = 0.73;
let selected: Feature<MultiPolygon, Properties> | undefined;
let active = new Set((hash.get('layers') || '').split(',').filter(id => overlays.some(o => o.id === id)));
let overlayOpacity: Record<string,number> = {};
let showCommunities = true, showProvinces = true;
let playing: ReturnType<typeof setInterval> | undefined;
let priorFocus: HTMLElement | null = null;
let modalController: AbortController | undefined;
let sourceErrors = new Set<string>();
let featureQuery: AbortController | undefined;

$('#app').innerHTML = `
<header class="topbar"><a class="brand" href="./" aria-label="El país, inicio"><span class="brand-symbol">${icon('mountain')}</span>El país<span class="brand-dot">.</span></a><span class="brand-caption">ATLAS ABIERTO DE ESPAÑA</span>
<nav aria-label="Navegación principal"><button class="nav-item current" id="explore">Explorar</button><button class="nav-item" id="catalog-open">Catálogo de datos ${icon('arrow-up-right')}</button></nav>
<div class="header-actions" aria-label="Información y enlaces"><span class="edition-label"><span class="live-dot"></span> PRIMERA EDICIÓN</span><a class="header-icon" href="https://github.com/AlejandroPico/Pais" target="_blank" rel="noopener" title="Repositorio del proyecto" aria-label="Repositorio del proyecto">${icon('github')}</a><button class="header-icon" id="about-open" title="Acerca de" aria-label="Acerca de">${icon('info')}</button></div></header>
<div class="workspace"><aside class="sidebar" id="sidebar" aria-label="Capas del mapa"><div class="sidebar-heading"><div><span class="eyebrow">TU FORMA DE VER ESPAÑA</span><h1>${icon('layers-3')} Capas del mapa</h1></div><button class="icon-button" id="collapse" title="Ocultar capas" aria-label="Ocultar capas">${icon('panel-left-close')}</button></div>
<div class="layer-search">${icon('search')}<input id="layer-search" type="search" placeholder="Buscar una capa…" aria-label="Buscar capas"><kbd>/</kbd></div>
<div class="sidebar-scroll"><section class="base-section"><div class="section-label">MAPA BASE <span>01</span></div><div class="base-options" role="group" aria-label="Mapa base">
<button data-base="terrain" class="base-card"><span class="base-art relief-art">${icon('mountain')}</span><span>Relieve</span></button><button data-base="satellite" class="base-card"><span class="base-art satellite-art">${icon('globe-2')}</span><span>Ortofoto</span></button><button data-base="street" class="base-card"><span class="base-art street-art">${icon('map')}</span><span>Callejero</span></button></div>
<button id="terrain-toggle" class="toggle-row"><span>${icon('mountain')} Terreno en 3D</span><span class="switch" aria-hidden="true"></span></button></section>
<div id="layer-groups">
<details class="layer-group" open data-search="organización territorial comunidades provincias municipios"><summary>${icon('scan')} Organización territorial ${icon('chevron-down')}</summary><div class="group-content">
<label class="check-row"><input type="checkbox" id="communities-toggle" checked><span>Comunidades autónomas</span><span class="line-sample community-line"></span></label>
<label class="check-row"><input type="checkbox" id="provinces-toggle" checked><span>Provincias</span><span class="line-sample province-line"></span></label>
<div id="municipal-slot"></div><button class="quiet-link" id="comarcas-info">¿Y las comarcas? ${icon('info')}</button></div></details>
<details class="layer-group" open data-search="población demografía densidad habitantes mujeres crecimiento"><summary>${icon('users')} Población y sociedad <span class="small-tag">INE</span>${icon('chevron-down')}</summary><div class="group-content">
${(['density','population','women','change'] as Metric[]).map(m=>`<label class="check-row metric-row"><input name="metric" type="radio" value="${m}"><span>${labels[m]}</span>${m==='density'?'<span class="small-tag green">HISTÓRICO</span>':''}</label>`).join('')}
<button class="quiet-link" id="clear-metric">Ocultar datos de población</button><div class="resolution"><label for="level">Mostrar por</label><select id="level"><option value="province">Provincia</option><option value="community">Comunidad autónoma</option></select></div></div></details>
<div id="overlay-groups"></div><div class="no-results" id="no-layer-results" hidden>No hay capas con ese nombre.<br><button class="quiet-link" id="search-catalog">Buscar en el catálogo del INE ${icon('arrow-up-right')}</button></div>
</div><div class="more-data"><span class="more-data-symbol">${icon('database')}</span><div><strong>El mapa acaba de empezar.</strong><p>Descubre las fuentes y los datos<br>que estamos reuniendo.</p><button id="more-sources">Explorar el catálogo ${icon('arrow-up-right')}</button></div></div></div>
<div class="sidebar-footer"><span class="live-dot"></span><span id="active-count">Preparando el atlas…</span><button id="sources-open" title="Ver fuentes y licencias" aria-label="Ver fuentes y licencias">${icon('info')}</button></div></aside>
<main class="map-area" aria-label="Explorador geográfico de España"><div id="map" aria-label="Mapa interactivo. Usa los botones de zoom y el buscador para explorar España."></div>
<button id="expand" class="floating-button expand" aria-label="Mostrar capas" title="Mostrar capas" hidden>${icon('panel-left-open')} Capas</button>
<div class="map-intro"><div class="eyebrow"><span></span> UNA NUEVA MIRADA A ESPAÑA</div><h2>Un territorio.<br><em>Infinitas miradas.</em></h2><p>Explora lo que somos, capa a capa.</p></div>
<div class="place-search"><div class="place-input">${icon('search')}<input type="search" id="place-search" placeholder="Busca una provincia o comunidad" aria-label="Buscar provincia o comunidad" autocomplete="off" aria-controls="place-results" aria-expanded="false"><kbd>⌕</kbd></div><div id="place-results" class="place-results" hidden></div></div>
<div class="map-tools"><button class="tool" id="zoom-in" title="Acercar" aria-label="Acercar">${icon('plus')}</button><button class="tool" id="zoom-out" title="Alejar" aria-label="Alejar">${icon('minus')}</button><span></span><button class="tool" id="north" title="Orientar al norte" aria-label="Orientar al norte">${icon('compass')}</button><button class="tool" id="reset" title="Vista de España" aria-label="Vista de España">${icon('locate-fixed')}</button></div>
<div class="view-tools"><button id="view-toggle">${icon('mountain')} <span>Vista 3D</span></button><button id="share" title="Copiar enlace al mapa" aria-label="Copiar enlace al mapa">${icon('link')}</button></div>
<div class="territory-shortcuts"><button id="canaries" class="canaries-card" title="Explorar las islas Canarias"><svg id="canaries-map" viewBox="0 0 180 64" aria-hidden="true"></svg><span>ISLAS CANARIAS ${icon('move-up-right')}</span></button><div><button data-place="ceuta">Ceuta ${icon('arrow-up-right')}</button><button data-place="melilla">Melilla ${icon('arrow-up-right')}</button></div></div>
<section id="info-panel" class="info-panel" aria-label="Información del territorio" hidden></section>
<div id="legend" class="legend" hidden></div><div id="overlay-legend" class="overlay-legend" hidden></div>
<div class="map-status" id="map-status" role="status">${icon('rotate-ccw')} Cargando cartografía oficial…</div>
<div class="map-caption">ESPAÑA <span>·</span> PENÍNSULA, ISLAS Y CIUDADES AUTÓNOMAS</div>
<section id="timeline" class="timeline" aria-label="Evolución temporal" hidden><button id="play" aria-label="Reproducir evolución" title="Reproducir evolución">${icon('play')}</button><div class="timeline-label"><span>SERIE HISTÓRICA · INE</span><strong id="year-value">2021</strong></div><div class="timeline-track"><input id="year" type="range" min="0" max="24" step="1" aria-label="Año de los datos"><div class="timeline-ticks"><span>1996</span><span>2005</span><span>2013</span><span>2021</span></div></div><button id="timeline-info" class="icon-button" aria-label="Información de la serie histórica" title="Información de la serie">${icon('info')}</button></section>
</main></div><div class="toast" id="toast" role="status" hidden></div>
<dialog id="modal" aria-labelledby="modal-title"><div class="modal-top"><span class="eyebrow">EL PAÍS · ATLAS ABIERTO</span><button class="icon-button" id="modal-close" aria-label="Cerrar ventana">${icon('x')}</button></div><div id="modal-body"></div></dialog>`;

function overlayRow(o: typeof overlays[number]) {
  return `<div class="overlay-entry"><label class="check-row"><input type="checkbox" data-overlay="${o.id}" ${active.has(o.id)?'checked':''}><span>${o.name}</span>${icon(o.icon,'row-icon')}</label><div class="overlay-controls" id="control-${o.id}" ${active.has(o.id)?'':'hidden'}><p>${o.note}</p><label>Opacidad <input type="range" min="10" max="100" value="85" data-opacity="${o.id}" aria-label="Opacidad de ${o.name}"></label></div></div>`;
}
$('#municipal-slot').innerHTML = overlayRow(overlays.find(o=>o.id==='municipal')!);
$('#overlay-groups').innerHTML = ['Agua y naturaleza','Movilidad y recorridos'].map(g=>`<details class="layer-group" open data-search="${normalize(g+' '+overlays.filter(o=>o.group===g).map(o=>o.name).join(' '))}"><summary>${icon(g==='Agua y naturaleza'?'waves':'route')}${g}${icon('chevron-down')}</summary><div class="group-content">${overlays.filter(o=>o.group===g).map(overlayRow).join('')}</div></details>`).join('');
icons();

let toastTimeout: ReturnType<typeof setTimeout>;
function toast(message: string) { $('#toast').textContent = message; $('#toast').hidden = false; clearTimeout(toastTimeout); toastTimeout = setTimeout(()=>$('#toast').hidden=true,6500); }
function syncUrl() {
  if (!ready) return;
  const c = map.getCenter();
  const params = new URLSearchParams({base,metric,year:String(year),level,data:thematic?'1':'0',flat:tilted?'0':'1',lng:c.lng.toFixed(4),lat:c.lat.toFixed(4),z:map.getZoom().toFixed(2),layers:[...active].join(',')});
  history.replaceState(null,'',`#${params}`);
}
function extent(feature: Feature<MultiPolygon,Properties>): [[number,number],[number,number]] {
  const points = feature.geometry.coordinates.flat(2);
  return [[Math.min(...points.map(p=>p[0])), Math.min(...points.map(p=>p[1]))],[Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))]];
}
function home() {map.fitBounds([[-11,34.2],[6,45]],{padding:{top:145,bottom:120,left:30,right:60},pitch:tilted?35:0,bearing:0,duration:1200});}
function selectedGeo() { return level==='province'?provinces:communities; }
function labelPoints() {
  return {type:'FeatureCollection' as const,features:provinces.features.map(f=>{
    const largest=[...f.geometry.coordinates].sort((a,b)=>b[0].length-a[0].length)[0][0];
    const xs=largest.map(p=>p[0]), ys=largest.map(p=>p[1]);
    return {type:'Feature' as const,properties:f.properties,geometry:{type:'Point' as const,coordinates:[(Math.min(...xs)+Math.max(...xs))/2,(Math.min(...ys)+Math.max(...ys))/2]}};
  })};
}
function addWms(o: typeof overlays[number]) {
  const tile = `${o.url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=${encodeURIComponent(o.layers)}&STYLES=${encodeURIComponent('styles' in o ? o.styles! : '')}&FORMAT=image/png&TRANSPARENT=TRUE&SRS=EPSG:3857&WIDTH=256&HEIGHT=256&BBOX={bbox-epsg-3857}`;
  map.addSource(o.id,{type:'raster',tiles:[tile],tileSize:256,bounds:[-18.5,27,4.7,44],attribution:'© IGN · CC BY 4.0'});
  map.addLayer({id:o.id,type:'raster',source:o.id,minzoom:o.minzoom || 0,layout:{visibility:active.has(o.id)?'visible':'none'},paint:{'raster-opacity':overlayOpacity[o.id]??0.85}},'province-lines');
}
function updateData() {
  if (!ready) return;
  for (const l of ['province','community'] as const) {
    const geo = l==='province'?provinces:communities;
    geo.features.forEach(f=>{
      const value = valueFor(population.data[l][f.properties.code],year,metric,f.properties.areaKm2);
      map.setFeatureState({source:l,id:f.id!},{value: value ?? -999999,missing:value===null});
    });
    const scale = scales[metric];
    const color = ['interpolate',['linear'],['feature-state','value'],...scale.stops.flatMap((stop,i)=>[stop,scale.colors[i]])] as ExpressionSpecification;
    map.setPaintProperty(`${l}-fill`,'fill-color',['case',['boolean',['feature-state','missing'],true],'#b8b6aa',color]);
    map.setPaintProperty(`${l}-fill`,'fill-opacity',thematic&&l===level?opacity:0);
  }
  $('#timeline').hidden = !thematic;
  $('#legend').hidden = !thematic;
  if (thematic) {
    const scale = scales[metric];
    $('#legend').innerHTML = `<div class="legend-title"><strong>${labels[metric]}</strong><span>${year}</span></div><p>${units[metric]} · ${level==='province'?'provincias':'comunidades'}</p><div class="color-scale" style="background:linear-gradient(90deg,${scale.colors.join(',')})"></div><div class="scale-labels"><span>${formatValue(scale.stops[0],metric)}</span><span>${formatValue(scale.stops[3],metric)}</span><span>≥ ${formatValue(scale.stops[6],metric)}</span></div><label class="legend-opacity">Opacidad <input id="thematic-opacity" type="range" min="10" max="100" value="${opacity*100}" aria-label="Opacidad de la capa estadística"></label><div class="legend-credit"><span class="missing-swatch"></span>Sin datos <span>INE · CC BY 4.0</span></div>`;
    $('#thematic-opacity').addEventListener('input',e=>{opacity=Number((e.target as HTMLInputElement).value)/100;map.setPaintProperty(`${level}-fill`,'fill-opacity',opacity);});
  }
  $('#year-value').textContent=String(year);
  const slider=$<HTMLInputElement>('#year'); slider.max=String(years.length-1); slider.value=String(years.indexOf(year)); slider.setAttribute('aria-valuetext',String(year));
  document.querySelectorAll<HTMLInputElement>('[name="metric"]').forEach(i=>i.checked=thematic&&i.value===metric);
  $<HTMLSelectElement>('#level').value=level;
  $('#active-count').textContent=`${Number(showCommunities)+Number(showProvinces)+Number(thematic)+active.size} capas activas · fuentes abiertas`;
  const visibleOverlays=overlays.filter(o=>active.has(o.id));
  $('#overlay-legend').hidden=!visibleOverlays.length;
  $('#overlay-legend').innerHTML=visibleOverlays.map(o=>`<span>${icon(o.icon)}${o.name}${map.getZoom()<(o.minzoom||0)?' · acerca el mapa':''}</span>`).join('');
  if(selected)renderInfo();
  icons();syncUrl();
}
function setBase(next:string) {
  base=next;
  if(ready)for(const b of ['terrain','satellite','street']) map.setLayoutProperty(`base-${b}`,'visibility',b===base?'visible':'none');
  document.querySelectorAll<HTMLButtonElement>('[data-base]').forEach(b=>{b.classList.toggle('selected',b.dataset.base===base);b.setAttribute('aria-pressed',String(b.dataset.base===base));});
  if(ready)syncUrl();
}
function terrain() {
  if(ready){map.setTerrain(tilted?{source:'dem',exaggeration:1.5}:null);map.easeTo({pitch:tilted?50:0,duration:800});}
  $('#terrain-toggle').setAttribute('aria-pressed',String(tilted));$('#terrain-toggle').classList.toggle('enabled',tilted);
  $('#view-toggle span').textContent=tilted?'Vista 3D':'Vista 2D';syncUrl();
}
function selectTerritory(feature: Feature<MultiPolygon,Properties>, zoom=false) {
  selected=feature;
  map.getSource('selection') && (map.getSource('selection') as maplibregl.GeoJSONSource).setData(feature);
  renderInfo();
  if(zoom)map.fitBounds(extent(feature),{padding:{top:95,bottom:180,left:35,right:innerWidth>1000?360:35},maxZoom:10,duration:1100,pitch:tilted?35:0});
}
async function queryObjects(lng:number,lat:number){
  featureQuery?.abort();featureQuery=new AbortController();const controller=featureQuery;
  const enabled=overlays.filter(o=>active.has(o.id)&&map.getZoom()>=(o.minzoom||0));
  if(!enabled.length)return;
  if(!selected){$('#info-panel').hidden=false;$('#info-panel').innerHTML=`<div class="info-heading"><span class="eyebrow">CONSULTA DEL MAPA</span><button id="info-close" class="icon-button" aria-label="Cerrar información">${icon('x')}</button></div><h3>En este lugar</h3><p class="data-note">${lat.toFixed(5)}, ${lng.toFixed(5)} · coordenadas del punto consultado</p>`;$('#info-close').onclick=()=>{controller.abort();$('#info-panel').hidden=true;};}
  let panel=$('#object-results');if(!panel){panel=document.createElement('div');panel.id='object-results';$('#info-panel').append(panel);}panel.innerHTML='<p class="data-note" role="status">Consultando las capas activas…</p>';
  const x=6378137*lng*Math.PI/180,y=6378137*Math.log(Math.tan(Math.PI/4+lat*Math.PI/360));
  const radius=156543.033928/2**map.getZoom()*7;
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
  $('#info-close').onclick=()=>{featureQuery?.abort();selected=undefined;$('#info-panel').hidden=true;(map.getSource('selection') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features:[]});};
  $('#download-territory').onclick=()=>{
    if(!t){toast('Este territorio no tiene observaciones en la serie del INE.');return;}
    const lines=['codigo;territorio;anio;poblacion;hombres;mujeres;superficie_aprox_km2;fuente',...years.map(y=>`${p.code};"${p.name.replace(/"/g,'""')}";${y};${t.series[y]?.['0']??''};${t.series[y]?.['1']??''};${t.series[y]?.['2']??''};${p.areaKm2};INE tablas 2852 y 2853`)].join('\r\n');
    download(`poblacion-${p.code}.csv`,'\uFEFF'+lines,'text/csv;charset=utf-8');
  };icons();
}
function download(name:string,content:string,type:string){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}

function openModal(html:string){
  priorFocus=document.activeElement as HTMLElement;
  modalController?.abort();modalController=new AbortController();
  $('#modal-body').innerHTML=html;const d=$<HTMLDialogElement>('#modal');if(!d.open)d.showModal();icons();
}
function about(){openModal(`
  <div class="about-brand"><img src="${import.meta.env.BASE_URL}favicon.svg" alt="Icono de El país" width="66" height="66"><div><h2 id="modal-title">El país<span>.</span></h2><span class="version-badge">Versión ${packageInfo.version} · Primera edición</span></div></div>
  <p class="about-tagline">Un país, todas sus capas.</p>
  <p class="modal-lead">Un atlas abierto para descubrir España a través de sus datos. Un lugar donde la información pública se pueda encontrar, entender y recorrer sobre el territorio.</p>
  <h3>La idea</h3><p>Reunir toda la información que pueda representarse sobre España: desde su población y su historia hasta sus bosques, viviendas, elecciones, vías de tren, senderos y aguas. Organizarla por temas, combinar capas y consultar cada lugar sin tener que recorrer innumerables tablas y portales.</p>
  <div class="about-grid"><article>${icon('layers-3')}<h3>Un mapa que se construye</h3><p>España como protagonista, con sus islas, ciudades autónomas y contexto marítimo. Del conjunto del país al detalle territorial que permita cada fuente.</p></article><article>${icon('book-open')}<h3>Datos con memoria</h3><p>Conocer qué ocurre y cómo cambia. Cada serie conserva su procedencia, sus años y sus límites; la falta de información se muestra como tal.</p></article></div>
  <h3>Qué incluye la versión ${packageInfo.version}</h3><p>Relieve elevado en 3D, ortofoto PNOA, callejero y límites oficiales. Población histórica de 1996 a 2021, densidad aproximada, proporción de mujeres y cambio desde 1996, por provincia o comunidad, con cronograma y descarga. Ríos, ferrocarriles, carreteras, caminos de Santiago y municipios como capas oficiales de imagen. Un inventario buscable de operaciones y tablas del INE y un directorio de fuentes.</p>
  <h3>Hacia dónde va</h3><p>Ampliar las series recientes e históricas y el detalle municipal; incorporar renta, vivienda, elecciones, clima, bosques, acuíferos y medio marino. Añadir comarcas y otras divisiones según su cobertura oficial. La intención es crecer sin excluir temas por parecer pequeños o poco habituales: si hay datos públicos útiles para el mapa, tienen un lugar aquí.</p>
  <p class="callout">Este atlas está en construcción. Una tabla catalogada todavía puede estar pendiente de descargar y adaptar. El cronograma modifica la estadística seleccionada, no la fecha del mapa base. Proyecto independiente, sin afiliación a los organismos citados.</p>
  <div class="about-links"><a class="primary-link" href="https://github.com/AlejandroPico/Pais" target="_blank" rel="noopener">${icon('github')} Repositorio del proyecto ${icon('arrow-up-right')}</a><a class="secondary-link" href="https://alejandropico.github.io/Portfolio/" target="_blank" rel="noopener">Portfolio de Alejandro Pico ${icon('arrow-up-right')}</a></div>
`);}
function seriesInfo(){openModal(`<h2 id="modal-title">Viajar en el tiempo, con contexto.</h2><p class="modal-lead">${esc(population?.note||'Serie histórica del Padrón municipal del INE.')}</p><ul class="method-list"><li>Fuente: INE, tablas 2852 (provincias) y 2853 (comunidades).</li><li>Datos a 1 de enero de cada año publicado, 1996–2021. El control salta 1997 porque la serie no lo contiene.</li><li>El cronograma cambia únicamente la capa estadística. Las imágenes, las redes y los límites corresponden a sus propios servicios y fechas.</li><li>La densidad usa superficie esférica aproximada calculada sobre los límites actuales del IGN; no sustituye a una densidad oficial.</li><li>Las fronteras históricas, las series recientes de otros censos y las rupturas metodológicas se integrarán de forma explícita.</li></ul><a href="https://www.ine.es/jaxiT3/Tabla.htm?t=2852" target="_blank" rel="noopener" class="primary-link">Consultar la serie original ${icon('arrow-up-right')}</a>`);}
async function showCatalog(tab='ine'){
  openModal(`<h2 id="modal-title">Un país de datos.</h2><p class="modal-lead">Fuentes abiertas, organizadas para empezar a explorar.</p><div class="catalog-tabs" role="tablist"><button data-tab="ine" role="tab">Inventario INE</button><button data-tab="sources" role="tab">Fuentes y licencias</button></div><div id="catalog-content"><p role="status">Cargando inventario…</p></div>`);
  document.querySelectorAll<HTMLButtonElement>('[data-tab]').forEach(b=>b.onclick=()=>renderTab(b.dataset.tab!));
  renderTab(tab);
}
async function renderTab(tab:string){
  document.querySelectorAll<HTMLButtonElement>('[data-tab]').forEach(b=>{b.classList.toggle('selected',b.dataset.tab===tab);b.setAttribute('aria-selected',String(b.dataset.tab===tab));});
  if(tab==='sources'){
    $('#catalog-content').innerHTML=`<p class="catalog-note">Integrado = hay capas utilizables. Por integrar = fuente identificada, aún sin datos en este mapa. Las capas de imagen requieren conexión al organismo.</p><div class="sources-grid">${sources.map(s=>`<article class="source-card"><div><span class="source-code">${s.short}</span><span class="status-tag ${s.status==='Integrado'?'integrated':''}">${s.status}</span></div><h3>${s.name}</h3><p class="source-topic">${s.topic}</p><p>${s.detail}</p><a href="${s.url}" target="_blank" rel="noopener">Consultar fuente ${icon('arrow-up-right')}</a></article>`).join('')}</div><p class="catalog-note">Proyecto independiente, sin afiliación a los organismos citados. Datos estadísticos y límites: sus respectivas licencias. Relieve 3D: <a href="https://github.com/tilezen/joerd/blob/master/docs/attribution.md" target="_blank" rel="noopener">créditos de los modelos originales</a>. El mapa base callejero procede del IGN.</p>`;icons();return;
  }
  try{if(!catalog)catalog=await load<Catalog>('ine-catalog.json');}catch{if($('[data-tab="ine"]')?.classList.contains('selected'))$('#catalog-content').innerHTML='<p>No se pudo cargar el catálogo. Cierra esta ventana y vuelve a intentarlo.</p>';return;}
  if(!$('[data-tab="ine"]')?.classList.contains('selected'))return;
  const unique=new Set(catalog.operations.flatMap(o=>o.tables.map(t=>t.Id)));
  $('#catalog-content').innerHTML=`<div class="catalog-stats"><div><strong>${catalog.operations.length}</strong><span>operaciones</span></div><div><strong>${unique.size.toLocaleString('es-ES')}</strong><span>tablas únicas catalogadas</span></div><div><strong>${catalog.operations.filter(o=>o.geographic).length}</strong><span>operaciones con geografía</span></div></div><p class="catalog-note">${esc(catalog.scope)} Inventario consultado el ${new Date(catalog.generatedAt).toLocaleDateString('es-ES')}.${catalog.errors.length?` ${catalog.errors.length} operaciones no pudieron enumerarse; consulta el archivo de errores.`:''}</p><div class="catalog-filters"><label class="layer-search">${icon('search')}<input id="catalog-search" type="search" placeholder="Buscar vivienda, empleo, agricultura…" aria-label="Buscar operaciones y tablas del INE"></label><label class="catalog-geo"><input id="geo-only" type="checkbox"> Con desglose geográfico</label></div><p id="catalog-count" class="catalog-note"></p><div id="catalog-results"></div><a class="download-catalog" href="./data/ine-catalog.json" download>Descargar inventario completo (JSON) ${icon('download')}</a>`;
  $('#catalog-search').addEventListener('input',filterCatalog);$('#geo-only').addEventListener('change',filterCatalog);filterCatalog();icons();
}
function filterCatalog(){
  const q=normalize($<HTMLInputElement>('#catalog-search').value.trim());const geo=$<HTMLInputElement>('#geo-only').checked;
  const results=catalog!.operations.filter(o=>(!geo||o.geographic)&&(!q||normalize(o.Nombre+' '+o.Codigo).includes(q)||o.tables.some(t=>normalize(t.Nombre).includes(q))));
  $('#catalog-count').textContent=`${results.length} operaciones encontradas · las tablas se abren en el INE`;
  $('#catalog-results').innerHTML=results.length?results.map(o=>{
    const matchName=normalize(o.Nombre+' '+o.Codigo).includes(q);
    const tables=o.tables.filter(t=>!q||matchName||normalize(t.Nombre).includes(q));
    return `<details class="operation"><summary><span><strong>${esc(o.Nombre)}</strong><small>${esc(o.Codigo)} · ${o.tables.length} tablas${o.geographic?' · con geografía':''}</small></span>${icon('chevron-down')}</summary><div class="operation-tables">${o.error?'<p>No se pudieron enumerar las tablas de esta operación.</p>':''}${tables.map(t=>`<a href="https://www.ine.es/jaxiT3/Tabla.htm?t=${encodeURIComponent(t.Id)}" target="_blank" rel="noopener"><span>${esc(t.Nombre)}<small>Tabla ${esc(t.Id)} · ${esc(t.Codigo||'desglose por verificar')}${t.Anyo_Periodo_ini?' · desde '+esc(t.Anyo_Periodo_ini):''}</small></span>${icon('arrow-up-right')}</a>`).join('')}<a class="operation-source" href="${esc(safeUrl(o.Url,'https://www.ine.es/datosabiertos/'))}" target="_blank" rel="noopener">Página de la operación ${icon('external-link')}</a></div></details>`;
  }).join(''):'<p class="empty-state">No hay resultados. Prueba con otra palabra o desactiva el filtro geográfico.</p>';icons();
}

async function load<T>(file:string):Promise<T>{const r=await fetch(`${import.meta.env.BASE_URL}data/${file}`);if(!r.ok)throw new Error(`${file}: ${r.status}`);return r.json();}
async function init(){
  try{
    [provinces,communities,population]=await Promise.all([load<Geo>('provinces.geojson'),load<Geo>('communities.geojson'),load<Population>('population.json')]);
    years=Object.keys(population.data.province['00'].series).map(Number).sort((a,b)=>a-b);if(!years.includes(year))year=years.at(-1)!;
    const lng=Number(hash.get('lng')),lat=Number(hash.get('lat')),z=Number(hash.get('z'));
    map=new maplibregl.Map({container:'map',center:[-3.8,39.7],zoom:5.6,pitch:tilted?35:0,maxZoom:18,minZoom:3,maxBounds:[[-20.5,25.5],[7,46.5]],renderWorldCopies:false,attributionControl:{compact:true},style:{version:8,glyphs:'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',sources:{
      terrain:{type:'raster',tiles:['https://tms-relieve.idee.es/1.0.0/relieve/{z}/{x}/{y}.jpeg'],scheme:'tms',tileSize:256,maxzoom:16,attribution:'© <a href="https://www.ign.es/">IGN</a> · CC BY 4.0'},
      satellite:{type:'raster',tiles:['https://www.ign.es/wmts/pnoa-ma?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=OI.OrthoimageCoverage&STYLE=default&FORMAT=image/jpeg&TILEMATRIXSET=GoogleMapsCompatible&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}'],tileSize:256,maxzoom:19,attribution:'<a href="https://pnoa.ign.es/">PNOA</a> © IGN y colaboradores · CC BY 4.0'},
      street:{type:'raster',tiles:['https://www.ign.es/wmts/ign-base?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=IGNBaseTodo&STYLE=default&FORMAT=image/png&TILEMATRIXSET=GoogleMapsCompatible&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}'],tileSize:256,maxzoom:19,attribution:'© IGN y colaboradores · CC BY 4.0'},
      dem:{type:'raster-dem',tiles:['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],encoding:'terrarium',tileSize:256,maxzoom:14,attribution:'<a href="https://github.com/tilezen/joerd/blob/master/docs/attribution.md">DEM: Mapzen / USGS et al.</a>'}
    },layers:[{id:'background',type:'background',paint:{'background-color':'#c8d8d8'}},...['terrain','satellite','street'].map(b=>({id:`base-${b}`,type:'raster' as const,source:b,layout:{visibility:b===base?'visible' as const:'none' as const},paint:{'raster-fade-duration':200}}))]}});
    map.addControl(new maplibregl.ScaleControl({maxWidth:120,unit:'metric'}),'bottom-left');
    map.on('error',e=>{
      const source=(e as unknown as {sourceId?:string}).sourceId || 'map';
      sourceErrors.add(source);$('#map-status').classList.add('warning');$('#map-status').hidden=false;$('#map-status').textContent='Algún servicio cartográfico no responde. Puedes cambiar el mapa base.';
      console.warn('Cartographic service error',e.error?.message);
    });
    map.on('load',()=>{
      map.addSource('context',{type:'geojson',data:`${import.meta.env.BASE_URL}data/context-mask.geojson`});
      map.addLayer({id:'muted-surroundings',type:'fill',source:'context',paint:{'fill-color':'#edf0e5','fill-opacity':0.73}});
      for(const l of ['province','community'] as const){map.addSource(l,{type:'geojson',data:l==='province'?provinces:communities});map.addLayer({id:`${l}-fill`,type:'fill',source:l,paint:{'fill-opacity':0,'fill-color':'#78a18a'}});}
      map.addLayer({id:'province-lines',type:'line',source:'province',paint:{'line-color':'#627f71','line-width':['interpolate',['linear'],['zoom'],4,.6,8,1.1,13,1.8],'line-opacity':.7}});
      map.addLayer({id:'community-lines',type:'line',source:'community',paint:{'line-color':'#244e41','line-width':['interpolate',['linear'],['zoom'],4,1.25,8,2.2,13,3],'line-opacity':.9}});
      map.addSource('selection',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
      map.addLayer({id:'selected-outline',type:'line',source:'selection',paint:{'line-color':'#d49744','line-width':3}});
      map.addSource('label-points',{type:'geojson',data:labelPoints()});
      map.addLayer({id:'province-labels',type:'symbol',source:'label-points',minzoom:5,layout:{'text-field':['get','name'],'text-font':['Noto Sans Regular'],'text-size':['interpolate',['linear'],['zoom'],5,10,9,13],'text-max-width':8},paint:{'text-color':'#274c40','text-halo-color':'#f6f5e9','text-halo-width':1.6}});
      overlays.forEach(addWms);
      if(tilted)map.setTerrain({source:'dem',exaggeration:1.5});
      ready=true;setBase(base);terrain();
      if(hash.has('lng')&&hash.has('lat')&&hash.has('z')&&Number.isFinite(lng)&&Number.isFinite(lat)&&Number.isFinite(z)&&lng>=-20&&lng<=8&&lat>=25&&lat<=47&&z>=3&&z<=18)map.jumpTo({center:[lng,lat],zoom:z});else home();
      updateData();drawCanaries();
      if(!sourceErrors.size)$('#map-status').hidden=true;
      map.on('moveend',()=>{syncUrl();if(active.has('municipal'))updateData();});
      map.on('click',e=>{const features=map.queryRenderedFeatures(e.point,{layers:[`${level}-fill`]});if(features[0]){const f=selectedGeo().features.find(f=>f.properties.code===features[0].properties.code);if(f)selectTerritory(f);}else{selected=undefined;$('#info-panel').hidden=true;(map.getSource('selection') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features:[]});}queryObjects(e.lngLat.lng,e.lngLat.lat);});
      map.on('mousemove',e=>{map.getCanvas().style.cursor=map.queryRenderedFeatures(e.point,{layers:[`${level}-fill`]}).length?'pointer':'';});
    });
  }catch(error){console.error(error);$('#map-status').hidden=false;$('#map-status').classList.add('warning');$('#map-status').innerHTML='No se ha podido iniciar el mapa. <button id="retry">Reintentar</button>';$('#retry').onclick=()=>location.reload();}
}
function drawCanaries(){
  const features=provinces.features.filter(f=>['35','38'].includes(f.properties.code));
  $('#canaries-map').innerHTML=features.flatMap(f=>f.geometry.coordinates.map(p=>`<path d="${p.map(r=>r.map((c,i)=>`${i?'L':'M'}${(c[0]+18.3)*43},${(29.5-c[1])*29}`).join(' ')+'Z').join(' ')}"/>`)).join('');
}

$('#catalog-open').onclick=()=>showCatalog();$('#more-sources').onclick=()=>showCatalog();$('#sources-open').onclick=()=>showCatalog('sources');$('#search-catalog').onclick=()=>showCatalog();$('#about-open').onclick=about;$('#comarcas-info').onclick=about;$('#timeline-info').onclick=seriesInfo;
$('#explore').onclick=()=>{if(ready)home();};
$('#modal-close').onclick=()=>{$<HTMLDialogElement>('#modal').close();};
$('#modal').addEventListener('close',()=>{modalController?.abort();priorFocus?.focus();});
$('#modal').addEventListener('click',e=>{if(e.target===$('#modal')){const r=$('#modal').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$<HTMLDialogElement>('#modal').close();}});
$('#collapse').onclick=()=>{$('#sidebar').classList.add('collapsed');$('#expand').hidden=false;setTimeout(()=>map?.resize(),250);};
$('#expand').onclick=()=>{$('#sidebar').classList.remove('collapsed');$('#expand').hidden=true;setTimeout(()=>map?.resize(),250);};
document.querySelectorAll<HTMLButtonElement>('[data-base]').forEach(b=>b.onclick=()=>setBase(b.dataset.base!));setBase(base);
$('#terrain-toggle').onclick=$('#view-toggle').onclick=()=>{tilted=!tilted;terrain();};terrain();
$('#zoom-in').onclick=()=>ready&&map.zoomIn();$('#zoom-out').onclick=()=>ready&&map.zoomOut();$('#north').onclick=()=>ready&&map.easeTo({bearing:0});$('#reset').onclick=()=>ready&&home();
$('#communities-toggle').onchange=e=>{showCommunities=(e.target as HTMLInputElement).checked;if(ready){map.setLayoutProperty('community-lines','visibility',showCommunities?'visible':'none');updateData();}};
$('#provinces-toggle').onchange=e=>{showProvinces=(e.target as HTMLInputElement).checked;if(ready){map.setLayoutProperty('province-lines','visibility',showProvinces?'visible':'none');map.setLayoutProperty('province-labels','visibility',showProvinces?'visible':'none');updateData();}};
document.querySelectorAll<HTMLInputElement>('[name="metric"]').forEach(input=>input.onchange=()=>{metric=input.value as Metric;thematic=true;updateData();});
$('#clear-metric').onclick=()=>{thematic=false;stopPlaying();updateData();};
$('#level').onchange=e=>{level=(e.target as HTMLSelectElement).value as typeof level;selected=undefined;$('#info-panel').hidden=true;if(ready)(map.getSource('selection') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features:[]});updateData();};
document.querySelectorAll<HTMLInputElement>('[data-overlay]').forEach(input=>input.onchange=()=>{
  const id=input.dataset.overlay!;if(input.checked)active.add(id);else active.delete(id);
  $(`#control-${id}`).hidden=!input.checked;
  if(ready){map.setLayoutProperty(id,'visibility',input.checked?'visible':'none');updateData();if(id==='municipal'&&input.checked&&map.getZoom()<8)toast('Los límites municipales aparecen al acercar el mapa (zoom 8 o superior).');}
});
document.querySelectorAll<HTMLInputElement>('[data-opacity]').forEach(i=>i.oninput=()=>{overlayOpacity[i.dataset.opacity!]=Number(i.value)/100;if(ready)map.setPaintProperty(i.dataset.opacity!,'raster-opacity',overlayOpacity[i.dataset.opacity!]);});
$('#layer-search').addEventListener('input',e=>{const q=normalize((e.target as HTMLInputElement).value);let count=0;document.querySelectorAll<HTMLDetailsElement>('.layer-group').forEach(g=>{const match=normalize(g.dataset.search||g.textContent||'').includes(q);g.hidden=!match;if(match){count++;if(q)g.open=true;}});$('#no-layer-results').hidden=!!count;});
$('#year').addEventListener('input',e=>{stopPlaying();year=years[Number((e.target as HTMLInputElement).value)];updateData();});
function stopPlaying(){clearInterval(playing);playing=undefined;$('#play').innerHTML=icon('play');$('#play').setAttribute('aria-label','Reproducir evolución');icons();}
$('#play').onclick=()=>{if(!ready)return;if(playing){stopPlaying();return;}$('#play').innerHTML=icon('pause');$('#play').setAttribute('aria-label','Pausar evolución');icons();playing=setInterval(()=>{const i=years.indexOf(year);year=years[(i+1)%years.length];updateData();},1100);};
$('#share').onclick=async()=>{syncUrl();try{await navigator.clipboard.writeText(location.href);toast('Enlace copiado. Incluye las capas, el año y la vista del mapa.');}catch{openModal(`<h2 id="modal-title">Comparte esta mirada.</h2><p>Copia este enlace para abrir las mismas capas y el mismo año.</p><input class="share-url" aria-label="Enlace al mapa" readonly value="${esc(location.href)}">`);$<HTMLInputElement>('.share-url').select();}};
$('#canaries').onclick=()=>ready&&map.fitBounds([[-18.3,27.5],[-13.3,29.5]],{padding:80,pitch:tilted?35:0,duration:1300});
document.querySelectorAll<HTMLButtonElement>('[data-place]').forEach(b=>b.onclick=()=>{if(ready){const f=provinces.features.find(f=>f.properties.code===(b.dataset.place==='ceuta'?'51':'52'));if(f){if(level!=='province'){level='province';updateData();}selectTerritory(f,true);}}});
$('#place-search').addEventListener('input',e=>{
  if(!ready)return;const q=normalize((e.target as HTMLInputElement).value.trim());const results=$('#place-results');
  if(!q){results.hidden=true;$<HTMLInputElement>('#place-search').setAttribute('aria-expanded','false');return;}
  const entries=[...provinces.features.map(f=>({f,l:'province' as const})),...communities.features.map(f=>({f,l:'community' as const}))].filter(({f})=>normalize(f.properties.name).includes(q)).slice(0,10);
  results.innerHTML=entries.length?entries.map(({f,l},i)=>`<button data-result="${i}">${icon('map-pin')}<span>${esc(f.properties.name)}<small>${l==='province'?'Provincia / ciudad autónoma':'Comunidad / ciudad autónoma'}</small></span>${icon('arrow-up-right')}</button>`).join(''):'<p>No se encuentran territorios con ese nombre.</p>';results.hidden=false;$<HTMLInputElement>('#place-search').setAttribute('aria-expanded','true');icons();
  results.querySelectorAll<HTMLButtonElement>('button').forEach(b=>b.onclick=()=>{const entry=entries[Number(b.dataset.result)];level=entry.l;updateData();selectTerritory(entry.f,true);results.hidden=true;$<HTMLInputElement>('#place-search').value=entry.f.properties.name;$<HTMLInputElement>('#place-search').setAttribute('aria-expanded','false');});
});
$('#place-search').addEventListener('keydown',e=>{if(e.key==='ArrowDown'){e.preventDefault();$('#place-results button')?.focus();}if(e.key==='Enter')$('#place-results button')?.click();if(e.key==='Escape'){$('#place-results').hidden=true;$<HTMLInputElement>('#place-search').setAttribute('aria-expanded','false');}});
document.addEventListener('click',e=>{if(!(e.target as HTMLElement).closest('.place-search')){$('#place-results').hidden=true;$<HTMLInputElement>('#place-search').setAttribute('aria-expanded','false');}});
document.addEventListener('keydown',e=>{if(e.key==='/'&&!(e.target as HTMLElement).matches('input,textarea,select')&&!$<HTMLDialogElement>('#modal').open){e.preventDefault();$('#layer-search').focus();}});
window.addEventListener('pagehide',stopPlaying);
if(matchMedia('(max-width:600px)').matches){$('#sidebar').classList.add('collapsed');$('#expand').hidden=false;}
init();
