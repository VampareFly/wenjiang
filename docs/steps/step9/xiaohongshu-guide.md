# 小红书卡片指南

本文件定义 Step 9 的小红书卡片生成规则。只有生成小红书卡片时才需要读取本文件。

---

## Step 9：小红书卡片

将 `article.md` 转为小红书图文笔记卡片，输出为 1080×1440（3:4）PNG：

```text
articles/<YYYYMMDD-HHMMSS>/小红书卡片-{01-N}.png
```

使用 `guizang-social-card-skill` 生成卡片，不替换 Skill，不修改 Skill 本体或其上游模板。主题/色系由 AI 根据内容类型自动匹配，不需要用户指定；除非用户明确要求 Swiss，公众号长文转小红书默认使用 `Editorial Magazine x E-ink` 视觉系统。

`小红书卡片-01.png` 固定为小红书封面，不得把公众号的 `cover.png` 误当成小红书封面。首图的任务是在信息流中让读者一眼看懂“对象 + 值得继续滑动的冲突或收益”，不是复制公众号标题或制作研究报告首页。

### 封面与素材复用

- 封面文案围绕文章核心判断生成最多 3 个短钩子，只保留文案本身，不输出长篇理由。选定文案必须比公众号标题更短，但不得扩大事实、风险或疗效。
- 首图必须有一个明确钩子、一个主要视觉对象或强数据视觉，以及清楚的标题层级。纯文字封面只能用于单句宣言式强视觉，不得用大面积无意义留白填充 3:4 画布。
- 生成新图前，先检查同一文章目录中的公众号封面和正文配图。优先复用能支持标题且适合 3:4 重新构图的现有素材；只有现有素材均不适合时，才额外生成 1 张竖版视觉素材。
- 正文卡片中的信息图必须在手机尺寸下可读；如果为了容纳完整信息图而导致文字过小，应拆页或改用局部摘要，不得只把整张图缩小。

### 背景硬规则

- 每张小红书卡片都必须有可感知的背景系统，不得交付纯白或只有单一扁平底色的卡片。背景用于建立氛围和层次，不得添加与内容无关的圆点、气泡、波浪线、贴纸或亮色装饰渐变。
- Editorial 默认使用 Skill 内置的分层背景：主题纸张底色 + 细微纸纹 + 墨晕或等高线氛围层；可使用冻结的 WebGL 墨流背景，失败时改用 2D 墨晕备用方案，不能退化成纯白底。
- 首图背景强度高于正文页：优先用已有 `cover.png` 或正文配图做大图、局部裁切或主视觉，再配合纸纹/墨晕建立文字安全区。素材不适合全幅时改用大图框或主题色抽取，不强行铺满导致主体被裁。
- 正文页背景应更弱：保留同一色系和纸纹/墨晕，但降低对比度，不得在正文、数字或小字背后放置强纹理。数据密集页仍需有弱背景，但以可读性为上限。
- 同一套卡片只使用一套色盘和一种视觉系统；可通过首图强背景、正文弱背景、结尾回应首图建立节奏，不得每页随机换风格。
- 健康科普优先从现有主题中选择：研究、检测、数据类使用 `Indigo Porcelain`；饮食、植物性食物、生活方式类使用 `Forest Ink`；中性科普使用 `Ink Classic`。不为了醒目擅自使用警报红、荧光色或恐惧化视觉。
- 如用户明确要求 Swiss，不使用亮色渐变或随机装饰；必须通过主题图像、大面积单色块、证据图框和严格网格建立背景层次，避免纯白画布。

### 首图主视觉硬门禁

- `小红书卡片-01.png` 必须包含明确的图片或插画主视觉，不得交付只有文字、纸纹或抽象背景的首图。
- 生成前优先复用文章目录中的 `cover.png` 或正文配图；若没有合适素材，必须先生成一张与主题直接相关的视觉素材，再开始排版。
- 渲染后必须检查首图 HTML 或渲染源是否引用有效图片文件，并目检确认图片主体在缩略图下仍可辨认、没有被标题遮挡。
- 若首图缺少图片主体，Step 9 不得通过；必须补图并重新渲染首图后才能继续流程。

生成完成后运行 `python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_9`，检查卡片存在、非空且从 `01` 连续编号。

为控制 Token，生成后默认只对 `小红书卡片-01.png` 做一次 AI 视觉复查，不逐张读取后续卡片。首图只检查五项：缩略图是否醒目、标题是否一眼读懂、是否有无意义的大面积空白、背景是否与主题有关且不是纯白/扁平底色、背景和视觉素材是否支持标题且不影响阅读。任一项明确不合格时，只调整首图并复查一次，不重做整套卡片；仍有主观风格分歧时留给用户判断。

后续卡片默认只做程序检查：尺寸、编号、文字溢出、字号、底部安全区、标题间距和 4 横带密度。截图前还必须在 DOM 中确认每张卡片存在非空的背景层（如 `.mag-bg`、`.grain`、`.ink-vignette` 或等价主题图层）；缺失背景层时视为客观失败，不需要逐张 AI 读图。只有程序报警、客观门禁失败或用户指出具体页面时，才读取对应卡片进行视觉检查。

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

生成小红书卡片后，删除截图脚本、临时 HTML、临时 JS、preview/debug 文件，只保留正式输出的 `小红书卡片-{01-N}.png`。最终发布资产复查见 `docs/steps/step11/final-cleanup-guide.md`。
