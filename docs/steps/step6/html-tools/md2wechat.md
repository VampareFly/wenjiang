# md2wechat 使用指南（Step 6 工具细则）

> 本文件是 `docs/steps/step6/html-guide.md` 中 `md2wechat` 路径的专属细则。仅在 Step 6 随机选中 `md2wechat` 后读取。

## 角色定位

md2wechat 是 Step 6 三个平等随机主工具之一，与 `baoyu-markdown-to-html`、`gzh-design-skill` 等概率被选中。它不再作为"主工具失败后的备选"——失败统一走 `docs/steps/step6/html-guide.md`「生成原则」节定义的"重随机"逻辑（排除已失败工具重新抽取），不设固定降级链路。公众号图片上传和草稿创建统一由 Step 8 的 `baoyu-post-to-wechat` API 方法完成，详见 `docs/steps/step8/wechat-guide.md`。

**注意**：AI 模式（`--mode ai`）只输出设计提示词 `article.prompt.txt`，不直接产出真实 HTML。AI 读取 prompt.txt 中的样式规范（色彩、排版、卡片间距等），生成匹配该主题的 `article.html`。

## 主题选择（根据内容类型自动匹配）

| 内容类型 | 主题参数 |
|---------|---------|
| 健康科普、财经商业、科技前沿 | `--theme ocean-calm` |
| 个人成长、访谈对话 | `--theme autumn-warm` |
| 生活技能、实用技巧、教育学习方法、心理健康情绪管理 | `--theme spring-fresh` |

## 参数说明

| 参数 | 说明 | 限制 |
|------|------|------|
| `--mode ai` | 使用 AI 模式生成 HTML（内置主题样式） | 必填 |
| `--theme` | 选择主题，必须与内容类型匹配 | 必填 |
| `--title` | 文章标题 | 最多 32 字符 |
| `--author` | 作者名 | 最多 16 字符 |
| `--digest` | 文章摘要 | 最多 128 字符 |
| `--cover` | 封面图片路径 | - |
| `-o` | 输出 HTML 文件路径 | - |

## AI 模式生成 HTML

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

### 流程

1. 运行 `md2wechat convert --mode ai` 获得 `article.prompt.txt`
2. AI 读取 prompt.txt 中的设计规范（主色调、字体、卡片间距、分割线等）
3. AI 根据这些规范自动生成 `article.html`
4. 图片替换规则见 `docs/steps/step6/html-guide.md`「HTML 图片硬检查」；正文配图须为 `<img src="配图N.png" alt="标题">`
5. `article.html` 生成完成后删除 `article.prompt.txt`，不要作为最终文章产物保留
