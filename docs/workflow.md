# 文章生产工作流

收到字幕文件后，按以下步骤依次执行。

所有内容集中在 `articles/<YYYYMMDD>/` 单一目录，不分散存放。

---

## 目录结构

```
articles/<YYYYMMDD>/
├── article.md / cover_prompt.md
├── cover.png + 配图{1-N}.png
├── article.html
└── 小红书卡片-{01-N}.png + 小红书文案.txt
```

**文件关系说明：**

| 文件 | 来源步骤 | 用途 |
|------|---------|------|
| `article.md` | Step 1 → Step 3 覆盖 | 原始 markdown → 经 `/baoyu-format-markdown` 排版优化后覆盖自身。**后续所有步骤基于此文件操作** |
| `article.html` | Step 4 | 公众号文章 HTML，用于上传微信草稿 |

---

## 上下文压缩策略

每步完成后压缩上下文以优化 token 使用。各步产出已保存在文件中，下一步直接读文件即可。

**关键原则：** 压缩时必须保留当前步骤号、用户决策（标题选择、配图删除等）和文件路径。压缩的是对话过程，不是文件内容。

| 时机 | 动作 | 原因 |
|------|------|------|
| Step 1-3 期间 | **不压缩** | 文章仍在打磨中，需要上下文连贯 |
| Step 3 完成后 | 压缩一次 | 文章已定稿，后续步骤全部基于文件操作 |
| Step 5 完成后 | 可压缩 | 图片已生成，Step 6-8 是机械操作 |
| Step 8 完成后 | 可压缩 | 草稿已上传，Step 9-10 独立于前序步骤 |

**自动压缩触发规则：**

每步执行完成后，AI 必须主动触发上下文压缩（通过 `/compact` 或等效机制），不要等待用户提醒。压缩是工作流的一部分，不是可选操作。

**压缩时必须保留的信息：**
- 当前执行到第几步
- 用户确认的标题
- 用户的特殊要求或修改（如删除配图、修改工作流规则等）
- `articles/<YYYYMMDD>/` 目录路径

---

## 流程

### Step 1：生成文章和配图提示词

- **article.md** — 按 `docs/content-types.md` 生成，正文尾部含：
  1. 5个爆款标题（备选）
  2. 正文内容
  3. 免责声明（`>` 引用格式，2句以内）
  4. 关注引导（50-80字，独立段落）
- **cover_prompt.md** — 封面 + 配图提示词（格式见 `docs/cover-prompt-format.md`）

### Step 2：选定标题（AI 自动）

AI 根据引流、曝光量和搜索量目标，从 5 个候选标题中自动选择最优标题：
- 放入 frontmatter 的 `title` 字段
- **从正文中删除候选标题列表**
- 选择标准：微信搜一搜关键词覆盖 > 认知冲突感 > 具体结论或数字 > 社交传播性
- 不向用户展示候选列表，不要求用户选择

### Step 3：格式化 Markdown（自动）

**自动调用** `/baoyu-format-markdown` skill 检查并格式化 article.md：
- 无需用户确认，直接执行
- **直接选择「优化格式」模式，跳过 skill 内的模式选择提问**
- **格式校验后，用格式化内容覆盖 `article.md`**（删除 `article-formatted.md` 中间文件，保持目录中唯一 `article.md`）
- 修复 CJK/英文间距、标点符号等排版问题
- 后续步骤基于 `article.md` 操作

### Step 4：生成公众号 HTML（自动）

**随机选择**（`baoyu-markdown-to-html` 60% / `md2wechat --mode ai` 40%）将 `article.md` 转为 `article.html`：

- 方案：`baoyu-markdown-to-html`（AI 按内容类型自动匹配主题和色系）或 `md2wechat --mode ai`
- 输出到 `articles/<YYYYMMDD>/article.html`
- HTML 中图片先用本地路径占位，后续 Step 5 生成后替换为实际路径
- 选定方案后直接执行，**不需要用户指定**

**方案一 — baoyu-markdown-to-html**

AI 按内容类型自动匹配主题和色系，详见 `docs/baoyu-markdown-to-html-usage.md`。输出文件名与输入文件名一致（`article.md` → `article.html`），直接生成 `article.html`。

**方案二 — md2wechat AI 模式**

运行 `md2wechat convert --mode ai` 获得 `article.prompt.txt`，AI 读取其中的设计规范后生成匹配的 `article.html`。详细命令参数、主题选择表见 `docs/md2wechat-usage.md`。

