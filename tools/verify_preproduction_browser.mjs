import { chromium } from 'playwright';

const url = process.env.PREPRODUCTION_URL;
if (!url) throw new Error('PREPRODUCTION_URL ontbreekt.');

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const errors = [];
page.on('pageerror', error => errors.push(error.message));

try {
  await page.goto(url, { waitUntil: 'networkidle', timeout: 180000 });
  await page.waitForFunction(() => {
    const input = document.getElementById('searchInput');
    const status = document.getElementById('status');
    return input && !input.disabled && /6\/6 regelingen geladen/.test(status?.textContent || '');
  }, { timeout: 180000 });
  if (errors.length) throw new Error('Browserfout: ' + errors.join(' | '));
  const regulations = await page.locator('#regulationSelect option').count();
  if (regulations !== 6) throw new Error('Verwacht 6 regelingen, vond ' + regulations + '.');
  console.log('Pre-productiesmoketest geslaagd: 6 regelingen geladen en zoeken is actief.');
} finally {
  await browser.close();
}
