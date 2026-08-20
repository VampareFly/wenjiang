# 公众号 HTML 与固定品牌排版指南

本文件定义 Step 6。此步骤只把 `article.md` 转为公众号兼容的 `article.html`，不创建草稿、不上传图片。

## 固定品牌配置

排版配置的唯一来源是 `config/wechat-brand.json`。当前品牌主题 v1 固定为：

- 渲染器：`gzh-design-skill`
- 主题：石墨极简风（`graphite-minimal`）
- 主题组件：`.agents/skills/gzh-design-skill/references/theme-graphite-minimal.md`
- 通用组件：`.agents/skills/gzh-design-skill/references/common-components.md`

不再从多个工具中随机选择，不在重开 Step 6 时自动换主题。渲染器、主题组件或校验失败时，修复当前路径；无法修复则 block Step 6，不用另一套工具静默生成不同风格。

`md-wechat`、`doocs/md` 等外部工具可以在独立样稿评测中作为对照，但未通过真实公众号粘贴、图片和长文回归前不得替换生产配置。

## 品牌排版原则

- 标题由公众号后台设置，正文不得重复文章标题。
- 以纯白、石墨灰、细线和留白建立层级；暖橙只作锚点，全篇最多 3 处。
- 优先使用正文、细线、下划线和左竖条，避免连续堆叠圆角卡片、渐变和装饰色块。
- 正文字号、行高、最大宽度和色值严格读取品牌配置，不临时改风格。
- 不新增金句、作者简介或互动文案；只转换 `article.md` 已有内容。
- 列表优先转换为独立段落或主题组件，避免微信剥离 `<ul>/<li>` 后破坏换行。

## 生成流程

1. 读取 `gzh-design` 的 `SKILL.md`、固定主题组件库和通用组件库。
2. 复制 `article.md` 为临时输入，把 `【配图N：标题】` 转为 `![标题](配图N.png)`；不得修改正式 `article.md`。
3. 在文章目录内按石墨极简主题装配 HTML，跳过正文标题组件。
4. 输出纯 `<section>…</section>` 片段并统一命名为 `article.html`。
5. 删除临时 Markdown 和主题原始输出文件。
6. 运行 gzh HTML 校验，ERROR 和 WARNING 都必须为 0。
7. 以约 390px 宽度生成移动端预览并检查首屏、段落、标题换行、卡片密度、图片比例和整体留白。
8. 写入 `wechat-layout-check.json`。

不得运行 `fix-html-images`，它会覆盖主题图片组件样式。

## 微信兼容性

- 禁止 `<style>`、`<script>`、`<div>`、`class`、`id`。
- 禁止 `position:fixed/absolute/sticky`、`float`、`display:grid`、CSS 变量。
- 样式必须内联；文字节点按主题要求使用 `<span leaf="">`。
- 正文图片使用相对路径 `配图N.png`，保留准确 `alt`。
- 图片数量必须等于 `article.md` 的配图标记数量，HTML 不得残留 `【配图`。

## 排版检查记录

生成 `wechat-layout-check.json`：

```json
{
  "schema_version": 1,
  "renderer": "gzh-design-skill",
  "theme_id": "graphite-minimal",
  "brand_config": "config/wechat-brand.json",
  "gzh_errors": 0,
  "gzh_warnings": 0,
  "mobile_preview": {
    "reviewed": true,
    "viewport_width": 390,
    "first_screen_clear": true,
    "headings_wrap_cleanly": true,
    "card_density_ok": true,
    "images_balanced": true,
    "spacing_consistent": true
  }
}
```

检查记录必须来自本次真实生成和预览，不得沿用旧文件。

## 门禁

```bash
python3 scripts/validate_workflow.py html articles/<YYYYMMDD-HHMMSS>
python3 scripts/validate_workflow.py wechat-layout articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_6
```

任一检查失败不得进入小红书策略轮。
