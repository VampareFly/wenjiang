# gzh-design-skill 集成到 Step 6 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 gzh-design-skill 作为 Step 6 的随机主工具之一集成进 `docs/html-guide.md` 与 `docs/workflow.md`，支持从 3 个工具随机选主、主题按工具内选择、失败重随机、共享输出规则。

**Architecture:** 仅修改两个文档（不改动脚本）。`html-guide.md` 改写章首决策逻辑、新增 gzh-design 节、改写 md2wechat 角色、补 fix-html-images 跳过说明；`workflow.md` 同步 Step 6 头部描述。设计依据见 `docs/superpowers/specs/2026-07-07-html-guide-gzh-design-integration.md`。

**Tech Stack:** Markdown 文档、git

## Global Constraints

- 随机选择从 3 个工具等概率：`baoyu-markdown-to-html` / `gzh-design-skill` / `md2wechat`
- 工具选择不写入 `workflow-state.json`
- 每次 Step 6 独立随机（重开可换工具）
- 主题只在已选工具内选，不跨工具匹配
- 失败重随机（排除已失败工具），3 个均失败调用 `workflow_state.py block step_6`
- gzh-design 配图：`【配图N：标题】` → `![标题](配图N.png)` 临时副本转换，不污染原 article.md
- gzh-design 标题去重：装配跳过标题块或用可识别标记剔除 `<section>` 标题节点
- gzh-design 跳过 `fix-html-images`；baoyu / md2wechat 保持
- gzh-design 校验：`validate_gzh_html.py` ERROR=0 且 WARNING=0
- 产物统一 `article.html`，与 `article.md` 同目录
- 不改动 `validate_workflow.py` 等脚本

---

### Task 1：改写 html-guide.md 章首"生成原则"决策逻辑

**Files:**
- Modify: `docs/html-guide.md:17-19`（"生成原则"节末尾两条）

**Interfaces:**
- Consumes: 无
- Produces: 新的章首决策文案，供 Task 2/3/4 与后续执行引用

- [ ] **Step 1：替换第 17 行（固定使用 → 随机选主）**

将：
```
Step 6 固定使用 `baoyu-markdown-to-html`，不随机选择工具。文章已在 Step 4 完成格式化并通过回归校验，因此调用时明确使用当前 `article.md`，不重复触发格式化轮。
```
替换为：
```
Step 6 从 3 个工具中等概率随机选一个主工具：`baoyu-markdown-to-html`、`gzh-design-skill`、`md2wechat`。文章已在 Step 4 完成格式化并通过回归校验，因此调用时明确使用当前 `article.md`，不重复触发格式化轮。每次 Step 6 独立随机，重开可能换工具；工具选择不写入状态文件。
```

- [ ] **Step 2：替换第 19 行（失败停止 + 用户选备选 → 失败重随机）**

将：
```
如果 `baoyu-markdown-to-html` 执行失败，先报告具体错误并停止。只有用户明确选择后，才可把 `md2wechat --mode ai` 作为备选；不得自动降级，也不得在两个工具之间随机切换。
```
替换为：
```
选中工具后按其流程生成 `article.html`；若生成或校验失败，排除已失败工具后重新随机选工具再生成。3 个工具均已失败时，调用 `python3 scripts/workflow_state.py block articles/<YYYYMMDD-HHMMSS> step_6 --reason "3 个 HTML 生成工具均失败"` 并停止，向用户报告具体原因。不设固定降级链路，不在工具间随机切换之外另行回退。
```

- [ ] **Step 3：验证旧文案已移除、新文案存在**

Run:
```bash
grep -n "固定使用" docs/html-guide.md || echo "OK: 旧文案已移除"
grep -n "从 3 个工具中等概率随机选" docs/html-guide.md
grep -n "重新随机选工具" docs/html-guide.md
```
Expected: 第一行无输出（显示 OK）；后两行各命中 1 处。

- [ ] **Step 4：提交**

```bash
git add docs/html-guide.md
git commit -m "docs(html-guide): Step 6 改为 3 工具随机选主，失败重随机"
```

---

### Task 2：html-guide.md 新增"gzh-design-skill 使用指南"节

**Files:**
- Modify: `docs/html-guide.md`（在"## baoyu-markdown-to-html 使用指南"节之前插入新节；即当前第 78 行 `### 角色定位` baoyu 节之前，或"详细参数"节（第 153-162 行）之后、"## HTML 图片硬检查"之前。推荐插在 baoyu 节的"详细参数"小节之后、"## HTML 图片硬检查"之前）

