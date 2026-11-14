import {appearanceFields,bindAppearance,layerAppearance,paletteFor} from './layer-appearance';
import type {Map as AtlasMap,MapMouseEvent,GeoJSONSource,ExpressionSpecification} from 'maplibre-gl';
import type {FeatureCollection} from 'geojson';
import {projectCollection,shiftedIds} from './atlas-coordinates';
import {addShiftedLayer} from './atlas-geography';
import {municipalCode} from './territory-data';
import {defaultDimensions,periodOrder,periodTimestamp,seriesCsv,unitFor,relativeChange,type DemographicIndex,type DemographicTable,type DemographicQuery,type DemographicResult} from './demography-data';

const esc=(v:unknown)=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
const fmt=(v:number|null)=>v===null?'Sin datos':new Intl.NumberFormat('es-ES',{maximumFractionDigits:2}).format(v);
const levels:Record<string,string>={national:'España',community:'Comunidades',province:'Provincias',municipal:'Municipios',district:'Distritos (consulta de series)',section:'Secciones (consulta de series)',island:'Islas (consulta de series)',unlocated:'Sin asignación territorial'};
const colors=['#edf1d5','#c9dea7','#a0c68a','#70a87b','#43866a','#266153','#123f38'];
type Options={info:HTMLElement;onActivate:()=>void;closeDrawer:()=>void;clearSelection:()=>void};

const statisticsConfig={
  demography:{prefix:'f02',urlPrefix:'',legend:'Leyenda demográfica',timeline:'Evolución demográfica',toggle:'Representar datos demográficos'},
  welfare:{prefix:'f03',urlPrefix:'w',legend:'Leyenda de renta y condiciones de vida',timeline:'Evolución de renta y condiciones de vida',toggle:'Representar renta y condiciones de vida'},
  labor:{prefix:'f04',urlPrefix:'l',legend:'Leyenda de empleo y salarios',timeline:'Evolución de empleo y salarios',toggle:'Representar datos de empleo y salarios'},
} as const;
export type StatisticsKind=keyof typeof statisticsConfig;

export class DemographyController{
  private map!:AtlasMap;private geometries!:Record<string,FeatureCollection>;private indexPromise?:Promise<DemographicIndex>;private index?:DemographicIndex;
  private table?:DemographicTable;private enabled=false;private pending=false;private density=false;private growth=false;private baselines=new Map<string,number>();private get appearanceId(){return this.kind+'-'+this.table?.id;}
  private get alpha(){return layerAppearance(this.appearanceId).opacity??.76;}
  private query:DemographicQuery={period:0,dims:[],level:'province',territory:0};private province='28';private municipality='28079';
  private panel?:HTMLElement;private worker?:Worker;private request=0;private result?:DemographicResult;private timer?:ReturnType<typeof setTimeout>;
  private legend=document.createElement('section');private timeline=document.createElement('section');private status='';private hash:URLSearchParams;
  constructor(private options:Options,private kind:StatisticsKind,params:URLSearchParams){
    this.hash=new URLSearchParams(params);
    const config=statisticsConfig[kind];
    const requestedKind=(['labor','welfare','demography'] as const).find(key=>this.hash.get(key));
    if(requestedKind!==kind)this.hash.delete(kind);
    this.legend.className='legend demography-legend';
    this.legend.hidden=true;
    this.legend.setAttribute('aria-label',config.legend);
    this.timeline.className='timeline demography-timeline';
    this.timeline.hidden=true;
    this.timeline.setAttribute('aria-label',config.timeline);
    document.querySelector('.map-area')!.append(this.legend,this.timeline);
  }

  private dataRoot(){return import.meta.env.BASE_URL+'data/'+this.kind+'/';}
  private layer(id:string){return id.replace('f02-',statisticsConfig[this.kind].prefix+'-');}
  private urlKey(key:string){
    if(key==='demography')return this.kind;
    const prefix=statisticsConfig[this.kind].urlPrefix;
    return prefix ? prefix+(key.startsWith('d')&&key!=='density'?key.slice(1):key) : key;
  }
  private restoreValue(key:string){return this.hash.get(this.urlKey(key));}
  get active(){return this.enabled;}

