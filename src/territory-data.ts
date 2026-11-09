import type {Geometry,Position} from 'geojson';
export function municipalCode(value:unknown):string|null{
  const code=String(value??'');
  if(/^\d{11}$/.test(code))return code.slice(-5);
  return /^\d{5}$/.test(code)?code:null;
}
export function coordinatesExtent(geometry:Geometry):[[number,number],[number,number]]{
  const points:Position[]=[];
  const walk=(v:unknown)=>{if(Array.isArray(v)&&typeof v[0]==='number')points.push(v as Position);else if(Array.isArray(v))v.forEach(walk);};
  if('coordinates' in geometry)walk(geometry.coordinates);
  if(!points.length)throw new Error('Geometría sin coordenadas');
  let west=Infinity,south=Infinity,east=-Infinity,north=-Infinity;
  for(const [x,y] of points){west=Math.min(west,x);south=Math.min(south,y);east=Math.max(east,x);north=Math.max(north,y);}
  return [[west,south],[east,north]];
}
export function validSpanishCoordinate(lng:unknown,lat:unknown):lng is number{return typeof lng==='number'&&typeof lat==='number'&&Number.isFinite(lng)&&Number.isFinite(lat)&&lng>=-19&&lng<=5&&lat>=27&&lat<=44;}

