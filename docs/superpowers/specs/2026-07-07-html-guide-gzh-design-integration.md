# HTML 生成指南：集成 gzh-design-skill

## 背景

项目目前 Step 6 固定使用 `baoyu-markdown-to-html` 生成公众号 HTML，`md2wechat --mode ai` 作为备选。已安装 `gzh-design-skill`（`.agents/skills/gzh-design-skill/`），需将其纳入 Step 6 作为另一个主工具。

## 变更摘要

| 文件 | 变更 |
|------|------|
| `docs/html-guide.md` | Step 6 顶部改为从 3 个工具随机选主工具 + 新增 gzh-design-skill 使用指南 + md2wechat 改为平等随机主工具 + 输出规则共享 |
| `docs/workflow.md` | Step 6 头部描述和注释从"固定使用 baoyu-markdown-to-html"改为"随机选择主工具" |

## 详细设计

### 1. Step 6 流程变更

原有"Step 6 固定使用 baoyu-markdown-to-html"改为：

1. **随机选择主工具**：AI 执行 `python3 -c "import random; print(random.choice(['baoyu-markdown-to-html','gzh-design-skill','md2wechat']))"` 从 3 个工具中等概率抽取一个。不写入 state。
2. **独立随机**：每次 Step 6 独立随机，同篇文章重开 Step 6 可能换工具。
3. **主题选择**：确认工具后，AI 按该工具自身的 theme 体系选主题——baoyu 用 `--theme/--color`，gzh-design 读 `theme-index.md`，md2wechat 用 `--theme`。根据文章气质自由推荐一套，用户一步确认。主题只在已选工具内选择，不存在跨工具主题不匹配问题。
4. **生成与校验**：按选中工具的流程生成 `article.html`，再跑该工具专属校验（仅 gzh-design 需 `validate_gzh_html.py`；baoyu/md2wechat 无专属脚本则跳过）和 workflow 的 `validate_workflow.py html`。
5. **失败重随机**：若生成或校验失败，排除已失败工具后重新执行步骤 1 随机选工具；若 3 个工具均已失败，调用 `python3 scripts/workflow_state.py block articles/<YYYYMMDD-HHMMSS> step_6 --reason "3 个 HTML 生成工具均失败"` 标记 blocked 并停止，向用户报告具体失败原因，不再尝试。不设固定降级链路。

### 2. gzh-design-skill 使用指南

新增独立章节，内容包括：

- **角色定位**：Step 6 的随机主工具之一。
- **调用方式**：
  1. 加载 gzh-design-skill（通过 `skill load gzh-design-skill`；workflow.md「按需文档路由」表 Step 6 只指向 html-guide.md，选中 gzh-design 时须显式加载，否则 AI 可能漏掉）
  2. 读取 `<skill_path>/references/theme-index.md` 获取主题清单
  3. AI 根据文章气质自由推荐最契合的主题，用户确认（取代 SKILL.md 与 theme-index.md 原生的"展示全部主题列表让用户选"流程——这里改为 AI 先推荐、用户确认，不逐条展示全部主题；theme-index.md 的"不替用户定"建议在本集成流程中同样放宽）
  4. 按 gzh-design-skill 的 SKILL.md 完整工作流执行（章节编号、关键词下划线、引言卡片等）