  private async loadIndex(){
    return this.indexPromise??=(async()=>{
      const compact=this.kind==='demography';
      const response=await fetch(this.dataRoot()+(compact?'viewer.json.gz':'index.json'));
      if(!response.ok)throw new Error('No se pudo cargar el catálogo estadístico.');
      if(!compact)return this.index=await response.json() as DemographicIndex;
      const raw=await response.arrayBuffer();
      const bytes=new Uint8Array(raw);
      const data=bytes[0]===31&&bytes[1]===139
        ?await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).json()
        :JSON.parse(new TextDecoder().decode(raw));
      const groups=data.territoryGroups as Record<string,DemographicTable['territories']>;
      const tables=(data.tables as (Omit<DemographicTable,'territories'>&{territoryGroup:string})[]).map(
        ({territoryGroup,...table})=>({...table,territories:groups[territoryGroup]}),
      );
      return this.index={revision:data.revision,inventoryTables:data.inventoryTables,operations:data.operations,tables};
    })().catch(error=>{this.indexPromise=undefined;throw error;});
  }
  attach(map:AtlasMap,provinces:FeatureCollection,communities:FeatureCollection){
    this.map=map;this.geometries={province:provinces,community:communities};
    map.addSource(this.layer('f02-statistics'),{type:'geojson',data:{type:'FeatureCollection',features:[]}});
    map.addSource(this.layer('f02-national'),{type:'geojson',data:import.meta.env.BASE_URL+'data/territory/country-atlas.geojson'});
    for(const [id,source] of [[this.layer('f02-fill'),this.layer('f02-statistics')],[this.layer('f02-national-fill'),this.layer('f02-national')]])map.addLayer({id,type:'fill',source,layout:{visibility:'none'},paint:{'fill-color':'#7fa788','fill-opacity':this.alpha}},'province-lines');
    const layer={id:this.layer('f02-municipal-fill'),type:'fill' as const,source:'f01-admin','source-layer':'municipio',minzoom:7,layout:{visibility:'none' as const},paint:{'fill-color':'#b8b6aa','fill-opacity':this.alpha}};
    map.addLayer(layer,'f01-municipal-line');addShiftedLayer(map,layer,'f01-municipal-line');
    const restored=Number(this.restoreValue('demography'));if(restored)void this.useTable(restored,true,true);
  }
  async mount(panel:HTMLElement){
    this.panel=panel;panel.innerHTML='<p class="data-note" role="status">Cargando tablas estadísticas…</p>';
    try{const index=await this.loadIndex();if(!panel.isConnected)return;if(!this.table)this.table=index.tables[0];if(!this.query.dims.length&&this.table){this.query.dims=defaultDimensions(this.table);this.query.period=periodOrder(this.table).at(-1)!;this.validSelection();}this.drawPanel();}
    catch(error){panel.innerHTML=`<p role="status">${esc(error instanceof Error?error.message:error)}</p><button id="demog-retry">Reintentar</button>`;panel.querySelector('button')!.onclick=()=>void this.mount(panel);}
  }
  private areaOptions(){return this.table?.territories.map((a,i)=>({a,i})).filter(({a})=>a.level===this.query.level&&(!['municipal','district','section'].includes(a.level)||a.provinceCode===this.province)&&(!['district','section'].includes(a.level)||a.municipalityCode===this.municipality))||[];}
  private validSelection(){
    const t=this.table!;const allowed=Object.keys(levels).filter(l=>t.territories.some(a=>a.level===l));
    if(!allowed.includes(this.query.level))this.query.level=allowed.includes('province')?'province':allowed[0];
    if(['municipal','district','section'].includes(this.query.level)&&!t.shards.some(s=>s.id===this.province))this.province=t.shards.find(s=>s.id!=='main')!.id;
    if(['district','section'].includes(this.query.level)&&!t.territories.some(a=>a.level===this.query.level&&a.provinceCode===this.province&&a.municipalityCode===this.municipality))this.municipality=t.territories.find(a=>a.level===this.query.level&&a.provinceCode===this.province)?.municipalityCode||'';
    const areas=this.areaOptions();if(!areas.some(x=>x.i===this.query.territory))this.query.territory=areas[0]?.i??0;
  }
  async useTable(id:number,activate=true,restore=false){
    try{
      const index=await this.loadIndex(),table=index.tables.find(t=>t.id===id);if(!table)throw new Error('Esta tabla no está disponible.');
      this.stop();this.table=table;this.query={period:periodOrder(table).at(-1)!,dims:defaultDimensions(table),level:'province',territory:0};this.density=false;this.growth=false;
      if(restore){
        const period=table.periods.findIndex(p=>p.id===this.restoreValue('dperiod'));if(period>=0)this.query.period=period;
        const dims=(this.restoreValue('ddims')||'').split(',').map(Number);if(dims.length===table.dimensions.length&&dims.every((v,i)=>Number.isInteger(v)&&v>=0&&v<table.dimensions[i].values.length))this.query.dims=dims;
        this.query.level=this.restoreValue('dlevel')||'province';this.province=this.restoreValue('dprovince')||'28';this.density=this.restoreValue('density')==='1'&&table.unit==='personas';this.growth=this.restoreValue('growth')==='1'&&table.unit==='personas';if(this.growth)this.density=false;
        const area=table.territories.findIndex(a=>a.id===this.restoreValue('darea'));if(area>=0){this.query.territory=area;this.municipality=table.territories[area].municipalityCode||this.municipality;}
      }
      this.validSelection();this.enabled=activate;this.result=undefined;if(activate)this.options.onActivate();this.drawPanel();this.run();
    }catch(error){this.status=error instanceof Error?error.message:'No se pudo abrir la tabla.';this.drawPanel();}
  }
  disable(){this.stop();this.enabled=false;this.request++;this.pending=false;this.legend.hidden=true;this.timeline.hidden=true;if(this.map)for(const id of [this.layer('f02-fill'),this.layer('f02-national-fill'),this.layer('f02-municipal-fill'),...shiftedIds(this.layer('f02-municipal-fill'))])if(this.map.getLayer(id))this.map.setLayoutProperty(id,'visibility','none');if(this.options.info.dataset.demography===this.kind){this.options.info.hidden=true;delete this.options.info.dataset.demography;}this.drawPanel();}
  private drawPanel(){
    const p=this.panel,t=this.table;if(!p?.isConnected||!t||!this.index)return;
    const families=[...new Set(this.index.tables.map(t=>t.family))],areas=this.areaOptions(),order=periodOrder(t);
    const provinces=this.geometries?.province.features.filter(f=>t.shards.some(s=>s.id===f.properties?.code))||[];
    p.innerHTML=`<label class="check-row"><input type="checkbox" id="demog-enabled" ${this.enabled?'checked':''}><span>${statisticsConfig[this.kind].toggle}</span></label><label class="field-label">Producto<select id="demog-table">${families.map(f=>`<optgroup label="${esc(f)}">${this.index!.tables.filter(t=>t.family===f).map(x=>`<option value="${x.id}" ${t.id===x.id?'selected':''}>${esc(x.label)}</option>`).join('')}</optgroup>`).join('')}</select></label><label class="field-label">Territorio<select id="demog-level">${Object.entries(levels).filter(([l])=>t.territories.some(a=>a.level===l)).map(([l,n])=>`<option value="${l}" ${this.query.level===l?'selected':''}>${n}</option>`).join('')}</select></label>${['municipal','district','section'].includes(this.query.level)?`<label class="field-label">Provincia del detalle municipal<select id="demog-province">${provinces.map(f=>`<option value="${f.properties!.code}" ${f.properties!.code===this.province?'selected':''}>${esc(f.properties!.name)}</option>`).join('')}</select></label>${this.query.level==='municipal'?'<p class="data-note">Acerca el mapa para ver los municipios de esta provincia; las ciudades autónomas se muestran en su marco.</p>':`<label class="field-label">Municipio de la subdivisión<select id="demog-municipality">${[...new Set(t.territories.filter(a=>a.level===this.query.level&&a.provinceCode===this.province).map(a=>a.municipalityCode))].map(code=>`<option value="${code}" ${code===this.municipality?'selected':''}>${esc(t.territories.find(a=>a.id==='municipal:'+code)?.name||code)}</option>`).join('')}</select></label><p class="data-note">Series de subdivisiones; sin sombreado de polígonos. Cada edición conserva su código original.</p>`}`:''}<label class="field-label">Periodo<select id="demog-period">${[...order].reverse().map(i=>`<option value="${i}" ${i===this.query.period?'selected':''}>${esc(t.periods[i].label)}</option>`).join('')}</select></label>${t.dimensions.map((d,i)=>d.values.length>1?`<label class="field-label">${esc(d.name)}<select data-demog-dim="${i}" aria-label="${esc(d.name)}">${d.values.map((v,j)=>`<option value="${j}" ${this.query.dims[i]===j?'selected':''}>${esc(v)}</option>`).join('')}</select></label>`:'').join('')}${t.unit==='personas'&&this.query.level!=='municipal'&&this.query.level!=='national'?`<label class="check-row"><input id="demog-density" type="checkbox" ${this.density?'checked':''}><span>Densidad aproximada del grupo seleccionado</span></label>`:''}${t.unit==='personas'?`<label class="check-row"><input id="demog-growth" type="checkbox" ${this.growth?'checked':''}><span>Cambio porcentual desde ${esc(t.periods[order[0]].label)}</span></label>`:''}<label class="field-label">Consultar territorio<select id="demog-area">${areas.map(({a,i})=>`<option value="${i}" ${this.query.territory===i?'selected':''}>${esc(a.name)}</option>`).join('')}</select></label><button id="demog-show" class="wide-button">Ver serie y ficha</button><p class="data-note" role="status" id="demog-status">${esc(this.status||`${fmt(t.rows)} observaciones · tabla completa, todas sus categorías y periodos.`)}</p><p class="data-note">${esc(t.note)}</p><a href="${esc(t.sourceUrl)}" target="_blank" rel="noopener">INE · tabla ${t.id} ↗</a><p class="data-note">${esc(t.unit)} · ${esc(t.license)}. Límites IGN actuales: el año estadístico no reconstruye fronteras históricas.</p>`;
    const spatial=['national','province','community','municipal'].includes(this.query.level);
    if(spatial){
      const appearance=document.createElement('div');
      appearance.innerHTML=appearanceFields(this.appearanceId,colors[3],.76);
      p.querySelector('#demog-show')?.before(appearance);
      bindAppearance(appearance,()=>this.renderMap());
    }
    const el=<T extends HTMLElement=HTMLElement>(s:string)=>p.querySelector<T>(s)!;
    el<HTMLInputElement>('#demog-enabled').onchange=e=>{if((e.target as HTMLInputElement).checked){this.enabled=true;this.options.onActivate();this.run();}else this.disable();};
    el<HTMLSelectElement>('#demog-table').onchange=e=>void this.useTable(Number((e.target as HTMLSelectElement).value));
    el<HTMLSelectElement>('#demog-level').onchange=e=>{this.query.level=(e.target as HTMLSelectElement).value;this.density=false;this.validSelection();this.drawPanel();if(this.query.level==='municipal')this.fitProvince();this.run();};
    el<HTMLSelectElement>('#demog-province')?.addEventListener('change',e=>{this.province=(e.target as HTMLSelectElement).value;this.validSelection();this.drawPanel();this.fitProvince();this.run();});
    el<HTMLSelectElement>('#demog-municipality')?.addEventListener('change',e=>{this.municipality=(e.target as HTMLSelectElement).value;this.validSelection();this.drawPanel();this.run();});
    el<HTMLSelectElement>('#demog-period').onchange=e=>{this.stop();this.query.period=Number((e.target as HTMLSelectElement).value);this.run();};
    p.querySelectorAll<HTMLSelectElement>('[data-demog-dim]').forEach(s=>s.onchange=()=>{this.stop();this.query.dims[Number(s.dataset.demogDim)]=Number(s.value);this.run();});
    el<HTMLInputElement>('#demog-density')?.addEventListener('change',e=>{this.density=(e.target as HTMLInputElement).checked;if(this.density)this.growth=false;this.drawPanel();this.renderMap();this.renderDetail();});
    el<HTMLInputElement>('#demog-growth')?.addEventListener('change',e=>{this.growth=(e.target as HTMLInputElement).checked;if(this.growth)this.density=false;this.drawPanel();this.renderMap();this.renderDetail();});
    el<HTMLSelectElement>('#demog-area').onchange=e=>{this.query.territory=Number((e.target as HTMLSelectElement).value);if(this.enabled)this.run();};
    el('#demog-show').onclick=()=>{if(!this.enabled){this.enabled=true;this.options.onActivate();}this.options.info.dataset.demography=this.kind;this.options.clearSelection();this.options.closeDrawer();this.run();};
  }
  private fitProvince(){const f=this.geometries.province.features.find(f=>f.properties?.code===this.province);if(!f)return;const coords=projectCollection({type:'FeatureCollection',features:[f]}).features[0].geometry;const points:number[][]=[];const walk=(a:unknown)=>{if(Array.isArray(a)&&typeof a[0]==='number')points.push(a);else if(Array.isArray(a))a.forEach(walk);};if('coordinates'in coords)walk(coords.coordinates);if(points.length)this.map.fitBounds([[Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1]))],[Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))]],{padding:45,maxZoom:9,duration:500});}
  private run(){
    if(!this.enabled||!this.table)return;this.pending=true;this.status='Consultando tabla…';this.drawPanel();if(!this.result)this.renderMap();
    if(!this.worker){this.worker=new Worker(new URL('./demography.worker.ts',import.meta.url),{type:'module'});this.worker.onmessage=(e:MessageEvent<{id:number;error?:string;result?:DemographicResult}>)=>{
      if(e.data.id!==this.request||!this.enabled)return;this.pending=false;
      if(e.data.error){this.stop();this.result=undefined;this.status=e.data.error;this.renderMap();this.drawPanel();return;}
      this.result=e.data.result;this.baselines.clear();const start=periodOrder(this.table!)[0];for(const d of this.result!.domain)if(d.period===start)this.baselines.set(this.table!.territories[d.area].code,d.value);this.status=`${fmt(this.result!.values.filter(v=>v.value!==null).length)} territorios con dato · ${this.table!.periods[this.query.period].label}`;this.renderMap();this.renderDetail();this.drawPanel();
    };this.worker.onerror=()=>{this.stop();this.status='No se pudo iniciar la consulta. Recarga la web para reintentar.';this.drawPanel();};}
    this.worker.postMessage({id:++this.request,base:new URL(this.dataRoot(),location.href).href,table:this.table,part:['municipal','district','section'].includes(this.query.level)?this.province:'main',query:this.query});this.renderTimeline();
  }
  private unit(){if(this.growth)return '% respecto a '+this.table!.periods[periodOrder(this.table!)[0]].label;return this.density&&['province','community'].includes(this.query.level)?'personas por km² · aprox.':unitFor(this.table!,this.query.dims);}
  private mappedValue(value:number|null,code:string){if(value===null)return null;if(this.growth)return relativeChange(value,this.baselines.get(code));if(this.density&&['province','community'].includes(this.query.level)){const area=this.geometries[this.query.level].features.find(f=>f.properties?.code===code)?.properties?.areaKm2;return area>0?value/area:null;}return value;}
  private renderMap(){
    if(!this.map||!this.enabled||!this.table)return;
    const values=new Map((this.result?.values||[]).map(r=>{const a=this.table!.territories[r.area];return [a.code,this.mappedValue(r.value,a.code)];}));
    const numbers=(this.result?.domain||[]).map(v=>this.mappedValue(v.value,this.table!.territories[v.area].code)).filter((v):v is number=>v!==null).sort((a,b)=>a-b);
    const divergent=this.growth||this.table.unit==='saldo de movimientos';const palette=paletteFor(divergent?['#a75f4c','#ca9779','#e3c8aa','#eee7cf','#b8cda1','#7fa788','#31665a']:colors,layerAppearance(this.appearanceId).color);
    const stops=divergent?[-1,-.5,-.15,0,.15,.5,1].map(x=>x*Math.max(1,...numbers.map(Math.abs))):[0,.15,.35,.5,.65,.85,1].map(q=>numbers[Math.floor(q*Math.max(0,numbers.length-1))]??0);
    const color=(v:number|null|undefined)=>v===null||v===undefined?'#b8b6aa':palette[stops.reduce((best,s,i)=>v>=s?i:best,0)];
    for(const id of [this.layer('f02-fill'),this.layer('f02-national-fill'),this.layer('f02-municipal-fill'),...shiftedIds(this.layer('f02-municipal-fill'))])if(this.map.getLayer(id))this.map.setLayoutProperty(id,'visibility','none');
    const city=this.query.level==='municipal'&&['51','52'].includes(this.province);
    if(['province','community'].includes(this.query.level)||city){
      const geo=projectCollection(this.geometries[city?'province':this.query.level]);geo.features=geo.features.filter(f=>!city||f.properties!.code===this.province).map(f=>{const code=city?this.province+'001':f.properties!.code;return {...f,properties:{...f.properties,code,demographicColor:color(values.get(code))}};});
      (this.map.getSource(this.layer('f02-statistics')) as GeoJSONSource).setData(geo);this.map.setPaintProperty(this.layer('f02-fill'),'fill-color',['get','demographicColor']);this.map.setLayoutProperty(this.layer('f02-fill'),'visibility','visible');
    }else if(this.query.level==='national'){
      this.map.setPaintProperty(this.layer('f02-national-fill'),'fill-color',color(values.get('ES')));this.map.setLayoutProperty(this.layer('f02-national-fill'),'visibility','visible');
    }else if(this.query.level==='municipal'){
      const expression:unknown[]=['match',['slice',['to-string',['get','nationalcode']],6,11],...([...values].flatMap(([code,v])=>[code,color(v)])),'#b8b6aa'];
      for(const id of [this.layer('f02-municipal-fill'),...shiftedIds(this.layer('f02-municipal-fill'))])if(this.map.getLayer(id)){this.map.setPaintProperty(id,'fill-color',expression.length>3?expression as ExpressionSpecification:'#b8b6aa');this.map.setLayoutProperty(id,'visibility','visible');this.map.setFilter(id,['==',['slice',['to-string',['get','nationalcode']],6,8],this.province]);}
    }
    const picked=this.table.dimensions.map((d,i)=>({name:d.name,value:d.values[this.query.dims[i]]})).filter(d=>! /^(total|ambos sexos|todas las edades|todos|total nacional|dato base)$/i.test(d.value));
    const selection=picked.map(d=>d.value).join(' · ');
    const spatial=['national','province','community','municipal'].includes(this.query.level);
    const scope=levels[this.query.level]+(this.query.level==='municipal'?' · '+(this.geometries.province.features.find(f=>f.properties?.code===this.province)?.properties?.name||this.province):'');
    this.legend.hidden=false;this.legend.innerHTML=`<div class="legend-title"><strong>${esc(this.table.label)}</strong><button id="demog-hide" aria-label="Desactivar estadística" class="icon-button">×</button></div><p>${esc(this.table.periods[this.query.period].label)} · ${esc(this.unit())}</p><p class="legend-credit">${esc(selection)}</p><p class="legend-credit">${esc(scope)}${spatial?'':' · consulta de series, sin sombreado'}</p><div class="color-scale" style="background:linear-gradient(90deg,${palette.join(',')})"></div><div class="scale-labels"><span>${fmt(numbers.length?stops[0]:null)}</span><span>${fmt(numbers.length?stops.at(-1)!:null)}</span></div><p class="legend-credit">Escala fija para todos los periodos · sin dato: gris · INE</p>`;
    this.legend.querySelector<HTMLButtonElement>('#demog-hide')!.onclick=()=>this.disable();for(const id of [this.layer('f02-fill'),this.layer('f02-national-fill'),this.layer('f02-municipal-fill'),...shiftedIds(this.layer('f02-municipal-fill'))])if(this.map.getLayer(id))this.map.setPaintProperty(id,'fill-opacity',this.alpha);this.renderTimeline();
  }
  private renderTimeline(){
    if(!this.table)return;this.timeline.hidden=!this.enabled;const order=periodOrder(this.table);
    this.timeline.innerHTML=`<button id="demog-play" aria-label="${this.timer?'Pausar':'Reproducir'} evolución">${this.timer?'Ⅱ':'▶'}</button><div class="timeline-label"><small>INE · ${this.table.id}</small><strong>${esc(this.table.periods[this.query.period].label)}</strong></div><div class="timeline-track"><input id="demog-year" type="range" min="0" max="${order.length-1}" value="${order.indexOf(this.query.period)}" aria-label="Periodo de los datos" aria-valuetext="${esc(this.table.periods[this.query.period].label)}"><div class="timeline-ticks"><span>${esc(this.table.periods[order[0]].label)}</span><span>${esc(this.table.periods[order.at(-1)!].label)}</span></div></div>`;
    this.timeline.querySelector<HTMLInputElement>('#demog-year')!.oninput=e=>{this.stop();this.query.period=order[Number((e.target as HTMLInputElement).value)];this.run();};
    this.timeline.querySelector<HTMLButtonElement>('#demog-play')!.onclick=()=>{if(this.timer){this.stop();this.renderTimeline();return;}this.timer=setInterval(()=>{if(this.pending)return;this.query.period=order[(order.indexOf(this.query.period)+1)%order.length];this.run();},1200);this.renderTimeline();};
  }
  private stop(){clearInterval(this.timer);this.timer=undefined;}
  inspect(map:AtlasMap,event:MapMouseEvent){
    if(!this.enabled||!this.table||!['municipal','province','community','national'].includes(this.query.level))return false;const layer=this.query.level==='municipal'?[this.layer('f02-fill'),this.layer('f02-municipal-fill'),...shiftedIds(this.layer('f02-municipal-fill'))]:this.query.level==='national'?[this.layer('f02-national-fill')]:[this.layer('f02-fill')];
    const hit=map.queryRenderedFeatures(event.point,{layers:layer.filter(l=>map.getLayer(l))})[0];if(!hit)return false;
    const code=this.query.level==='municipal'?(hit.layer.id===this.layer('f02-fill')?String(hit.properties.code):municipalCode(hit.properties.nationalcode)):this.query.level==='national'?'ES':hit.properties.code;
    const i=this.table.territories.findIndex(a=>a.level===this.query.level&&a.code===code);if(i<0)return true;
    this.query.territory=i;this.options.info.dataset.demography=this.kind;this.options.clearSelection();this.options.closeDrawer();this.run();return true;
  }
  private renderDetail(){
    const t=this.table,r=this.result,info=this.options.info;if(!t||!r||info.dataset.demography!==this.kind||!this.enabled)return;
    const a=t.territories[this.query.territory],datum=r.series.find(x=>x.period===this.query.period),value=this.mappedValue(datum?.value??null,a.code);
    const series=r.series.map(x=>({...x,value:this.mappedValue(x.value,a.code)})),valid=series.filter(x=>x.value!==null),ys=valid.map(x=>x.value!),lo=Math.min(...ys),hi=Math.max(...ys),order=periodOrder(t);
    const start=periodTimestamp(t.periods[order[0]].id),end=periodTimestamp(t.periods[order.at(-1)!].id);let path='',pen=false,prior=-1;for(const d of series){if(d.value===null){pen=false;continue;}const position=order.indexOf(d.period);if(prior>=0&&position>prior+1)pen=false;prior=position;const x=8+(periodTimestamp(t.periods[d.period].id)-start)/Math.max(1,end-start)*264,y=57-(d.value-lo)/(hi-lo||1)*44;path+=`${pen?'L':'M'}${x},${y}`;pen=true;}
    const sourceId=a.publicationTableId||(t.sourceTables?undefined:t.id),captured=t.sourceTables?.find(s=>s.id===datum?.sourceTableId)?.url,sourceUrl=sourceId?'https://www.ine.es/jaxiT3/Tabla.htm?t='+sourceId:(captured||t.sourceUrl);
    const pyramid=this.kind==='demography'?r.pyramid:[],max=Math.max(1,...pyramid.flatMap(p=>[p.men||0,p.women||0])),step=Math.max(7,Math.min(19,330/Math.max(1,pyramid.length))),height=step*pyramid.length+22;
    info.hidden=false;info.innerHTML=`<div class="info-heading"><span class="eyebrow">${esc(levels[a.level]||a.level)} · ${esc(a.code)}</span><button id="demog-info-close" class="icon-button" aria-label="Cerrar información">×</button></div><h3>${esc(a.name.replace(/^\d+\s+/,''))}</h3><div class="info-main"><span>${esc(t.label)}</span><strong>${fmt(value)}</strong><small>${esc(this.unit())} · ${esc(t.periods[this.query.period].label)}</small></div><p class="data-note">${t.dimensions.map((d,i)=>`${esc(d.name)}: ${esc(d.values[this.query.dims[i]])}`).join(' · ')}</p>${datum?.status?`<p class="data-note">Estado original: ${esc(datum.status)}.${datum.value===null?' No se interpreta como cero.':''}</p>`:''}${valid.length>1?`<svg class="sparkline" viewBox="0 0 280 68" role="img" aria-label="Serie temporal de las observaciones publicadas"><path d="${path}" fill="none" stroke="#7fa788" stroke-width="2"/></svg><div class="sparkline-labels"><span>${esc(t.periods[order[0]].label)}</span><span>${esc(t.periods[order.at(-1)!].label)}</span></div>`:''}${pyramid.length?`<h4>Estructura por edad y sexo</h4><p class="data-note">Hombres a la izquierda · mujeres a la derecha · ${esc(t.unit)}. Conserva los otros filtros.</p><svg class="demog-pyramid" viewBox="0 0 300 ${height}" role="img" aria-label="Pirámide de población por edad y sexo">${[...pyramid].reverse().map((p,i)=>{const y=8+i*step;return `${p.men===null?'':`<rect x="${125-p.men/max*115}" y="${y}" width="${p.men/max*115}" height="${step-1}" fill="#70a8aa"><title>${esc(p.age)} · hombres: ${fmt(p.men)}</title></rect>`}${p.women===null?'':`<rect x="175" y="${y}" width="${p.women/max*115}" height="${step-1}" fill="#bd9bce"><title>${esc(p.age)} · mujeres: ${fmt(p.women)}</title></rect>`}${pyramid.length<30||i%5===0?`<text x="150" y="${y+step*.8}" text-anchor="middle" fill="currentColor" font-size="8">${esc(p.age.replace(/De | años/g,''))}</text>`:''}`;}).join('')}</svg><details><summary>Valores de la pirámide</summary><table class="demog-table"><thead><tr><th>Edad</th><th>Hombres</th><th>Mujeres</th></tr></thead><tbody>${pyramid.map(p=>`<tr><td>${esc(p.age)}</td><td>${fmt(p.men)}</td><td>${fmt(p.women)}</td></tr>`).join('')}</tbody></table></details>`:''}<details><summary>Serie completa de esta selección</summary><table class="demog-table"><thead><tr><th>Periodo</th><th>Valor</th><th>Estado</th></tr></thead><tbody>${series.map(s=>`<tr><td>${esc(t.periods[s.period].label)}</td><td>${fmt(s.value)}</td><td>${esc(s.status)}</td></tr>`).join('')}</tbody></table></details><p class="data-note">${esc(t.note)}${this.growth?' Cambio respecto al primer periodo disponible, con idénticos filtros y definición. Si el valor inicial es cero o no existe, no se calcula porcentaje.':''}${this.density?' Densidad con superficie esférica aproximada de límites IGN actuales.':''}</p><div class="info-footer"><a href="${esc(sourceUrl)}" target="_blank" rel="noopener">INE · ${sourceId||'datos'} ↗</a><button id="demog-csv">Descargar serie CSV</button></div>${captured?`<a class="data-note" href="${esc(captured)}" target="_blank" rel="noopener">Respuesta original de la API ↗</a>`:''}<p class="data-note">La descarga conserva valores originales (${esc(unitFor(t,this.query.dims))}), filtros, estados y procedencia.</p>`;
    info.querySelector<HTMLButtonElement>('#demog-info-close')!.onclick=()=>{delete info.dataset.demography;info.hidden=true;};
    info.querySelector<HTMLButtonElement>('#demog-csv')!.onclick=()=>{const url=URL.createObjectURL(new Blob([seriesCsv(t,this.query,r.series)],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=`ine-${t.id}-${a.code}.csv`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  }
}
