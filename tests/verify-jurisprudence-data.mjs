import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const context={window:{},Object};
vm.runInNewContext(fs.readFileSync('js/app-config.js','utf8'),context,{filename:'js/app-config.js'});
const regulations=new Set(context.window.OWZ_CONFIG.regulations.map(item=>item.id));
const data=JSON.parse(fs.readFileSync('data/jurisprudence.json','utf8'));

assert.equal(data.schema,2,'Gebruik het regeling-onafhankelijke jurisprudentieschema.');
assert.ok(Array.isArray(data.coverage),'Dekking per regeling ontbreekt.');
assert.deepEqual(new Set(data.coverage.map(item=>item.id)),regulations,'Iedere opgenomen regeling moet dekking krijgen.');
assert.ok(Array.isArray(data.cases),'De gecontroleerde uitspraken ontbreken.');
assert.ok(!Object.hasOwn(data,'by_article'),'De artikelindex moet in de browser uit references worden opgebouwd.');
for(const item of data.cases){
  assert.match(item.ecli,/^ECLI:NL:/,'Elke uitspraak moet een ECLI hebben.');
  assert.ok(!Object.hasOwn(item,'articles'),'Artikelkoppelingen mogen niet dubbel naast references worden opgeslagen.');
  assert.ok(Array.isArray(item.references)&&item.references.length,'Elke uitspraak moet minstens één gecontroleerde koppeling hebben.');
  for(const reference of item.references){
    assert.ok(regulations.has(reference.regulation),`Onbekende regeling: ${reference.regulation}`);
    assert.match(String(reference.article),/^\d+(?:\.\d+)+[a-z]?$/i,'Ongeldig artikelnummer in jurisprudentiekoppeling.');
    assert.equal(reference.review_status,'gecontroleerd','Alleen gecontroleerde koppelingen mogen worden gepubliceerd.');
  }
}
console.log('Jurisprudentiegegevens zijn regeling-onafhankelijk en gecontroleerd.');
