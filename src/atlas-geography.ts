import * as maplibregl from 'maplibre-gl';
import type {Map as AtlasMap,LayerSpecification,SourceSpecification} from 'maplibre-gl';
import {WORLD,mercY,ATLAS_REGIONS,ATLAS_FRAMES,vectorTileAddress} from './atlas-coordinates';

type RasterOptions={size?:number;scheme?:'xyz'|'tms';dem?:boolean;shiftOnly?:boolean;vector?:boolean;region?:string;maxzoom?:number};
export function atlasTileUrl(template:string,options:RasterOptions={}){
  return 'pais-atlas://tiles/{z}/{x}/{y}?'+new URLSearchParams({url:template,size:String(options.size||256),scheme:options.scheme||'xyz',dem:options.dem?'1':'0',shift:options.shiftOnly?'1':'0',vector:options.vector?'1':'0',region:options.region||'',max:String(options.maxzoom??(options.dem?15:19))});
}
export function tintedTileUrl(template:string,color:string){
  return 'pais-atlas://tint/{z}/{x}/{y}?'+new URLSearchParams({url:template,color});
}
function tileBox(z:number,x:number,y:number){const step=WORLD/2**z;return [x*step-WORLD/2,WORLD/2-(y+1)*step,(x+1)*step-WORLD/2,WORLD/2-y*step];}
function sourceUrl(template:string,z:number,x:number,y:number,scheme:string){
  return template.replaceAll('{z}',String(z)).replaceAll('{x}',String(x)).replaceAll('{y}',String(scheme==='tms'?2**z-1-y:y)).replaceAll('{bbox-epsg-3857}',tileBox(z,x,y).join(','));
}
export function registerAtlasProtocol(){
  const load:maplibregl.AddProtocolAction=async(params,abort)=>{
    const url=new URL(params.url),[z,x,y]=url.pathname.split('/').filter(Boolean).map(Number);
    if(url.host==='tint'){
      const template=url.searchParams.get('url')!;
      const tile=sourceUrl(template,z,x,y,'xyz');
      const bytes=tile.startsWith('pais-atlas:')?await load({...params,url:tile},abort)
        :{data:await fetch(tile,{signal:abort.signal}).then(response=>{
          if(!response.ok)throw new Error('Servicio cartográfico: '+response.status);
          return response.arrayBuffer();
        })};
      const bitmap=await createImageBitmap(new Blob([bytes.data as ArrayBuffer]));
      const canvas=new OffscreenCanvas(bitmap.width,bitmap.height),ctx=canvas.getContext('2d')!;
      ctx.drawImage(bitmap,0,0);
      bitmap.close();
      const image=ctx.getImageData(0,0,canvas.width,canvas.height),color=url.searchParams.get('color')!;
      const rgb=[1,3,5].map(offset=>parseInt(color.slice(offset,offset+2),16));
      for(let i=0;i<image.data.length;i+=4){
        if(!image.data[i+3])continue;
        const shade=.4+.6*(.2126*image.data[i]+.7152*image.data[i+1]+.0722*image.data[i+2])/255;
        for(let c=0;c<3;c++)image.data[i+c]=rgb[c]*shade;
      }
      ctx.putImageData(image,0,0);
      return {data:await(await canvas.convertToBlob({type:'image/png'})).arrayBuffer()};
    }
    const template=url.searchParams.get('url')!,size=Number(url.searchParams.get('size'))||256,scheme=url.searchParams.get('scheme')||'xyz',max=Number(url.searchParams.get('max'))||19;
    const bitmapOptions:ImageBitmapOptions=url.searchParams.get('dem')==='1'?{colorSpaceConversion:'none',premultiplyAlpha:'none'}:{};
    const shiftOnly=url.searchParams.get('shift')==='1',vector=url.searchParams.get('vector')==='1',regionId=url.searchParams.get('region');
    const regions=regionId?ATLAS_REGIONS.filter(r=>r.id===regionId):ATLAS_REGIONS;
    const read=async(tz:number,tx:number,ty:number)=>{const response=await fetch(sourceUrl(template,tz,tx,ty,scheme),{signal:abort.signal});if(!response.ok)throw new Error('Servicio cartográfico: '+response.status);return response.arrayBuffer();};
    if(vector){const r=regions[0];if(!r||z<r.vectorMinzoom)throw new Error('Escala vectorial no disponible');const tile=vectorTileAddress(r,z,x,y);return {data:await read(tile.z,tile.x,tile.y)};}
    const box=tileBox(z,x,y),step=box[2]-box[0];
    const intersecting=regions.map(r=>({r,b:[r.display[0]/360*WORLD,mercY(r.display[1]),r.display[2]/360*WORLD,mercY(r.display[3])]})).filter(({b})=>box[0]<b[2]&&box[2]>b[0]&&box[1]<b[3]&&box[3]>b[1]);
    if(!intersecting.length&&!shiftOnly)return {data:await read(z,x,y)};
    const canvas=new OffscreenCanvas(size,size),ctx=canvas.getContext('2d')!;ctx.imageSmoothingEnabled=false;
    if(!shiftOnly){const image=await createImageBitmap(new Blob([await read(z,x,y)]),bitmapOptions);ctx.drawImage(image,0,0,size,size);image.close();}
    for(const {r,b} of intersecting){
      const clipped=[Math.max(box[0],b[0]),Math.max(box[1],b[1]),Math.min(box[2],b[2]),Math.min(box[3],b[3])];
      ctx.save();ctx.beginPath();ctx.rect((clipped[0]-box[0])/step*size,(box[3]-clipped[3])/step*size,(clipped[2]-clipped[0])/step*size,(clipped[3]-clipped[1])/step*size);ctx.clip();ctx.clearRect(0,0,size,size);
      const sourceZ=Math.min(max,z+Math.log2(r.scale)),sourceStep=WORLD/2**sourceZ;
      const west=(clipped[0]-r.dx)/r.scale,east=(clipped[2]-r.dx)/r.scale,north=(clipped[3]-r.dy)/r.scale,south=(clipped[1]-r.dy)/r.scale;
      const firstX=Math.floor((west+WORLD/2)/sourceStep),lastX=Math.floor((east+WORLD/2-1e-7)/sourceStep),firstY=Math.floor((WORLD/2-north)/sourceStep),lastY=Math.floor((WORLD/2-south-1e-7)/sourceStep);
      const tasks=[];
      for(let sy=firstY;sy<=lastY;sy++)for(let sx=firstX;sx<=lastX;sx++)tasks.push((async()=>{
        const bitmap=await createImageBitmap(new Blob([await read(sourceZ,sx,sy)]),bitmapOptions),sb=tileBox(sourceZ,sx,sy);
        const dx=(sb[0]*r.scale+r.dx-box[0])/step*size,dy=(box[3]-(sb[3]*r.scale+r.dy))/step*size,dSize=sourceStep*r.scale/step*size;
        ctx.drawImage(bitmap,dx,dy,dSize,dSize);bitmap.close();
      })());
      await Promise.all(tasks);ctx.restore();
    }
    if(abort.signal.aborted)throw new DOMException('Aborted','AbortError');
    return {data:await(await canvas.convertToBlob({type:'image/png'})).arrayBuffer()};
  };
  maplibregl.addProtocol('pais-atlas',load);
}
const intersects=(a:number[],b:number[])=>a[0]<b[2]&&a[2]>b[0]&&a[1]<b[3]&&a[3]>b[1];
export function addShiftedLayer(m:AtlasMap,layer:LayerSpecification,before?:string):string[]{
  if(!('source' in layer)||typeof layer.source!=='string'||layer.type==='hillshade')return [];
  const live=m.getSource(layer.source);if(!live||!['raster','vector'].includes(live.type))return [];
  const source=m.getStyle().sources[layer.source];if(!source||!['raster','vector'].includes(source.type)||!('tiles' in source)||!source.tiles)return [];
  const ids=[];
  for(const r of ATLAS_REGIONS){
    if(source.bounds&&!intersects(source.bounds,r.original))continue;
    const vector=source.type==='vector',shift=Math.log2(r.scale),id=layer.source+'-atlas-'+r.id;
    if(!m.getSource(id))m.addSource(id,{...source,tiles:source.tiles.map(t=>atlasTileUrl(t,{shiftOnly:true,vector,region:r.id,size:'tileSize'in source?source.tileSize:256,maxzoom:source.maxzoom??19})),bounds:r.display,minzoom:vector?r.vectorMinzoom:0,maxzoom:Math.max(vector?r.vectorMinzoom:0,(source.maxzoom??19)-shift),scheme:'xyz'} as SourceSpecification);
    const shifted={...layer,id:layer.id+'-'+r.id,source:id,minzoom:Math.max(0,(layer.minzoom||0)-shift,vector?r.vectorMinzoom:0)} as LayerSpecification;
    m.addLayer(shifted,before);ids.push(shifted.id);
  }
  return ids;
}
export function addAtlasSeparation(m:AtlasMap){
  m.addSource('atlas-visible-sea',{type:'geojson',data:import.meta.env.BASE_URL+'datos/territorio/sea-atlas.geojson'});
  m.addLayer({id:'atlas-opaque-sea',type:'fill',source:'atlas-visible-sea',paint:{'fill-color':'#0b2842','fill-opacity':1}});
  m.addSource('atlas-islets',{type:'geojson',data:import.meta.env.BASE_URL+'datos/territorio/islets-atlas.geojson'});m.addLayer({id:'atlas-islets-shape',type:'fill',source:'atlas-islets',paint:{'fill-color':'#9aa98d','fill-opacity':.35,'fill-outline-color':'#e8e5c8'}});m.addLayer({id:'atlas-islets-edge',type:'line',source:'atlas-islets',paint:{'line-color':'#e8e5c8','line-width':.8}});
  const features:GeoJSON.Feature[]=ATLAS_FRAMES.flatMap(f=>{const [w,s,e,n]=f.bounds;return [{type:'Feature',properties:{name:f.name},geometry:{type:'LineString',coordinates:[[w,s],[e,s],[e,n],[w,n],[w,s]]}},{type:'Feature',properties:{name:f.name},geometry:{type:'Point',coordinates:[w+.12,n-.12]}}];}) as GeoJSON.Feature[];
  for(const r of ATLAS_REGIONS.slice(3)){const b=r.display;features.push({type:'Feature',properties:{name:(r.id==='velez'?'Vélez':r.name)+'\n×'+r.scale,anchor:'center'},geometry:{type:'Point',coordinates:[(b[0]+b[2])/2,35.95]}});}
  m.addSource('atlas-separation',{type:'geojson',data:{type:'FeatureCollection',features} as GeoJSON.FeatureCollection});
  m.addLayer({id:'atlas-separation-line',type:'line',source:'atlas-separation',filter:['==',['geometry-type'],'LineString'],paint:{'line-color':'#91aabc','line-width':1,'line-dasharray':[4,4],'line-opacity':.7}});
  m.addLayer({id:'atlas-separation-label',type:'symbol',source:'atlas-separation',maxzoom:8,filter:['==',['geometry-type'],'Point'],layout:{'text-field':['get','name'],'text-font':['Noto Sans Regular'],'text-size':10,'text-anchor':['coalesce',['get','anchor'],'top-left'],'text-max-width':12,'text-allow-overlap':true},paint:{'text-color':'#c0d1dc','text-halo-color':'#0b2842','text-halo-width':1}});
}
