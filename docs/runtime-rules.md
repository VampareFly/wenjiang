# Agent 运行规则

本文件定义文章生产过程中 Agent 必须遵守的运行时规则，包括字幕清洗和临时文件清理。

---

## 临时文件清理规则

### 字幕读取与清洗校验

在 AI 读取字幕内容前，先用本地脚本移除字幕时间轴和格式元数据，输出压缩后的纯字幕文本。

```bash
python3 scripts/clean_subtitle.py articles/<YYYYMMDD-HHMMSS>/source.srt \
  --stats \
  --verify \
  --preview 20
```

默认输出同目录的 `source.cleaned.txt`。如果原始文件是 `.vtt` 或字幕 `.txt`，命令相同：

```bash
python3 scripts/clean_subtitle.py articles/<YYYYMMDD-HHMMSS>/source.vtt --stats --verify
```

- AI 生成文章时默认只读取 `*.cleaned.txt`，不要把原始 `.srt` / `.vtt` 全量贴入对话。
- 原始字幕只在需要定位视频时间点、核对争议句或排查清洗异常时回查。
- 清洗脚本在本地运行，目标是尽量减少 AI 对话上下文占用和 token 消耗。
- `--verify` 必须通过；如果发现残留时间轴，先修正清洗结果或回查原字幕，不要直接进入 Step 2。
- `--preview 20` 用于人工快速抽查前 20 行，确认真实字幕内容没有被误删。

### 最终产物与临时文件

**最终只保留：**
- `article.md`
- `article.html`
- `cover.png`
- `配图{1-N}.png`
- `小红书卡片-{01-N}.png`
- `小红书文案.txt`

**必须删除的临时文件：**
- 原始字幕和清洗字幕：`source.srt`、`source.vtt`、`source.cleaned.txt`
- 中间提示词：`cover_prompt.md`、`article.prompt.txt`
- 图片生成临时文件：`batch.json`、`prompts/`
- 截图和卡片生成临时文件：临时 HTML、临时 JS、preview/debug 文件
- 格式化中间文件：`article-formatted.md`
- 备份文件：`*.backup-*`

**清理时机：**
- Step 4 完成后：删除 `article-formatted.md`，只保留覆盖后的 `article.md`
- Step 5 完成后：确认图片文件存在且尺寸合理后，删除 `cover_prompt.md`、`batch.json`、`prompts/` 和图片备份文件
- Step 6 完成后：如果使用 `md2wechat --mode ai`，删除 `article.prompt.txt`
- Step 11 完成后：删除小红书卡片生成过程中的临时 HTML、临时 JS、preview/debug 文件，只保留文章目录中的正式 `小红书卡片-{01-N}.png` 和 `小红书文案.txt`
- Step 12 前：删除原始字幕和 `source.cleaned.txt`，最终目录只保留正式发布资产
