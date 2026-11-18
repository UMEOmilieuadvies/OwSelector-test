import { chromium } from 'playwright';

const baseUrl = process.env.PREPRODUCTION_URL;
const expectedVersion = process.env.EXPECTED_VERSION;
if (!baseUrl) throw new Error('PREPRODUCTION_URL ontbreekt.');
if (!expectedVersion) throw new Error('EXPECTED_VERSION ontbreekt.');

const attempts = 5;
const delayMs = 15000;
async function dismissReleaseWelcome(page) {
  const dialog = page.locator('#releaseWelcomeModal[open]');
  if (await dialog.isVisible().catch(() => false)) {
    await page.locator('#continueReleaseWelcome').click();
    await dialog.waitFor({ state: 'hidden', timeout: 10000 });
  }
}

async function runAttempt(browser, attempt) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = [];
  const consoleMessages = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (['error', 'warning'].includes(message.type())) consoleMessages.push(`${message.type()}: ${message.text()}`);
  });
  try {
    const separator = baseUrl.includes('?') ? '&' : '?';
    await page.goto(`${baseUrl}${separator}smoke_attempt=${attempt}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForFunction(version => {
      const input = document.getElementById('searchInput');
      const status = document.getElementById('status');
      const regulations = window.OWZ_CONFIG?.regulations || [];
      const loaded = new RegExp(`${regulations.length}/${regulations.length} regelingen geladen`);
      return window.OWZ_CONFIG?.version === version && input && !input.disabled && loaded.test(status?.textContent || '');
    }, expectedVersion, { timeout: 60000 });
    await dismissReleaseWelcome(page);
    if (errors.length) throw new Error(`Browserfout: ${errors.join(' | ')}`);

    const regulations = await page.locator('#regulationSelect option').count();
    const expectedRegulations = await page.evaluate(() => window.OWZ_CONFIG?.regulations?.length || 0);
    if (regulations !== expectedRegulations) throw new Error(`Verwacht ${expectedRegulations} regelingen, vond ${regulations}.`);
    console.log(`Browsertest 1/4: ${expectedVersion}, ${expectedRegulations} regelingen geladen en zoeken is actief.`);

    const target = await page.evaluate(async () => {
      const references = await (await fetch('data/back_references.json')).json();
      for (const regulation of window.OWZ_CONFIG.regulations) {
        const graph = await (await fetch(`data/graph/${regulation.file}`)).json();
        for (const node of graph.nodes || []) {
          if (node.type !== 'article') continue;
          const rows = references.references?.[`${regulation.id}:${node.id}`] || [];
          if (rows.some(row => row.regulation !== regulation.id)) return {
            regulation: regulation.id,
            article: String(node.number_display || node.number || '')
          };
        }
      }
      return null;
    });
    if (!target?.article) throw new Error('Geen artikel met een terugverwijzing gevonden voor de browsertest.');

    console.log(`Browsertest 2/4: zoek en open ${target.regulation} artikel ${target.article}.`);
    await page.selectOption('#regulationSelect', target.regulation);
    await page.locator('#searchInput').fill(target.article);
    await page.waitForFunction(() => !document.getElementById('searchButton')?.disabled, null, { timeout: 10000 });
    await page.locator('#searchButton').click();
    const articleResult = page.locator(`.searchResult[data-result-type="article"][data-article-result="${target.regulation}:${target.article}"]`).first();
    await articleResult.waitFor({ timeout: 30000 });
    await articleResult.click();
    const articleFavorite = page.locator('.articleFavorite').first();
    await articleFavorite.waitFor({ timeout: 30000 });

    console.log('Browsertest 3/4: controleer favorietenknop en volledige terugverwijzing.');
    await articleFavorite.click();
    await page.locator('#favoriteConsentModal[open]').waitFor({ timeout: 10000 });
    await page.evaluate(() => document.getElementById('favoriteConsentModal')?.close());
    const backReference = page.locator('#side [data-back-reference]').first();
    await backReference.waitFor({ timeout: 30000 });
    await backReference.click();
    await page.locator('.referenceArticleContext').waitFor({ timeout: 30000 });

    console.log('Browsertest 4/4: open de artikelsgewijze toelichting in een nieuw tabblad.');
    const [notesPage] = await Promise.all([
      page.waitForEvent('popup'),
      page.locator('.articleNotesButton').click()
    ]);
    await notesPage.waitForLoadState('domcontentloaded');
    if (!/article-notes\.html\?/.test(notesPage.url())) throw new Error('De NvT-knop opent niet de artikelsgewijze toelichting.');
    await notesPage.close();
    console.log('Pre-productiebrowsertest geslaagd: zoeken, favorietenknop, terugverwijzing en NvT-knop werken.');
  } catch (error) {
    await page.screenshot({ path: `test-results/smoke-attempt-${attempt}.png`, fullPage: true }).catch(() => {});
    const diagnostics = [String(error?.stack || error), ...errors, ...consoleMessages];
    throw new Error(diagnostics.join('\n'));
  } finally {
    await context.close();
  }
}

const browser = await chromium.launch({ headless: true });
let lastError;
try {
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      await runAttempt(browser, attempt);
      lastError = null;
      break;
    } catch (error) {
      lastError = error;
      if (attempt < attempts) {
        console.warn(`Poging ${attempt}/${attempts} nog niet gereed: ${error.message}`);
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }
  }
} finally {
  await browser.close();
}

if (lastError) throw lastError;
