# md2wechat 使用指南

## 角色定位

md2wechat 是主路径工具，覆盖 HTML 生成、图片上传、草稿上传三个环节。

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
| `--draft` | 自动创建微信草稿 | 可选 |
| `--upload` | 上传图片到微信并替换 URL | 可选 |
| `-o` | 输出 HTML 文件路径 | - |

## 使用示例

### 上传图片到微信素材库

```bash
md2wechat upload_image articles/<YYYYMMDD>/cover.jpg
md2wechat upload_image articles/<YYYYMMDD>/配图1.jpg
```

### 上传草稿

```bash
md2wechat test-draft articles/<YYYYMMDD>/article.html articles/<YYYYMMDD>/cover.jpg
```

`test-draft` 不支持设置标题、作者、摘要，这些需要在微信公众号后台手动填写。

## AI 模式生成 HTML

md2wechat AI 模式产出的是设计提示词 `article.prompt.txt`，**不直接生成 HTML**。AI 读取 prompt.txt 中的样式规范后，生成匹配的 `article.html`。

### 转换命令

```bash
md2wechat convert articles/<YYYYMMDD>/article.md \
  --mode ai \
  --theme <AI按内容类型自动匹配> \
  --title "标题" \
  --author "身心漫游" \
  --digest "摘要"
```

- `--theme` 按内容类型自动匹配（见上方主题选择表）
- 此时图片未生成，`--cover` 暂不填写
- `-o` 参数不传；AI 模式仅输出 `article.prompt.txt`，不产出真实 HTML

### 流程

1. 运行 `md2wechat convert --mode ai` 获得 `article.prompt.txt`
2. AI 读取 prompt.txt 中的设计规范（主色调、字体、卡片间距、分割线等）
3. AI 根据这些规范自动生成 `article.html`
4. HTML 中图片先用本地路径占位（`配图1.jpg`），后续上传后替换为 CDN 地址
5. `article.html` 生成完成后删除 `article.prompt.txt`，不要作为最终文章产物保留

## 工作流程

1. **生成阶段**：使用 `md2wechat convert --mode ai` 生成设计提示词，AI 据此生成 HTML
2. **预览阶段**：用户打开 article.html 预览效果
3. **上传图片**：`md2wechat upload_image` → 替换 HTML 中的 CDN 地址
4. **上传草稿**：`md2wechat test-draft`
5. **后台发布**：手动设置标题/作者/摘要后发布
