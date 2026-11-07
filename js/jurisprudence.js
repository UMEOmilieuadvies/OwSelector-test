'use strict';
(() => {
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const params=new URLSearchParams(location.search);
  const regulation=String(params.get('regeling')||'').trim().toUpperCase();
  const article=String(params.get('artikel')||'').trim().toLowerCase();
  const title=document.getElementById('jurisprudenceTitle');
  const intro=document.getElementById('jurisprudenceIntro');
  const content=document.getElementById('jurisprudenceContent');
  const caseCard=item=>{const summary=item.summary&&typeof item.summary==='object'?item.summary:{core:String(item.summary||''),ruling:'',relevance:''};return `<article class="jurisprudenceCard"><div class="jurisprudenceCardHead"><h2>${esc(item.ecli)}</h2><span>${esc(item.court)} · ${esc(item.year)}</span></div><dl class="jurisprudenceSummaryList"><div><dt>Kern</dt><dd>${esc(summary.core)}</dd></div>${summary.ruling?`<div><dt>Oordeel</dt><dd>${esc(summary.ruling)}</dd></div>`:''}${summary.relevance?`<div><dt>Betekenis voor de regeling</dt><dd>${esc(summary.relevance)}</dd></div>`:''}</dl><p class="jurisprudenceArticles">Gekoppeld aan: ${item.articles.map(number=>`Artikel ${esc(number)} BAL`).join(', ')}.</p><a class="jurisprudenceSource" href="${esc(item.official_url)}" target="_blank" rel="noopener noreferrer">Open officiële uitspraak op Rechtspraak.nl ↗</a></article>`};
  function empty(message){content.innerHTML=`<section class="articleNotesEmpty"><h2>Geen proefresultaten</h2><p>${esc(message)}</p></section>`}
  async function load(){
    try{
      const response=await fetch('data/jurisprudence.json',{cache:'no-store'});
      if(!response.ok)throw new Error('proefgegevens ontbreken');
      const data=await response.json();
      const all=Array.isArray(data.cases)?data.cases:[];
      if(regulation&&article){
        title.textContent=`Jurisprudentie bij artikel ${article}`;
        intro.textContent=`Besluit activiteiten leefomgeving (BAL) · ${data.scope||'Gecontroleerde proefkoppelingen.'}`;
        const rows=all.filter(item=>regulation==='BAL'&&item.articles.map(String).includes(article));
        if(!rows.length){empty('Voor dit artikel bevat de proefset nog geen gecontroleerde uitspraken.');return}
        content.innerHTML=`<section class="jurisprudenceSummary"><h2>${rows.length} ${rows.length===1?'uitspraak':'uitspraken'} in de proefset</h2><p>Alleen uitspraken met een expliciete verwijzing naar dit BAL-artikel staan hier. De korte samenvatting is informatief; de officiële uitspraak is leidend.</p></section><section class="jurisprudenceList">${rows.map(caseCard).join('')}</section>`;
        return;
      }
      title.textContent='Jurisprudentie';
      intro.textContent=data.scope||'Gecontroleerde proefkoppelingen.';
      content.innerHTML=`<section class="jurisprudenceSummary"><h2>Proefopstelling</h2><p>Deze afzonderlijke pagina bevat alleen handmatig gecontroleerde koppelingen met gepubliceerde Rechtspraak-uitspraken. De juridische bron blijft altijd de officiële uitspraak.</p></section><section class="jurisprudenceList">${all.map(caseCard).join('')}</section>`;
    }catch(_){
      empty('De proefgegevens kunnen nu niet worden geladen. Probeer het later opnieuw.');
    }
  }
  load();
})();
