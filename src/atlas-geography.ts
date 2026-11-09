import * as maplibregl from 'maplibre-gl';
import type {Map as AtlasMap,LayerSpecification,SourceSpecification} from 'maplibre-gl';
import type {Feature,FeatureCollection,Geometry,Position} from 'geojson';

// An atlas layout, not a change to the source coordinates. The displacement is
// an exact tile offset from zoom 7 onward, so official vector tiles remain intact.
import {WORLD,mercY,CANARY_DISPLAY,CANARY_ORIGINAL} from './atlas-coordinates';

type RasterOptions={size?:number;scheme?:'xyz'|'tms';dem?:boolean;shiftOnly?:boolean;vector?:boolean};
export function atlasTileUrl(template:string,options:RasterOptions={}){
  return 'pais-atlas://tiles/{z}/{x}/{y}?'+new URLSearchParams({url:template,size:String(options.size||256),scheme:options.scheme||'xyz',dem:options.dem?'1':'0',shift:options.shiftOnly?'1':'0',vector:options.vector?'1':'0'});
}
function tileBox(z:number,x:number,y:number){const step=WORLD/2**z;return [x*step-WORLD/2,WORLD/2-(y+1)*step,(x+1)*step-WORLD/2,WORLD/2-y*step];}
function sourceUrl(template:string,z:number,x:number,y:number,scheme:string){
  const box=tileBox(z,x,y);
  return template.replaceAll('{z}',String(z)).replaceAll('{x}',String(x)).replaceAll('{y}',String(scheme==='tms'?2**z-1-y:y)).replaceAll('{bbox-epsg-3857}',box.join(','));
}
export function registerAtlasProtocol(){
  maplibregl.addProtocol('pais-atlas',async(params,abort)=>{
    const url=new URL(params.url);const [z,x,y]=url.pathname.split('/').filter(Boolean).map(Number);
    const template=url.searchParams.get('url')!,size=Number(url.searchParams.get('size'))||256,scheme=url.searchParams.get('scheme')||'xyz';
    const bitmapOptions:ImageBitmapOptions=url.searchParams.get('dem')==='1'?{colorSpaceConversion:'none',premultiplyAlpha:'none'}:{};
    const shiftOnly=url.searchParams.get('shift')==='1',vector=url.searchParams.get('vector')==='1';
    const read=async(tileX:number,tileY:number)=>{const response=await fetch(sourceUrl(template,z,tileX,tileY,scheme),{signal:abort.signal});if(!response.ok)throw new Error('Servicio cartográfico: '+response.status);return response.arrayBuffer();};
    const dx=2**(z-7),dy=4*dx;
    if(vector){if(z<7)throw new Error('Vector displacement requires zoom 7');return {data:await read(x-dx,y+dy)};}
    const box=tileBox(z,x,y),region=[CANARY_DISPLAY[0]/360*WORLD,mercY(CANARY_DISPLAY[1]),CANARY_DISPLAY[2]/360*WORLD,mercY(CANARY_DISPLAY[3])];
    const intersects=box[0]<region[2]&&box[2]>region[0]&&box[1]<region[3]&&box[3]>region[1];
    if(!intersects&&!shiftOnly)return {data:await read(x,y)};
    const canvas=new OffscreenCanvas(size,size),ctx=canvas.getContext('2d')!;ctx.imageSmoothingEnabled=false;
    if(!shiftOnly){const image=await createImageBitmap(new Blob([await read(x,y)]),bitmapOptions);ctx.drawImage(image,0,0,size,size);image.close();}
    if(intersects){
      const step=box[2]-box[0],left=(Math.max(box[0],region[0])-box[0])/step*size,right=(Math.min(box[2],region[2])-box[0])/step*size;
      const top=(box[3]-Math.min(box[3],region[3]))/step*size,bottom=(box[3]-Math.max(box[1],region[1]))/step*size;
      ctx.save();ctx.beginPath();ctx.rect(left,top,right-left,bottom-top);ctx.clip();ctx.clearRect(0,0,size,size);
      const actualX=x-dx,actualY=y+dy,ix=Math.floor(actualX),iy=Math.floor(actualY);
      const offsetX=(actualX-ix)*size,offsetY=(actualY-iy)*size;
      const tasks=[];
      for(let row=0;row<=(offsetY>0?1:0);row++)for(let col=0;col<=(offsetX>0?1:0);col++)tasks.push((async()=>{const data=await read(ix+col,iy+row);const bitmap=await createImageBitmap(new Blob([data]),bitmapOptions);ctx.drawImage(bitmap,col*size-offsetX,row*size-offsetY,size,size);bitmap.close();})());
      await Promise.all(tasks);ctx.restore();
    }
    if(abort.signal.aborted)throw new DOMException('Aborted','AbortError');
    return {data:await(await canvas.convertToBlob({type:'image/png'})).arrayBuffer()};
  });
}

