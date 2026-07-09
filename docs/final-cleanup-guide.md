# 最终清理指南

本文件定义 Step 11 的最终目录清理规则。只有发布前整理正式产物时才需要读取本文件。

只有 `workflow-state.json` 中 Step 8、Step 9、Step 10 全部为 `passed`，才能开始最终清理。微信上传失败、卡片缺失或小红书文案未完成时不得提前删除来源和中间文件。

---

## 最终只保留

文章目录最终只保留可发布、可复用的正式资产：

- `article.md`
- `article.html`
- `cover.png`
- `配图{1-N}.png`
- `公众号草稿信息.txt`
- `小红书卡片-{01-N}.png`
- `小红书文案.txt`
- `workflow-state.json`

---

## 必须删除

发布前必须删除以下中间文件：

- 原始字幕和清洗字幕：`source.srt`、`source.vtt`、`source.txt`、`source.cleaned.txt`
- 写作草稿和蓝图：`article.draft.md`、`article.plan.md`
- 中间提示词：`cover_prompt.md`、`article.prompt.txt`
- 图片生成临时文件：`batch.json`、`prompts/`
- 截图和卡片生成临时文件：临时 HTML、临时 JS、preview/debug 文件
- 格式化中间文件：`article-formatted.md`
- 备份文件：`*.backup-*`
- HTML 和其他工具备份：`*.bak-*`

如果某个阶段已经按对应指南清理过中间文件，Step 11 只需复查并补删残留文件。

清理后执行硬检查：

```bash
python3 scripts/validate_workflow.py final articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_11
```

发现任何未列入“最终只保留”的文件时，校验失败；先判断文件用途再处理，不使用宽泛通配符误删正式资产。
