import type {Map as AtlasMap,LayerSpecification,RasterTileSource} from 'maplibre-gl';
import {tintedTileUrl} from './atlas-geography';

type Appearance={color?:string;opacity?:number};
const key='pais-layer-appearance';
const saved:Record<string,Appearance>=Object.create(null);
try{
  const stored:unknown=JSON.parse(localStorage.getItem(key)||'{}');
  if(stored&&typeof stored==='object')for(const [id,entry] of Object.entries(stored)){
    if(!entry||typeof entry!=='object')continue;
    const {color,opacity}=entry as Appearance;
    saved[id]={color:validColor(color)?color:undefined,opacity:Number.isFinite(opacity)&&opacity!>=0&&opacity!<=1?opacity:undefined};
  }
}catch{ /* Storage may be unavailable in private browsing. */ }
const defaults=new WeakMap<AtlasMap,Map<string,LayerSpecification>>();
const rasterTiles=new WeakMap<RasterTileSource,{tiles:string[];color?:string}>();

function validColor(color:unknown):color is string{return typeof color==='string'&&/^#[0-9a-f]{6}$/i.test(color);}
export function layerAppearance(id:string){return Object.hasOwn(saved,id)?saved[id]:{};}
export function appearanceFields(id:string,defaultColor:string,opacity=1,tint=false){
  const appearance=layerAppearance(id);
  const amount=Math.round((appearance.opacity??opacity)*100);
  return `<div class="layer-appearance" ${tint?'data-raster="true"':''} data-appearance="${id}" data-default-color="${defaultColor}" data-default-opacity="${Math.round(opacity*100)}">
    <label class="layer-color">${tint?'Tinte':'Color'}<input type="color" data-layer-color value="${appearance.color??defaultColor}"></label>
    <label class="layer-opacity">Opacidad <span data-opacity-value aria-hidden="true">${amount}%</span><input type="range" min="0" max="100" value="${amount}" aria-label="Opacidad" data-layer-opacity></label>
    <button type="button" class="text-button" data-layer-reset>Restablecer aspecto</button>
  </div>`;
}
export function bindAppearance(root:HTMLElement,apply:(id:string)=>void){
  root.querySelectorAll<HTMLElement>('[data-appearance]').forEach(group=>{
    const id=group.dataset.appearance!;
    const color=group.querySelector<HTMLInputElement>('[data-layer-color]')!;
    const opacity=group.querySelector<HTMLInputElement>('[data-layer-opacity]')!;
    const output=group.querySelector<HTMLElement>('[data-opacity-value]')!;
    const syncOpacity=()=>{
      output.textContent=opacity.value+'%';
      opacity.setAttribute('aria-valuetext',output.textContent);
    };
    syncOpacity();
    const write=(value:Appearance)=>{
      if(value.color===undefined&&value.opacity===undefined)delete saved[id];
      else saved[id]=value;
      try{localStorage.setItem(key,JSON.stringify(saved));}catch{ /* In-memory settings still apply. */ }
      apply(id);
    };
    let tintTimer:ReturnType<typeof setTimeout>|undefined;
    const applyColor=()=>{
      clearTimeout(tintTimer);
      write({...layerAppearance(id),color:color.value});
    };
    color.oninput=()=>{
      if(!group.dataset.raster){applyColor();return;}
      clearTimeout(tintTimer);
      tintTimer=setTimeout(applyColor,180);
    };
    color.onchange=applyColor;
    opacity.oninput=()=>{syncOpacity();write({...layerAppearance(id),opacity:Number(opacity.value)/100});};
    group.querySelector<HTMLButtonElement>('[data-layer-reset]')!.onclick=()=>{
      clearTimeout(tintTimer);
      color.value=group.dataset.defaultColor!;
      opacity.value=group.dataset.defaultOpacity!;
      syncOpacity();
      write({});
    };
  });
}
export function rememberRaster(source:RasterTileSource,tiles:string[]){
  rasterTiles.set(source,{tiles});
  source.setTiles(tiles);
}
export function paintLayer(map:AtlasMap,id:string,appearance:Appearance,original?:LayerSpecification){
  let specs=defaults.get(map);
  if(!specs){specs=new Map();defaults.set(map,specs);}
  if(original){specs.set(id,structuredClone(original));if(appearance.color===undefined&&appearance.opacity===undefined)return;}
  const spec=specs.get(id);
  if(!spec||!map.getLayer(id))return;
  const {color,opacity}=appearance;
  if(spec.type==='raster'){
    map.setPaintProperty(id,'raster-opacity',opacity??spec.paint?.['raster-opacity']??1);
    const source=map.getSource<RasterTileSource>(spec.source);
    if(!source)return;
    let info=rasterTiles.get(source);
    if(!info){
      const specification=source.serialize();
      if(!specification.tiles)return;
      info={tiles:specification.tiles.slice()};
      rasterTiles.set(source,info);
    }
    if(info.color===color)return;
    info.color=color;
    source.setTiles(color?info.tiles.map(tile=>tintedTileUrl(tile,color)):info.tiles);
    return;
  }
  if(spec.type==='hillshade'){
    map.setPaintProperty(id,'hillshade-exaggeration',opacity===undefined?spec.paint?.['hillshade-exaggeration']??.5:opacity);
    map.setPaintProperty(id,'hillshade-shadow-color',color??spec.paint?.['hillshade-shadow-color']??'#000000');
    return;
  }
  if(spec.type==='fill'){
    const paint=spec.paint;
    const alpha=paint?.['fill-opacity']??1;
    if(alpha!==0){
      map.setPaintProperty(id,'fill-color',color??paint?.['fill-color']??'#000000');
      map.setPaintProperty(id,'fill-outline-color',color??paint?.['fill-outline-color']);
    }
    map.setPaintProperty(id,'fill-opacity',typeof alpha==='number'?alpha*(opacity??1):alpha);
  }else if(spec.type==='line'){
    const alpha=spec.paint?.['line-opacity']??1;
    map.setPaintProperty(id,'line-color',color??spec.paint?.['line-color']??'#000000');
    map.setPaintProperty(id,'line-opacity',typeof alpha==='number'?alpha*(opacity??1):alpha);
  }else if(spec.type==='circle'){
    map.setPaintProperty(id,'circle-color',color??spec.paint?.['circle-color']??'#000000');
    map.setPaintProperty(id,'circle-opacity',opacity??spec.paint?.['circle-opacity']??1);
  }else if(spec.type==='symbol'){
    map.setPaintProperty(id,'text-color',color??spec.paint?.['text-color']??'#000000');
    map.setPaintProperty(id,'text-opacity',opacity??spec.paint?.['text-opacity']??1);
  }
}
export function paletteFor(original:readonly string[],color?:string){
  if(!validColor(color))return original;
  const channels=[1,3,5].map(offset=>parseInt(color.slice(offset,offset+2),16));
  return original.map((_,i)=>{
    const t=i/Math.max(1,original.length-1);
    const rgb=channels.map(value=>Math.round(t<.55?255+(value-255)*(.12+.88*t/.55):value*(1-.7*(t-.55)/.45)));
    return '#'+rgb.map(value=>value.toString(16).padStart(2,'0')).join('');
  });
}