export function addShiftedLayer(m:AtlasMap,layer:LayerSpecification,before?:string):string|undefined{
  if(!('source' in layer)||typeof layer.source!=='string'||layer.type==='hillshade')return;
  const liveSource=m.getSource(layer.source);if(!liveSource||!['raster','vector'].includes(liveSource.type))return;
  const source=m.getStyle().sources[layer.source];if(!source||!['raster','vector'].includes(source.type)||!('tiles' in source)||!source.tiles)return;
  const id=layer.source+'-atlas-canarias';
  if(!m.getSource(id)){
    const spec={...source,tiles:source.tiles.map(t=>atlasTileUrl(t,{shiftOnly:true,vector:source.type==='vector',size:'tileSize' in source?source.tileSize:256})),bounds:CANARY_DISPLAY,minzoom:source.type==='vector'?7:5,scheme:'xyz'};
    m.addSource(id,spec as SourceSpecification);
  }
  const shifted={...layer,id:layer.id+'-canarias',source:id,minzoom:Math.max(layer.minzoom||0,source.type==='vector'?7:5)} as LayerSpecification;
  m.addLayer(shifted,before);return shifted.id;
}
export function updateShiftedTiles(m:AtlasMap,sourceId:string,tiles:string[]){
  const source=m.getSource(sourceId+'-atlas-canarias') as {setTiles?:(tiles:string[])=>void}|undefined;
  source?.setTiles?.(tiles.map(t=>atlasTileUrl(t,{shiftOnly:true})));
}
export function addAtlasSeparation(m:AtlasMap,originalCanaries:FeatureCollection){
  m.addSource('atlas-margin',{type:'geojson',data:{type:'Feature',properties:{},geometry:{type:'Polygon',coordinates:[[[-180,-85],[180,-85],[180,85],[-180,85],[-180,-85]],[[-20.5,25.5],[-20.5,46.5],[7,46.5],[7,25.5],[-20.5,25.5]]]}}});
  m.addLayer({id:'atlas-margin',type:'fill',source:'atlas-margin',paint:{'fill-color':'#0b2842'}});
  m.addSource('atlas-original-canaries',{type:'geojson',data:originalCanaries});
  m.addLayer({id:'atlas-original-sea',type:'fill',source:'atlas-original-canaries',paint:{'fill-color':'#0b2842'}});
  m.addLayer({id:'atlas-original-sea-edge',type:'line',source:'atlas-original-canaries',paint:{'line-color':'#0b2842','line-width':5}});
  const east=CANARY_DISPLAY[2]+.35,south=CANARY_DISPLAY[1]-.25,north=CANARY_DISPLAY[3]+.25;
  m.addSource('atlas-separation',{type:'geojson',data:{type:'FeatureCollection',features:[{type:'Feature',properties:{},geometry:{type:'LineString',coordinates:[[east-.4,south],[east,south+.3],[east,north-.3],[east+.4,north]]}},{type:'Feature',properties:{name:'Canarias'},geometry:{type:'Point',coordinates:[CANARY_DISPLAY[0],north]}}]}});
  m.addLayer({id:'atlas-separation-line',type:'line',source:'atlas-separation',filter:['==',['geometry-type'],'LineString'],paint:{'line-color':'#b8c9d5','line-width':1,'line-dasharray':[5,4],'line-opacity':.75}});
  m.addLayer({id:'atlas-separation-label',type:'symbol',source:'atlas-separation',maxzoom:8,filter:['==',['geometry-type'],'Point'],layout:{'text-field':['get','name'],'text-font':['Noto Sans Regular'],'text-size':10,'text-anchor':'left','text-allow-overlap':true},paint:{'text-color':'#b8c9d5','text-halo-color':'#0b2842','text-halo-width':1}});
}
