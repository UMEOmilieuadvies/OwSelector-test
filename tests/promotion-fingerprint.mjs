import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

export function digest(value){return crypto.createHash('sha256').update(value,'utf8').digest('hex')}
export function read(root,file){return fs.readFileSync(path.join(root,file),'utf8')}
export function normalizeApp(source){
  return source
    .replaceAll("CONFIG.environment!=='test'","CONFIG.environment!=='__ENV__'")
    .replaceAll("CONFIG.environment!=='production'","CONFIG.environment!=='__ENV__'")
    .replaceAll('de testconfiguratie','de omgevingsconfiguratie')
    .replaceAll('de productieconfiguratie','de omgevingsconfiguratie')
    .replaceAll('het testversienummer','het omgevingsversienummer')
    .replaceAll('het productieversienummer','het omgevingsversienummer')
    .replaceAll('de test-Supabase-koppeling','de omgevings-Supabase-koppeling')
    .replaceAll('de productie-Supabase-koppeling','de omgevings-Supabase-koppeling')
    .replaceAll('de openbare test-Supabase-sleutel','de openbare omgevings-Supabase-sleutel')
    .replaceAll('de openbare productie-Supabase-sleutel','de openbare omgevings-Supabase-sleutel')
    .replaceAll('de gescheiden testfavorietenopslag','de gescheiden omgevingsfavorietenopslag')
    .replaceAll('de gescheiden productiefavorietenopslag','de gescheiden omgevingsfavorietenopslag')
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