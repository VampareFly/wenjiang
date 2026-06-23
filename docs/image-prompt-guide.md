# 图片提示词指南

本文件定义 Step 2 生成 `cover_prompt.md` 时需要遵守的提示词格式、配图标记和安全规范。只有生成文章配图提示词时才需要读取本文件。

---

## cover_prompt.md 格式规范

### 配图标记规范

正文中标记配图位置：

```text
【配图1：光照抑制食欲通路】
【配图2：饥饿素节律】
```

- 编号与 `cover_prompt.md` 中的提示词 section 一一对应。
- 封面不计入编号。
- `article.md` 中必须包含正文配图标记：`【配图N：标题】`。
- `cover_prompt.md` 中每个正文配图 section 必须与 `article.md` 中的配图标记一一对应。
- 配图编号必须连续，从 `配图1` 开始，不得跳号。
- 配图标题必须完全一致，例如 `article.md` 中的 `【配图1：脂肪膜结构】` 对应 `cover_prompt.md` 中的 `## 【配图1：脂肪膜结构】`。
- 如果 `article.md` 中没有任何正文配图标记，不得进入 Step 4，必须先补充配图标记。

### cover_prompt.md 文件格式

```md
# 封面图提示词

## 英文提示词（Codex 文生图使用）
[英文提示词，适合封面横向 16:9，主体完整居中]

## 中文说明
[关键元素、风格、氛围说明]

---

## 【配图1：标题】

### 英文提示词（Codex 文生图使用）
[英文提示词]

### 中文说明
[内容描述、风格、配色建议]
```

- 封面+配图提示词在同一个文件。
- 每个配图一个独立 section，用 `---` 分隔。
- section 标题为 `【配图N：标题】`，与正文编号完全一致。
- 封面始终横向 16:9。

---

## 中文文字要求（强制）

图片面向中文读者，含文字的图片必须在提示词中注明中文渲染：

- 封面/一般图片含文字 → 加 `all text labels in Simplified Chinese`
- 信息图/图表类 → 加 `all chart labels, legends, and annotations in Simplified Chinese`
- 纯视觉插图（无文字）→ 不需要加
- 禁止生成含英文标注的科普/信息图

---

## 配图提示词安全规范

### 明确禁止的词汇类

- 人体器官/解剖学写实描述 → 改为抽象/隐喻表达。
- 医疗场景写实 → 改为 medical illustration / diagram / scientific visualization。
- 真实人物姓名/肖像 → 改为泛化描述（a scientist in lab coat）。
- 疾病症状写实 → 改为 cellular process / biological mechanism。
- 血液/创伤/暴力暗示。
- 药品/毒品/成瘾物质。
- 年龄暗示的孤立描述 → 改为 diverse age group。

### 具体改写规则

- 科学内容统一加 safety modifier：medical illustration / diagram / infographic。
- 解剖学概念使用 schematic / cross-section / abstract representation。
- 人体部位使用 silhouette / outline / icon 风格。
- 健康数据使用 chart / graph / data visualization。
- 提示词偏 educational / textbook-style / classroom diagram。
- 正文配图优先 isometric view / flat illustration。

---

## 封面图特殊要求

封面是公众号文章的第一印象，应以视觉冲击力为主，减少文字干扰：

- **优先纯视觉构图**：用画面传达核心概念，不依赖文字解释。
- **避免堆砌文字元素**：封面不要包含标题、说明性文字、标签列表等。如果必须有文字，控制在 1-3 个关键词以内。
- **主体居中完整**：适合 16:9 横向构图，主体在画面中央，四周留白。
- **风格统一**：与正文配图保持一致的色调和风格。

---

## 提示词生成检查清单（生成 cover_prompt.md 后必须逐项核对）

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | 封面提示词格式 | 包含 `## 英文提示词` 和 `## 中文说明` 两个部分 |
| 2 | 封面中文渲染指令 | 如果封面可能含文字，末尾必须加 `all text labels in Simplified Chinese` |
| 3 | 封面文字数量 | 优先无文字构图；如有文字，控制在 1-3 个关键词 |
| 4 | 正文配图中文渲染 | 信息图/图表类必须加 `all chart labels, legends, and annotations in Simplified Chinese` |
| 5 | 配图编号对应 | `cover_prompt.md` 中的 `【配图N：标题】` 与 `article.md` 完全一致 |
| 6 | 配图编号连续 | 从 `配图1` 开始，不得跳号 |
| 7 | 安全规范 | 无真实人物姓名、无解剖写实、无医疗场景写实 |
| 8 | 风格一致性 | 封面与正文配图风格统一 |

**常见遗漏**：
- 封面忘记加 `all text labels in Simplified Chinese` → 生成英文文字
- 信息图使用 `all text labels` 而非 `all chart labels, legends, and annotations` → 标注不完整
- 封面堆砌过多文字元素 → 视觉杂乱，缺乏冲击力
