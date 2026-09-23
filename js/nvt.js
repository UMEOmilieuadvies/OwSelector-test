'use strict';

(()=>{
  const $=id=>document.getElementById(id);
  const escapeHtml=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normalise=s=>String(s??'').replace(/\s+/g,' ').trim();
  let regulations=[];
  const requestedId=new URLSearchParams(location.search).get('regeling')||'BAL';

  function noteHeading(doc){
    const headings=[...doc.querySelectorAll('h1,h2,h3,h4,h5,h6')]
      .filter(node=>normalise(node.textContent).toUpperCase()==='NOTA VAN TOELICHTING');
    return headings.at(-1)||null;
  }

  function contentsLinks(doc){
    const seen=new Set();
    return [...doc.querySelectorAll('a[href^="#"]')].map(link=>({
      target:decodeURIComponent(link.getAttribute('href').slice(1)),
      label:normalise(link.textContent)
    })).filter(item=>item.target&&item.label&&!seen.has(`${item.target}|${item.label}`)&&seen.add(`${item.target}|${item.label}`));
  }

  function showContents(frame){
    const slot=frame.closest('.nvtDocument').querySelector('.nvtTocSlot');
    const doc=frame.contentDocument;
    if(!doc||!slot)return;
    const links=contentsLinks(doc);
    if(!links.length){slot.innerHTML='<p class="nvtTocNotice">De officiële inhoudsopgave is niet als koppelingen beschikbaar in dit document.</p>';return;}
    slot.innerHTML=`<nav class="nvtToc" aria-label="Inhoudsopgave"><strong>Inhoudsopgave</strong><p>Ga direct naar een onderdeel van deze toelichting.</p><div class="nvtTocList">${links.map(item=>`<button type="button" data-nvt-target="${escapeHtml(item.target)}">${escapeHtml(item.label)}</button>`).join('')}</div></nav>`;
    slot.querySelectorAll('[data-nvt-target]').forEach(button=>button.addEventListener('click',()=>{
      const target=doc.getElementById(button.dataset.nvtTarget);
      if(target)target.scrollIntoView({behavior:'smooth',block:'start'});
    }));
  }

  function prepareFrame(frame){
    frame.addEventListener('load',()=>{
      const doc=frame.contentDocument;
      if(!doc)return;
      showContents(frame);
      const heading=noteHeading(doc);
      if(heading)requestAnimationFrame(()=>heading.scrollIntoView({block:'start'}));
    });
  }

  function show(key){
    const regulation=regulations.find(item=>item.id===key)||regulations[0];
    if(!regulation)return;
    $('nvtTitle').textContent=`Memorie van toelichting — ${regulation.name}`;
    $('nvtIntro').textContent=`Volledige officiële toelichtingen bij ${regulation.name}, lokaal opgenomen en buiten de gewone zoekindex.`;
    $('originalDocument').href=`https://wetten.overheid.nl/${regulation.bwb}`;
    $('nvtRegulations').innerHTML=regulations.map(item=>`<a class="${item.id===regulation.id?'active':''}" href="nvt.html?regeling=${item.id}">${escapeHtml(item.short)}</a>`).join('');
    $('nvtDocuments').innerHTML=regulation.documents.map((document,index)=>`<article class="nvtDocument"><p class="helpPanelLabel">${index?'Wijziging':'Oorspronkelijke regeling'}</p><h2>${escapeHtml(document.title)}</h2><dl><div><dt>Publicatie</dt><dd>${escapeHtml(document.publication)}</dd></div><div><dt>Datum</dt><dd>${escapeHtml(document.date)}</dd></div></dl><div class="nvtTocSlot" aria-live="polite"></div><iframe class="nvtFrame" src="data/nvt/${escapeHtml(document.file)}" title="${escapeHtml(document.title)}"></iframe></article>`).join('');
    $('nvtDocuments').querySelectorAll('.nvtFrame').forEach(prepareFrame);
  }

  fetch('nvt_catalog.json',{cache:'no-store'}).then(response=>response.json()).then(data=>{regulations=data.regulations||[];show(requestedId)}).catch(()=>{$('nvtIntro').textContent='Het overzicht kan nu niet worden geladen.'});
})();
