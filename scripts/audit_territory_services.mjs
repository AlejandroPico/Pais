import fs from 'node:fs';
import crypto from 'node:crypto';
import {territoryLayers} from '../src/territory-config.ts';
const providers=[...new Map(territoryLayers.flatMap(l=>l.providers||[]).map(p=>[p.url+'|'+p.layers,p])).values()];
const cities={F008:[-3.366,40.483],F007:[-3.366,40.483],F165:[-1.6458,42.818],F177:[-2.672,42.847],F178:[-2.934,43.263],F179:[-1.982,43.322],F155:[-15.43,28.12]};
const results=[];
for(let start=0;start<providers.length;start+=4){
  const batch=await Promise.all(providers.slice(start,start+4).map(async p=>{
    const [lng,lat]=cities[p.sourceId];const x=6378137*lng*Math.PI/180,y=6378137*Math.log(Math.tan(Math.PI/4+lat*Math.PI/360));
    const params=new URLSearchParams({SERVICE:'WMS',VERSION:'1.3.0',REQUEST:'GetMap',LAYERS:p.layers,STYLES:p.styles||'',CRS:'EPSG:3857',BBOX:`${x-150},${y-150},${x+150},${y+150}`,WIDTH:'256',HEIGHT:'256',FORMAT:'image/png',TRANSPARENT:'TRUE'});
    const url=p.url+'?'+params;
    try{
      const r=await fetch(url,{headers:{Origin:'https://alejandropico.github.io'},signal:AbortSignal.timeout(25000)});
      const bytes=Buffer.from(await r.arrayBuffer());const png=bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]));
      const cors=r.headers.get('access-control-allow-origin');
      return {sourceId:p.sourceId,service:p.url,layers:p.layers,url,status:r.status,png,cors,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),...(png?{}:{error:bytes.toString('utf8').slice(0,500)})};
    }catch(e){return {sourceId:p.sourceId,service:p.url,layers:p.layers,url,error:e.message};}
  }));results.push(...batch);
}
fs.writeFileSync(new URL('../datos/territorio/service-audit.json',import.meta.url),JSON.stringify({checkedAt:new Date().toISOString(),scope:'Muestras técnicas de imagen; no verifican toda la cobertura geográfica ni todas las consultas.',results},null,2)+'\n');
console.log(JSON.stringify(results.map(r=>({source:r.sourceId,layers:r.layers,status:r.status,png:r.png,cors:r.cors,error:r.error})),null,2));
