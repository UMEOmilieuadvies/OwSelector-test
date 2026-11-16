import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

console.log('Gebruikersstroom 1/5: laad gedeelde gedragsregels.');
const context={};
vm.runInNewContext(fs.readFileSync('js/app-behavior.js','utf8'),context,{filename:'js/app-behavior.js'});
const behavior=context.OWZ_BEHAVIOR;
assert.ok(behavior,'De gedeelde gedragslaag ontbreekt.');
const navigationContext={};
vm.runInNewContext(fs.readFileSync('js/app-navigation.js','utf8'),navigationContext,{filename:'js/app-navigation.js'});
const loadingContext={fetch:async path=>({ok:true,status:200,json:async()=>({path})})};
vm.runInNewContext(fs.readFileSync('js/app-data-loading.js','utf8'),loadingContext,{filename:'js/app-data-loading.js'});
const viewerContext={};
vm.runInNewContext(fs.readFileSync('js/app-viewer.js','utf8'),viewerContext,{filename:'js/app-viewer.js'});
assert.ok(navigationContext.OWZ_NAVIGATION&&loadingContext.OWZ_DATA_LOADING&&viewerContext.OWZ_VIEWER,'Navigatie-, laad- of viewermodule ontbreekt.');
assert.equal(navigationContext.OWZ_NAVIGATION.roots([{id:'a',type:'chapter'},{id:'b',type:'article',parent:'a'}],node=>node.parent||'',node=>node.type).length,1,'Navigatiemodule vindt hoofdstukwortels niet.');
assert.equal((await loadingContext.OWZ_DATA_LOADING.json('data/test.json')).path,'data/test.json','Laadmodule haalt JSON niet op.');
assert.equal((await loadingContext.OWZ_DATA_LOADING.regulations([{id:'BAL'}],async()=>{}))[0].ok,true,'Laadmodule geeft geen geslaagd resultaat terug.');
assert.match(viewerContext.OWZ_VIEWER.referenceNotice('Test',value=>value),/referenceArticleContext/,'Viewermodule maakt geen verwijzingsmelding.');

console.log('Gebruikersstroom 2/5: favoriet blijft uniek en kan worden verwijderd.');
const favorite={nodeId:'BAL:4.1',reg:'BAL',label:'BAL › Artikel 4.1'};
assert.equal(JSON.stringify(behavior.favoriteRecord([],favorite)),JSON.stringify([favorite]));
assert.equal(JSON.stringify(behavior.favoriteRecord([favorite],favorite)),JSON.stringify([]));

console.log('Gebruikersstroom 3/5: zoekgeschiedenis vervangt dezelfde zoekopdracht.');
const history=behavior.historyRecord([{query:'opslag',reg:'BAL',label:'opslag — BAL'}],{query:'opslag',reg:'BAL'},7);
assert.equal(history.length,1);
assert.equal(history[0].query,'opslag');

console.log('Gebruikersstroom 4/5: terugverwijzing houdt volledige broncontext.');
assert.equal(behavior.referenceContext('Artikel 5.4','Artikel 4.1','eerste lid'),'Dit volledige artikel (Artikel 5.4) verwijst naar Artikel 4.1. Vindplaats: eerste lid.');

console.log('Gebruikersstroom 5/5: hoofdapp gebruikt uitsluitend de gedeelde gedragslaag.');
const app=fs.readFileSync('js/app.js','utf8');
assert.match(app,/BEHAVIOR\.favoriteRecord/,'De favorietenstroom gebruikt de gedeelde gedragslaag niet.');
assert.match(app,/BEHAVIOR\.historyRecord/,'De zoekgeschiedenis gebruikt de gedeelde gedragslaag niet.');
assert.match(app,/BEHAVIOR\.referenceContext/,'De terugverwijzing gebruikt de gedeelde gedragslaag niet.');
assert.match(fs.readFileSync('index.html','utf8'),/app-behavior\.js[\s\S]*app\.js/,'De gedragslaag moet vóór de hoofdapp laden.');
console.log('Kritieke gebruikersstromen zijn gecontroleerd.');
