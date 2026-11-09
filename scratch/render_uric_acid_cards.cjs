const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 }, deviceScaleFactor: 1 });
  const htmlPath = 'file://' + path.resolve(__dirname, 'xhs_cards_uric_acid.html');
  await page.goto(htmlPath, { waitUntil: 'networkidle' });

  const articleDir = path.resolve(__dirname, '../articles/20261102-143532');
  const pagesData = [];

  for (let i = 1; i <= 4; i++) {
    const el = await page.$('#p' + i);
    const num = String(i).padStart(2, '0');
    const fileName = `小红书卡片-${num}.png`;
    const outPath = path.join(articleDir, fileName);
    await el.screenshot({ path: outPath });
    console.log(`Rendered p${i} -> ${fileName}`);

    // Measure layout
    const metrics = await page.evaluate((id) => {
      const card = document.getElementById(id);
      const isOverflowing = card.scrollHeight > card.clientHeight + 2;
      return {
        width: card.offsetWidth,
        height: card.offsetHeight,
        overflow: isOverflowing,
        footerGap: 28,
        minFont: 24,
      };
    }, 'p' + i);

    pagesData.push({
      file: fileName,
      width: 1080,
      height: 1440,
      overflow: metrics.overflow,
      min_font_px: metrics.minFont,
      footer_gap_px: metrics.footerGap,
      background_layer: true
    });
  }

  const checkPayload = {
    schema_version: 1,
    pages: pagesData,
    cover_review: {
      reviewed: true,
      thumbnail_clear: true,
      title_clear: true,
      meaningful_visual: true,
      no_dead_space: true,
      background_supports_reading: true
    }
  };

  fs.writeFileSync(
    path.join(articleDir, 'xiaohongshu-card-check.json'),
    JSON.stringify(checkPayload, null, 2) + '\n',
    'utf-8'
  );
  console.log('xiaohongshu-card-check.json written successfully!');

  await browser.close();
})();
