# 最终清理指南

本文件定义 Step 12。只有 Step 8、9、10、11 全部通过，才能清理中间资产。

## 最终保留

- `article.md`
- `article.html`
- `cover.png`
- `配图{1-N}.png`
- `公众号草稿信息.txt`
- `小红书卡片-{01-N}.png`
- `小红书文案.txt`
- `今日头条文章.md`
- `微头条.txt`
- `toutiao-cover-{1-3}.png`
- `workflow-state.json`
- 一个 `source.srt`、`source.vtt` 或 `source.txt`
- 成对存在的 `source-link.txt` 和 `source-map.json`


## 删除中间资产

- `source.cleaned.txt`
- `article.draft.md`、`article.plan.md`
- `cover_prompt.md`、`article.prompt.txt`
- `xiaohongshu-strategy.json`
- `xiaohongshu-card-check.json`
- `wechat-layout-check.json`
- `batch.json`、`prompts/`
- 临时 HTML、JS、截图、preview/debug 文件
- `article-formatted.md`
- `*.backup-*`、`*.bak-*`

删除前逐项判断用途，不用宽泛通配符误删正式资产。完成后运行：

```bash
python3 scripts/workflow_state.py start articles/<YYYYMMDD-HHMMSS> step_12
python3 scripts/validate_workflow.py final articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_12
```