**Interfaces:**
- Consumes: Task 1 的随机选主逻辑
- Produces: gzh-design 完整使用指南，供 Step 6 执行时调用

- [ ] **Step 1：在"## HTML 图片硬检查"标题前插入以下完整新节**

在 `docs/html-guide.md` 中找到 `## HTML 图片硬检查`（当前第 166 行）这一行，在其**前面**插入以下内容（保留原 `---` 分隔与后续内容）：

```markdown
## gzh-design-skill 使用指南

### 角色定位

`gzh-design-skill` 是 Step 6 的随机主工具之一，与 `baoyu-markdown-to-html`、`md2wechat` 等概率被选中。它将 Markdown 转为粘贴进公众号编辑器且不掉样式的 HTML，自带 6 套主题、章节编号、关键词下划线、引言卡片等特色。

### 调用方式

1. **加载 skill**：选中本工具时显式执行 `skill load gzh-design-skill`（workflow.md「按需文档路由」表 Step 6 只指向本文件，不会自动加载，须手动加载）。
2. **读主题清单**：读取 `<skill_path>/references/theme-index.md` 获取主题清单（`<skill_path>` 即 `.agents/skills/gzh-design-skill`）。
3. **推荐主题**：AI 根据文章气质自由推荐最契合的一套主题，用户一步确认。此步取代 SKILL.md 与 theme-index.md 原生的"展示全部主题列表让用户选"流程——AI 先推荐、用户确认，不逐条展示全部主题；theme-index.md 的"不替用户定"建议在本集成流程中同样放宽。
4. **按 SKILL.md 工作流装配**：读取所选主题的 `references/theme-{标识}.md` 与 `references/common-components.md`，按 SKILL.md 的"解析 Markdown → 按配方选组件 → 装配 HTML → 校验"完整流程生成。

### 标题去重（关键）

`baoyu-markdown-to-html` 默认正文不含标题（`--keep-title false`），但 `gzh-design-skill` 会从 frontmatter 读 `title` 并写入正文（SKILL.md 规定）。而公众号后台另从 frontmatter 设标题。若 gzh-design 把标题写进正文，预览时标题会出现两次（正文标题块 + 后台标题栏）。

**注意**：gzh-design 平台红线禁止 `<h1>`/`<h2>`（仅允许 `<h3>`），标题由主题库的标题 `<section>` 组件渲染，并非 H1/H2 节点，不能用"剔除 H1/H2"去重。解决（二选一，优先前者）：

- 装配时明确指示 gzh-design 跳过标题章节（公众号后台已提供标题）；
- 生成后按主题库标题组件的可识别标记（特定 `class`/`data` 或首个 `<section>` 标题块）剔除该节点。

最终 `article.html` 正文不得含与后台重复的标题。

### 主题推荐机制

不绑定内容类型。AI 读取 `theme-index.md` 获取主题清单后，自由判断当前文章最适合哪套，推荐时附简短理由，用户可确认或换一套。

### 产物路径与目录

`gzh-design-skill` 原生生成 `{原文件名}_排版_{主题名}({英文标识}).html`（SKILL.md 规定），保存于**当前工作目录**，无 `-o` 参数。集成时须在 `articles/<YYYYMMDD-HHMMSS>/` 目录内执行，确保产物落在 `article.md` 同目录；生成后：

1. 重命名前先备份旧稿：`cp article.html article.html.bak-<时间戳>`（与 baoyu 行为对齐，避免重开 Step 6 丢失旧稿）；
2. 重命名：`mv {原文件名}_排版_{主题名}({英文标识}).html article.html`；
3. `{...}_预览.html` 可不生成（非必须），`<skill_path>/scripts/wrap_preview.py` 在此集成流程中跳过。

### 跳过 fix-html-images

`gzh-design-skill` 路径**不运行** `validate_workflow.py fix-html-images`。该命令会正则覆盖每个 `<img>` 的 inline style，破坏 gzh-design 主题库的图片组件样式（圆角、阴影、说明）。`baoyu-markdown-to-html` / `md2wechat` 路径保持原 `fix-html-images` 步骤不变。

### 配图标记格式转换（关键前置）

工作流的 `article.md` 使用 `【配图N：标题】` 占位符（Step 5 规范、html-guide.md 生成原则、validate_workflow.py 均依赖此格式），但 `gzh-design-skill` 只识别 Markdown 图片语法 `![说明](url)`。两者不兼容：若直接把含 `【配图N：标题】` 的 `article.md` 交给 gzh-design，它会跳过或残留占位符，导致生成的 `article.html` 缺图、`validate_workflow.py html` 因 `<img>` 数量不符而失败。

解决方案：调用 gzh-design 前，复制 `article.md` 为临时文件，把 `【配图N：标题】` 逐条替换为 `![标题](配图N.png)`；用临时文件驱动 gzh-design 生成，生成完删除临时文件，不污染原 `article.md`。

- 替换规则：`【配图(\d+)：(.+?)】` → `![\2](配图\1.png)`，标题作为 alt、文件名作为 src。
- 生成后仍需满足输出规则：`<img>` 数量 = `【配图N：...】` 数量、无残留 `【配图`、本地路径 `src="配图N.png"`、含 `alt`。

### 校验

生成后运行 `<skill_path>/scripts/validate_gzh_html.py article.html`，ERROR 清零且半角标点 WARNING 同样修到 0 才交付（所有 WARNING 类，含 ASCII 引号 `" '`，均须 0）。

