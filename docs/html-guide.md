# 公众号 HTML 指南

本文件定义 Step 6 生成公众号 HTML 时需要读取的工具参数、主题选择、兼容性约束和硬检查规则。

---

## 生成原则

Step 6 只负责把 `article.md` 转为可预览、可上传的 `article.html`：

- 只使用 HTML 生成所需参数，不触发上传、草稿创建等发布副作用。
- 等待用户在 Step 7 预览确认后，才进入 Step 8 创建微信草稿。
- 图片已在 Step 5 生成完毕，HTML 中必须用 `<img src="配图N.png" alt="标题">` 标签插入正文配图，不能只输出图片文件名文本。
- 标题不放在卡片内，单独作为顶部元素或由公众号后台自动处理。
- 正文列表在 HTML 中优先转为独立段落，避免微信编辑器剥离 `<ul>` / `<li>` 后破坏换行。

Step 6 从 3 个工具中等概率随机选一个主工具：`baoyu-markdown-to-html`、`gzh-design-skill`、`md2wechat`。文章已在 Step 4 完成格式化并通过回归校验，因此调用时明确使用当前 `article.md`，不重复触发格式化轮。每次 Step 6 独立随机，重开可能换工具；工具选择不写入状态文件。

选中工具后按其流程生成 `article.html`；若生成或校验失败，排除已失败工具后重新随机选工具再生成。3 个工具均已失败时，调用 `python3 scripts/workflow_state.py block articles/<YYYYMMDD-HHMMSS> step_6 --reason "3 个 HTML 生成工具均失败"` 并停止，向用户报告具体原因。不设固定降级链路，不在工具间随机切换之外另行回退。

---

## 微信 HTML 兼容性约束

公众号 HTML 必须遵守以下约束：

- 禁止使用 `<style>` 标签，所有样式必须为 inline style。
- 禁止使用 flex `gap` 属性，卡片间距用 `margin-bottom` 实现。
- 微信编辑器会剥掉 `<ul>` / `<li>` 标签，导致列表换行失效。正文中的列举内容统一使用独立 `<p>` 段落 + `margin-bottom` 控制间距，不用 `<ul><li>`。

---

## md2wechat 使用指南

### 角色定位

md2wechat 是 Step 6 三个平等随机主工具之一，与 `baoyu-markdown-to-html`、`gzh-design-skill` 等概率被选中。它不再作为"主工具失败后的备选"——失败统一走"生成原则"节定义的"重随机"逻辑（排除已失败工具重新抽取），不设固定降级链路。公众号图片上传和草稿创建统一由 Step 8 的 `baoyu-post-to-wechat` API 方法完成，详见 `docs/wechat-guide.md`。

**注意**：AI 模式（`--mode ai`）只输出设计提示词 `article.prompt.txt`，不直接产出真实 HTML。AI 读取 prompt.txt 中的样式规范（色彩、排版、卡片间距等），生成匹配该主题的 `article.html`。

### 主题选择（根据内容类型自动匹配）

| 内容类型 | 主题参数 |
|---------|---------|
| 健康科普、财经商业、科技前沿 | `--theme ocean-calm` |
| 个人成长、访谈对话 | `--theme autumn-warm` |
| 生活技能、实用技巧、教育学习方法、心理健康情绪管理 | `--theme spring-fresh` |

### 参数说明

| 参数 | 说明 | 限制 |
|------|------|------|
| `--mode ai` | 使用 AI 模式生成 HTML（内置主题样式） | 必填 |
| `--theme` | 选择主题，必须与内容类型匹配 | 必填 |
| `--title` | 文章标题 | 最多 32 字符 |
| `--author` | 作者名 | 最多 16 字符 |
| `--digest` | 文章摘要 | 最多 128 字符 |
| `--cover` | 封面图片路径 | - |
| `-o` | 输出 HTML 文件路径 | - |

### AI 模式生成 HTML

```bash
md2wechat convert articles/<YYYYMMDD-HHMMSS>/article.md \
  --mode ai \
  --theme <AI按内容类型自动匹配> \
  --title "标题" \
  --author "身心漫游" \
  --digest "摘要"
```

- `--theme` 按内容类型自动匹配（见上方主题选择表）。
- 如果图片已在 Step 5 生成，`--cover` 可填写封面路径。
- `-o` 参数不传；AI 模式仅输出 `article.prompt.txt`，不产出真实 HTML。

#### 流程

