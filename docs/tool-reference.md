# 工具参考

本文件定义 Markdown 转公众号 HTML、微信图片上传、草稿上传相关工具的使用方式。

---

## md2wechat 使用指南

### 角色定位

md2wechat 是主路径工具，覆盖 HTML 生成、图片上传、草稿上传三个环节。

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
| `--draft` | 自动创建微信草稿 | 可选 |
| `--upload` | 上传图片到微信并替换 URL | 可选 |
| `-o` | 输出 HTML 文件路径 | - |

### 使用示例

#### 上传图片到微信素材库

```bash
md2wechat upload_image articles/<YYYYMMDD-HHMMSS>/cover.png
md2wechat upload_image articles/<YYYYMMDD-HHMMSS>/配图1.png
```

#### CDN 替换规则

每张图片上传成功后，必须立即记录 `md2wechat upload_image` 返回的 CDN URL，并在 `article.html` 中精确替换对应本地路径：

| 本地路径 | 替换目标 |
| --- | --- |
| `src="cover.png"` | 封面 CDN URL（如 HTML 正文中实际使用封面） |
| `src="配图1.png"` | `配图1.png` 上传后返回的 CDN URL |
| `src="配图N.png"` | 同编号配图上传后返回的 CDN URL |

替换只改 `src` 属性值，不改 `alt`、正文、标题和样式。不要把 `配图1.png` 错替换成其他编号的 CDN URL，也不要用封面 URL 替换正文配图。

替换完成后必须校验：

- `article.html` 中不得残留 `src="cover.png"` 或 `src="配图N.png"` 本地图片路径
- `<img` 数量与上传前一致
- 每个正文配图的 CDN URL 与原本的 `配图N.png` 编号一一对应
- 所有图片 URL 都应为微信返回的可访问 CDN 地址，通常以 `http://mmbiz.qpic.cn/` 或 `https://mmbiz.qpic.cn/` 开头

#### 上传草稿

草稿上传使用 `baoyu-post-to-wechat` API 方法，支持自动设置标题、摘要和作者。详见下方 `baoyu-post-to-wechat 使用指南`。

### AI 模式生成 HTML

md2wechat AI 模式产出的是设计提示词 `article.prompt.txt`，**不直接生成 HTML**。AI 读取 prompt.txt 中的样式规范后，生成匹配的 `article.html`。

#### 转换命令

```bash
md2wechat convert articles/<YYYYMMDD-HHMMSS>/article.md \
  --mode ai \
  --theme <AI按内容类型自动匹配> \
  --title "标题" \
  --author "身心漫游" \
  --digest "摘要"
```

- `--theme` 按内容类型自动匹配（见上方主题选择表）
- 如果图片已在 Step 5 生成，`--cover` 可填写封面路径
- `-o` 参数不传；AI 模式仅输出 `article.prompt.txt`，不产出真实 HTML

#### 流程

1. 运行 `md2wechat convert --mode ai` 获得 `article.prompt.txt`
2. AI 读取 prompt.txt 中的设计规范（主色调、字体、卡片间距、分割线等）
3. AI 根据这些规范自动生成 `article.html`
4. HTML 中必须把正文里的 `【配图N：标题】` 占位符替换为本地图片标签：`<img src="配图N.png" alt="标题" style="width:100%;...">`
5. 图片路径使用相对路径和实际文件名（如 `配图1.png`），不要只保留文件名文本，也不要继续保留 `【配图N：标题】` 占位符；后续上传后再替换为 CDN 地址
6. `article.html` 生成完成后删除 `article.prompt.txt`，不要作为最终文章产物保留

### 工作流程

1. **生成阶段**：使用 `md2wechat convert --mode ai` 生成设计提示词，AI 据此生成 HTML
2. **预览阶段**：用户打开 article.html 预览效果
3. **上传图片**：逐张执行 `md2wechat upload_image`，记录返回的 CDN URL，按文件名一一替换 `article.html` 中对应 `<img src="...">`，并校验无本地图片路径残留
4. **上传草稿**：使用 `baoyu-post-to-wechat` API 方法，自动设置标题、摘要和作者
5. **后台发布**：在微信公众号后台「内容管理」→「草稿箱」中核对后发布

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

