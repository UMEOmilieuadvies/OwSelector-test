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

const index=fs.readFileSync(path.join(siteDir,'index.html'),'utf8');
assert.ok(!index.includes('__OWZ_VERSION__'),'De samengestelde startpagina bevat een onvervangen versieplaatsaanduiding.');
assert.ok(index.includes(`Omgevingswet Zoeker ${version}`),'De samengestelde startpagina toont niet het juiste versienummer.');
assert.ok(index.includes(`release-${version}`),'De samengestelde startpagina gebruikt geen cacheversie die bij de release past.');

const files=[];
function collect(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const file=path.join(dir,entry.name);if(entry.isDirectory())collect(file);else files.push(file)}}
collect(siteDir);
const content=files.filter(file=>/\.(?:html|js|json|css)$/i.test(file)).map(file=>fs.readFileSync(file,'utf8')).join('\n');
assert.ok(!content.includes('__OWZ_VERSION__'),'De publicatiemap bevat nog een onvervangen versieplaatsaanduiding.');

if(environment==='test'){
  assert.equal(config.supabase.url,'https://lemcbncvqcsffatsxpdq.supabase.co','De testsite gebruikt niet de testdatabase.');
  assert.equal(config.storage.favoritesKey,'owz_test_favorites','De testsite gebruikt niet de aparte testfavorietenopslag.');
  assert.ok(index.includes('Testomgeving — wijzigingen zijn nog niet definitief.'),'De testsite mist de verplichte testaanduiding.');
  assert.ok(!content.includes('pqpsajcjydvagrfxfeye'),'De productiedatabase is aangetroffen in de testpublicatie.');
}else{
  assert.equal(config.supabase.url,'https://pqpsajcjydvagrfxfeye.supabase.co','De productiesite gebruikt niet de productiedatabase.');
  assert.equal(config.storage.favoritesKey,'owz_favorites','De productiesite gebruikt niet de aparte productiefavorietenopslag.');
  assert.ok(!index.includes('Testomgeving — wijzigingen zijn nog niet definitief.'),'De productiepagina bevat een testaanduiding.');
  assert.ok(!content.includes('lemcbncvqcsffatsxpdq'),'De testdatabase is aangetroffen in de productiepublicatie.');
}

console.log(`Publicatiebundel voor ${environment} met versie ${version} is gecontroleerd.`);
