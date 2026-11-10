import type {Feature,FeatureCollection,Position} from 'geojson';
export const WORLD=40075016.68557849;
export const mercY=(lat:number)=>6378137*Math.log(Math.tan(Math.PI/4+lat*Math.PI/360));
export const latitude=(y:number)=>(2*Math.atan(Math.exp(y/6378137))-Math.PI/2)*180/Math.PI;
export type AtlasRegion={id:string;name:string;original:[number,number,number,number];display:[number,number,number,number];scale:number;dx:number;dy:number;vectorMinzoom:number};
const contains=(p:Position,b:number[])=>p[0]>=b[0]&&p[0]<=b[2]&&p[1]>=b[1]&&p[1]<=b[3];
const bounds=(b:number[])=>[b[0]/360*WORLD,mercY(b[1]),b[2]/360*WORLD,mercY(b[3])];
function region(id:string,name:string,original:AtlasRegion['original'],center:[number,number],scale=1):AtlasRegion{
  const b=bounds(original),cx=(b[0]+b[2])/2,cy=(b[1]+b[3])/2,grid=WORLD/1024;
  const dx=Math.round((center[0]/360*WORLD-cx*scale)/grid)*grid,dy=Math.round((mercY(center[1])-cy*scale)/grid)*grid;
  return {id,name,original,scale,dx,dy,vectorMinzoom:10,display:[(b[0]*scale+dx)/WORLD*360,latitude(b[1]*scale+dy),(b[2]*scale+dx)/WORLD*360,latitude(b[3]*scale+dy)]};
}
const canaryOriginal:[number,number,number,number]=[-18.5,27.4,-13.15,29.6];
const canary:AtlasRegion={id:'canarias',name:'Canarias',original:canaryOriginal,scale:1,dx:WORLD/128,dy:WORLD*6/128,vectorMinzoom:7,display:[canaryOriginal[0]+360/128,latitude(mercY(canaryOriginal[1])+WORLD*6/128),canaryOriginal[2]+360/128,latitude(mercY(canaryOriginal[3])+WORLD*6/128)]};
export const ATLAS_REGIONS:AtlasRegion[]=[canary,
  region('ceuta','Ceuta',[-5.39,35.86,-5.27,35.93],[-14.7,38.8],16),
  region('melilla','Melilla',[-2.98,35.25,-2.91,35.33],[-11.7,38.8],16),
  region('velez','Vélez de la Gomera',[-4.303,35.169,-4.295,35.175],[-15.45,36.6],128),
  region('alhucemas','Alhucemas',[-3.906,35.211,-3.886,35.221],[-14.0,36.6],64),
  region('chafarinas','Chafarinas',[-2.447,35.173,-2.416,35.187],[-12.5,36.6],32),
  region('alboran','Alborán',[-3.038,35.937,-3.029,35.943],[-11.0,36.6],128)
];
export const CANARY_ORIGINAL=canary.original,CANARY_DISPLAY=canary.display;
export const ATLAS_BOUNDS:[[number,number],[number,number]]=[[-16.5,35.55],[4.75,44.15]];
export const ATLAS_FRAMES=[
  {id:'canarias',name:'Canarias',bounds:[-16.25,40.35,-10.05,43.25]},
  {id:'ceuta',name:'Ceuta · ×16',bounds:[-16.25,37.75,-13.25,39.8]},
  {id:'melilla',name:'Melilla · ×16',bounds:[-13.05,37.75,-10.05,39.8]},
  {id:'otros',name:'Otros territorios · escalas ampliadas',bounds:[-16.25,35.65,-10.05,37.55]}
];
export function displayRegion(p:Position){return ATLAS_REGIONS.find(r=>contains(p,r.display));}
export function toAtlas(p:Position):Position{const r=ATLAS_REGIONS.find(r=>contains(p,r.original));return r?[(p[0]/360*WORLD*r.scale+r.dx)/WORLD*360,latitude(mercY(p[1])*r.scale+r.dy),...p.slice(2)]:[...p];}
export function fromAtlas(p:Position):Position{const r=displayRegion(p);return r?[(p[0]/360*WORLD-r.dx)/r.scale/WORLD*360,latitude((mercY(p[1])-r.dy)/r.scale),...p.slice(2)]:[...p];}
export function shiftedIds(base:string){return ATLAS_REGIONS.map(r=>base+'-'+r.id);}
export function projectFeature<T extends Feature>(feature:T):T{
  const walk=(v:unknown):unknown=>Array.isArray(v)&&typeof v[0]==='number'?toAtlas(v as Position):Array.isArray(v)?v.map(walk):v;
  const geometry=feature.geometry;
  return {...feature,geometry:'coordinates' in geometry?{...geometry,coordinates:walk(geometry.coordinates)}:geometry} as T;
}
export function projectCollection<T extends FeatureCollection>(collection:T):T{return {...collection,features:collection.features.map(projectFeature)} as T;}


export function vectorTileAddress(region:AtlasRegion,z:number,x:number,y:number){const step=WORLD/2**z;return {z:z+Math.log2(region.scale),x:Math.round(x+(region.scale-1)*2**(z-1)-region.dx/step),y:Math.round(y+(region.scale-1)*2**(z-1)+region.dy/step)};}
