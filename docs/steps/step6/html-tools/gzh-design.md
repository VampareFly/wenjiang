# gzh-design-skill 使用指南（Step 6 工具细则）

> 本文件是 `docs/steps/step6/html-guide.md` 中 `gzh-design-skill` 路径的专属细则。仅在 Step 6 随机选中 `gzh-design-skill` 后读取。

## 角色定位

`gzh-design-skill` 是 Step 6 的随机主工具之一，与 `baoyu-markdown-to-html`、`md2wechat` 等概率被选中。它将 Markdown 转为粘贴进公众号编辑器且不掉样式的 HTML，自带 6 套主题、章节编号、关键词下划线、引言卡片等特色。

## 调用方式

1. **加载 skill**：选中本工具时显式执行 `skill load gzh-design-skill`（workflow.md「按需文档路由」表 Step 6 只指向 `docs/steps/step6/html-guide.md`，不会自动加载，须手动加载）。
2. **读主题清单**：读取 `<skill_path>/references/theme-index.md` 获取主题清单（`<skill_path>` 即 `.agents/skills/gzh-design-skill`）。
3. **推荐主题**：AI 读取 `theme-index.md` 每套主题的"适用场景"列，据当前文章特征推荐最契合的一套（如教程/测评→摸鱼绿、深度分析→红白、禅意随笔→留白禅意），用户一步确认。此步取代 SKILL.md 与 theme-index.md 原生的"展示全部主题列表让用户选"流程——AI 先推荐、用户确认，不逐条展示全部主题；theme-index.md 的"不替用户定"建议在本集成流程中同样放宽。
4. **按 SKILL.md 工作流装配**：读取所选主题的 `references/theme-{标识}.md` 与 `references/common-components.md`，按 SKILL.md 的"解析 Markdown → 按配方选组件 → 装配 HTML → 校验"完整流程生成。

## 标题去重（关键）

`baoyu-markdown-to-html` 默认正文不含标题（`--keep-title false`），但 `gzh-design-skill` 会从 frontmatter 读 `title` 并写入正文（SKILL.md 规定）。而公众号后台另从 frontmatter 设标题。若 gzh-design 把标题写进正文，预览时标题会出现两次（正文标题块 + 后台标题栏）。

**注意**：gzh-design 平台红线禁止 `<h1>`/`<h2>`（仅允许 `<h3>`），标题由主题库的标题 `<section>` 组件渲染，并非 H1/H2 节点，不能用"剔除 H1/H2"去重。解决（二选一，优先前者）：

- 装配时明确指示 gzh-design 跳过标题章节（公众号后台已提供标题）；
- 生成后按主题库标题组件的可识别标记（特定 `class`/`data` 或首个 `<section>` 标题块）剔除该节点。

最终 `article.html` 正文不得含与后台重复的标题。

## 主题推荐机制

主题不绑定内容类型（区别于 baoyu/md2wechat 按内容类型匹配），AI 自由判断后推荐，用户可确认或换一套。

## 产物路径与目录

`gzh-design-skill` 原生生成 `{原文件名}_排版_{主题名}({英文标识}).html`（SKILL.md 规定），保存于**当前工作目录**，无 `-o` 参数。集成时须在 `articles/<YYYYMMDD-HHMMSS>/` 目录内执行，确保产物落在 `article.md` 同目录；生成后：

1. 重命名前先备份旧稿：`cp article.html article.html.bak-<时间戳>`（与 baoyu 行为对齐，避免重开 Step 6 丢失旧稿）；
2. 重命名：`mv {原文件名}_排版_{主题名}({英文标识}).html article.html`；
3. `{...}_预览.html` 可不生成（非必须），`<skill_path>/scripts/wrap_preview.py` 在此集成流程中跳过。

## 跳过 fix-html-images

`gzh-design-skill` 路径**不运行** `validate_workflow.py fix-html-images`。该命令会正则覆盖每个 `<img>` 的 inline style，破坏 gzh-design 主题库的图片组件样式（圆角、阴影、说明）。`baoyu-markdown-to-html` / `md2wechat` 路径保持原 `fix-html-images` 步骤不变。

## 配图标记格式转换（关键前置）

工作流的 `article.md` 使用 `【配图N：标题】` 占位符（标准约定），但 `gzh-design-skill` 只识别 Markdown 图片语法 `![说明](url)`。两者不兼容：若直接把含 `【配图N：标题】` 的 `article.md` 交给 gzh-design，它会跳过或残留占位符，导致生成的 `article.html` 缺图、`validate_workflow.py html` 因 `<img>` 数量不符而失败。

解决方案：调用 gzh-design 前，复制 `article.md` 为临时文件，用脚本（sed 或 python 一行）把 `【配图N：标题】` 批量替换为 `![标题](配图N.png)`；用临时文件驱动 gzh-design 生成，生成完删除临时文件，不污染原 `article.md`。

- 替换规则：`【配图(\d+)：(.+?)】` → `![\2](配图\1.png)`，标题作为 alt、文件名作为 src。
- 生成后仍需满足输出规则：`<img>` 数量 = `【配图N：...】` 数量、无残留 `【配图`、本地路径 `src="配图N.png"`、含 `alt`。

## 校验

生成后运行 `<skill_path>/scripts/validate_gzh_html.py article.html`，ERROR 清零且半角标点 WARNING 同样修到 0 才交付（所有 WARNING 类，含 ASCII 引号 `" '`，均须 0）。

## Step 8 上传兼容性

gzh-design 输出为纯 `<section>…</section>` 片段（SKILL.md 规定，无 `<!DOCTYPE>`/`<body>`）。Step 8 的 `baoyu-post-to-wechat` 通过扫描 `<img src="...">` 上传图片、整体粘贴 HTML 到编辑器，`<section>` 是公众号编辑器原生支持的富文本容器，应兼容。实施时首次跑通 gzh-design 路径须验证 Step 8 能正常创建草稿；若编辑器拒绝片段，在 `article.html` 外再裹一层 `<section>` 容器即可。
