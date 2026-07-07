# HTML 生成指南：集成 gzh-design-skill

## 背景

项目目前 Step 6 固定使用 `baoyu-markdown-to-html` 生成公众号 HTML，`md2wechat --mode ai` 作为备选。已安装 `gzh-design-skill`（`.agents/skills/gzh-design-skill/`），需将其纳入 Step 6 作为另一个主工具。

## 变更摘要

- `docs/html-guide.md`：Step 6 顶部改为随机选择主工具 + 新增 gzh-design-skill 使用指南 + md2wechat 改为自动降级 + 输出规则共享

## 详细设计

### 1. Step 6 流程变更

原有"Step 6 固定使用 baoyu-markdown-to-html"改为：

1. **随机选择主工具**：AI 从 `baoyu-markdown-to-html` 和 `gzh-design-skill` 中均等概率随机抽取一个。
2. **记录选择**：选择结果写入 `workflow-state.json` 的当前 step 元数据（`tool` 字段）。
3. **独立随机**：每次 Step 6 独立随机，同篇文章重开 Step 6 可能换工具。
4. **自动降级**：选中主工具执行失败（报错或校验不通过）时，自动降级到 `md2wechat --mode ai`，不再询问。
5. **主题推荐**：选定工具后，AI 读该工具的 theme 体系，根据文章气质自由推荐一套主题，用户一步确认。

### 2. gzh-design-skill 使用指南

新增独立章节，内容包括：

- **角色定位**：Step 6 的随机主工具之一。
- **调用方式**：
  1. 加载 gzh-design-skill
  2. 读取 `<skill_path>/references/theme-index.md` 获取主题清单
  3. AI 根据文章气质自由推荐最契合的主题，用户确认
  4. 按 gzh-design-skill 的 SKILL.md 完整工作流执行（章节编号、关键词下划线、引言卡片等）
- **主题推荐机制**：不绑定内容类型。AI 读完 6 套主题（摸鱼绿/红白/石墨极简/留白禅意/摸鱼票据/橄榄手记）后，自由判断当前文章最适合哪套。推荐时附简短理由，用户可以确认或换一套。
- **产物路径**：输出强制重定向为 `article.html`（与 baoyu 一致），保持 `workflow-state.json` 中文件契约不破。
- **校验**：生成后运行 `<skill_path>/scripts/validate_gzh_html.py article.html`，ERROR 清零才通过。

### 3. 输出规则统一

三个工具共享以下规则（已在 html-guide.md 中，仅确认不调整）：

- 产物文件：`article.html`，与 `article.md` 同目录
- 图片检查：`<img>` 数量 = `【配图N】` 数量，无残留 `【配图`，本地路径 `src="配图N.png"`
- 兼容性约束：无 `<style>` / 全 inline / 无 `<ul><li>`（用 `<p>` 替代）
- 门禁命令：`validate_workflow.py html` → `workflow_state.py pass`

### 4. md2wechat 备选策略变更

- 原：baoyu-markdown-to-html 失败后 + 用户明确选择才启用
- 改：任意主工具失败后自动降级，不再询问用户

## 影响范围

| 文件 | 变更 |
|------|------|
| `docs/html-guide.md` | 重写章首决策逻辑、新增 gzh-design 节、调整 md2wechat 角色描述、输出规则部分确认不变 |

不涉及脚本变更（`validate_workflow.py` 等保持原样）。

## 不变约束

- Step 6 仍只生成 HTML、不上传不发稿
- 图片在 Step 5 已完成生成
- Step 7 用户预览确认的硬门禁不变