**工作流规则（强制）：**
- 生成 HTML 时，只使用基本参数（不加 `--draft` 和 `--upload`）
- 等待用户预览确认后，再执行上传命令
- `md2wechat` 同时负责图片上传（`upload_image`）和草稿上传（`test-draft`）

**微信 HTML 兼容性（生成 HTML 后必须检查）：**
- 微信编辑器会剥掉 `<ul>` / `<li>` 标签，导致列表换行失效。正文中的列举内容统一使用独立 `<p>` 段落 + `margin-bottom` 控制间距，不用 `<ul><li>`
- 禁止使用 `<style>` 标签，所有样式必须为 inline style
- 禁止使用 flex `gap` 属性（公众号不支持），卡片间距用 `margin-bottom` 实现

### Step 5：生成配图

使用 `/baoyu-image-gen` skill 从 `cover_prompt.md` 自动批量出图：

- 提取 `cover_prompt.md` 中各 section 的英文提示词
- 组装 batch file，调用 `baoyu-image-gen` 批量生成
- 封面 `cover.png`（16:9）、配图 `配图N.png`（按 `cover_prompt.md` 指定的比例）
- 图片保存到 `articles/<YYYYMMDD>/` 目录

详细流程见 `docs/image-gen-usage.md`。

**覆盖与备份规则：**
如果文章目录里已存在同名图片，先备份旧图再保存新文件（文件名追加 `.backup-YYYYMMDD-HHMMSS`）。

**图片路径替换：**
配图生成完成后，立即将 `article.html` 中的占位路径（如 `配图1.jpg`）替换为实际生成的图片文件名（如 `配图1.png`）。确保 Step 6 预览时图片能正确显示。

### Step 6：预览确认

**用户打开 `article.html` 预览，确认：**

- 排版正确
- 图片位置和说明正常
- 内容无误

确认后进入下一步。如需修改，返回 Step 1-5 对应环节。

### Step 7：上传图片并替换 CDN 地址

用户确认后，用 `md2wechat upload_image` 逐张上传封面和配图，将 HTML 中的本地路径替换为返回的 CDN 地址。

详细命令见 `docs/md2wechat-usage.md`。

### Step 8：上传公众号草稿

使用 `md2wechat test-draft` 上传 `article.html` 和封面到微信草稿箱。

获得草稿 ID 后告知用户：
- 标题（从 frontmatter 提取）
- 作者
- 摘要

让用户在微信公众号后台手动设置标题/作者/摘要后发布。

### Step 9：生成小红书卡片

**随机选择**（`guizang-social-card-skill` 60% / `claude-design-card` 40%）将 `article.md` 内容转为小红书图文笔记卡片：

- 格式：小红书图文笔记（1080×1440，3:4）
- 数量：AI 根据内容自动决定（封面 + 若干内容卡片 + 收尾总结）
- 输出到 `articles/<YYYYMMDD>/小红书卡片-{01-N}.png`
- 选定 skill 后，其内部的主题/色系由 AI 根据内容类型自动匹配，**不需要用户指定**
- **skill 内的图片来源由 AI 自动决策**：评估已有配图（`cover.png`, `配图1-N.png`）是否适合卡片设计，决定使用本地图片还是从网络获取更适合的素材
- **skill 内的风格模式由 AI 根据文章内容自动选择**（Editorial 或 Swiss），不询问用户

**截图脚本规则：**

- 使用 `element.screenshot()` 而非 `page.screenshot({clip})` — 自动将目标元素滚入视口
- 脚本文件先用 Write 工具创建，再用 Bash 执行（避免 sandbox 拦截）
- viewport 高度设大（≥所有卡片高度总和 + 间距）
- `names` 数组和选择器根据实际卡片动态调整

**claude-design-card**：按技能指引生成标准化信息卡片。
**guizang-social-card-skill**：按技能指引生成杂志风社交卡片，具体流程参考其 Style Mode 和 Layout Recipes。

### Step 10：生成小红书文案

基于 `article.md` 内容生成小红书发布文案：
- 标题（第一行，小红书自动识别为标题，**≤20字**）
- 正文（短句、emoji 点缀、话题标签）
- 输出到 `articles/<YYYYMMDD>/小红书文案.txt`

### Step 11：手动发布小红书

用户将 `小红书卡片-{01-N}.png` + `小红书文案.txt` 的内容手动发布到小红书平台。
