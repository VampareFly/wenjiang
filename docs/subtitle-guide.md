# 字幕清洗指南

本文件定义 Step 1 的字幕读取与清洗校验规则。只有处理输入字幕时才需要读取本文件。

---

## 字幕读取与清洗校验

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
