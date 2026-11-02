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
      console.log(`Pre-productiesmoketest geslaagd op poging ${attempt}: ${expectedVersion}, ${expectedRegulations} regelingen geladen en zoeken is actief.`);
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