- **标题去重（关键）**：`baoyu-markdown-to-html` 默认 `--keep-title false`，HTML 正文不含标题；但 gzh-design-skill 会从 frontmatter 读 `title` 并写入正文（SKILL.md:50）。而 WeChat 后台另从 frontmatter 设标题（wechat-guide.md:56）。若 gzh-design 把标题写进正文，预览时标题会出现两次（正文标题块 + 后台标题栏）。**注意 gzh-design 平台红线禁止 `<h1>/<h2>`（SKILL.md:125 仅允许 `<h3>`），标题由主题库的标题 `<section>` 组件渲染，并非 H1/H2 节点**，因此不能用"剔除 H1/H2"的方式去重。**解决（二选一，优先前者）**：① 装配时明确指示 gzh-design 跳过标题章节（公众号后台已提供标题）；② 生成后按主题库标题组件的可识别标记（如特定 `class`/`data` 或首个 `<section>` 标题块）剔除该节点。无论哪种，最终 article.html 正文不得含与后台重复的标题。
- **主题推荐机制**：不绑定内容类型。AI 读取 `theme-index.md` 获取主题清单后，自由判断当前文章最适合哪套。推荐时附简短理由，用户可以确认或换一套。
- **产物路径与目录**：gzh-design-skill 原生生成 `{原文件名}_排版_{主题名}({英文标识}).html`（SKILL.md 第 90 行），保存于**当前工作目录**，且没有 `-o` 参数。集成时须在 `articles/<YYYYMMDD-HHMMSS>/` 目录内执行 gzh-design，确保产物落在 article.md 同目录；生成后手动重命名：`mv {原文件名}_排版_{主题名}({英文标识}).html article.html`。重命名前先备份旧 article.html：`cp article.html article.html.bak-<时间戳>`（与 baoyu 行为对齐，避免重开 Step 6 丢失旧稿）。`{...}_预览.html` 可不生成（非必须），`<skill_path>/scripts/wrap_preview.py` 在此集成流程中跳过。
- **跳过 fix-html-images**：gzh-design 路径**不运行** `validate_workflow.py fix-html-images`。该命令会正则覆盖每个 `<img>` 的 inline style（validate_workflow.py:256），破坏 gzh-design 主题库的图片组件样式（圆角、阴影、说明）。baoyu / md2wechat 路径保持原 `fix-html-images` 步骤不变。
- **校验**：生成后运行 `<skill_path>/scripts/validate_gzh_html.py article.html`，ERROR 清零且半角标点 WARNING 同样修到 0 才交付（所有 WARNING 类，含 ASCII 引号 `" '`，均须 0）。
- **Step 8 上传兼容性**：gzh-design 输出为纯 `<section>…</section>` 片段（SKILL.md:88，无 `<!DOCTYPE>/<body>`）。Step 8 的 `baoyu-post-to-wechat` 通过扫描 `<img src="...">` 上传图片、整体粘贴 HTML 到编辑器（wechat-guide.md:13、45），`<section>` 是公众号编辑器原生支持的富文本容器，应兼容。实施时首次跑通 gzh-design 路径须验证 Step 8 能正常创建草稿；若编辑器拒绝片段，在 article.html 外再裹一层 `<section>` 容器即可。
- **配图标记格式转换（关键前置）**：工作流的 `article.md` 使用 `【配图N：标题】` 占位符（Step 5 规范、html-guide.md:135、validate_workflow.py:37 均依赖此格式），但 gzh-design-skill 只识别 Markdown 图片语法 `![说明](url)`（SKILL.md:56、common-components.md:60）。**两者不兼容**：若直接把含 `【配图N：标题】` 的 article.md 交给 gzh-design，它会跳过或残留占位符，导致生成的 article.html 缺图、`validate_workflow.py html` 因 `<img>` 数量不符而失败。
  - 解决方案：调用 gzh-design 前，复制 article.md 为临时文件，把 `【配图N：标题】` 逐条替换为 `![标题](配图N.png)`；用临时文件驱动 gzh-design 生成，生成完删除临时文件，不污染原 article.md。
  - 替换规则：`【配图(\d+)：(.+?)】` → `![\2](配图\1.png)`，标题作为 alt、文件名作为 src。
  - 生成后仍需满足输出规则：`<img>` 数量 = `【配图N：...】` 数量、无残留 `【配图`、本地路径 `src="配图N.png"`、含 `alt`。

### 3. 输出规则统一

三个工具共享以下规则（已在 html-guide.md 中，仅确认不调整）：

- 产物文件：`article.html`，与 `article.md` 同目录
- 图片检查：`<img>` 数量 = `【配图N：...】` 数量，无残留 `【配图`，本地路径 `src="配图N.png"`，每个 `<img>` 必须含 `alt`
- 兼容性约束：无 `<style>` / 全 inline / 无 `<ul><li>`（用 `<p>` 替代）。**注意**：此条是生成阶段必须遵守的规范，`validate_workflow.py html` 仅校验 `<img>` 数量/路径/alt，不校验 `<style>`/`<ul><li>`；md2wechat `--mode ai` 自由写 HTML 时 AI 须自觉遵守，不要误以为有门禁强制。
- 门禁命令：`validate_workflow.py html` → `workflow_state.py pass`

### 4. md2wechat 角色变更

- 原：baoyu-markdown-to-html 失败后的备选（需用户明确选择）
- 改：Step 6 三个平等随机主工具之一，与 baoyu-markdown-to-html、gzh-design-skill 等概率被选中
- **取消固定降级链路**：不再有"主工具失败 → 自动降级 md2wechat"的写死逻辑，统一改为 §1.5 的"失败重随机"（排除已失败工具后重新抽取）
- md2wechat 选中时的步骤（保持现有两步流程，AI 透明处理）：
  1. 运行 `md2wechat convert article.md --mode ai --theme <自动匹配> --title "..." --author "身心漫游" --digest "摘要"`
  2. 获得 `article.prompt.txt`
  3. AI 读取 prompt.txt 中的设计规范（主色调、字体、卡片间距等），按规范生成 `article.html`
  4. 删除 `article.prompt.txt`
  5. 若 md2wechat 也失败，按 §1.5 重随机（不会再选 md2wechat，直到所有工具耗尽）

## 影响范围

| 文件 | 变更 |
|------|------|
| `docs/html-guide.md` | 重写章首决策逻辑、新增 gzh-design 节、调整 md2wechat 角色描述、输出规则部分确认不变 |
| `docs/workflow.md` | Step 6 头部文字从"固定使用 baoyu-markdown-to-html"改为"随机选择主工具"、注释同步更新 |

不涉及脚本变更（`validate_workflow.py` 等保持原样）。

## 不变约束

- Step 6 仍只生成 HTML、不上传不发稿
- 图片在 Step 5 已完成生成
- Step 7 用户预览确认的硬门禁不变