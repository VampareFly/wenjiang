# 图片提示词指南

本文件定义 Step 2 生成 `cover_prompt.md` 时需要遵守的提示词格式、配图标记和安全规范。只有生成文章配图提示词时才需要读取本文件。

---

## cover_prompt.md 格式规范

### 封面与头条三图规格规范

1. **公众号主封面 (`cover.png`)**：
   - 目标比例为 `2.35:1`，推荐生成尺寸不低于 `1800×766`，最低可按 `900×383` 设计。
   - 提示词必须包含：`WeChat Official Account article cover, primary crop 2.35:1`。
   - 封面优先无文字构图；如果必须有文字，文字要短、清晰，不要靠近画面边缘。
2. **正文配图 (`配图1~N.png`)**：
   - 默认使用横向 `16:9`，以科学机制图解、流程说明、解剖示意或信息图为主。
3. **今日头条专属爆款三图封面 (`toutiao-cover-1~3.png`)**：
   - 比例固定为 `16:9` 横图（写实摄影风格，具有极强的情绪张力与视觉反差）；
   - **头条封面 1（痛点共鸣）**：生活化写实摄影，直击读者日常痛点与情绪纠结（例：深夜面对高热量炸鸡甜食的食欲挣扎）；
   - **头条封面 2（反差对比）**：高反差食物或行为并排对比（例：超加工零食 vs 鲜嫩深绿高纤维蔬菜与蛋白质）；
   - **头条封面 3（科学赋能）**：阳光明媚的清晨户外、充满活力的健康生活或名医研究成果。

### 配图标记规范

正文中标记配图位置：

```text
【配图1：光照抑制食欲通路】
【配图2：饥饿素节律】
```

- 编号与 `cover_prompt.md` 中的正文配图 section 一一对应。
- 封面与头条三图不计入正文配图编号。
- `article.md` 中必须包含正文配图标记：`【配图N：标题】`。
- `cover_prompt.md` 中每个正文配图 section 必须与 `article.md` 中的配图标记一一对应。
- 配图编号必须连续，从 `配图1` 开始，不得跳号。
- 配图标题必须完全一致，例如 `article.md` 中的 `【配图1：脂肪膜结构】` 对应 `cover_prompt.md` 中的 `## 【配图1：脂肪膜结构】`。
- 如果 `article.md` 中没有任何正文配图标记，不得进入 Step 4，必须先补充配图标记。

### cover_prompt.md 文件格式

```md
# 封面图提示词

## 英文提示词（Codex 文生图使用）
[英文提示词，适合公众号封面 2.35:1 主裁剪]

## 中文说明
[关键元素、风格、氛围说明]

---

## 【配图1：标题】

### 英文提示词（Codex 文生图使用）
[英文提示词，16:9 科学图解]

### 中文说明
[内容描述、风格、配色建议]

---

# 今日头条专属爆款三图封面提示词

## 【头条封面1：扎心痛点场景】
### 英文提示词
[16:9 写实摄影，直击现实生活痛点/情绪冲突]
### 中文说明
[痛点场景说明]

---

## 【头条封面2：关键食物反差对比】
### 英文提示词
[16:9 写实摄影，左右高反差食物或行为对比]
### 中文说明
[反差细节说明]

---

## 【头条封面3：科学证据与正向活力改变】
### 英文提示词
[16:9 写实摄影，阳光明媚/活力健康/科学突破]
### 中文说明
[正向赋能说明]
```

- 包含公众号封面、正文配图与今日头条专属三图封面的完整提示词。
- 每个配图和头条封面一个独立 section，用 `---` 分隔。


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

## 生成后检查清单

| 检查项 | 要求 |
|--------|------|
| 封面比例 | 主封面按 `2.35:1` 设计，不再使用 `16:9` 作为公众号图文封面目标比例 |
| 封面构图 | 画面应优先服务 `2.35:1` 横向封面美感；关键文字不要贴边 |
| 封面中文渲染 | 含文字时末尾加 `all text labels in Simplified Chinese`；优先无文字构图 |
| 正文配图中文渲染 | 信息图/图表类加 `all chart labels, legends, and annotations in Simplified Chinese` |
| 配图编号 | 与 `article.md` 一致，从 `配图1` 连续编号 |
| 安全规范 | 无真实人物姓名、无解剖写实、无医疗场景写实 |