### Step 8 上传兼容性

gzh-design 输出为纯 `<section>…</section>` 片段（SKILL.md 规定，无 `<!DOCTYPE>`/`<body>`）。Step 8 的 `baoyu-post-to-wechat` 通过扫描 `<img src="...">` 上传图片、整体粘贴 HTML 到编辑器，`<section>` 是公众号编辑器原生支持的富文本容器，应兼容。实施时首次跑通 gzh-design 路径须验证 Step 8 能正常创建草稿；若编辑器拒绝片段，在 `article.html` 外再裹一层 `<section>` 容器即可。

---
```

- [ ] **Step 2：验证新节已插入且关键短语存在**

Run:
```bash
grep -n "## gzh-design-skill 使用指南" docs/html-guide.md
grep -n "skill load gzh-design-skill" docs/html-guide.md
grep -n "跳过 fix-html-images" docs/html-guide.md
grep -n "配图标记格式转换" docs/html-guide.md
```
Expected: 四行各命中 1 处。

- [ ] **Step 3：提交**

```bash
git add docs/html-guide.md
git commit -m "docs(html-guide): 新增 gzh-design-skill 使用指南节"
```

---

### Task 3：改写 html-guide.md 的 md2wechat 角色

**Files:**
- Modify: `docs/html-guide.md:35-37`（md2wechat 使用指南的"角色定位"段）

**Interfaces:**
- Consumes: Task 1 的随机选主逻辑
- Produces: md2wechat 作为平等随机主工具的定位说明

- [ ] **Step 1：替换 md2wechat"角色定位"段（第 35-37 行）**

将：
```
### 角色定位

md2wechat 仅作为主工具失败后、由用户明确选择的备选。它不参与自动工具选择。公众号图片上传和草稿创建统一由 Step 8 的 `baoyu-post-to-wechat` API 方法完成，详见 `docs/wechat-guide.md`。
```
替换为：
```
### 角色定位

md2wechat 是 Step 6 三个平等随机主工具之一，与 `baoyu-markdown-to-html`、`gzh-design-skill` 等概率被选中。它不再作为"主工具失败后的备选"——失败统一走 Task 1 定义的"重随机"逻辑（排除已失败工具重新抽取），不设固定降级链路。公众号图片上传和草稿创建统一由 Step 8 的 `baoyu-post-to-wechat` API 方法完成，详见 `docs/wechat-guide.md`。
```

- [ ] **Step 2：验证旧备选措辞已移除**

Run:
```bash
grep -n "仅作为主工具失败后" docs/html-guide.md || echo "OK: 旧备选措辞已移除"
grep -n "三个平等随机主工具之一" docs/html-guide.md
```
Expected: 第一行无输出（OK）；第二行命中 1 处。

- [ ] **Step 3：提交**

```bash
git add docs/html-guide.md
git commit -m "docs(html-guide): md2wechat 改为平等随机主工具，取消固定降级"
```

---

### Task 4：html-guide.md 输出规则补 fix-html-images 跳过说明

**Files:**
- Modify: `docs/html-guide.md:184`（"HTML 图片硬检查"节首段，或在该节开头补一句）

**Interfaces:**
- Consumes: Task 2 的"gzh-design 跳过 fix-html-images"决定
- Produces: 明确各工具 fix-html-images 执行差异，避免实施时误用

- [ ] **Step 1：在"## HTML 图片硬检查"节开头补一句说明**

在 `docs/html-guide.md` 的 `## HTML 图片硬检查` 标题下方、原"生成后必须执行 HTML 图片硬检查"句之前，插入：