1. 运行 `md2wechat convert --mode ai` 获得 `article.prompt.txt`
2. AI 读取 prompt.txt 中的设计规范（主色调、字体、卡片间距、分割线等）
3. AI 根据这些规范自动生成 `article.html`
4. 图片替换规则见下方"输出规则"
5. `article.html` 生成完成后删除 `article.prompt.txt`，不要作为最终文章产物保留

---

## baoyu-markdown-to-html 使用指南

### 角色定位

baoyu-markdown-to-html 将 Markdown 转换为微信公众号兼容的带样式 HTML。

AI 根据内容类型自动匹配主题和色系，无需用户指定。

### 主题 & 色系选择（根据内容类型自动匹配）

| 内容类型 | 推荐主题 | 推荐色系 |
|---------|---------|---------|
| 健康科普 | modern | green / blue |
| 科技前沿 | modern | blue / sky |
| 财经商业 | default | blue / black |
| 个人成长 | grace | orange / rose |
| 访谈对话 | grace | purple / orange |
| 生活技能 | simple | green / orange |
| 教育学习方法 | grace | purple / blue |
| 心理健康情绪管理 | grace | rose / purple |

### 主题说明

| 主题 | 描述 |
|------|------|
| `default` | 经典布局，居中标题带底边，H2 白字彩色背景 |
| `grace` | 优雅风格，文字阴影、圆角卡片、精致引用 |
| `simple` | 简约现代，非对称圆角，干净留白 |
| `modern` | 现代风格，大圆角、药丸标题、宽松行高（配 `--color red` 即传统红金风格） |

### 色系预设

| 名称 | Hex | 说明 |
|------|-----|------|
| blue | #0F4C81 | 经典蓝 |
| green | #009874 | 翡翠绿 |
| vermilion | #FA5151 | 朱红 |
| purple | #92617E | 薰衣草紫 |
| sky | #55C9EA | 天蓝 |
| rose | #B76E79 | 玫瑰金 |
| orange | #D97757 | 暖橙（modern 默认） |
| red | #A93226 | 中国红 |
| black | #333333 | 石墨黑 |

### 输出规则

- **输出文件名**与输入文件名一致（`article.md` → `article.html`）。
- **输出目录**与输入文件同级。
- 如果 HTML 已存在，自动备份：`article.html.bak-YYYYMMDDHHMMSS`。
- HTML 中把 `【配图N：标题】` 占位符转换为 `<img src="配图N.png" alt="标题">` 标签，使用实际图片文件名；后续由 `baoyu-post-to-wechat` 发布脚本在草稿内容中替换为微信 CDN。

### 使用示例

```bash
# 基本转换（当前目录）
bun <skill-path>/scripts/main.ts article.md

# 指定主题和色系
bun <skill-path>/scripts/main.ts article.md --theme modern --color blue

# 指定主题、色系、标题
bun <skill-path>/scripts/main.ts article.md --theme grace --color orange --title "文章标题"

# 微信外链转底部引用
bun <skill-path>/scripts/main.ts article.md --cite
```

### 详细参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--theme <name>` | 主题：default, grace, simple, modern | default |
| `--color <name\|hex>` | 主色：预设名或 hex | 主题默认 |
| `--font-size <N>` | 字号：14-18px | 16px |
| `--title <title>` | 覆盖 frontmatter 标题 | - |
| `--cite` | 外链转底部引用 | false |
| `--keep-title` | 保留内容中的第一个标题 | false（删除） |

---

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

## HTML 图片硬检查

生成后必须执行 HTML 图片硬检查，失败即停止，不得进入预览确认：

- `article.html` 中 `<img` 数量必须等于 `article.md` 中 `【配图N：...】` 数量。
- `article.html` 中不得残留 `【配图`。
- 每个正文图片必须使用本地相对路径：`src="配图N.png"`。
- 每个正文图片必须包含 `alt`。
- 如果 `<img` 数量为 0，且 `article.md` 中存在配图标记，必须停止并修复。

推荐检查命令：

```bash
rg -n "【配图[0-9]+：" articles/<YYYYMMDD-HHMMSS>/article.md
rg -n "<img" articles/<YYYYMMDD-HHMMSS>/article.html
rg -n "【配图" articles/<YYYYMMDD-HHMMSS>/article.html
```

以上人工命令只用于定位问题，阶段门禁统一执行：

```bash
python3 scripts/validate_workflow.py html articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_6
```

校验失败不得进入 Step 7。
