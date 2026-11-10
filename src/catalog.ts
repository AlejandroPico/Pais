import {normalize,safeUrl} from './data';
import type {RegistryIndex,RegistryProduct,ProductQuery} from './registry';

const esc=(s:unknown)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
const number=(n:number)=>n.toLocaleString('es-ES');
let indexPromise:Promise<RegistryIndex>|undefined;
const base=`${import.meta.env.BASE_URL}data/registry/`;
const kinds:Record<string,string>={available:'Disponibles en el mapa',welfare:'Inventario de renta y condiciones de vida',demography:'Tablas demográficas · INE',territory:'Servicios cartográficos F01',ioe:'Operaciones IOE',ine:'Tablas INEbase',national:'Catálogo nacional'};

export async function mountCatalog(root:HTMLElement,options:{category?:string;signal:AbortSignal;icons:()=>void;activate:(action:string)=>void}) {
  const {signal,icons,activate}=options;
  const index:RegistryIndex=await(indexPromise??=fetch(base+'index.json').then(r=>{if(!r.ok)throw new Error('No se pudo cargar el registro de fuentes');return r.json();}).catch(e=>{indexPromise=undefined;throw e;}));
  if(signal.aborted)return;
  let tab=options.category?'products':'sources';
  let worker:Worker|undefined,request=0,timer:ReturnType<typeof setTimeout>;
  let query:ProductQuery={kind:options.category&&!['F01','F02','F03'].includes(options.category)?'ioe':'available',q:'',category:options.category||'',source:'',status:'',page:0};
  signal.addEventListener('abort',()=>{worker?.terminate();clearTimeout(timer);});
  root.innerHTML=`<h2 id="modal-title">Fuentes</h2><p class="modal-lead">Procedencia, productos y cobertura. Revisión del ${esc(index.revision.split('-').reverse().join('/'))}.</p>
  <nav class="catalog-tabs" aria-label="Apartados de Fuentes"><button data-catalog-tab="sources">Fuentes</button><button data-catalog-tab="products">Productos</button><button data-catalog-tab="coverage">Cobertura</button></nav>
  <div id="catalog-content"></div><footer class="catalog-footer"><a href="${base}index.json" download>Descargar registro de fuentes</a><a href="https://github.com/AlejandroPico/Pais/blob/main/docs/F00.md" target="_blank" rel="noopener">Método y actualización ↗</a></footer>`;
  const $=<T extends HTMLElement=HTMLElement>(q:string)=>root.querySelector<T>(q)!;
  root.querySelectorAll<HTMLButtonElement>('[data-catalog-tab]').forEach(b=>b.onclick=()=>{tab=b.dataset.catalogTab!;render();});
  function render(){
    root.querySelectorAll<HTMLButtonElement>('[data-catalog-tab]').forEach(b=>b.setAttribute('aria-current',String(b.dataset.catalogTab===tab)));
    if(tab==='sources')renderSources();else if(tab==='coverage')renderCoverage();else renderProducts();
    icons();
  }
  function renderSources(){
    $('#catalog-content').innerHTML=`<div class="registry-counts"><span><b>182</b> fichas de fuentes</span><span><b>238</b> publicadores federados</span></div><p class="catalog-note">Son dos directorios relacionados; una entidad puede aparecer en ambos. El estado se registra por producto, porque un organismo puede estar integrado solo en parte.</p>
    <div class="catalog-filters"><input id="source-search" type="search" aria-label="Buscar fuentes" placeholder="Buscar organismo, tema o territorio…"><select id="source-kind" aria-label="Directorio"><option value="research">Fuentes investigadas</option><option value="publisher">Publicadores federados</option><option value="auxiliary">Cartografía auxiliar</option></select></div><p id="source-count" class="catalog-note" role="status"></p><div id="source-results"></div><div id="source-pages" class="pagination"></div>`;
    let page=0;
    const draw=()=>{
      const terms=normalize($<HTMLInputElement>('#source-search').value).split(/\s+/).filter(Boolean);
      const kind=$<HTMLSelectElement>('#source-kind').value;
      const matches=index.sources.filter(s=>s.kind===kind&&terms.every(t=>normalize([s.name,s.coverage,s.group,...s.families].join(' ')).includes(t)));
      const pages=Math.max(1,Math.ceil(matches.length/20));page=Math.min(page,pages-1);
      $('#source-count').textContent=`${number(matches.length)} resultados · página ${page+1} de ${pages}`;
      $('#source-results').innerHTML=matches.slice(page*20,page*20+20).map(s=>`<article class="source-card"><span class="eyebrow">${esc(s.id)}${s.group?' · '+esc(s.group):''}</span><h3>${esc(s.name)}</h3><p>${esc(s.coverage||'Cobertura según producto')}${s.datasetCount!==undefined?' · '+number(s.datasetCount)+' títulos catalogados':''}</p><details><summary>Contenido y acceso</summary><p>${esc(s.notes)}</p>${s.families.length?`<ul class="family-list">${s.families.map(f=>`<li>${esc(f)}</li>`).join('')}</ul>`:''}<p>${esc(s.access||'Consultar el producto original')}</p><p>Licencia: ${esc(s.license||'verificar en cada producto')}</p></details><a href="${esc(safeUrl(s.url,'https://datos.gob.es/'))}" target="_blank" rel="noopener">Consultar fuente ↗</a></article>`).join('')||'<p class="empty-state">No hay fuentes con esos filtros.</p>';
      $('#source-pages').innerHTML=`<button id="source-prev" ${page===0?'disabled':''}>Anterior</button><span>${page+1} / ${pages}</span><button id="source-next" ${page>=pages-1?'disabled':''}>Siguiente</button>`;
      $('#source-prev').onclick=()=>{page--;draw();};$('#source-next').onclick=()=>{page++;draw();};
    };
    $('#source-search').oninput=()=>{page=0;draw();};$('#source-kind').onchange=()=>{page=0;draw();};draw();
  }
  function renderCoverage(){
    $('#catalog-content').innerHTML=`<p class="catalog-note">Disponible significa que el producto puede utilizarse; no que su capa esté activada. Un fascículo parcial conserva productos pendientes. Los candidatos IOE necesitan revisión individual y pueden pertenecer a varios temas.</p><div class="coverage-table"><table><thead><tr><th>Tema</th><th>Disponibles</th><th>Candidatos IOE</th><th>Estado</th></tr></thead><tbody>${index.categoryCoverage.map(c=>`<tr><td>${esc(index.categories.find(x=>x.id===c.categoryId)?.name)}</td><td>${c.available}</td><td>${c.ioeCandidates}</td><td>${c.status==='parcial'?'Parcial':'Pendiente'}</td></tr>`).join('')}</tbody></table></div><p class="catalog-note">El reparto de los títulos del catálogo nacional y de las tablas generales sigue pendiente. Una ausencia de clasificación no equivale a ausencia de datos.</p>`;
  }
  function renderProducts(){
    const availableSources=index.sources.filter(s=>query.kind==='national'?s.kind==='publisher':s.kind!=='publisher');
    $('#catalog-content').innerHTML=`<div class="catalog-filters"><select id="inventory-kind" aria-label="Inventario">${Object.entries(kinds).map(([id,label])=>`<option value="${id}" ${query.kind===id?'selected':''}>${label} · ${number(index.files[id].count)}</option>`).join('')}</select><input id="product-search" type="search" placeholder="Buscar productos…" aria-label="Buscar productos" value="${esc(query.q)}"></div>
    <div class="catalog-filters"><select id="product-category" aria-label="Filtrar por tema"><option value="">Todos los temas y pendientes de clasificar</option>${index.categories.map(c=>`<option value="${c.id}" ${query.category===c.id?'selected':''}>${esc(c.name)}</option>`).join('')}</select><select id="product-source" aria-label="Filtrar por fuente"><option value="">Todas las fuentes</option>${availableSources.map(s=>`<option value="${esc(s.id)}" ${query.source===s.id?'selected':''}>${esc(s.name)}</option>`).join('')}</select><select id="product-status" aria-label="Estado de integración"><option value="">Todos los estados</option>${Object.entries(index.statusLabels).map(([id,label])=>`<option value="${id}" ${query.status===id?'selected':''}>${esc(label)}</option>`).join('')}</select></div>
    <p class="catalog-note">${query.kind==='available'?'Productos utilizables en esta versión.':'Metadatos de descubrimiento; las observaciones y las condiciones de reutilización requieren revisión.'} ${query.kind==='national'||query.kind==='ine'?'Este inventario todavía no tiene clasificación temática individual.':''} ${query.kind==='ioe'?'El filtro temático usa los destinos orientativos del sector oficial.':''}</p>
    <p id="product-count" class="catalog-note" role="status">Preparando consulta…</p><div id="product-results"></div><div id="product-pages" class="pagination"></div><a id="inventory-download" class="download-catalog" href="${base+index.files[query.kind].file}" download>Descargar este inventario comprimido (.json.gz)</a>`;
    $('#inventory-kind').onchange=()=>{query={...query,kind:$<HTMLSelectElement>('#inventory-kind').value,source:'',page:0};renderProducts();};
    $('#product-search').oninput=()=>{query.q=$<HTMLInputElement>('#product-search').value;query.page=0;clearTimeout(timer);timer=setTimeout(search,180);};
    for(const [id,key] of [['product-category','category'],['product-source','source'],['product-status','status']] as const)$('#'+id).onchange=()=>{query[key]=$<HTMLSelectElement>('#'+id).value;query.page=0;search();};
    search();
  }
  function search(){
    if(signal.aborted||tab!=='products')return;
    $('#product-count').textContent=`Consultando ${kinds[query.kind].toLowerCase()}…`;
    $('#product-results').setAttribute('aria-busy','true');
    if(!worker){
      worker=new Worker(new URL('./catalog.worker.ts',import.meta.url),{type:'module'});
      worker.onmessage=(e:MessageEvent<{id:number;error?:string;total:number;page:number;pages:number;rows:RegistryProduct[]}>)=>{
        if(e.data.id!==request||tab!=='products'||signal.aborted)return;
        $('#product-results').removeAttribute('aria-busy');
        if(e.data.error){$('#product-count').textContent=e.data.error;$('#product-results').innerHTML='<button id="catalog-retry">Reintentar consulta</button>';$('#catalog-retry').onclick=search;return;}
        const {total,page,pages,rows}=e.data;query.page=page;
        $('#product-count').textContent=`${number(total)} ${total===1?'resultado':'resultados'} · página ${page+1} de ${pages}`;
        $('#product-results').innerHTML=rows.map(card).join('')||'<p class="empty-state">No hay productos con estos filtros. Los inventarios sin clasificación todavía no aparecen al seleccionar un tema.</p>';
        $('#product-pages').innerHTML=`<button id="product-prev" ${page===0?'disabled':''}>Anterior</button><span>${page+1} / ${pages}</span><button id="product-next" ${page>=pages-1?'disabled':''}>Siguiente</button>`;
        $('#product-prev').onclick=()=>{query.page--;search();};$('#product-next').onclick=()=>{query.page++;search();};
        root.querySelectorAll<HTMLButtonElement>('[data-map-action]').forEach(b=>b.onclick=()=>activate(b.dataset.mapAction!));
      };
      worker.onerror=()=>{if(tab==='products')$('#product-count').textContent='No se pudo iniciar la búsqueda. Recarga la página para reintentar.';};
    }
    worker.postMessage({id:++request,index,query,base:new URL(base,location.href).href});
  }
  function card(p:RegistryProduct){
    const source=index.sources.find(s=>s.id===p.sourceId);
    const period=typeof p.period==='string'?p.period:p.period?[p.period.from,p.period.to].filter(Boolean).join(' – '):'Por verificar';
    return `<article class="product-card"><div class="product-meta"><span>${esc(p.id.startsWith('http')?'CATÁLOGO NACIONAL':p.id)}</span><span class="status-tag ${p.status==='integrado'?'integrated':''}">${esc(index.statusLabels[p.status]||p.status)}</span></div><h3>${esc(p.title)}</h3><p>${esc(p.responsible||source?.name||p.sourceId)}</p><details><summary>Cobertura y procedencia</summary><dl><dt>Territorio / escala</dt><dd>${esc(p.coverage||'Por verificar en el producto original')}</dd><dt>Periodo / frecuencia</dt><dd>${esc(period||'Por verificar')}</dd><dt>Licencia</dt><dd>${esc(p.license||'Pendiente de verificar')}</dd>${p.unit?`<dt>Unidad</dt><dd>${esc(p.unit)}</dd>`:''}</dl>${p.notes?`<p>${esc(p.notes)}</p>`:''}${p.review?`<p>Revisión: ${esc(p.review.updatedAt)} · ${esc(p.review.reason)}</p>${p.review.nextAction?`<p>Siguiente paso: ${esc(p.review.nextAction)}</p>`:''}`:''}${p.fields?`<dl>${Object.entries(p.fields).map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`:''}${p.links?Object.entries(p.links).filter(([,u])=>u.startsWith('https://')).map(([k,u])=>`<a href="${esc(safeUrl(u,p.url))}" target="_blank" rel="noopener">${esc(({enlaceDatos:'Datos',enlaceCalendario:'Calendario',enlaceMetodologia:'Metodología',enlaceMetodEstand2:'Informe metodológico'} as Record<string,string>)[k]||'Documentación original')} ↗</a>`).join(' · '):''}</details><div class="product-actions"><a href="${esc(safeUrl(p.url,'https://datos.gob.es/'))}" target="_blank" rel="noopener">Origen ↗</a>${p.mapAction?`<button data-map-action="${esc(p.mapAction)}">Ver en el mapa</button>`:''}</div></article>`;
  }
  render();
}
