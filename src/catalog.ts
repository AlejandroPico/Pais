import {normalize,safeUrl} from './data';
import type {RegistryIndex,RegistryProduct,RegistrySource,ProductQuery} from './registry';

const esc=(s:unknown)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
const number=(n:number)=>n.toLocaleString('es-ES');
const base=`${import.meta.env.BASE_URL}data/registry/`;
const kinds:Record<string,string>={
  available:'Disponibles en el mapa',territory:'Inventario cartográfico',demography:'Inventario demográfico',
  welfare:'Inventario de renta',labor:'Tablas de empleo y salarios',ioe:'Operaciones IOE',ine:'Tablas INEbase',national:'Catálogo nacional',
};
let indexPromise:Promise<RegistryIndex>|undefined;

type Options={
  category?:string;signal:AbortSignal;icons:()=>void;
  activate:(action:string)=>void;setTitle:(title:string)=>void;
};
type Reply={id:number;error?:string;total:number;page:number;pages:number;rows:RegistryProduct[]};

export async function mountCatalog(root:HTMLElement,{category,signal,activate,setTitle}:Options){
  const index=await(indexPromise??=fetch(base+'index.json').then(response=>{
    if(!response.ok)throw new Error('No se pudo cargar el registro de fuentes');
    return response.json() as Promise<RegistryIndex>;
  }).catch(error=>{indexPromise=undefined;throw error;}));
  if(signal.aborted)return;

  setTitle('El país · Fuentes · Revisión '+index.revision.split('-').reverse().join('/'));
  let tab=category?'products':'sources';
  let worker:Worker|undefined;
  let request=0;
  let timer:ReturnType<typeof setTimeout>;
  let observer:ResizeObserver|undefined;
  let sourcePage=0,coveragePage=0,sourceTerm='',sourceKind='research';
  let pageSize=1;
  const query:ProductQuery={
    kind:category&&!['F01','F02','F03','F04'].includes(category)?'ioe':'available',
    q:'',category:category||'',source:'',status:'',page:0,
  };
  signal.addEventListener('abort',()=>{worker?.terminate();observer?.disconnect();clearTimeout(timer);});

  root.innerHTML=`
    <nav class="catalog-tabs" aria-label="Apartados de Fuentes">
      <button data-catalog-tab="sources">Fuentes</button><button data-catalog-tab="products">Productos</button>
      <button data-catalog-tab="coverage">Cobertura</button>
    </nav>
    <div id="catalog-content"></div>
    <footer class="catalog-footer">
      <a id="catalog-download" href="${base}index.json" download>Descargar registro</a>
      <a href="https://github.com/AlejandroPico/Pais/blob/main/docs/F00.md" target="_blank" rel="noopener">Metodología ↗</a>
    </footer>`;
  const $=<T extends HTMLElement=HTMLElement>(selector:string)=>root.querySelector<T>(selector)!;
  const link=(url:string,label:string)=>`<a href="${esc(safeUrl(url,'https://datos.gob.es/'))}" target="_blank" rel="noopener">${label} ↗</a>`;
  root.querySelectorAll<HTMLButtonElement>('[data-catalog-tab]').forEach(button=>{
    button.onclick=()=>{tab=button.dataset.catalogTab!;render();};
  });

  function render(){
    ++request;
    observer?.disconnect();
    root.querySelectorAll('[data-catalog-tab]').forEach(button=>{
      button.setAttribute('aria-current',String(button.getAttribute('data-catalog-tab')===tab));
    });
    const download=$<HTMLAnchorElement>('#catalog-download');
    download.href=base+(tab==='products'?index.files[query.kind].file:'index.json');
    download.textContent=tab==='products'?'Descargar inventario':'Descargar registro';
    if(tab==='sources')renderSources();
    else if(tab==='products')renderProducts();
    else renderCoverage();
  }

  function listShell(filters=''){
    $('#catalog-content').innerHTML=`${filters}
      <p class="catalog-status" role="status" id="catalog-count">Cargando…</p>
      <div class="catalog-results" id="catalog-results"></div>
      <nav class="pagination" aria-label="Paginación" id="catalog-pages"></nav>`;
  }

  function fitPage(draw:()=>void){
    observer?.disconnect();
    const results=$('#catalog-results');
    const measure=(redraw=true)=>{
      const styles=getComputedStyle(results);
      const columns=styles.gridTemplateColumns.split(' ').length;
      const row=parseFloat(styles.gridAutoRows);
      const gap=parseFloat(styles.rowGap);
      const next=Math.max(1,Math.floor((results.clientHeight+gap)/(row+gap)))*columns;
      if(Number.isFinite(next)&&next!==pageSize){pageSize=next;if(redraw)draw();}
    };
    observer=new ResizeObserver(()=>measure());
    observer.observe(results);
    measure(false);
    draw();
  }

  function pages(total:number,page:number,count:number,change:(page:number)=>void){
    $('#catalog-count').textContent=`${number(total)} ${total===1?'resultado':'resultados'}`;
    $('#catalog-pages').innerHTML=`
      <button id="catalog-prev" ${page<=0?'disabled':''}>Anterior</button>
      <span aria-label="Página ${page+1} de ${count}">${page+1} / ${count}</span>
      <button id="catalog-next" ${page>=count-1?'disabled':''}>Siguiente</button>`;
    $('#catalog-prev').onclick=()=>change(page-1);
    $('#catalog-next').onclick=()=>change(page+1);
  }

  function row(title:string,summary:string,actions=''){
    return `<article class="catalog-row"><div><h3 title="${esc(title)}">${esc(title)}</h3><p>${esc(summary)}</p></div>
      ${actions?'<div class="catalog-row-actions">'+actions+'</div>':''}</article>`;
  }

  function bindRows(details:(i:number)=>void){
    root.querySelectorAll<HTMLButtonElement>('[data-row]').forEach(button=>{
      button.onclick=()=>details(Number(button.dataset.row));
    });
    root.querySelectorAll<HTMLButtonElement>('[data-map-action]').forEach(button=>{
      button.onclick=()=>activate(button.dataset.mapAction!);
    });
  }

  function detail(title:string,body:string){
    ++request;
    observer?.disconnect();
    $('#catalog-content').innerHTML=`<div><button id="catalog-back">← Volver al listado</button></div>
      <article class="catalog-detail"><h3>${esc(title)}</h3>${body}</article>`;
    $('#catalog-back').onclick=render;
    $('#catalog-back').focus();
  }

  function sourceDetail(source:RegistrySource){
    detail(source.name,`<p>${esc(source.coverage||'Según el producto')}</p><p>${esc(source.notes)}</p>
      ${source.families.length?`<ul class="family-list">${source.families.map(f=>'<li>'+esc(f)+'</li>').join('')}</ul>`:''}
      <p>${esc(source.access||'Consultar el producto original')}</p><p>${link(source.url,'Abrir fuente')}</p>`);
  }

  function renderSources(){
    listShell(`<div class="catalog-filters"><input id="source-search" type="search" aria-label="Buscar fuentes" placeholder="Buscar organismos…" value="${esc(sourceTerm)}">
      <select id="source-kind" aria-label="Directorio"><option value="research">Fuentes investigadas</option>
      <option value="publisher">Publicadores federados</option><option value="auxiliary">Cartografía auxiliar</option></select></div>`);
    $<HTMLSelectElement>('#source-kind').value=sourceKind;
    const draw=()=>{
      const terms=normalize(sourceTerm).split(/\s+/).filter(Boolean);
      const matches=index.sources.filter(source=>source.kind===sourceKind&&terms.every(term=>
        normalize([source.name,source.coverage,source.group,...source.families].join(' ')).includes(term)));
      const count=Math.max(1,Math.ceil(matches.length/pageSize));
      sourcePage=Math.min(sourcePage,count-1);
      const rows=matches.slice(sourcePage*pageSize,(sourcePage+1)*pageSize);
      $('#catalog-results').innerHTML=rows.map((source,i)=>row(source.name,source.coverage||source.group||'Según el producto',
        `<button data-row="${i}">Ficha</button>`)).join('')||'<p class="catalog-status">No hay fuentes con esos filtros.</p>';
      bindRows(i=>sourceDetail(rows[i]));
      pages(matches.length,sourcePage,count,page=>{sourcePage=page;draw();});
    };
    $('#source-search').oninput=()=>{sourceTerm=$<HTMLInputElement>('#source-search').value;sourcePage=0;draw();};
    $('#source-kind').onchange=()=>{sourceKind=$<HTMLSelectElement>('#source-kind').value;sourcePage=0;draw();};
    fitPage(draw);
  }

  function renderCoverage(){
    listShell();
    fitPage(()=>{
      const entries=index.categoryCoverage;
      const count=Math.max(1,Math.ceil(entries.length/pageSize));
      coveragePage=Math.min(coveragePage,count-1);
      const rows=entries.slice(coveragePage*pageSize,(coveragePage+1)*pageSize);
      $('#catalog-results').innerHTML=rows.map((entry,i)=>row(index.categories.find(c=>c.id===entry.categoryId)?.name||entry.categoryId,
        `${entry.available} disponibles · ${entry.status==='parcial'?'Parcial':entry.status==='completo'?'Completo':'Pendiente'}`,
        `<button data-row="${i}">Productos</button>`)).join('');
      bindRows(i=>{
        query.category=rows[i].categoryId;
        query.kind=rows[i].available?'available':'ioe';
        query.page=0;query.source='';query.status='';query.q='';
        tab='products';render();
      });
      pages(entries.length,coveragePage,count,page=>{coveragePage=page;renderCoverage();});
    });
  }

  function renderProducts(){
    const options=Object.entries(kinds).filter(([id])=>index.files[id]);
    const sources=index.sources.filter(source=>query.kind==='national'?source.kind==='publisher':source.kind!=='publisher');
    listShell(`<div class="catalog-filters">
      <select id="inventory-kind" aria-label="Inventario">${options.map(([id,label])=>`<option value="${id}">${label} · ${number(index.files[id].count)}</option>`).join('')}</select>
      <input id="product-search" type="search" placeholder="Buscar productos…" aria-label="Buscar productos" value="${esc(query.q)}">
    </div><div class="catalog-filters secondary">
      <select id="product-category" aria-label="Tema"><option value="">Todos los temas</option>${index.categories.map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join('')}</select>
      <select id="product-source" aria-label="Fuente"><option value="">Todas las fuentes</option>${sources.map(s=>`<option value="${esc(s.id)}">${esc(s.name)}</option>`).join('')}</select>
      <select id="product-status" aria-label="Estado"><option value="">Todos los estados</option>${Object.entries(index.statusLabels).map(([id,label])=>`<option value="${id}">${esc(label)}</option>`).join('')}</select>
    </div>`);
    $<HTMLSelectElement>('#inventory-kind').value=query.kind;
    for(const [id,key] of [['product-category','category'],['product-source','source'],['product-status','status']] as const){
      const select=$<HTMLSelectElement>('#'+id);
      select.value=query[key];
      select.onchange=()=>{query[key]=select.value;query.page=0;search();};
    }
    $('#inventory-kind').onchange=()=>{
      query.kind=$<HTMLSelectElement>('#inventory-kind').value;
      query.source='';query.page=0;
      if(['ine','national'].includes(query.kind))query.category='';
      render();
    };
    $('#product-search').oninput=()=>{
      query.q=$<HTMLInputElement>('#product-search').value;query.page=0;
      clearTimeout(timer);timer=setTimeout(search,180);
    };
    fitPage(search);
  }

  function search(){
    if(signal.aborted||tab!=='products'||!$('#catalog-results'))return;
    $('#catalog-count').textContent='Consultando…';
    if(!worker){
      worker=new Worker(new URL('./catalog.worker.ts',import.meta.url),{type:'module'});
      worker.onmessage=({data}:MessageEvent<Reply>)=>{
        if(data.id!==request||tab!=='products'||signal.aborted)return;
        if(data.error){
          $('#catalog-count').textContent=data.error;
          $('#catalog-results').innerHTML='<p><button id="catalog-retry">Reintentar</button></p>';
          $('#catalog-retry').onclick=search;
          return;
        }
        const {total,page,pages:count,rows}=data;
        query.page=page;
        $('#catalog-results').innerHTML=rows.map((product,i)=>row(product.title,
          [product.responsible||index.sources.find(s=>s.id===product.sourceId)?.name,
            index.statusLabels[product.status]||product.status].filter(Boolean).join(' · '),
          `<button data-row="${i}">Ficha</button>${product.mapAction?`<button data-map-action="${esc(product.mapAction)}">Ver mapa</button>`:''}`))
          .join('')||'<p class="catalog-status">No hay productos con esos filtros.</p>';
        bindRows(i=>productDetail(rows[i]));
        pages(total,page,count,next=>{query.page=next;search();});
      };
      worker.onerror=()=>{if(tab==='products'&&$('#catalog-count'))$('#catalog-count').textContent='No se pudo iniciar la búsqueda.';};
    }
    worker.postMessage({id:++request,index,query,pageSize,base:new URL(base,location.href).href});
  }

  function productDetail(product:RegistryProduct){
    const period=typeof product.period==='string'?product.period:
      [product.period?.from,product.period?.to].filter(Boolean).join(' – ');
    const fields={
      'Territorio':product.coverage||'Por verificar',
      'Periodo':period||'Por verificar',
      'Licencia':product.license||'Por verificar',
      ...(product.unit?{Unidad:product.unit}:{}),
      ...product.fields,
    };
    detail(product.title,`<p>${esc(index.statusLabels[product.status]||product.status)}</p>
      <dl>${Object.entries(fields).map(([key,value])=>`<dt>${esc(key)}</dt><dd>${esc(value)}</dd>`).join('')}</dl>
      ${product.notes?`<p>${esc(product.notes)}</p>`:''}
      ${product.review?`<p>${esc(product.review.updatedAt)} · ${esc(product.review.reason)}</p>`:''}
      ${product.review?.nextAction?`<p>${esc(product.review.nextAction)}</p>`:''}
      <p>${link(product.url,'Fuente original')}</p>
      ${Object.entries(product.links||{}).filter(([,url])=>url.startsWith('https://')).map(([key,url])=>
        `<p>${link(url,({enlaceDatos:'Datos',enlaceCalendario:'Calendario',enlaceMetodologia:'Metodología',enlaceMetodEstand2:'Informe metodológico'} as Record<string,string>)[key]||'Documentación original')}</p>`).join('')}
      ${product.mapAction?'<button id="catalog-open-map">Ver en el mapa</button>':''}`);
    if(product.mapAction)$('#catalog-open-map').onclick=()=>activate(product.mapAction!);
  }

  render();
}
