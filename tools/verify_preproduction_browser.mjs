import { chromium } from 'playwright';

const baseUrl = process.env.PREPRODUCTION_URL;
const expectedVersion = process.env.EXPECTED_VERSION;
if (!baseUrl) throw new Error('PREPRODUCTION_URL ontbreekt.');
if (!expectedVersion) throw new Error('EXPECTED_VERSION ontbreekt.');

const attempts = 5;
const delayMs = 15000;
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
let succeeded = false;
let lastError;

try {
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const errors = [];
    page.removeAllListeners('pageerror');
    page.on('pageerror', error => errors.push(error.message));
    const separator = baseUrl.includes('?') ? '&' : '?';
    try {
      await page.goto(`${baseUrl}${separator}smoke_attempt=${attempt}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForFunction(version => {
        const input = document.getElementById('searchInput');
        const status = document.getElementById('status');
        const regulations = window.OWZ_CONFIG?.regulations || [];
        const loaded = new RegExp(`${regulations.length}/${regulations.length} regelingen geladen`);
        return window.OWZ_CONFIG?.version === version && input && !input.disabled && loaded.test(status?.textContent || '');
      }, expectedVersion, { timeout: 60000 });
      if (errors.length) throw new Error('Browserfout: ' + errors.join(' | '));
      const regulations = await page.locator('#regulationSelect option').count();
      const expectedRegulations = await page.evaluate(() => window.OWZ_CONFIG?.regulations?.length || 0);
      if (regulations !== expectedRegulations) throw new Error(`Verwacht ${expectedRegulations} regelingen, vond ${regulations}.`);
      console.log(`Browsertest 1/4: ${expectedVersion}, ${expectedRegulations} regelingen geladen en zoeken is actief.`);

      const target = await page.evaluate(async () => {
        const references = await (await fetch('data/back_references.json')).json();
        for (const regulation of window.OWZ_CONFIG.regulations) {
          const graph = await (await fetch(`data/graph/${regulation.file}`)).json();
          for (const node of graph.nodes || []) {
            const rows = references.references?.[`${regulation.id}:${node.id}`] || [];
            if (rows.some(row => row.regulation !== regulation.id)) {
              return {regulation:regulation.id, article:String(node.number_display || node.number || '')};
            }
          }
        }
        return null;
      });
      if (!target?.article) throw new Error('Geen artikel met een terugverwijzing gevonden voor de browsertest.');

      console.log(`Browsertest 2/4: zoek en open ${target.regulation} artikel ${target.article}.`);
      await page.selectOption('#regulationSelect', target.regulation);
      await page.locator('#searchInput').fill(target.article);
      await page.locator('#searchButton').click();
      await page.locator('.searchResult').first().waitFor({timeout:30000});
      await page.locator('.searchResult').first().click();
      const articleFavorite = page.locator('.articleFavorite').first();
      await articleFavorite.waitFor({timeout:30000});

      console.log('Browsertest 3/4: controleer favorietenknop en volledige terugverwijzing.');
      await articleFavorite.click();
      await page.locator('#favoriteConsentModal[open]').waitFor({timeout:10000});
      await page.evaluate(() => document.getElementById('favoriteConsentModal')?.close());
      const backReference = page.locator('#side [data-back-reference]').first();
      await backReference.waitFor({timeout:30000});
      await backReference.click();
      await page.locator('.referenceArticleContext').waitFor({timeout:30000});

      console.log('Browsertest 4/4: open de artikelsgewijze toelichting in een nieuw tabblad.');
      const [notesPage] = await Promise.all([
        page.waitForEvent('popup'),
        page.locator('.articleNotesButton').click()
      ]);
      await notesPage.waitForLoadState('domcontentloaded');
      if (!/article-notes\.html\?/.test(notesPage.url())) throw new Error('De NvT-knop opent niet de artikelsgewijze toelichting.');
      await notesPage.close();
      console.log('Pre-productiebrowsertest geslaagd: zoeken, favorietenknop, terugverwijzing en NvT-knop werken.');
      succeeded = true;
      break;
    } catch (error) {
      lastError = error;
      if (attempt === attempts) break;
      console.warn(`Poging ${attempt}/${attempts} nog niet gereed: ${error.message}`);
      await page.waitForTimeout(delayMs);
    }
  }
} finally {
  await browser.close();
}

if (!succeeded) throw lastError;
