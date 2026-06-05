# cover_prompt.md 格式规范

## 配图标记规范

正文中需配图的位置用编号标记：

```
【配图1：光照抑制食欲通路】
【配图2：饥饿素节律】
```

- 编号与 `cover_prompt.md` 中的提示词 section 一一对应
- 封面不计入编号

## cover_prompt.md 文件格式

```
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

- 封面+配图提示词在同一个文件
- 每个配图一个独立 section，用 `---` 分隔
- section 标题为 `【配图N：标题】`，与正文编号完全一致
- 封面始终横向 16:9

## 配图提示词安全规范

### 明确禁止的词汇类
- 人体器官/解剖学写实描述 → 改为抽象/隐喻表达
- 医疗场景写实 → 改为 medical illustration / diagram / scientific visualization
- 真实人物姓名/肖像 → 改为泛化描述（a scientist in lab coat）
- 疾病症状写实 → 改为 cellular process / biological mechanism
- 血液/创伤/暴力暗示
- 药品/毒品/成瘾物质
- 年龄暗示的孤立描述 → 改为 diverse age group

### 具体改写规则
- 科学内容统一加 safety modifier：medical illustration / diagram / infographic
- 解剖学概念使用 schematic / cross-section / abstract representation
- 人体部位使用 silhouette / outline / icon 风格
- 健康数据使用 chart / graph / data visualization
- 提示词偏 educational / textbook-style / classroom diagram
- 正文配图优先 isometric view / flat illustration
