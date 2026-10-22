import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const configSource=fs.readFileSync('js/app-config.js','utf8');
const context={window:{},Object};
vm.runInNewContext(configSource,context,{filename:'js/app-config.js'});
const config=context.window.OWZ_CONFIG;
assert.equal(config.environment,'test','De testomgeving moet expliciet zijn ingesteld.');
assert.equal(config.version,'1.1g-test','Configuratie en testversie moeten gelijk lopen.');
assert.equal(config.supabase.url,'https://lemcbncvqcsffatsxpdq.supabase.co','Alleen de test-Supabase is toegestaan.');
assert.equal(config.storage.favoritesKey,'owz_test_favorites','Testfavorieten moeten een eigen opslag gebruiken.');
assert.equal(config.regulations.length,6,'Exact zes regelingen moeten beschikbaar zijn.');
assert.equal(new Set(config.regulations.map(regulation=>regulation.id)).size,6,'Regelingcodes moeten uniek zijn.');
const source=fs.readFileSync('js/app.js','utf8');
assert.ok(!source.includes('pqpsajcjydvagrfxfeye'),'Productie-Supabase mag niet in de testcode voorkomen.');
assert.ok(!source.includes("const VERSION='"),'Versie hoort alleen in app-config.js te staan.');
for(const name of ['searchVariants','buildIndex','chooseReg','setupEvents','load']){
  assert.match(source,new RegExp(`function ${name}\\(`),`Ontbrekende startfunctie: ${name}`);
}
console.log('Clientconfiguratie en kritieke startfuncties zijn gecontroleerd.');
assert.match(fs.readFileSync('index.html','utf8'),/js\/app-config\.js[\s\S]*js\/app\.js/,'Configuratie moet vóór de applicatie laden.');

assert.ok(source.includes('FAVORITES_KEY'),'Favorieten moeten de omgevingsspecifieke opslag gebruiken.');
assert.ok(!source.includes("localStorage.getItem('owz_favorites')"),'De gedeelde favorietensleutel mag niet meer worden gelezen.');
