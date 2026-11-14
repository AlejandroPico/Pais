import {normalize} from './data';

type Province = {code:string;name:string};
type Index = {source:string;provinces:Record<string,{file:string;count:number;sha256:string}>};
type Data = {entries:string[];notes:string};
const root=import.meta.env.BASE_URL+'datos/poblacion/intercensal/';
const esc=(value:string)=>value.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));

function format(entry:string){
  const [,,years,...lines]=entry.split('\n').filter(line=>line.trim());
  const period=years.split(';').slice(1,-1);
  const dimensions=lines.slice(0,3).map(line=>line.split(';').slice(0,-1));
  return `<table class="demog-table"><thead><tr><th>Censo</th>${dimensions.map(row=>`<th>${esc(row[0])}</th>`).join('')}</tr></thead>
    <tbody>${period.map((year,index)=>`<tr><th scope="row">${esc(year)}</th>${dimensions.map(row=>`<td>${esc(row[index+1])}</td>`).join('')}</tr>`).join('')}</tbody></table>
    ${lines.slice(3).map(note=>`<p class="data-note">${esc(note)}</p>`).join('')}
    <button class="text-button" data-historical-export>Descargar CSV</button>`;
}

export async function mountHistoricalCensus(panel:HTMLElement,provinces:Province[]){
  panel.innerHTML='<p role="status">Cargando censos históricos…</p>';
  try{
    const response=await fetch(root+'index.json');
    if(!response.ok)throw new Error('No se pudo consultar el catálogo histórico.');
    const index:Index=await response.json();
    if(!panel.isConnected)return;
    panel.innerHTML=`
      <label class="field-label">Provincia<select>${provinces.filter(p=>index.provinces[p.code]).map(p=>`<option value="${esc(p.code)}">${esc(p.name)}</option>`).join('')}</select></label>
      <label class="field-label">Municipio o código<input type="search" placeholder="Buscar en esta provincia"></label>
      <p role="status" class="data-note"></p><div class="historical-results"></div><details class="nomen-entry"><summary>Notas de la fuente</summary><p data-history-notes class="data-note"></p></details>
      <div class="pagination"><button data-history-prev>Anterior</button><span></span><button data-history-next>Siguiente</button></div>
      <p><a href="${esc(index.source)}" target="_blank" rel="noopener">Consulta y metodología del INE ↗</a></p>`;
    const select=panel.querySelector('select')!;
    const input=panel.querySelector('input')!;
    const results=panel.querySelector('.historical-results')!;
    const status=panel.querySelector('[role=status]')!;
    const previous=panel.querySelector<HTMLButtonElement>('[data-history-prev]')!;
    const next=panel.querySelector<HTMLButtonElement>('[data-history-next]')!;
    const pageLabel=panel.querySelector('.pagination span')!;
    if(index.provinces['28'])select.value='28';
    let entries:string[]=[];
    let page=0;
    let request=0;
    function draw(){
      const term=normalize(input.value.trim());
      const match=entries.filter(entry=>normalize(entry.split('\n',1)[0]).includes(term));
      const pages=Math.max(1,Math.ceil(match.length/10));
      const visible=match.slice(page*10,(page+1)*10);
      status.textContent=match.length+' registros censales';
      pageLabel.textContent=(page+1)+' / '+pages;
      previous.disabled=page===0;
      next.disabled=page+1>=pages;
      results.innerHTML=visible.map(entry=>{
        const title=entry.split('\n',1)[0].split(/ {3,}/).at(-1)!.replace(/^Municipio:\s*/,'');
        return `<details class="nomen-entry"><summary>${esc(title)}</summary><div></div></details>`;
      }).join('');
      results.querySelectorAll('details').forEach((detail,i)=>{
        detail.ontoggle=()=>{
          const content=detail.querySelector('div')!;
          if(!detail.open||content.hasChildNodes())return;
          const entry=visible[i];
          content.innerHTML=format(entry);
          content.querySelector<HTMLButtonElement>('button')!.onclick=()=>{
            const blob=new Blob(['\uFEFF'+entry],{type:'text/csv;charset=utf-8'});
            const url=URL.createObjectURL(blob);
            const link=document.createElement('a');
            link.href=url;link.download='censo-historico-'+select.value+'.csv';link.click();
            setTimeout(()=>URL.revokeObjectURL(url),1000);
          };
        };
      });
    }
    async function load(){
      const serial=++request;
      const part=index.provinces[select.value];
      entries=[];page=0;draw();status.textContent='Cargando provincia…';
      try{
        const response=await fetch(root+part.file);
        if(!response.ok)throw new Error('No se pudo cargar la provincia.');
        const raw=await response.arrayBuffer();
        const digest=await crypto.subtle.digest('SHA-256',raw);
        const hash=Array.from(new Uint8Array(digest),value=>value.toString(16).padStart(2,'0')).join('');
        if(hash!==part.sha256)throw new Error('El archivo provincial no coincide con el catálogo.');
        const data:Data=JSON.parse(new TextDecoder().decode(raw));
        if(data.entries.length!==part.count)throw new Error('El archivo provincial está incompleto.');
        if(serial!==request||!panel.isConnected)return;
        entries=data.entries;
        panel.querySelector('[data-history-notes]')!.textContent=data.notes;
        draw();
      }catch(error){
        if(serial===request)status.textContent=error instanceof Error?error.message:'No se pudo cargar la provincia.';
      }
    }
    input.oninput=()=>{page=0;draw();};
    select.onchange=()=>void load();
    previous.onclick=()=>{page--;draw();};
    next.onclick=()=>{page++;draw();};
    await load();
  }catch(error){
    panel.textContent=error instanceof Error?error.message:'No se pudo cargar el censo histórico.';
  }
}