- **输出文件名**与输入文件名一致（`article.md` → `article.html`）
- **输出目录**与输入文件同级
- 如果 HTML 已存在，自动备份：`article.html.bak-YYYYMMDDHHMMSS`
- HTML 中把 `【配图N：标题】` 占位符转换为 `<img src="配图N.png" alt="标题">` 标签，使用实际图片文件名，后续上传后替换为 CDN 地址

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

## baoyu-format-markdown 使用指南

Step 4 自动调用 `/baoyu-format-markdown` skill 检查并格式化 `article.md`：

- 无需用户确认，直接执行
- **直接选择「优化格式」模式，跳过 skill 内的模式选择提问**
- **格式校验后，用格式化内容覆盖 `article.md`**
- 删除 `article-formatted.md` 中间文件，保持文章目录中唯一 `article.md`
- 修复 CJK/英文间距、标点符号等排版问题
- 后续步骤全部基于覆盖后的 `article.md` 操作

---

## baoyu-post-to-wechat 使用指南

Step 9 使用 `baoyu-post-to-wechat` 的 API 方法上传草稿到微信公众号，支持自动设置标题、摘要、作者等元数据。

### 前置条件

- 微信公众号 API 凭据已配置（`~/.baoyu-skills/.env` 中设置 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`）
- 本机 IP 已加入微信公众号后台的 IP 白名单

### 使用方式

```bash
bun ~/.agents/skills/baoyu-post-to-wechat/scripts/wechat-api.ts \
  articles/<YYYYMMDD-HHMMSS>/article.html \
  --theme default \
  --title "文章标题" \
  --summary "文章摘要" \
  --author "作者名" \
  --cover articles/<YYYYMMDD-HHMMSS>/cover.png
```

### 元数据来源

| 字段 | 优先级 |
|------|--------|
| 标题 | CLI `--title` → frontmatter `title` → 自动生成 |
| 摘要 | CLI `--summary` → frontmatter `description` → 自动生成 |
| 作者 | CLI `--author` → EXTEND.md `default_author` |
| 封面 | CLI `--cover` → frontmatter `cover` → `imgs/cover.png` → 首张内联图 |

### 输出

上传成功后返回 `media_id`，需记录到 `公众号草稿信息.txt`。

---

## 微信 HTML 兼容性约束

公众号 HTML 必须遵守以下约束：

- 禁止使用 `<style>` 标签，所有样式必须为 inline style。
- 禁止使用 flex `gap` 属性，卡片间距用 `margin-bottom` 实现。
- 微信编辑器会剥掉 `<ul>` / `<li>` 标签，导致列表换行失效。正文中的列举内容统一使用独立 `<p>` 段落 + `margin-bottom` 控制间距，不用 `<ul><li>`。

---

## HTML 生成阶段规则

生成公众号 HTML 时遵循以下规则：

- 生成阶段只使用基本参数，**不加 `--draft` 和 `--upload`**
- 等待用户预览确认后，再执行上传命令
- 随机选择方案：`baoyu-markdown-to-html`（60%）/ `md2wechat --mode ai`（40%），不需要用户指定
- 图片已在生图步骤生成完毕，HTML 中必须用 `<img src="配图N.png" alt="标题">` 标签插入正文配图，不能只输出图片文件名文本
- 生成后检查 HTML：`<img` 数量必须等于 `article.md` 中 `【配图N：...】` 数量，且 HTML 中不得残留 `【配图`
- 标题不放在卡片内，单独作为顶部元素或由公众号后台自动处理
- 正文列表在 HTML 中优先转为独立段落，避免微信编辑器剥离 `<ul>` / `<li>` 后破坏换行

---

## 公众号草稿信息文件格式

使用 `baoyu-post-to-wechat` API 方法上传草稿后，必须在文章目录输出 `公众号草稿信息.txt`，内容包括：

```text
草稿 media_id：{media_id}
标题：{从 frontmatter 提取}
作者：{作者名}
摘要：{摘要}
推荐话题：{3-5 个，基于文章内容和微信搜一搜高频词}

后台操作说明：
草稿已自动设置标题、作者和摘要，请在微信公众号后台「内容管理」→「草稿箱」中核对后发布。
```
