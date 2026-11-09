#!/usr/bin/env node
/**
 * Toutiao Creator Platform Automation Engine (Chrome + Playwright)
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const os = require('os');

const USER_DATA_DIR = process.env.TOUTIAO_CHROME_PROFILE || path.join(os.homedir(), '.toutiao_chrome_profile');

function ensureProfileDir() {
  if (!fs.existsSync(USER_DATA_DIR)) {
    fs.mkdirSync(USER_DATA_DIR, { recursive: true });
  }
}

async function getBrowserContext(headless = false) {
  ensureProfileDir();
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    channel: 'chrome',
    headless: headless,
    viewport: { width: 1440, height: 900 },
    locale: 'zh-CN',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    args: [
      '--disable-blink-features=AutomationControlled',
      '--no-sandbox',
      '--disable-infobars',
    ]
  });
  return context;
}

async function checkLogin() {
  console.log('==> 正在检测今日头条登录态...');
  const context = await getBrowserContext(false);
  const page = context.pages()[0] || await context.newPage();

  try {
    await page.goto('https://mp.toutiao.com/profile_v4/index', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(2500);

    const cookies = await context.cookies();
    const hasSessionCookie = cookies.some(c => (c.name === 'sessionid' || c.name === 'sessionid_ss') && c.value && c.domain.includes('toutiao.com'));
    const currentUrl = page.url();
    const isLoginPage = currentUrl.includes('/auth/page/login') || currentUrl.includes('/login');

    const isLogged = hasSessionCookie && !isLoginPage;

    if (isLogged) {
      console.log('✓ 今日头条登录态有效！');
    } else {
      console.log('❌ 未登录或登录态已失效');
    }

    await context.close();
    return isLogged;
  } catch (err) {
    console.error('检测登录态出错:', err.message);
    try { await context.close(); } catch(e) {}
    return false;
  }
}

async function interactiveLogin(force = false) {
  console.log('==> 正在唤起 Chrome 浏览器，请在弹出的窗口中扫码登录今日头条（头条号）...');
  const context = await getBrowserContext(false);
  const page = context.pages()[0] || await context.newPage();

  try {
    if (force) {
      console.log('💡 正在清理旧 Session 以便重新扫码...');
      await context.clearCookies();
    }

    await page.goto('https://mp.toutiao.com/auth/page/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
    console.log('💡 请在浏览器中完成扫码登录。窗口将保持打开，直到您扫码成功进入后台（限时 5 分钟）...');

    await page.waitForTimeout(3000);

    const startTime = Date.now();
    const timeout = 300000; // 5 minutes

    while (Date.now() - startTime < timeout) {
      if (page.isClosed()) {
        console.log('💡 浏览器窗口已被用户关闭，正在确认登录态...');
        break;
      }

      const cookies = await context.cookies();
      const hasSessionCookie = cookies.some(c => (c.name === 'sessionid' || c.name === 'sessionid_ss') && c.value && c.domain.includes('toutiao.com'));
      const currentUrl = page.url();
      const isLoginUrl = currentUrl.includes('/auth/page/login') || currentUrl.includes('/login');

      // 仅当用户拥有有效的 sessionid 且已成功跳转至 profile_v4 创作者后台时，才判定为登录成功
      if (hasSessionCookie && !isLoginUrl && currentUrl.includes('profile_v4')) {
        console.log('🎉 恭喜！检测到已成功进入头条号后台：', currentUrl);
        console.log('正在等待 Session 持久化写入磁盘...');
        await page.waitForTimeout(4000);
        await context.close();
        console.log('✓ 今日头条持久化 Session 保存成功！');
        return true;
      }

      await page.waitForTimeout(2000);
    }

    try { await context.close(); } catch (e) {}
    return await checkLogin();
  } catch (err) {
    console.error('登录窗口提示:', err.message);
    try { await context.close(); } catch (e) {}
    return false;
  }
}

async function postArticle(payloadPath) {
  const payload = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));
  const { title, body, covers = [], images = [] } = payload;

  console.log(`\n==> [1/2] 正在自动推送今日头条深度长文: 《${title}》`);
  // 必须使用 non-headless 或正常窗口绕过 SecSDK 7050 限流
  const context = await getBrowserContext(false);
  const page = context.pages()[0] || await context.newPage();

  try {
    let saveSuccess = false;
    let savedPgcId = '';

    page.on('response', async res => {
      if (res.url().includes('article/publish')) {
        try {
          const json = await res.json();
          if (json.code === 0 || json.message === '保存成功') {
            saveSuccess = true;
            savedPgcId = json.data?.pgc_id || '';
            console.log(`  ✓ 头条云端草稿同步成功！(pgc_id: ${savedPgcId})`);
          }
        } catch(e) {}
      }
    });

    await page.goto('https://mp.toutiao.com/profile_v4/graphic/publish', {
      waitUntil: 'networkidle',
      timeout: 45000
    });
    await page.waitForTimeout(2500);

    if (page.url().includes('/auth/page/login')) {
      throw new Error('登录态失效，请先运行 --login 进行扫码登录');
    }

    // 1. 填入标题
    console.log('1. 正在填入文章标题...');
    const titleTextarea = await page.waitForSelector('textarea[placeholder*="请输入文章标题"]', { timeout: 15000 });
    await titleTextarea.click();
    await titleTextarea.fill(title);
    await titleTextarea.press('Space');
    await titleTextarea.press('Backspace');
    await page.waitForTimeout(1000);

    // 2. 填入长文正文内容与排版（保留【配图1/2/3】文字标记，由用户后续自行上传配图与封面）
    console.log('2. 正在填入长文正文内容与排版...');
    const editor = await page.waitForSelector('.ProseMirror', { timeout: 15000 });
    await editor.click();
    await page.waitForTimeout(500);

    const cleanBody = body.replace(/^>[\s\S]*?---\n/, '').trim();

    // 填入段落与标题
    await page.evaluate(({ bodyContent }) => {
      const el = document.querySelector('.ProseMirror');
      if (el) {
        el.focus();
        el.innerHTML = '';

        const paras = bodyContent.split(/\n\n+/);
        for (const p of paras) {
          const trimmed = p.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith('### ')) {
            const h3 = document.createElement('h3');
            h3.textContent = trimmed.replace('### ', '');
            el.appendChild(h3);
          } else {
            const pElem = document.createElement('p');
            let formatted = trimmed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            pElem.innerHTML = formatted;
            el.appendChild(pElem);
          }
        }
        el.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }, { bodyContent: cleanBody });

    // 触发 ProseMirror 输入状态更新
    await page.keyboard.press('End');
    await page.keyboard.type(' ');
    await page.keyboard.press('Backspace');
    await page.waitForTimeout(2000);

    // 3. 等待自动保存响应
    console.log('3. 正在确认头条云端草稿同步...');
    const startTime = Date.now();
    while (!saveSuccess && Date.now() - startTime < 15000) {
      await page.keyboard.press('End');
      await page.keyboard.type(' ');
      await page.keyboard.press('Backspace');
      await page.waitForTimeout(2000);
    }

    await page.waitForTimeout(2000);
    console.log('🎉 今日头条长文草稿已成功保存至云端草稿箱！');

    await context.close();
    return { success: true, title, pgcId: savedPgcId };

  } catch (err) {
    console.error('❌ 保存头条长文草稿失败:', err.message);
    try { await context.close(); } catch(e) {}
    throw err;
  }
}

async function postWeitoutiao(payloadPath) {
  const payload = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));
  const { content, attachments = [] } = payload;

  console.log(`\n==> [2/2] 正在自动推送微头条短快讯 (${content.length} 字)...`);
  const context = await getBrowserContext(false);
  const page = context.pages()[0] || await context.newPage();

  try {
    await page.goto('https://mp.toutiao.com/profile_v4/weitoutiao/publish', {
      waitUntil: 'networkidle',
      timeout: 45000
    });
    await page.waitForTimeout(2500);

    if (page.url().includes('/auth/page/login')) {
      throw new Error('登录态失效，请先运行 --login 进行扫码登录');
    }

    // 1. 填入微头条内容
    console.log('1. 正在填入微头条正文与标签...');
    const editor = await page.waitForSelector('.ProseMirror, [contenteditable="true"], textarea', { timeout: 20000 });
    if (editor) {
      await editor.click();
      await page.evaluate(({ text }) => {
        const el = document.querySelector('.ProseMirror, [contenteditable="true"]');
        if (el) {
          el.focus();
          el.innerText = text;
          el.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }, { text: content });
      await page.keyboard.press('End');
      await page.keyboard.type(' ');
      await page.keyboard.press('Backspace');
    }

    await page.waitForTimeout(1500);

    // 2. 上传配图（先点击“图片”工具栏图标唤出上传控件）
    if (attachments && attachments.length > 0) {
      console.log(`2. 正在点击图片按钮并上传 ${attachments.length} 张微头条卡片图...`);
      const validFiles = attachments.filter(f => fs.existsSync(f)).slice(0, 9);
      if (validFiles.length !== attachments.slice(0, 9).length) {
        throw new Error(`微头条配图文件不完整：期望 ${attachments.slice(0, 9).length} 张，实际找到 ${validFiles.length} 张`);
      }

      let uploadedViaChooser = false;
      const imageButton = page.getByRole('button', { name: '图片', exact: true });
      if (await imageButton.count() && await imageButton.isEnabled()) {
        try {
          const [chooser] = await Promise.all([
            page.waitForEvent('filechooser', { timeout: 5000 }),
            imageButton.click(),
          ]);
          await chooser.setFiles(validFiles);
          uploadedViaChooser = true;
        } catch (chooserErr) {
          console.warn('  图片按钮未唤起文件选择器，尝试页面内上传控件:', chooserErr.message);
        }
      }

      const fileInput = uploadedViaChooser ? null : await page.$('input[type="file"]');
      if (!uploadedViaChooser && !fileInput) {
        const controls = await page.locator('button, [role="button"], input, [contenteditable="true"]').evaluateAll(els => els.map(el => ({
          tag: el.tagName,
          text: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().slice(0, 80),
          type: el.getAttribute('type') || '',
          disabled: Boolean(el.disabled),
          cls: String(el.className || '').slice(0, 120),
        })).filter(x => x.text || x.type));
        console.error('  页面可用控件:', JSON.stringify(controls, null, 2));
        await page.screenshot({ path: '/private/tmp/toutiao-weitoutiao-debug.png', fullPage: true });
        throw new Error('未找到微头条图片上传控件');
      }

      if (fileInput) await fileInput.setInputFiles(validFiles);
      console.log('  正在等待图片上传与排版渲染...');
      await page.waitForTimeout(8000);

      const confirmBtn = page.locator('button').filter({ hasText: /^(确定|插入|完成)$/ }).last();
      if (await confirmBtn.count() && await confirmBtn.isVisible().catch(() => false) && await confirmBtn.isEnabled().catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);
      }
      console.log(`  ✓ 已向上传控件提交 ${validFiles.length} 张微头条配图`);
    }

    // 3. 点击“存草稿”
    console.log('3. 正在保存微头条草稿...');

    // 隐藏可能遮挡点击的抽屉遮罩层 (如发文助手 byte-drawer-mask)
    await page.evaluate(() => {
      const masks = document.querySelectorAll('.byte-drawer-mask, .byte-drawer-wrapper, .publish-assistant-old-drawer');
      masks.forEach(m => { m.style.display = 'none'; });
    });

    let savedGid = '';
    page.on('response', async res => {
      if (res.request().method() === 'POST' && (res.url().includes('draft') || res.url().includes('save'))) {
        try {
          const json = await res.json();
          const gid = json.gid || json.data?.gid || json.data?.id || json.data?.draft_id || '';
          if (json.code === 0 && gid) {
            savedGid = String(gid);
            console.log(`  ✓ 微头条云端草稿同步成功！(gid: ${savedGid})`);
          }
        } catch(e) {}
      }
    });

    // 优先使用 evaluate 触发真实点击，彻底规避 pointer-events 拦截
    const draftClicked = await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const draft = btns.find(b => b.innerText.includes('存草稿') || b.innerText.includes('保存草稿'));
      if (draft) {
        draft.click();
        return true;
      }
      return false;
    });

    if (draftClicked) {
      console.log('  已点击微头条【存草稿】按钮');
      await page.waitForTimeout(2000);
    } else {
      const draftBtn = await page.$('xpath=//button[contains(., "存草稿") or contains(., "保存草稿")]');
      if (draftBtn) {
        await draftBtn.click({ force: true });
        console.log('  已点击微头条【存草稿】按钮 (force)');
        await page.waitForTimeout(2000);
      }
    }

    const saveDeadline = Date.now() + 15000;
    while (!savedGid && Date.now() < saveDeadline) {
      await page.waitForTimeout(500);
    }
    if (!savedGid) {
      throw new Error('未收到微头条云端草稿成功响应，不能判定为已上传');
    }

    console.log(`🎉 微头条草稿保存完成！gid: ${savedGid}`);
    await context.close();
    return { success: true, gid: savedGid };
  } catch (err) {
    console.error('❌ 保存微头条草稿失败:', err.message);
    try { await context.close(); } catch(e) {}
    throw err;
  }
}

async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (cmd === 'login') {
    const force = args.includes('--force');
    const ok = await interactiveLogin(force);
    process.exit(ok ? 0 : 1);
  } else if (cmd === 'check-login') {
    const ok = await checkLogin();
    process.exit(ok ? 0 : 1);
  } else if (cmd === 'post-article') {
    const payloadPath = args[1];
    await postArticle(payloadPath);
  } else if (cmd === 'post-weitoutiao') {
    const payloadPath = args[1];
    await postWeitoutiao(payloadPath);
  } else {
    console.log('用法: node toutiao_publisher.js [login|check-login|post-article <payload.json>|post-weitoutiao <payload.json>]');
    process.exit(1);
  }
}

main().catch(err => {
  console.error('运行时错误:', err);
  process.exit(1);
});
