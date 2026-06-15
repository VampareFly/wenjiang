# 工具参考

本文件定义 Markdown 转公众号 HTML、微信草稿上传相关工具的使用方式。

---

## md2wechat 使用指南

### 角色定位

md2wechat 仅作为 HTML 生成的可选工具之一。公众号图片上传和草稿创建统一由 `baoyu-post-to-wechat` API 方法完成。

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
5. 图片路径使用相对路径和实际文件名（如 `配图1.png`），不要只保留文件名文本，也不要继续保留 `【配图N：标题】` 占位符；后续由 `baoyu-post-to-wechat` 发布脚本上传并替换为微信 CDN
6. `article.html` 生成完成后删除 `article.prompt.txt`，不要作为最终文章产物保留

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
- HTML 中把 `【配图N：标题】` 占位符转换为 `<img src="配图N.png" alt="标题">` 标签，使用实际图片文件名；后续由 `baoyu-post-to-wechat` 发布脚本在草稿内容中替换为微信 CDN

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

Step 8 使用 `baoyu-post-to-wechat` 的 API 方法上传草稿到微信公众号，支持自动上传正文图片、上传封面素材，并设置标题、摘要、作者等元数据。

本项目传入 Step 7 已预览确认的 `article.html`，而不是重新传 `article.md` 让发布脚本渲染。这样可以保留 Step 6 生成并确认过的版式。`wechat-api.ts` 支持 HTML 输入，会读取同目录 `article.md` 的 frontmatter，并扫描 HTML 中的 `<img src="...">` 处理本地正文图片。

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

### 图片上传与替换

发布脚本会在创建草稿前自动处理图片：

- 扫描 `article.html` 中的 `<img src="配图N.png">` 本地正文图片
- 调用微信 `media/uploadimg` 上传正文图片，得到微信 CDN URL，并写入即将提交到草稿箱的 HTML 内容
- 调用微信 `material/add_material` 上传封面图，得到草稿 `thumb_media_id`
- 同一张本地图片只上传一次，正文图片和封面素材按用途分别处理

本项目只关心最终草稿箱内容，因此不要求把 CDN URL 回写到本地 `article.html`。本地 `article.html` 可继续保留 `src="配图N.png"`，用于预览和复查。

### 元数据来源

| 字段 | 优先级 |
|------|--------|
| 标题 | CLI `--title` → frontmatter `title` → 自动生成 |
| 摘要 | CLI `--summary` → frontmatter `description` → 自动生成 |
| 作者 | CLI `--author` → EXTEND.md `default_author` |
| 封面 | CLI `--cover` → frontmatter `cover` → `imgs/cover.png` → 首张内联图 |

### 输出

草稿创建成功后返回草稿 `media_id`，需记录到 `公众号草稿信息.txt`。

---

## 微信 HTML 兼容性约束

公众号 HTML 必须遵守以下约束：

- 禁止使用 `<style>` 标签，所有样式必须为 inline style。
- 禁止使用 flex `gap` 属性，卡片间距用 `margin-bottom` 实现。
- 微信编辑器会剥掉 `<ul>` / `<li>` 标签，导致列表换行失效。正文中的列举内容统一使用独立 `<p>` 段落 + `margin-bottom` 控制间距，不用 `<ul><li>`。

---

## HTML 生成阶段规则

生成公众号 HTML 时遵循以下规则：

- 生成阶段只使用 HTML 生成所需的基本参数，不触发上传、草稿创建等发布副作用
- 等待用户预览确认后，再执行 `baoyu-post-to-wechat` API 发布命令
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
