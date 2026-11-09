const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 }, deviceScaleFactor: 1 });
  const htmlPath = 'file://' + path.resolve(__dirname, 'xhs_cards_sunlight.html');
  await page.goto(htmlPath, { waitUntil: 'networkidle' });

  for (let i = 1; i <= 5; i++) {
    const el = await page.$('#p' + i);
    const num = String(i).padStart(2, '0');
    const outPath = path.resolve(__dirname, `../articles/20260928-152827/小红书卡片-${num}.png`);
    await el.screenshot({ path: outPath });
    console.log(`Rendered p${i} -> 小红书卡片-${num}.png`);
  }

  await browser.close();
  console.log('All 5 sunlight cards rendered successfully!');
})();
