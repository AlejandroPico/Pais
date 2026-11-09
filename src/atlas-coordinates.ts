import type {Feature,FeatureCollection,Position} from 'geojson';
export const WORLD=40075016.68557849;
export const CANARY_ORIGINAL:[number,number,number,number]=[-18.5,27.4,-13.15,29.6];
const DX=WORLD/128,DY=WORLD*4/128;
export const mercY=(lat:number)=>6378137*Math.log(Math.tan(Math.PI/4+lat*Math.PI/360));
const latitude=(y:number)=>(2*Math.atan(Math.exp(y/6378137))-Math.PI/2)*180/Math.PI;
export const CANARY_DISPLAY:[number,number,number,number]=[CANARY_ORIGINAL[0]+360/128,latitude(mercY(CANARY_ORIGINAL[1])+DY),CANARY_ORIGINAL[2]+360/128,latitude(mercY(CANARY_ORIGINAL[3])+DY)];
const contains=(p:Position,b:number[])=>p[0]>=b[0]&&p[0]<=b[2]&&p[1]>=b[1]&&p[1]<=b[3];
export function toAtlas(p:Position):Position{return contains(p,CANARY_ORIGINAL)?[p[0]+360/128,latitude(mercY(p[1])+DY),...p.slice(2)]:[...p];}
export function fromAtlas(p:Position):Position{return contains(p,CANARY_DISPLAY)?[p[0]-360/128,latitude(mercY(p[1])-DY),...p.slice(2)]:[...p];}
export function projectFeature<T extends Feature>(feature:T):T{
  const walk=(v:unknown):unknown=>Array.isArray(v)&&typeof v[0]==='number'?toAtlas(v as Position):Array.isArray(v)?v.map(walk):v;
  const geometry=feature.geometry;
  return {...feature,geometry:'coordinates' in geometry?{...geometry,coordinates:walk(geometry.coordinates)}:geometry} as T;
}
export function projectCollection<T extends FeatureCollection>(collection:T):T{return {...collection,features:collection.features.map(projectFeature)} as T;}

