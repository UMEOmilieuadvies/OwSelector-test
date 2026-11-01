'use strict';

(()=>{
  const params=new URLSearchParams(location.search);
  const article=String(params.get('artikel')||'').trim();
  const regulation=String(params.get('regeling')||'').toUpperCase();
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const officialUrl=source=>{
    const match=String(source||'').match(/^Stb\.(\d{4})-(\d+)$/);
    return match?`https://zoek.officielebekendmakingen.nl/stb-${match[1]}-${match[2]}.html`:'';
  };
  function sourceCard(note){
    const shared=Array.isArray(note.shared_for)&&note.shared_for.length>1
      ?`<p class="articleNotesMeta">Gezamenlijke toelichting bij artikelen ${note.shared_for.map(esc).join(', ')}.</p>`:'';
    return `<section class="articleNotesSource"><h2>${esc(note.source)}</h2>${shared}<a href="${esc(note.url||officialUrl(note.source))}" target="_blank" rel="noopener">Open de officiële bron</a><div class="articleNotesText">${esc(note.text).replace(/\n/g,'<br>')}</div></section>`;
  }
  function render(record){
    $('articleNotesTitle').textContent=`Nota van toelichting bij ${record.label}`;
    $('articleNotesIntro').textContent=`${record.paragraph||'BAL'} · actuele ontstaansbron: ${record.source||'onbekend'}`;
    if(!record.notes.length){
      $('articleNotesContent').innerHTML=`<section class="articleNotesEmpty"><h2>Geen afzonderlijke artikelsgewijze toelichting opgenomen</h2><p>In de geraadpleegde officiële nota’s is geen afzonderlijke of gezamenlijke artikelsgewijze kop gevonden waarin ${esc(record.label)} voorkomt. Daarom is geen aanvullende tekst aan dit artikel gekoppeld.</p><p>Algemene of paragraafgewijze toelichting wordt niet als toelichting bij dit afzonderlijke artikel gepresenteerd.</p></section>`;
      return;
    }
    $('articleNotesContent').innerHTML=`<section class="articleNotesSummary"><h2>Artikelsgewijze toelichting</h2><p>Hieronder staat uitsluitend officiële toelichting die rechtstreeks aan dit artikel, of aan een gezamenlijke artikelkop waarin dit artikel voorkomt, is gekoppeld.</p></section>${record.notes.map(sourceCard).join('')}`;
  }
  async function load(){
    if(regulation!=='BAL'||!/^4\.\d+[a-z]*$/i.test(article)){
      $('articleNotesIntro').textContent='Deze testfunctie is momenteel gecontroleerd voor artikelen uit BAL hoofdstuk 4.';
      $('articleNotesContent').innerHTML='<section class="articleNotesEmpty"><h2>Niet beschikbaar in deze test</h2><p>Voor dit artikel is nog geen gecontroleerde artikelsgewijze toelichtingskoppeling opgebouwd.</p></section>';
      return;
    }
    try{
      const response=await fetch('data/article_notes_bal_chapter4.json',{cache:'no-store'});
      if(!response.ok)throw new Error('gegevens ontbreken');
      const data=await response.json();
      const record=data.articles?.[article];
      if(!record)throw new Error('artikel ontbreekt');
      render(record);
    }catch(_){
      $('articleNotesIntro').textContent='De toelichtingsgegevens konden niet worden geladen.';
      $('articleNotesContent').innerHTML='<section class="articleNotesEmpty"><h2>Nu niet beschikbaar</h2><p>Probeer het later opnieuw.</p></section>';
    }
  }
  load();
})();
