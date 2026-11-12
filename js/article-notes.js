'use strict';

(()=>{
  const params=new URLSearchParams(location.search);
  const article=String(params.get('artikel')||'').trim();
  const appendix=String(params.get('bijlage')||'').trim().toLowerCase();
  const regulation=String(params.get('regeling')||'').toUpperCase();
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const officialUrl=source=>{
    const match=String(source||'').match(/^Stb\.(\d{4})-(\d+)$/);
    return match?`https://zoek.officielebekendmakingen.nl/stb-${match[1]}-${match[2]}.html`:'';
  };
  const memberHeading=/^(?:eerste|tweede|derde|vierde|vijfde|zesde|zevende|achtste|negende|tiende) lid$/i;
  const articleHeading=/^Artikel\s+[0-9]+(?:\.[0-9]+)*[a-z]?\b/i;
  const appendixHeading=/^Bijlage(?:\s+[IVXLCDM]+[a-z]*)?\b/i;
  const legalHeading=line=>articleHeading.test(line)||appendixHeading.test(line);
  function cleanLines(value){return String(value||'').split(/\n+/).map(line=>line.replace(/\s+/g,' ').trim()).filter(Boolean)}
  function marker(line){
    let match=line.match(/^(\d+°\.)\s+(.+)$/);
    if(match)return {label:match[1],text:match[2],level:2};
    match=line.match(/^(\d+\.)\s+(.+)$/);
    if(match)return {label:match[1],text:match[2],level:0};
    match=line.match(/^([a-z]\.)\s+(.+)$/i);
    if(match)return {label:match[1],text:match[2],level:1};
    match=line.match(/^([•–])\s+(.+)$/);
    return match?{label:match[1],text:match[2],level:1}:null;
  }
  function structuredText(lines){
    const blocks=[];let current=null;
    const flush=()=>{if(current?.text)blocks.push(current);current=null};
    for(const line of lines){
      const item=marker(line);
      if(legalHeading(line)||memberHeading.test(line)){
        flush();blocks.push({kind:'heading',text:line});continue;
      }
      if(item){flush();current={kind:'item',...item};continue}
      if(!current){current={kind:'paragraph',text:line};continue}
      current.text+=` ${line}`;
      if(current.kind==='paragraph'&&/[.;:]$/.test(line))flush();
    }
    flush();
    return blocks.map(block=>{
      if(block.kind==='heading')return `<h4>${esc(block.text)}</h4>`;
      if(block.kind==='item')return `<div class="articleNotesItem level${block.level}"><span class="articleNotesMarker">${esc(block.label)}</span><span>${esc(block.text)}</span></div>`;
      return `<p>${esc(block.text)}</p>`;
    }).join('');
  }
  function splitText(value){
    const lines=cleanLines(value), first=lines.findIndex(line=>legalHeading(line));
    const second=first<0?-1:lines.findIndex((line,index)=>index>first&&legalHeading(line));
    if(second<0)return {excerpt:[],explanation:lines};
    return {excerpt:lines.slice(first,second),explanation:lines.slice(second+1)};
  }
  function sourceCard(note){
    const sharedFor=Array.isArray(note.shared_for)?note.shared_for:[];
    const coveredArticles=[article,...sharedFor].filter(Boolean);
    const paragraph=cleanLines(note.text)[0]?.match(/^§\s*([0-9]+(?:\.[0-9]+)+[a-z]?)/i);
    const shared=sharedFor.length
      ?`<p class="articleNotesMeta">${paragraph?`Toelichting bij § ${esc(paragraph[1])}`:'Deze toelichting'}; geldt voor de artikelen ${coveredArticles.map(esc).join(', ')}.</p>`:'';
    const via=note.applies_via_article?`<p class="articleNotesMeta">Toelichting bij het aanwijzende ${esc(note.applies_via_article)}.</p>`:'';
    const parts=splitText(note.text);
    const excerpt=parts.excerpt.length?`<section class="articleNotesExcerpt"><h3>Wettekst waarop de toelichting ziet</h3>${structuredText(parts.excerpt)}</section>`:'';
    const explanation=structuredText(parts.explanation);
    return `<section class="articleNotesSource"><div class="articleNotesSourceHead"><h2>${esc(note.source)}</h2><a href="${esc(note.url||officialUrl(note.source))}" target="_blank" rel="noopener">Open de officiële bron</a></div>${shared}${via}${excerpt}<section class="articleNotesText"><h3>${excerpt?'Artikelsgewijze toelichting':'Officiële artikelsgewijze toelichting'}</h3>${explanation}</section></section>`;
  }
  function render(record){
    const isAppendix=record.kind==='appendix';
    $('articleNotesTitle').textContent=`Nota van toelichting bij ${record.label}`;
    $('articleNotesIntro').textContent=`${record.paragraph||regulation} · actuele ontstaansbron: ${record.source||'onbekend'}`;
    if(!record.notes.length){
      $('articleNotesContent').innerHTML=`<section class="articleNotesEmpty"><h2>Geen afzonderlijke toelichting opgenomen</h2><p>In de geraadpleegde officiële nota’s is geen afzonderlijke ${isAppendix?'bijlage':'artikelsgewijze'} toelichting gevonden voor ${esc(record.label)}.</p><p>Algemene of paragraafgewijze toelichting wordt niet als toelichting bij dit afzonderlijke onderdeel gepresenteerd.</p></section>`;
      return;
    }
    $('articleNotesContent').innerHTML=`<section class="articleNotesSummary"><h2>${isAppendix?'Toelichting bij de bijlage':'Artikelsgewijze toelichting'}</h2><p>Hieronder staat uitsluitend officiële toelichting die rechtstreeks aan dit onderdeel, of aan het aanwijzende artikel, is gekoppeld.</p></section>${record.notes.map(sourceCard).join('')}`;
  }
  async function load(){
    if(!regulation||(!article&&!appendix)){$('articleNotesIntro').textContent='Geen artikel of bijlage gekozen.';return;}
    try{
      const response=await fetch('data/article_notes.json',{cache:'no-store'});
      if(!response.ok)throw new Error('gegevens ontbreken');
      const data=await response.json();
      const stored=data.regulations?.[regulation];
      const record=appendix?stored?.appendices?.[appendix]:stored?.[article];
      if(!record)throw new Error('onderdeel ontbreekt');
      render({...record,kind:appendix?'appendix':'article'});
    }catch(_){
      $('articleNotesIntro').textContent='De toelichtingsgegevens konden niet worden geladen.';
      $('articleNotesContent').innerHTML='<section class="articleNotesEmpty"><h2>Nu niet beschikbaar</h2><p>Probeer het later opnieuw.</p></section>';
    }
  }
  load();
})();
