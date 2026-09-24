// Re-export the PNG brand assets from assets.html.
// Needs Playwright:  npm i -D playwright  (or a global install), then:  node brand/src/export.js
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(path.join(process.env.PLAYWRIGHT_GLOBAL || '/opt/node22/lib/node_modules', 'playwright'))); }

const FRAMES = {
  profile: 'profile-800.png',
  og: 'og-1200x630.png',
  linkedin: 'linkedin-banner-1584x396.png',
  post1: 'post-01-1080.png',
  'logo-dark': 'logo-dark.png',
  'logo-light': 'logo-light.png',
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1800, height: 1200 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'assets.html'));
  await page.evaluate(async () => { await Promise.all([...document.fonts].map(f => f.load())); await document.fonts.ready; });
  const ok = await page.evaluate(() => [...document.fonts].length > 0 && [...document.fonts].every(f => f.status === 'loaded'));
  if (!ok) console.warn('warning: brand fonts did not load; PNGs will use a fallback font');
  for (const [id, file] of Object.entries(FRAMES)) {
    await page.locator('#' + id).screenshot({ path: path.join(__dirname, '..', 'png', file) });
    console.log('wrote brand/png/' + file);
  }
  await browser.close();
})();
