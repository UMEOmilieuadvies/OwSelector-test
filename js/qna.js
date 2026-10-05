'use strict';
(() => {
const SUPABASE_URL='https://lemcbncvqcsffatsxpdq.supabase.co';
const SUPABASE_KEY='sb_publishable_xvnpAGVE1Kf3DhO0PDck7g_ck1nix2O';
const REGS=[
 {id:'OW',name:'Omgevingswet'}, {id:'BAL',name:'Besluit activiteiten leefomgeving (BAL)'},
 {id:'BBL',name:'Besluit bouwwerken leefomgeving (BBL)'}, {id:'BKL',name:'Besluit kwaliteit leefomgeving (BKL)'},
 {id:'OB',name:'Omgevingsbesluit (OB)'}, {id:'OR',name:'Omgevingsregeling (OR)'}
];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $=id=>document.getElementById(id);
function nlDate(value){const m=String(value||'').match(/^(\d{4})-(\d{2})-(\d{2})$/);return m?`${m[3]}-${m[2]}-${m[1]}`:'onbekend'}
function versionList(data){const versions=data?.regulations||{};return `<section class="qnaVersions"><strong>Laatst geïmporteerde versies</strong><ul>${REGS.map(reg=>`<li>${esc(reg.name)} — versie: ${esc(nlDate(versions[reg.id]?.imported_on))}</li>`).join('')}</ul></section>`}
function visual(category){const key=String(category||'').toLocaleLowerCase('nl-NL');if(key==='zoeken')return '<div class="qnaVisual qnaVisualSearch" aria-hidden="true"><span></span><i></i><b></b></div>';if(key==='navigatie')return '<div class="qnaVisual qnaVisualColumns" aria-hidden="true"><span>1</span><span>2</span><span>3</span></div>';if(key==='tekst en verwijzingen')return '<div class="qnaVisual qnaVisualLinks" aria-hidden="true"><span></span><i></i><b></b></div>';return '<div class="qnaVisual qnaVisualUpdate" aria-hidden="true"><span>↻</span><i></i></div>'}
function answer(text,versions){return esc(text).replace('[[VERSIES]]',versionList(versions)).replace(/\n/g,'<br>')}
function render(rows,versions){const box=$('qnaContent');if(!rows.length){box.innerHTML='<p class="qnaLoading">Er zijn nog geen zichtbare vragen en antwoorden.</p>';return}const groups=new Map();rows.forEach(row=>{const k=String(row.rubriek||'Overig');if(!groups.has(k))groups.set(k,[]);groups.get(k).push(row)});box.innerHTML=[...groups].map(([category,items])=>`<section class="qnaSection"><div class="qnaSectionHead">${visual(category)}<h2>${esc(category)}</h2></div><div class="qnaItems">${items.map((row,index)=>`<details class="qnaItem"${index===0?' open':''}><summary>${esc(row.vraag)}</summary><div class="qnaAnswer">${answer(row.antwoord,versions)}</div></details>`).join('')}</div></section>`).join('')}
async function load(){const box=$('qnaContent');try{const [qna,versions]=await Promise.all([fetch(`${SUPABASE_URL}/rest/v1/qna?select=rubriek,vraag,antwoord,volgorde&zichtbaar=eq.true&order=rubriek.asc,volgorde.asc`,{headers:{apikey:SUPABASE_KEY,Authorization:`Bearer ${SUPABASE_KEY}`}}),fetch('data/regulation_versions.json',{cache:'no-store'})]);if(!qna.ok)throw new Error('Q&A kan niet worden gelezen');render(await qna.json(),versions.ok?await versions.json():{})}catch(_){box.innerHTML='<p class="qnaLoading">De vragen en antwoorden zijn nu niet beschikbaar. Probeer het later opnieuw.</p>'}}
load();
})();
