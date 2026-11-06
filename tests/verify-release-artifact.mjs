import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const args=process.argv.slice(2);
const environment=args[args.indexOf('--environment')+1];
const siteDir=args[args.indexOf('--site')+1]||'_site';
assert.ok(['test','production'].includes(environment),'Gebruik --environment test of production.');

const version=fs.readFileSync('VERSION','utf8').trim();
const release=JSON.parse(fs.readFileSync('release.json','utf8'));
assert.equal(release.version,version,'VERSION en release.json moeten hetzelfde versienummer bevatten.');

const configSource=fs.readFileSync(path.join(siteDir,'js','app-config.js'),'utf8');
const context={window:{},Object};
vm.runInNewContext(configSource,context,{filename:'_site/js/app-config.js'});
const config=context.window.OWZ_CONFIG;
assert.equal(config.version,version,'De samengestelde site gebruikt niet het centrale versienummer.');
assert.equal(config.environment,environment,'De samengestelde site heeft de verkeerde omgevingsmarkering.');

const staticPages=['index.html','help.html','qna.html','nvt.html','beheer.html','historie.html','article-notes.html','jurisprudentie.html'];
for(const page of staticPages){
  const rendered=fs.readFileSync(path.join(siteDir,page),'utf8');
  assert.ok(!rendered.includes('__OWZ_VERSION__'),`${page} bevat een onvervangen versieplaatsaanduiding.`);
  assert.ok(rendered.includes(version),`${page} toont niet het centrale versienummer.`);
  assert.ok(rendered.includes(`release-${version}`),`${page} gebruikt geen cacheversie die bij de release past.`);
}
const index=fs.readFileSync(path.join(siteDir,'index.html'),'utf8');
assert.ok(fs.existsSync(path.join(siteDir,'article-notes.html')),'De pagina met artikelsgewijze toelichting ontbreekt in de publicatiebundel.');
assert.ok(fs.existsSync(path.join(siteDir,'js','article-notes.js')),'De bediening van artikelsgewijze toelichting ontbreekt in de publicatiebundel.');
assert.ok(fs.existsSync(path.join(siteDir,'jurisprudentie.html')),'De afzonderlijke pagina met jurisprudentie ontbreekt in de publicatiebundel.');
assert.ok(fs.existsSync(path.join(siteDir,'js','jurisprudence.js')),'De bediening van de jurisprudentiepagina ontbreekt in de publicatiebundel.');
assert.ok(fs.existsSync(path.join(siteDir,'data','jurisprudence.json')),'De jurisprudentieproefgegevens ontbreken in de publicatiebundel.');
assert.ok(fs.existsSync(path.join(siteDir,'data','article_notes_bal_chapter4.json')),'De toelichtingsgegevens ontbreken in de publicatiebundel.');

const files=[];
function collect(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const file=path.join(dir,entry.name);if(entry.isDirectory())collect(file);else files.push(file)}}
collect(siteDir);
const content=files.filter(file=>/\.(?:html|js|json|css)$/i.test(file)).map(file=>fs.readFileSync(file,'utf8')).join('\n');
assert.ok(!content.includes('__OWZ_'),'De publicatiemap bevat nog een onvervangen omgevingsplaatsaanduiding.');

if(environment==='test'){
  assert.equal(config.supabase.url,'https://lemcbncvqcsffatsxpdq.supabase.co','De testsite gebruikt niet de testdatabase.');
  assert.equal(config.storage.favoritesKey,'owz_test_favorites','De testsite gebruikt niet de aparte testfavorietenopslag.');
  assert.ok(index.includes('Testomgeving — wijzigingen zijn nog niet definitief.'),'De testsite mist de verplichte testaanduiding.');
  assert.ok(content.includes('testomgeving'),'De testsite mist de omgevingsaanduiding in vaste pagina’s.');
  assert.ok(content.includes('in de testdatabase'),'De testsite mist de testopslagtekst voor favorieten.');
  assert.ok(!content.includes('pqpsajcjydvagrfxfeye'),'De productiedatabase is aangetroffen in de testpublicatie.');
}else{
  assert.equal(config.supabase.url,'https://pqpsajcjydvagrfxfeye.supabase.co','De productiesite gebruikt niet de productiedatabase.');
  assert.equal(config.storage.favoritesKey,'owz_favorites','De productiesite gebruikt niet de aparte productiefavorietenopslag.');
  assert.ok(!index.includes('Testomgeving — wijzigingen zijn nog niet definitief.'),'De productiepagina bevat een testaanduiding.');
  assert.ok(!content.includes('lemcbncvqcsffatsxpdq'),'De testdatabase is aangetroffen in de productiepublicatie.');
}

console.log(`Publicatiebundel voor ${environment} met versie ${version} is gecontroleerd.`);
