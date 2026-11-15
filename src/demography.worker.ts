import {appendCubeResult,queryCube,type Cube,type DemographicResult,type DemographicTable,type DemographicQuery} from './demography-data';

const cache = new Map<string,Cube>();
const cacheRowLimit = 550_000;
let cachedRows=0;
let active:AbortController|undefined;

async function loadCube(key:string,hash:string,signal:AbortSignal){
  const saved=cache.get(key);
  if(saved){
    cache.delete(key);
    cache.set(key,saved);
    return saved;
  }
  const response=await fetch(key,{signal});
  if(!response.ok)throw new Error('No se pudo descargar la tabla.');
  const bytes=await response.arrayBuffer();
  const magic=new Uint8Array(bytes);
  const content=magic[0]===0x1f&&magic[1]===0x8b
    ?await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()
    :bytes;
  const digest=await crypto.subtle.digest('SHA-256',content);
  const actual=Array.from(new Uint8Array(digest),n=>n.toString(16).padStart(2,'0')).join('');
  if(actual!==hash)throw new Error('La tabla no coincide con su ficha. Recarga la página para actualizarla.');
  signal.throwIfAborted();
  const cube=JSON.parse(new TextDecoder().decode(content)) as Cube;
  if(cube.rows.length<=cacheRowLimit){
    while(cachedRows+cube.rows.length>cacheRowLimit){
      const oldest=cache.keys().next().value!;
      cachedRows-=cache.get(oldest)!.rows.length;
      cache.delete(oldest);
    }
    cache.set(key,cube);
    cachedRows+=cube.rows.length;
  }
  return cube;
}

self.onmessage=async(e:MessageEvent<{id:number;base:string;table:DemographicTable;parts:string[];query:DemographicQuery}>)=>{
  active?.abort();
  const controller=active=new AbortController();
  const {signal}=controller;
  const {id,base,table,parts,query}=e.data;
  try{
    if(!parts.length)throw new Error('Este ámbito no tiene datos en la tabla para los filtros elegidos.');
    const shards=new Map(table.shards.map(shard=>[shard.id,shard]));
    const result:DemographicResult={values:[],domain:[],series:[],pyramid:[]};
    for(let offset=0;offset<parts.length;offset+=6){
      await Promise.all(parts.slice(offset,offset+6).map(async part=>{
        const shard=shards.get(part);
        if(!shard)throw new Error('Este ámbito no está publicado en la tabla.');
        const cube=await loadCube(base+shard.file,shard.contentSha256,signal);
        signal.throwIfAborted();
        appendCubeResult(result,queryCube(table,cube,query));
      }));
    }
    if(!signal.aborted)self.postMessage({id,result});
  }catch(error){
    if(signal.aborted)return;
    controller.abort();
    self.postMessage({id,error:error instanceof Error?error.message:'No se pudo consultar esta tabla.'});
  }
};
