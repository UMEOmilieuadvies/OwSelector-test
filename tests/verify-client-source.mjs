import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const configSource=fs.readFileSync('js/app-config.js','utf8');
const context={window:{},Object};
vm.runInNewContext(configSource,context,{filename:'js/app-config.js'});
const config=context.window.OWZ_CONFIG;
assert.equal(config.environment,'test','De testomgeving moet expliciet zijn ingesteld.');
const declaredVersion=fs.readFileSync('VERSION','utf8').trim();
assert.equal(config.version,declaredVersion,'Configuratie en testversie moeten gelijk lopen.');
assert.equal(JSON.parse(fs.readFileSync('release.json','utf8')).version,declaredVersion,'release.json en testversie moeten gelijk lopen.');
assert.match(config.version,/^\d+\.\d+(?:[a-z])?-test$/,'Het testversienummer moet geldig zijn.');
assert.equal(config.supabase.url,'https://lemcbncvqcsffatsxpdq.supabase.co','Alleen de test-Supabase is toegestaan.');
assert.equal(config.storage.favoritesKey,'owz_test_favorites','Testfavorieten moeten een eigen opslag gebruiken.');
assert.match(fs.readFileSync('js/app.js','utf8'),/function favoriteCodeIsStored\(\)/,'De toepassing moet aantoonbaar maken of de herstelcode in deze browser is bewaard.');
assert.match(fs.readFileSync('js/app.js','utf8'),/herstelcode is niet in deze browser bewaard/i,'Een niet-bewaarde herstelcode moet duidelijk worden gemeld.');
assert.match(fs.readFileSync('js/app.js','utf8'),/Na herladen moet u hem opnieuw invoeren/,'Een tijdelijk gebruikte herstelcode moet duidelijk worden gemeld.');
assert.equal(config.regulations.length,7,'Exact zeven regelingen moeten beschikbaar zijn.');
assert.equal(new Set(config.regulations.map(regulation=>regulation.id)).size,7,'Regelingcodes moeten uniek zijn.');
assert.ok(config.regulations.some(regulation=>regulation.id==='IWO'&&regulation.bwb==='BWBR0043660'),'De Invoeringswet Omgevingswet ontbreekt.');
const notesCatalog=JSON.parse(fs.readFileSync('nvt_catalog.json','utf8'));
assert.ok(notesCatalog.regulations.some(regulation=>regulation.id==='IWO'&&regulation.bwb==='BWBR0043660'),'De toelichtingscatalogus mist de Invoeringswet Omgevingswet.');
const source=fs.readFileSync('js/app.js','utf8');
assert.ok(!source.includes('pqpsajcjydvagrfxfeye'),'Productie-Supabase mag niet in de testcode voorkomen.');
assert.ok(!source.includes("const VERSION='"),'Versie hoort alleen in app-config.js te staan.');
for(const file of fs.readdirSync('js').filter(name=>name.endsWith('.js')&&name!=='app-config.js').map(name=>`js/${name}`)){
  const clientSource=fs.readFileSync(file,'utf8');
  assert.ok(!/https:\/\/[^\s"']+\.supabase\.co/.test(clientSource),`${file} mag geen eigen Supabase-adres bevatten.`);
  assert.ok(!clientSource.includes('sb_publishable_'),`${file} mag geen eigen openbare Supabase-sleutel bevatten.`);
}
for(const file of ['js/app.js','js/qna.js','js/beheer.js']){
  assert.match(fs.readFileSync(file,'utf8'),/OWZ_CONFIG|CONFIG/,`${file} moet de centrale omgevingsconfiguratie gebruiken.`);
}
for(const name of ['searchVariants','buildIndex','chooseReg','setupEvents','setupReleaseWelcome','showReleaseWelcomeIfNeeded','load']){
  assert.match(source,new RegExp(`function ${name}\\(`),`Ontbrekende startfunctie: ${name}`);
}
assert.match(source,/if\(!notes\.length\)return;/,'Zonder releasenotities mag het wijzigingsvenster niet verschijnen.');
assert.match(source,/data\?\.user_notes/,'Het wijzigingsvenster mag uitsluitend gebruikerswijzigingen tonen.');
assert.ok(!source.includes('Voor deze versie is geen korte wijzigingssamenvatting beschikbaar.'),'Een lege wijzigingssamenvatting mag geen venster meer opleveren.');
console.log('Clientconfiguratie en kritieke startfuncties zijn gecontroleerd.');
assert.match(fs.readFileSync('index.html','utf8'),/js\/app-config\.js[\s\S]*js\/app\.js/,'Configuratie moet vóór de applicatie laden.');
for(const page of ['qna.html','beheer.html']){
  const pageSource=fs.readFileSync(page,'utf8');
  assert.match(pageSource,/js\/app-config\.js[\s\S]*js\/(qna|beheer)\.js/,`${page} moet de configuratie vóór de eigen code laden.`);
}

assert.ok(source.includes('FAVORITES_KEY'),'Favorieten moeten de omgevingsspecifieke opslag gebruiken.');
assert.ok(!source.includes("localStorage.getItem('owz_favorites')"),'De gedeelde favorietensleutel mag niet meer worden gelezen.');
assert.match(source,/function groupBackReferenceRows\(rows\)/,'Terugverwijzingen moeten per bronartikel gegroepeerd kunnen worden.');
assert.match(source,/backReferenceFindings/,'Elke afzonderlijke vindplaats moet als eigen klikbare keuze worden weergegeven.');
assert.match(source,/externalReferenceRows\(context\)\.find\(item=>item\.index===Number\(index\)\)/,'De contextverwijzing moet de oorspronkelijke bronindex gebruiken.');
console.log('Terugverwijzingen zijn gegroepeerd en vindplaatsen openen gericht.');
assert.match(source,/function renderArticleFavoriteAction\(ar\)/,'Artikelen in kolom 2 moeten een favorietenactie tonen.');
assert.match(source,/data-article-favorite/,'De favorietenknop in kolom 2 moet een artikel identificeren.');
console.log('Artikelen in kolom 2 kunnen als favoriet worden bewaard.');
assert.match(source,/function renderArticleNotesAction\(ar\)/,'BAL-artikelen moeten een toelichtingsactie kunnen tonen.');
assert.ok(fs.existsSync('article-notes.html'),'De pagina met de artikelsgewijze toelichting ontbreekt.');
assert.ok(fs.existsSync('js/article-notes.js'),'De bediening van de artikelsgewijze toelichting ontbreekt.');
assert.ok(fs.existsSync('data/article_notes_bal_chapter4.json'),'De gecontroleerde BAL-toelichtingsgegevens ontbreken.');
assert.ok(fs.existsSync('tools/build_article_notes_all.py'),'De bouwer voor bijlage-toelichtingen ontbreekt.');
assert.ok(fs.existsSync('tests/verify_appendix_notes.py'),'De broncontrole voor bijlagetoelichtingen ontbreekt.');
assert.match(source,/function renderAppendixNotesAction\(a\)/,'Bijlagen moeten een toelichtingsactie kunnen tonen.');
assert.match(source,/appendix_notes_index\.json/,'De bijlageactie moet alleen verschijnen bij beschikbare toelichting.');
console.log('De testfunctie voor artikelsgewijze toelichting is aanwezig.');
assert.ok(fs.existsSync('tools/build_integrated_nvt.py'),'De bouwer voor de geïntegreerde NVT ontbreekt.');
assert.ok(fs.existsSync('tests/verify_integrated_nvt.py'),'De structuurcontrole voor de geïntegreerde NVT ontbreekt.');
assert.match(fs.readFileSync('nvt.html','utf8'),/id="nvtSearch"/,'De geïntegreerde NVT moet een eigen zoekveld hebben.');
assert.match(fs.readFileSync('js/nvt.js','utf8'),/integrated_index\.json/,'De geïntegreerde NVT moet haar eigen index laden.');
console.log('De geïntegreerde, doorzoekbare NVT is aanwezig.');
assert.match(source,/function loadAboutVisits\(\)/,'De Over-sectie moet bezoekcijfers kunnen laden.');
assert.match(source,/site_visit_monthly/,'De Over-sectie moet de maandelijkse bezoekcijfers gebruiken.');
assert.match(fs.readFileSync('index.html','utf8'),/id="aboutVisits"/,'De Over-sectie mist de plaats voor bezoekcijfers.');
assert.ok(!source.includes('/^1\\.1g-test$/'),'De startcontrole mag niet op één vaste testversie zijn vastgezet.');
const staticPages=['index.html','help.html','qna.html','nvt.html','beheer.html','historie.html','article-notes.html','jurisprudentie.html'];
for(const page of staticPages){
  const pageSource=fs.readFileSync(page,'utf8');
  assert.ok(pageSource.includes('__OWZ_VERSION__'),`${page} moet de centrale versieplaatsaanduiding gebruiken.`);
}
const indexSource=fs.readFileSync('index.html','utf8');
assert.ok(indexSource.includes('Testomgeving — wijzigingen zijn nog niet definitief.'),'De testpagina moet een zichtbare testaanduiding hebben.');
console.log('Teststart en releasepagina gebruiken geen vast testversienummer.');
assert.match(source,/function renderArticleJurisprudenceAction\(ar\)/,'Artikelen met proefresultaten moeten een jurisprudentieactie tonen.');
assert.ok(fs.existsSync('jurisprudentie.html'),'De afzonderlijke pagina voor jurisprudentie ontbreekt.');
assert.ok(fs.existsSync('js/jurisprudence.js'),'De bediening van de jurisprudentiepagina ontbreekt.');
assert.ok(fs.existsSync('data/jurisprudence.json'),'De gecontroleerde proefgegevens voor jurisprudentie ontbreken.');
console.log('Jurisprudentie opent uitsluitend in een afzonderlijk tabblad.');
assert.match(source,/'Testfase':'testing'/,'De status Testfase moet ongewijzigd uit Supabase worden weergegeven.');
console.log('De opmerkingenstatus Testfase wordt rechtstreeks weergegeven.');
