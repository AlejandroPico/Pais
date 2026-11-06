import {matchesProduct,type RegistryIndex,type RegistryProduct,type ProductQuery} from './registry';

const cache=new Map<string,Promise<RegistryProduct[]>>();
let newest=0;
async function records(index:RegistryIndex, kind:string,base:string):Promise<RegistryProduct[]> {
  if(!cache.has(kind))cache.set(kind,(async()=>{
    const descriptor=index.files[kind];if(!descriptor)throw new Error('Inventario desconocido');
    const response=await fetch(base+descriptor.file);if(!response.ok)throw new Error('No se pudo descargar el inventario');
    const bytes=await response.arrayBuffer();
    // Fetch may already decode gzip if the server declares Content-Encoding.
    const gzip=new Uint8Array(bytes)[0]===0x1f&&new Uint8Array(bytes)[1]===0x8b;
    const content=gzip?await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer():bytes;
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',content)),b=>b.toString(16).padStart(2,'0')).join('');
    if(digest!==descriptor.contentSha256)throw new Error('El inventario ha cambiado. Recarga la página para actualizar su índice.');
    const rows=JSON.parse(new TextDecoder().decode(content)) as RegistryProduct[];
    if(rows.length!==descriptor.count)throw new Error('El inventario está incompleto');
    return rows;
  })().catch(e=>{cache.delete(kind);throw e;}));
  return cache.get(kind)!;
}
self.onmessage=async(e:MessageEvent<{id:number;index:RegistryIndex;query:ProductQuery;base:string}>)=>{
  const {id,index,query,base}=e.data;newest=id;
  try{
    const rows=await records(index,query.kind,base);if(id!==newest)return;
    const matches=rows.filter(p=>matchesProduct(p,query));
    const pages=Math.max(1,Math.ceil(matches.length/40));const page=Math.min(Math.max(query.page,0),pages-1);
    if(id===newest)self.postMessage({id,total:matches.length,page,pages,rows:matches.slice(page*40,page*40+40)});
  }catch(error){if(id===newest)self.postMessage({id,error:error instanceof Error?error.message:'No se pudo consultar el inventario'});}
};
