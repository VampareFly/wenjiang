# 小红书指南

本文件定义 Step 9 的小红书卡片生成规则和 Step 10 的小红书发布文案规则。只有生成小红书卡片或 `小红书文案.txt` 时才需要读取本文件。

---

## Step 9：小红书卡片

将 `article.md` 转为小红书图文笔记卡片，输出为 1080×1440（3:4）PNG：

```text
articles/<YYYYMMDD-HHMMSS>/小红书卡片-{01-N}.png
```

使用 `guizang-social-card-skill` 生成卡片。主题/色系由 AI 根据内容类型自动匹配，不需要用户指定。

生成完成后运行 `python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_9`，检查卡片存在、非空且从 `01` 连续编号。

默认禁止生成后视觉复查。Step 9 不使用 `view_image` 或其他 AI 读图方式检查卡片内容，不因排版观感、文案视觉效果、风格偏好等主观判断重渲染。卡片质量控制必须前置到 HTML/CSS 设计和截图前的数值测量；生成后只运行状态机客观校验。只有客观校验失败、截图脚本报错、输出尺寸错误、文件编号缺失或用户明确要求时，才允许重新截图或调整卡片。

### 截图脚本规则

- Playwright 依赖在 `.agents/skills/guizang-social-card-skill/node_modules/`，截图脚本必须设置 `NODE_PATH` 指向该目录，否则 `require('playwright')` 会报 `MODULE_NOT_FOUND`：
  ```bash
  NODE_PATH=.agents/skills/guizang-social-card-skill/node_modules node screenshot.js
  ```
- 本机没有 Playwright 托管的 Chromium binary，启动浏览器时必须使用系统 Chrome：
  ```js
  const browser = await chromium.launch({ channel: "chrome" });
  ```
  禁止使用 `chromium.launch()` 不带 `channel` 参数——那会去查找不存在的 `ms-playwright` 托管路径。
- 使用 `element.screenshot()` 而非 `page.screenshot({clip})`，自动将目标元素滚入视口。
- 脚本文件先用 Write 工具创建，再用 Bash 执行，避免 sandbox 拦截。
- viewport 高度设大（≥所有卡片高度总和 + 间距）。
- `names` 数组和选择器根据实际卡片动态调整。

### 固定高度卡片的图片与文案布局规则

小红书卡片是固定画布（1080×1440）。当单页同时包含标题、表格/要点、正文配图和底部署名时，不能只靠 `width:100%; height:auto` 或随意调小图片，否则容易出现两类问题：图片被裁剪，或图片完整显示后把文案挤到底部分割线/画布外。

必须采用三段式约束：

- 内容区必须为底部 footer 预留安全区，例如 `.content { padding-bottom: 160px; }`，不能让正文元素流到 footer 的绝对定位区域。
- 图片必须放入固定高度图片盒，例如 `.image-box { height: 300-420px; display:flex; align-items:center; justify-content:center; overflow:hidden; }`。
- 图片容器默认不加装饰背景或描边；如需强调，应作用于外层卡片或局部标题，而不是图片盒本身。
- 图片本身使用 `width:100%; height:100%; object-fit:contain;`，保证完整显示且不裁剪。
- 不要使用会强制裁切原图的比例容器（如固定 `16:10`、`3:4` 的 `object-fit: cover`）展示正文信息图，除非确认裁切不影响信息。
- 页面主体使用 flex column 时，统一控制 `gap`、标题字号、表格行距；不要同时叠加大字号、大间距、大图和绝对定位 footer。
- 底部 footer 如果绝对定位，渲染前必须用 Playwright 测量：正文最后一个元素底部与 footer 顶部至少保留 24px 间距；否则必须继续调整图片盒高度或主体间距。

推荐测量逻辑：

```js
const rows = await page.$$eval('.poster.xhs', posters => posters.map(p => {
  const strip = p.querySelector('.issue-strip').getBoundingClientRect();
  const content = p.querySelector('.content');
  const last = [...content.children].at(-1).getBoundingClientRect();
  const poster = p.getBoundingClientRect();
  return {
    id: p.id,
    lastContentBottom: Math.round(last.bottom - poster.top),
    footerTop: Math.round(strip.top - poster.top),
    gap: Math.round(strip.top - last.bottom)
  };
}));
if (rows.some(r => r.gap < 24)) throw new Error('content overlaps footer safe zone');
```

以上测量必须发生在截图前或截图脚本执行过程中，属于数值门禁，不属于生成后 AI 读图复查。测量失败时修 HTML/CSS 后重新截图；测量通过且状态机校验通过时，不再额外目检图片内容。

### 临时文件清理

生成小红书卡片后，删除截图脚本、临时 HTML、临时 JS、preview/debug 文件，只保留正式输出的 `小红书卡片-{01-N}.png`。最终发布资产复查见 `docs/final-cleanup-guide.md`。

---

## Step 10：小红书文案

### 输出位置

基于 `article.md` 内容生成：

```text
articles/<YYYYMMDD-HHMMSS>/小红书文案.txt
```

---

### 写作规则

- 字幕和 `article.md` 是唯一事实基准，不新增个人经历、粉丝反馈、数据、疗效或外部结论。
- 第一行为标题，小红书会自动识别为标题，控制在 20 字以内。
- 正文使用短句，保留文章最强观点、反差或实用结论。
- 不复述长文全文，只提炼最适合小红书传播的切口。
- 可用少量 emoji 点缀，但不要堆砌。
- 文末添加与主题相关的话题标签。

生成完成后运行 `python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_10`，检查标题长度和 3-6 个话题标签。

---

### 结构建议

1. 标题：一句话给出反差、结论或痛点。
2. 开头：用 1-2 句说明为什么这件事值得看。
3. 正文：列出 3-5 个核心要点，每点尽量短。
4. 结尾：给一个低压力的提醒或行动建议。
5. 标签：添加 3-6 个相关话题。

---

### 禁止

- 不要把公众号关注引导搬到小红书文案。
- 不要承诺疗效、收益或确定改变。
- 不要使用“速看”“必看”“不看后悔”等强营销词。
- 不要为了平台感编造个人经历或粉丝反馈。
