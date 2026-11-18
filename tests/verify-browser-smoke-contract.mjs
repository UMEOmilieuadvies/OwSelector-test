import assert from 'node:assert/strict';
import fs from 'node:fs';

const smoke = fs.readFileSync('tools/verify_preproduction_browser.mjs', 'utf8');
const workflow = fs.readFileSync('.github/workflows/preproduction-smoke.yml', 'utf8');
const app = fs.readFileSync('js/app.js', 'utf8');

assert.match(smoke, /browser\.newContext\(\)/, 'Iedere browserpoging moet een schone context gebruiken.');
assert.match(smoke, /dismissReleaseWelcome/, 'De browserproef moet het wijzigingsvenster beheersen.');
assert.match(smoke, /searchButton'\)\?\.disabled/, 'De browserproef moet wachten op een actieve zoekknop.');
assert.match(smoke, /data-article-result/, 'De browserproef moet een stabiele artikelidentificatie gebruiken.');
assert.match(smoke, /page\.screenshot/, 'De browserproef moet bij een fout diagnose vastleggen.');
assert.match(workflow, /npm ci/, 'Browserafhankelijkheden moeten uit het lockbestand worden geïnstalleerd.');
assert.match(workflow, /ubuntu-24\.04/, 'De browserrunner moet bewust zijn gekozen.');
assert.match(workflow, /concurrency:/, 'Overlappende browserproeven moeten worden voorkomen.');
assert.match(workflow, /upload-artifact@v5/, 'Browserdiagnose moet bij een fout beschikbaar zijn.');
assert.match(app, /data-article-result/, 'Zoekresultaten moeten een stabiele artikelidentificatie aanbieden.');

console.log('Het contract voor de browser-smoketest is gecontroleerd.');
