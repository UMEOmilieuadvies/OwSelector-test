'use strict';
(() => {
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const params=new URLSearchParams(location.search);
  const regulation=String(params.get('regeling')||'').trim().toUpperCase();
  const article=String(params.get('artikel')||'').trim().toLowerCase();
  const title=document.getElementById('jurisprudenceTitle');
  const intro=document.getElementById('jurisprudenceIntro');
  const content=document.getElementById('jurisprudenceContent');
  const MAX_ARTICLES_PER_REGULATION=3;
  const referencesOf=item=>Array.isArray(item.references)?item.references:[];
  const regulationName=(data,id)=>data.regulations?.[id]?.name||id;
  const testArticlesForRegulation=(cases,regulationId)=>{
    const articles=new Map();
    for(const item of cases){for(const reference of referencesOf(item)){
      if(String(reference.regulation).toUpperCase()!==regulationId)continue;
      const article=String(reference.article||'').trim();
      if(!article)continue;
      if(!articles.has(article))articles.set(article,new Set());
      articles.get(article).add(item.ecli);
    }}
    return [...articles.entries()].slice(0,MAX_ARTICLES_PER_REGULATION).map(([article,eclis])=>({article,count:eclis.size}));
  };
  const caseCard=(data,item)=>{const summary=item.summary&&typeof item.summary==='object'?item.summary:{core:String(item.summary||''),ruling:'',relevance:''};const references=referencesOf(item);return `<article class="jurisprudenceCard"><div class="jurisprudenceCardHead"><h2>${esc(item.ecli)}</h2><span>${esc(item.court)} · ${esc(item.year)}</span></div><dl class="jurisprudenceSummaryList"><div><dt>Kern</dt><dd>${esc(summary.core)}</dd></div>${summary.ruling?`<div><dt>Oordeel</dt><dd>${esc(summary.ruling)}</dd></div>`:''}${summary.relevance?`<div><dt>Betekenis voor de regeling</dt><dd>${esc(summary.relevance)}</dd></div>`:''}</dl><p class="jurisprudenceArticles">Gekoppeld aan: ${references.map(reference=>`${esc(regulationName(data,reference.regulation))}, artikel ${esc(reference.article)}`).join('; ')}.</p><a class="jurisprudenceSource" href="${esc(item.official_url)}" target="_blank" rel="noopener noreferrer">Open officiële uitspraak op Rechtspraak.nl ↗</a></article>`};
  function empty(message){content.innerHTML=`<section class="articleNotesEmpty"><h2>Geen proefresultaten</h2><p>${esc(message)}</p></section>`}
  async function load(){
    try{
      const response=await fetch('data/jurisprudence.json',{cache:'no-store'});
      if(!response.ok)throw new Error('proefgegevens ontbreken');
      const data=await response.json();
      const all=Array.isArray(data.cases)?data.cases:[];
      if(regulation&&article){
        title.textContent=`Jurisprudentie bij artikel ${article}`;
        intro.textContent=`${regulationName(data,regulation)} · ${data.scope||'Gecontroleerde koppelingen.'}`;
        const rows=all.filter(item=>referencesOf(item).some(reference=>String(reference.regulation).toUpperCase()===regulation&&String(reference.article).toLowerCase()===article));
        if(!rows.length){empty('Voor dit artikel bevat de proefset nog geen gecontroleerde uitspraken.');return}
        content.innerHTML=`<section class="jurisprudenceSummary"><h2>${rows.length} ${rows.length===1?'uitspraak':'uitspraken'} in de proefset</h2><p>Alleen handmatig gecontroleerde koppelingen staan hier. De korte samenvatting is informatief; de officiële uitspraak is leidend.</p></section><section class="jurisprudenceList">${rows.map(item=>caseCard(data,item)).join('')}</section>`;
        return;
      }
      title.textContent='Jurisprudentie';
      intro.textContent=data.scope||'Gecontroleerde proefkoppelingen.';
      const regulations=Object.keys(data.regulations||{});
      const overview=regulations.map(regulationId=>{
        const articles=testArticlesForRegulation(all,regulationId);
        if(!articles.length)return '';
        const links=`<ul>${articles.map(({article,count})=>`<li><a href="jurisprudentie.html?regeling=${encodeURIComponent(regulationId)}&artikel=${encodeURIComponent(article)}">Artikel ${esc(article)}</a> · ${count} ${count===1?'uitspraak':'uitspraken'}</li>`).join('')}</ul>`;
        return `<section class="jurisprudenceSummary"><h3>${esc(regulationName(data,regulationId))}</h3>${links}</section>`;
      }).filter(Boolean).join('');
      const testList=overview?`<section class="jurisprudenceSummary"><h2>Gericht testen</h2><p>Per regeling staan hieronder maximaal ${MAX_ARTICLES_PER_REGULATION} artikelen met gecontroleerde jurisprudentie. De beperking geldt alleen voor deze testlijst; alle uitspraken blijven hieronder beschikbaar.</p>${overview}</section>`:'';
      content.innerHTML=`<section class="jurisprudenceSummary"><h2>Proefopstelling voor alle regelingen</h2><p>Deze afzonderlijke pagina bevat alleen handmatig gecontroleerde koppelingen met gepubliceerde Rechtspraak-uitspraken. Een teller van nul betekent uitsluitend dat nog geen gecontroleerde koppeling is opgenomen. De juridische bron blijft altijd de officiële uitspraak.</p></section>${testList}<section class="jurisprudenceList">${all.map(item=>caseCard(data,item)).join('')}</section>`;
    }catch(_){
      empty('De proefgegevens kunnen nu niet worden geladen. Probeer het later opnieuw.');
    }
  }
  load();
})();
