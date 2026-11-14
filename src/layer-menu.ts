const desktop=matchMedia('(min-width: 960px)');
type Card={details:HTMLDetailsElement;body:HTMLElement;panel:HTMLElement;marker:Comment};
export function bindLayerMenu(root:HTMLElement,dock:HTMLElement){
  const cards:Card[]=[];
  let count=0;
  const refresh=()=>{
    dock.dataset.depth=String(cards.length);
    cards.forEach((card,index)=>{
      const covered=index<cards.length-1;
      card.panel.classList.toggle('covered',covered);
      card.body.inert=covered;
    });
  };
  const closeFrom=(index:number)=>{
    for(const card of cards.splice(index).reverse()){
      card.marker.replaceWith(...card.body.childNodes);
      card.panel.remove();
      card.details.firstElementChild?.removeAttribute('aria-controls');
      card.details.open=false;
    }
    refresh();
  };
  const change=()=>{
    closeFrom(0);
    if(desktop.matches)root.querySelectorAll<HTMLDetailsElement>('details.submenu[open]').forEach(details=>details.open=false);
  };
  const show=(details:HTMLDetailsElement,summary:HTMLElement,parentIndex:number)=>{
    const index=parentIndex+1;
    if(cards[index]?.details===details){closeFrom(index);summary.focus();return;}
    closeFrom(index);
    const body=document.createElement('div');
    body.className='layer-card-body';
    for(const node of [...details.childNodes])if(node!==summary)body.append(node);
    const marker=document.createComment('submenu');
    details.append(marker);
    details.open=true;
    const panel=document.createElement('section');
    panel.className='layer-card';
    panel.style.setProperty('--card-index',String(index));
    const title=summary.querySelector('.submenu-label')?.textContent||summary.textContent?.replace(/›/g,'').trim()||'';
    const back=document.createElement('button');
    back.type='button';
    back.className='layer-card-back';
    back.textContent='‹ '+title;
    back.setAttribute('aria-label','Volver a '+title);
    back.onclick=()=>{
      if(index<cards.length-1){closeFrom(index+1);back.focus();}
      else {closeFrom(index);summary.focus();}
    };
    const header=document.createElement('header');
    header.append(back);
    panel.append(header,body);
    dock.append(panel);
    const id='layer-card-'+(++count);
    panel.id=id;
    panel.setAttribute('aria-label',title);
    summary.setAttribute('aria-controls',id);
    cards.push({details,body,panel,marker});
    refresh();
    back.focus({preventScroll:true});
  };
  const click=(event:MouseEvent)=>{
    if(!desktop.matches||!(event.target instanceof Element))return;
    const summary=event.target.closest<HTMLElement>('details.submenu > summary');
    const details=summary?.parentElement;
    if(!summary||!(details instanceof HTMLDetailsElement))return;
    const parent=summary.closest('.layer-card');
    const index=cards.findIndex(card=>card.panel===parent);
    if(parent&&index===-1)return;
    event.preventDefault();
    show(details,summary,index);
  };
  root.addEventListener('click',click);
  dock.addEventListener('click',click);
  desktop.addEventListener('change',change);
  change();
  return {
    close(){closeFrom(0);root.removeEventListener('click',click);dock.removeEventListener('click',click);desktop.removeEventListener('change',change);},
    back(){if(!cards.length)return false;const summary=cards.at(-1)!.details.firstElementChild as HTMLElement;
      closeFrom(cards.length-1);summary.focus();return true;},
    open(details:HTMLDetailsElement){
      if(!desktop.matches){details.open=true;return;}
      const summary=details.querySelector<HTMLElement>(':scope > summary');
      if(summary&&cards[0]?.details!==details)show(details,summary,-1);
    },
  };
}
