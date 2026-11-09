const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1200, height: 1600 }, deviceScaleFactor: 1 });
  await page.goto('file://' + process.cwd() + '/scratch/xhs_cards_reflux.html', { waitUntil: 'networkidle' });
  for (let i = 1; i <= 5; i++) {
    const el = await page.$('#p' + i);
    const num = String(i).padStart(2, '0');
    await el.screenshot({ path: `articles/20260911-142743/小红书卡片-${num}.png` });
    console.log(`Rendered p${i} -> 小红书卡片-${num}.png`);
  }
  await browser.close();
})();
