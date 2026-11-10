import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync('js/article-notes.js','utf8');
const elements=new Map(['articleNotesTitle','articleNotesIntro','articleNotesContent'].map(id=>[id,{textContent:'',innerHTML:''}]));
const data={regulations:{BAL:{'3.50':{label:'Artikel 3.50',paragraph:'§ 3.4',source:'Stb.2018-293',notes:[{source:'Stb.2018-293',url:'',shared_for:[],text:`Artikel 3.50 (aanwijzing)
1. Een eerste lid loopt door
op de volgende bronregel.
2. Dit lid bevat:
a. een letteronderdeel;
b. een tweede letteronderdeel met uitzondering van:
1°. een subonderdeel.
Artikel 3.50 (aanwijzing)
Eerste lid
De toelichting loopt logisch door
in dezelfde alinea.`}]}}}};
const context={
  URLSearchParams,
  location:{search:'?regeling=BAL&artikel=3.50'},
  document:{getElementById:id=>elements.get(id)},
  fetch:async()=>({ok:true,json:async()=>data}),
};
vm.runInNewContext(source,context,{filename:'js/article-notes.js'});
await new Promise(resolve=>setImmediate(resolve));

const html=elements.get('articleNotesContent').innerHTML;
assert.match(html,/Wettekst waarop de toelichting ziet/,'De wettekst moet afzonderlijk herkenbaar zijn.');
assert.match(html,/Artikelsgewijze toelichting/,'De eigenlijke toelichting moet afzonderlijk herkenbaar zijn.');
assert.match(html,/articleNotesItem level1/,'Letteronderdelen moeten worden ingesprongen.');
assert.match(html,/articleNotesItem level2/,'Subonderdelen moeten verder worden ingesprongen.');
assert.match(html,/Een eerste lid loopt door op de volgende bronregel\./,'Afgebroken bronregels moeten logisch doorlopen.');
assert.doesNotMatch(html,/<br>/,'De toelichting mag niet als platte tekst met regeleinden worden weergegeven.');

const appendixElements=new Map(['articleNotesTitle','articleNotesIntro','articleNotesContent'].map(id=>[id,{textContent:'',innerHTML:''}]));
const appendixData={regulations:{BAL:{appendices:{i:{label:'Bijlage I',source:'Stb.2018-293',notes:[{source:'Stb.2018-293',url:'',shared_for:[],applies_via_article:'Artikel 1.1',text:'Artikel 1.1\nDeze toelichting hoort bij de aanwijzende bepaling.'}]}}}}};
const appendixContext={
  URLSearchParams,
  location:{search:'?regeling=BAL&bijlage=i'},
  document:{getElementById:id=>appendixElements.get(id)},
  fetch:async()=>({ok:true,json:async()=>appendixData}),
};
vm.runInNewContext(source,appendixContext,{filename:'js/article-notes.js'});
await new Promise(resolve=>setImmediate(resolve));
assert.equal(appendixElements.get('articleNotesTitle').textContent,'Nota van toelichting bij Bijlage I','De bijlage moet een eigen NVT-titel krijgen.');
assert.match(appendixElements.get('articleNotesContent').innerHTML,/Toelichting bij de bijlage/,'De pagina moet bijlagetoelichting herkennen.');
assert.match(appendixElements.get('articleNotesContent').innerHTML,/aanwijzende Artikel 1.1/,'Toelichting via een aanwijzend artikel moet herkenbaar blijven.');
console.log('Artikelsgewijze toelichting wordt logisch gegroepeerd en ingesprongen weergegeven.');
