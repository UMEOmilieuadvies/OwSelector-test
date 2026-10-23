import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

export function digest(value){return crypto.createHash('sha256').update(value.replace(/\r\n/g,'\n'),'utf8').digest('hex')}
export function read(root,file){return fs.readFileSync(path.join(root,file),'utf8')}
export function normalizeApp(source){
  return source
    .replace(/function startupProblems\(\)\{.*?(?=function showStartupFailure)/s,'function startupProblems(){/* environment-specific */}\n')
    .replaceAll('owz_test_favorite_recovery_code','owz_environment_favorite_recovery_code')
    .replaceAll('owz_production_favorite_recovery_code','owz_environment_favorite_recovery_code');
}
export function normalizeIndex(source){
  return source
    .replace('<body><div class="environmentBanner" role="status">Testomgeving — wijzigingen zijn nog niet definitief.</div>','<body>')
    .replaceAll('__OWZ_VERSION__','__VERSION__')
    .replace(/release-\d+\.\d+[a-z]*/g,'release-__VERSION__')
    .replace(/Omgevingswet Zoeker \d+\.\d+[a-z]*/g,'Omgevingswet Zoeker __VERSION__')
    .replaceAll('testdatabase','omgevingsdatabase')
    .replaceAll('productiedatabase','omgevingsdatabase');
}
export function fingerprints(root){
  return {
    app_js:digest(normalizeApp(read(root,'js/app.js'))),
    index_html:digest(normalizeIndex(read(root,'index.html'))),
    app_css:digest(read(root,'css/app.css'))
  };
}