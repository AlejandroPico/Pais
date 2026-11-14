import {normalize} from './data';

type Row=[string,number,string,'sex'|'edad'|'naci',...number[]];
type Index={
  source:string;
  editions:{year:number;files:Record<string,number>}[];
  provinces:Record<string,{file:string;rows:number;contentSha256:string}>;
};

const root=import.meta.env.BASE_URL+'datos/territorio/nomenclator/';
const fmt=new Intl.NumberFormat('es-ES');
const esc=(value:string)=>value.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
let indexPromise:Promise<Index>|undefined;

async function rowsFor(part:Index['provinces'][string],signal:AbortSignal){
  const response=await fetch(root+part.file,{signal});
  if(!response.ok)throw new Error('No se pudo cargar la provincia.');
  const raw=await response.arrayBuffer();
  const bytes=new Uint8Array(raw);
  const content=bytes[0]===31&&bytes[1]===139
    ?await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()
    :raw;
  const digest=await crypto.subtle.digest('SHA-256',content);
  const hash=Array.from(new Uint8Array(digest),value=>value.toString(16).padStart(2,'0')).join('');
  if(hash!==part.contentSha256)throw new Error('El archivo provincial no coincide con el catálogo.');
  const rows=new TextDecoder().decode(content).trimEnd().split('\n').map(line=>JSON.parse(line) as Row);
  if(rows.length!==part.rows)throw new Error('El archivo provincial está incompleto.');
  return rows;
}

export async function mountNomenclator(panel:HTMLElement,provinces:{code:string;name:string}[]){
  panel.innerHTML='<p role="status">Cargando ediciones del Nomenclátor…</p>';
  try{
    const index=await(indexPromise??=fetch(root+'index.json').then(response=>{
      if(!response.ok)throw new Error('No se pudo cargar el Nomenclátor.');
      return response.json() as Promise<Index>;
    }).catch(error=>{indexPromise=undefined;throw error;}));
    if(!panel.isConnected)return;
    const $=<T extends HTMLElement=HTMLElement>(id:string)=>panel.querySelector<T>('#'+id)!;
    panel.innerHTML=`
      <label class="field-label">Provincia<select id="nomen-province">${provinces.filter(p=>index.provinces[p.code]).map(p=>`<option value="${esc(p.code)}">${esc(p.name)}</option>`).join('')}</select></label>
      <label class="field-label">Año<select id="nomen-year">${[...index.editions].reverse().map(edition=>`<option>${edition.year}</option>`).join('')}</select></label>
      <label class="field-label">Nombre o código<input id="nomen-search" type="search" placeholder="Buscar una unidad de población…"></label>
      <p class="data-note" id="nomen-count" role="status"></p><div id="nomen-list"></div>
      <div class="pagination"><button id="nomen-prev">Anterior</button><span id="nomen-page"></span><button id="nomen-next">Siguiente</button></div>
      <p><a href="${esc(index.source)}" target="_blank" rel="noopener">Nomenclátor del INE ↗</a> · <a id="nomen-download" download>Descargar datos de la provincia</a></p>`;

    const province=$<HTMLSelectElement>('nomen-province');
    if(index.provinces['28'])province.value='28';
    let rows:Row[]=[];
    let page=0;
    let controller:AbortController|undefined;
    function draw(){
      const term=normalize($<HTMLInputElement>('nomen-search').value.trim());
      const year=Number($<HTMLSelectElement>('nomen-year').value);
      const filtered=rows.filter(row=>row[1]===year&&row[3]==='sex'&&normalize(row[0]+' '+row[2]).includes(term));
      const pages=Math.max(1,Math.ceil(filtered.length/12));
      page=Math.max(0,Math.min(page,pages-1));
      const visible=filtered.slice(page*12,(page+1)*12);
      const codes=new Set(visible.map(row=>row[0]));
      const details=new Map<string,Row[]>();
      for(const row of rows){
        if(row[1]!==year||row[3]==='sex'||!codes.has(row[0]))continue;
        const group=details.get(row[0])||[];
        group.push(row);details.set(row[0],group);
      }
      $('nomen-count').textContent=fmt.format(filtered.length)+' unidades de población';
      $('nomen-list').innerHTML=visible.map(row=>{
        const [, ,name,,total,men,women,historical]=row;
        const extras=details.get(row[0])||[];
        return `<details class="nomen-entry"><summary>${esc(name)} <small>${fmt.format(total)} ${year===1981?'habitantes de hecho':'habitantes'}</small></summary>
          <p>Código ${row[0]} · ${fmt.format(men)} hombres · ${fmt.format(women)} mujeres</p>
          ${historical===undefined?'':`<p>Población de derecho: ${fmt.format(historical)}.</p>`}
          ${extras.map(([, , ,measure, ,first,second,third])=>measure==='edad'
            ?`<p>Edad · ${fmt.format(first)} menores de 16, ${fmt.format(second)} de 16 a 64 y ${fmt.format(third)} de 65 o más.</p>`
            :`<p>Nacionalidad · ${fmt.format(first)} española y ${fmt.format(second)} extranjera.</p>`).join('')}
        </details>`;
      }).join('');
      $('nomen-page').textContent=`${page+1} / ${pages}`;
      $<HTMLButtonElement>('nomen-prev').disabled=page===0;
      $<HTMLButtonElement>('nomen-next').disabled=page>=pages-1;
    }
    async function load(){
      controller?.abort();
      const active=controller=new AbortController();
      const part=index.provinces[province.value];
      $<HTMLAnchorElement>('nomen-download').href=root+part.file;
      rows=[];page=0;draw();$('nomen-count').textContent='Cargando provincia…';
      try{
        const loaded=await rowsFor(part,active.signal);
        if(active.signal.aborted||!panel.isConnected)return;
        rows=loaded;draw();
      }catch(error){
        if(!active.signal.aborted)$('nomen-count').textContent=error instanceof Error?error.message:'No se pudo cargar la provincia.';
      }
    }
    province.onchange=()=>void load();
    for(const id of ['nomen-search','nomen-year'])$(id).oninput=()=>{page=0;draw();};
    $('nomen-prev').onclick=()=>{page--;draw();};
    $('nomen-next').onclick=()=>{page++;draw();};
    await load();
  }catch(error){
    panel.textContent=error instanceof Error?error.message:'No se pudo cargar el Nomenclátor.';
  }
}
