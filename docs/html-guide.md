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

工具选择由 AI 自动完成：`baoyu-markdown-to-html`（60%）/ `md2wechat --mode ai`（40%），不需要用户指定。

---

## 微信 HTML 兼容性约束

公众号 HTML 必须遵守以下约束：

- 禁止使用 `<style>` 标签，所有样式必须为 inline style。
- 禁止使用 flex `gap` 属性，卡片间距用 `margin-bottom` 实现。
- 微信编辑器会剥掉 `<ul>` / `<li>` 标签，导致列表换行失效。正文中的列举内容统一使用独立 `<p>` 段落 + `margin-bottom` 控制间距，不用 `<ul><li>`。

---

## md2wechat 使用指南

### 角色定位

md2wechat 仅作为 HTML 生成的可选工具之一。公众号图片上传和草稿创建统一由 Step 8 的 `baoyu-post-to-wechat` API 方法完成，详见 `docs/wechat-guide.md`。

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
