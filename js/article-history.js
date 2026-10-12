'use strict';
(() => {
const REGS={
  OW:{name:'Omgevingswet',bwb:'BWBR0037885'}, BAL:{name:'Besluit activiteiten leefomgeving (BAL)',bwb:'BWBR0041330'},
  BBL:{name:'Besluit bouwwerken leefomgeving (BBL)',bwb:'BWBR0041297'}, BKL:{name:'Besluit kwaliteit leefomgeving (BKL)',bwb:'BWBR0041313'},
  OB:{name:'Omgevingsbesluit (OB)',bwb:'BWBR0041278'}, OR:{name:'Omgevingsregeling (OR)',bwb:'BWBR0045528'}
};
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const date=value=>/^\d{4}-\d{2}-\d{2}$/.test(String(value||''))?String(value).split('-').reverse().join('-'):String(value||'onbekend');
const params=new URLSearchParams(location.search),regId=String(params.get('regeling')||'').toUpperCase(),article=String(params.get('artikel')||'').trim(),reg=REGS[regId];
const title=document.getElementById('historyTitle'),subtitle=document.getElementById('historySubtitle'),content=document.getElementById('historyContent');
function officialUrl(record){return record?.official_url||`https://wetten.overheid.nl/${reg.bwb}/informatie`}
function row(entry){const source=entry.source_url?`<a href="${esc(entry.source_url)}" target="_blank" rel="noopener noreferrer">${esc(entry.source||'Officiële bekendmaking')} ↗</a>`:esc(entry.source||'Officiële bron');return `<article class="historyItemCard"><h2>${esc(date(entry.effective_date))} — ${esc(entry.subject||'Officiële versie')}</h2>${entry.published_date?`<p>Bekendgemaakt: ${esc(date(entry.published_date))}</p>`:''}${entry.signed_date?`<p>Ondertekend: ${esc(date(entry.signed_date))}</p>`:''}<p class="historySource">${source}</p></article>`}
async function load(){
  if(!reg||!article){title.textContent='Artikelhistorie niet beschikbaar';subtitle.textContent='De regeling of het artikel ontbreekt in de link.';content.innerHTML='<div class="historyEmpty">Open de historie vanuit een artikel in Omgevingswet Zoeker.</div>';return}
  title.textContent=`Historie van artikel ${article}`;
  subtitle.textContent=`${reg.name} — alleen officiële wijzigingsmomenten.`;
  try{
    const response=await fetch('data/article_history.json',{cache:'no-store'});
    if(!response.ok)throw new Error('historiebestand ontbreekt');
    const data=await response.json(),record=data.articles?.[`${regId}:${article.toLowerCase()}`];
    if(!record)throw new Error('geen gegevens voor dit artikel');
    const changes=Number(record.modification_count)||0,entries=Array.isArray(record.entries)?record.entries:[];
    content.innerHTML=`<div class="historySummary"><strong>${changes} officiële ${changes===1?'wijziging':'wijzigingen'}</strong> na de oorspronkelijke regeling. Dagelijkse broncontroles zijn hierin niet opgenomen.</div><div class="historyList">${entries.map(row).join('')||'<div class="historyEmpty">Voor dit artikel zijn geen afzonderlijke wijzigingsmomenten aangetroffen.</div>'}</div><p class="historySource">De gegevens zijn overgenomen uit het officiële wijzigingenoverzicht op <a href="${esc(officialUrl(record))}" target="_blank" rel="noopener noreferrer">wetten.nl ↗</a>.</p>`;
  }catch(_){
    content.innerHTML=`<div class="historyEmpty">De compacte historie is nog niet beschikbaar. <a href="${esc(officialUrl())}" target="_blank" rel="noopener noreferrer">Open het officiële wijzigingenoverzicht op wetten.nl ↗</a>.</div>`;
  }
}
load();
})();
