import {queryCube,type Cube,type DemographicTable,type DemographicQuery} from './demography-data';
const cache=new Map<string,Cube>();
self.onmessage=async(e:MessageEvent<{id:number;base:string;table:DemographicTable;part:string;query:DemographicQuery}>)=>{
  const {id,base,table,part,query}=e.data;
  try{
    const shard=table.shards.find(s=>s.id===part);if(!shard)throw new Error('Este ámbito no está publicado en la tabla.');
    const key=base+shard.file;let cube=cache.get(key);
    if(!cube){
      const response=await fetch(key);if(!response.ok)throw new Error('No se pudo descargar la tabla.');
      const bytes=await response.arrayBuffer();
      const magic=new Uint8Array(bytes);const compressed=magic[0]===0x1f&&magic[1]===0x8b;
      const content=compressed?await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer():bytes;
      const digest=await crypto.subtle.digest('SHA-256',content);const hash=Array.from(new Uint8Array(digest),n=>n.toString(16).padStart(2,'0')).join('');
      if(hash!==shard.contentSha256)throw new Error('La tabla no coincide con su ficha. Recarga la web para actualizarla.');
      cube=JSON.parse(new TextDecoder().decode(content)) as Cube;
      if(cache.size>=3)cache.delete(cache.keys().next().value!);cache.set(key,cube);
    }
    self.postMessage({id,result:queryCube(table,cube,query)});
  }catch(error){self.postMessage({id,error:error instanceof Error?error.message:'No se pudo consultar esta tabla.'});}
};
