# 最终清理指南

本文件定义 Step 11 的最终目录清理规则。只有发布前整理正式产物时才需要读取本文件。

---

## 最终只保留

文章目录最终只保留可发布、可复用的正式资产：

- `article.md`
- `article.html`
- `cover.png`
- `配图{1-N}.png`
- `小红书卡片-{01-N}.png`
- `小红书文案.txt`

---

## 必须删除

发布前必须删除以下中间文件：

- 原始字幕和清洗字幕：`source.srt`、`source.vtt`、`source.cleaned.txt`
- 中间提示词：`cover_prompt.md`、`article.prompt.txt`
- 图片生成临时文件：`batch.json`、`prompts/`
- 截图和卡片生成临时文件：临时 HTML、临时 JS、preview/debug 文件
- 格式化中间文件：`article-formatted.md`
- 备份文件：`*.backup-*`

如果某个阶段已经按对应指南清理过中间文件，Step 11 只需复查并补删残留文件。
