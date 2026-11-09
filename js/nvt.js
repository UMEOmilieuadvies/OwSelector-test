'use strict';

(()=>{
  const $=id=>document.getElementById(id);
  const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const clean=value=>String(value??'').replace(/\s+/g,' ').trim();
  let index={regulations:[]};
  let current=null;
  const requested=new URLSearchParams(location.search).get('regeling')||'BAL';

  function words(){return clean($('nvtSearch').value).toLocaleLowerCase('nl-NL').split(' ').filter(Boolean);}
  function officialUrl(section){return `${section.official_url}${section.anchor?`#${encodeURIComponent(section.anchor)}`:''}`;}
  function matches(section){
    const kind=$('nvtKind').value;
    const article=clean($('nvtArticle').value).toLocaleLowerCase('nl-NL');
    const haystack=`${section.title} ${section.text}`.toLocaleLowerCase('nl-NL');
    return (!kind||section.kind===kind)&&(!article||section.article.toLocaleLowerCase('nl-NL')===article)&&words().every(word=>haystack.includes(word));
  }
  function card(section){
    const paragraphs=(section.paragraphs||[section.text]).map(paragraph=>`<p>${escapeHtml(paragraph)}</p>`).join('');
    const label=section.kind==='article'?'Artikelsgewijze toelichting':'Algemene toelichting';
    const open=words().length||$('nvtArticle').value?' open':'';
    return `<details class="integratedNvtSection"${open}><summary><span class="integratedNvtKind">${label}</span><strong>${escapeHtml(section.title)}</strong></summary><div class="integratedNvtSectionBody"><div class="integratedNvtText">${paragraphs||'<p>Geen tekst beschikbaar.</p>'}</div><aside class="integratedNvtSource"><strong>Officiële bron</strong><span>${escapeHtml(section.source)} · ${escapeHtml(section.publication)} (${escapeHtml(section.date)})</span><a href="${escapeHtml(officialUrl(section))}" target="_blank" rel="noopener">Open de officiële vindplaats</a></aside></div></details>`;
  }
  function render(){
    if(!current)return;
    const sections=current.documents.flatMap(document=>document.sections||[]).filter(matches);
    $('nvtStats').textContent=`${sections.length} ${sections.length===1?'onderdeel':'onderdelen'} gevonden in ${current.regulation.name}.`;
    $('nvtContent').innerHTML=sections.length?sections.map(card).join(''):'<p class="nvtLoading">Geen toelichtingsonderdelen voldoen aan deze selectie.</p>';
  }
  async function loadRegulation(id){
    const regulation=index.regulations.find(item=>item.id===id)||index.regulations[0];
    if(!regulation)return;
    $('nvtRegulation').value=regulation.id;
    $('nvtContent').innerHTML='<p class="nvtLoading">De geïntegreerde toelichting wordt geladen…</p>';
    $('nvtStats').textContent='';
    const response=await fetch(`data/nvt/integrated/${encodeURIComponent(regulation.file)}`,{cache:'no-store'});
    if(!response.ok)throw new Error('NVT-bestand niet beschikbaar');
    current=await response.json();
    history.replaceState(null,'',`nvt.html?regeling=${encodeURIComponent(regulation.id)}`);
    render();
  }
  async function init(){
    const response=await fetch('data/nvt/integrated_index.json',{cache:'no-store'});
    if(!response.ok)throw new Error('NVT-index niet beschikbaar');
    index=await response.json();
    $('nvtRegulation').innerHTML=index.regulations.map(regulation=>`<option value="${escapeHtml(regulation.id)}">${escapeHtml(regulation.name)}</option>`).join('');
    $('nvtRegulation').addEventListener('change',()=>loadRegulation($('nvtRegulation').value).catch(failed));
    for(const id of ['nvtSearch','nvtArticle','nvtKind'])$(id).addEventListener('input',render);
    $('nvtReset').addEventListener('click',()=>{$('nvtSearch').value='';$('nvtArticle').value='';$('nvtKind').value='';render();});
    await loadRegulation(index.regulations.some(item=>item.id===requested)?requested:index.regulations[0]?.id);
  }
  function failed(){
    $('nvtStats').textContent='';
    $('nvtContent').innerHTML='<p class="nvtLoading">De geïntegreerde toelichting kan nu niet worden geladen. Open eventueel de officiële bron via wetten.nl.</p>';
  }
  init().catch(failed);
})();
