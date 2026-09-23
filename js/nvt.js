'use strict';

(()=>{
  const $=id=>document.getElementById(id);
  const escapeHtml=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normalise=s=>String(s??'').replace(/\s+/g,' ').trim();
  let regulations=[];
  const requestedId=new URLSearchParams(location.search).get('regeling')||'BAL';

  function showContents(slot, documentFile, contents){
    const links=contents?.items||[];
    if(!links.length){slot.innerHTML='<p class="nvtTocNotice">De officiële inhoudsopgave is niet als koppelingen beschikbaar in dit document.</p>';return;}
    slot.innerHTML=`<nav class="nvtToc" aria-label="Inhoudsopgave"><strong>Inhoudsopgave</strong><p>Ga direct naar een onderdeel van deze toelichting.</p><div class="nvtTocList">${links.map(item=>`<button type="button" data-nvt-target="${escapeHtml(item.target)}">${escapeHtml(item.label)}</button>`).join('')}</div></nav>`;
    slot.querySelectorAll('[data-nvt-target]').forEach(button=>button.addEventListener('click',()=>{
      const frame=slot.closest('.nvtDocument').querySelector('.nvtFrame');
      frame.src=`data/nvt/${encodeURIComponent(documentFile)}#${encodeURIComponent(button.dataset.nvtTarget)}`;
    }));
  }

  function documentUrl(document, contents){
    const anchor=contents?.note_anchor;
    return `data/nvt/${encodeURIComponent(document.file)}${anchor?`#${encodeURIComponent(anchor)}`:''}`;
  }

  function show(key){
    const regulation=regulations.find(item=>item.id===key)||regulations[0];
    if(!regulation)return;
    $('nvtTitle').textContent=`Memorie van toelichting — ${regulation.name}`;
    $('nvtIntro').textContent=`Volledige officiële toelichtingen bij ${regulation.name}, lokaal opgenomen en buiten de gewone zoekindex.`;
    $('originalDocument').href=`https://wetten.overheid.nl/${regulation.bwb}`;
    $('nvtRegulations').innerHTML=regulations.map(item=>`<a class="${item.id===regulation.id?'active':''}" href="nvt.html?regeling=${item.id}">${escapeHtml(item.short)}</a>`).join('');
    $('nvtDocuments').innerHTML=regulation.documents.map((document,index)=>`<article class="nvtDocument"><p class="helpPanelLabel">${index?'Wijziging':'Oorspronkelijke regeling'}</p><h2>${escapeHtml(document.title)}</h2><dl><div><dt>Publicatie</dt><dd>${escapeHtml(document.publication)}</dd></div><div><dt>Datum</dt><dd>${escapeHtml(document.date)}</dd></div></dl><div class="nvtTocSlot" aria-live="polite"></div><iframe class="nvtFrame" src="${documentUrl(document, nvtContents[document.file])}" title="${escapeHtml(document.title)}"></iframe></article>`).join('');
    regulation.documents.forEach((document,index)=>showContents($('nvtDocuments').children[index].querySelector('.nvtTocSlot'),document.file,nvtContents[document.file]));
  }

  let nvtContents={};
  Promise.all([fetch('nvt_catalog.json',{cache:'no-store'}).then(response=>response.json()),fetch('data/nvt/toc.json',{cache:'no-store'}).then(response=>response.ok?response.json():{})]).then(([data,contents])=>{regulations=data.regulations||[];nvtContents=contents||{};show(requestedId)}).catch(()=>{$('nvtIntro').textContent='Het overzicht kan nu niet worden geladen.'});
})();