```
> **fix-html-images 执行差异**：`baoyu-markdown-to-html` 与 `md2wechat` 路径在下方门禁前先运行 `validate_workflow.py fix-html-images`；`gzh-design-skill` 路径跳过此步（其图片组件样式由主题库决定，fix-html-images 会覆盖破坏，详见「gzh-design-skill 使用指南」）。
```

- [ ] **Step 2：验证说明已插入**

Run:
```bash
grep -n "fix-html-images 执行差异" docs/html-guide.md
```
Expected: 命中 1 处。

- [ ] **Step 3：提交**

```bash
git add docs/html-guide.md
git commit -m "docs(html-guide): 输出规则补 gzh-design 跳过 fix-html-images 说明"
```

---

### Task 5：改写 workflow.md Step 6 头部

**Files:**
- Modify: `docs/workflow.md:183-187`（Step 6 描述与命令块注释）

**Interfaces:**
- Consumes: Task 1 的随机选主逻辑、Task 2 的 gzh-design 调用方式
- Produces: workflow.md Step 6 与 html-guide.md 一致的随机选主描述

- [ ] **Step 1：替换第 183 行描述**

将：
```
按 `docs/html-guide.md` 固定使用 `baoyu-markdown-to-html`：
```
替换为：
```
按 `docs/html-guide.md` 从 3 个工具随机选主工具生成公众号 HTML：
```

- [ ] **Step 2：替换第 187 行注释**

将：
```
# 调用 baoyu-markdown-to-html
```
替换为：
```
# 随机选主工具后按其流程调用（baoyu-markdown-to-html / gzh-design-skill / md2wechat）
```

- [ ] **Step 3：验证 workflow.md 旧措辞已移除**

Run:
```bash
grep -n "固定使用" docs/workflow.md || echo "OK: 旧措辞已移除"
grep -n "随机选主工具后按其流程调用" docs/workflow.md
```
Expected: 第一行无输出（OK）；第二行命中 1 处。

- [ ] **Step 4：提交**

```bash
git add docs/workflow.md
git commit -m "docs(workflow): Step 6 头部改为随机选主工具描述"
```

---

### Task 6：跨文档一致性校验

**Files:**
- Read: `docs/html-guide.md`、`docs/workflow.md`

**Interfaces:**
- Consumes: Task 1-5 的全部修改
- Produces: 确认两份文档无残留旧逻辑、关键新逻辑齐备

- [ ] **Step 1：确认两份文档均无"固定使用"残留**

Run:
```bash
grep -rn "固定使用\|自动降级\|仅作为主工具失败后" docs/html-guide.md docs/workflow.md || echo "OK: 无旧逻辑残留"
```
Expected: 输出 "OK: 无旧逻辑残留"。

- [ ] **Step 2：确认关键新逻辑齐备**

Run:
```bash
grep -c "随机" docs/html-guide.md docs/workflow.md
grep -n "gzh-design-skill 使用指南" docs/html-guide.md
grep -n "三个平等随机主工具之一" docs/html-guide.md
grep -n "重新随机选工具" docs/html-guide.md
```
Expected: 各文件随机相关命中 ≥2；后三行各命中 1 处。

- [ ] **Step 3：提交（若本步仅校验无改动则跳过提交）**

若 Step 1/2 均无问题且无文件改动，无需提交；若有微调，按对应文件补提交。

---

## 自审（Spec 覆盖核对）

| Spec 要求 | 对应 Task |
|-----------|-----------|
| 3 工具等概率随机 | Task 1 (§1.1)、Task 5 |
| 不写入 state、独立随机 | Task 1 (§1.2) |
| 主题按工具内选 | Task 2 (§调用方式/主题推荐机制) |
| 失败重随机、3 均失败 block | Task 1 (§1.5)、Task 5 |
| gzh-design skill load 分叉 | Task 2 (§调用方式 1) |
| 标题去重 | Task 2 (§标题去重) |
| 产物路径/目录/备份/跳过 preview | Task 2 (§产物路径与目录) |
| 跳过 fix-html-images | Task 2 (§跳过 fix-html-images)、Task 4 |
| 配图标记格式转换 | Task 2 (§配图标记格式转换) |
| 校验 ERROR+WARNING=0 | Task 2 (§校验) |
| Step 8 兼容性 | Task 2 (§Step 8 上传兼容性) |
| md2wechat 平等随机主工具 | Task 3 |
| workflow.md 同步 | Task 5 |
| 一致性校验 | Task 6 |
