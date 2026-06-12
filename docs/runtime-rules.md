# Agent 运行规则

本文件定义文章生产过程中 Agent 必须遵守的运行时规则，包括临时文件清理、上下文压缩和配置维护约束。

---

## 临时文件清理规则

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
- Step 11 完成后：删除小红书卡片生成过程中的临时 HTML、临时 JS、preview/debug 文件
- Step 12 前：删除原始字幕和 `source.cleaned.txt`，最终目录只保留正式发布资产

---

## 上下文压缩策略

每步完成后应压缩上下文以优化 token 使用。各步产出已保存在文件中，下一步直接读文件即可。

**关键原则：** 压缩时必须保留当前步骤号、用户决策（标题选择、配图删除等）和文件路径。压缩的是对话过程，不是文件内容。

| 时机 | 动作 | 原因 |
|------|------|------|
| Step 2-4 期间 | **不压缩** | 文章仍在打磨中，需要上下文连贯 |
| Step 4 完成后 | 压缩一次 | 文章已定稿，后续步骤全部基于文件操作 |
| Step 6 完成后 | 可压缩 | 图片已生成，Step 7-9 是机械操作 |
| Step 9 完成后 | 可压缩 | 草稿已上传，Step 10-11 独立于前序步骤 |

**提示用户触发压缩的规则：**

AI 无法自动触发上下文压缩。在上述时机节点完成对应步骤后，AI 必须主动向用户发出提示，建议用户执行 `/compact` 或等效操作。提示模板：

```text
当前步骤已完成，建议执行 /compact 压缩上下文以节省 token。
压缩后我会保留以下关键信息：
- 当前进度：Step X
- 标题：{已选定标题}
- 文章目录：articles/<YYYYMMDD-HHMMSS>/
- 你的特殊要求：{如有}
```

**压缩时必须保留的信息：**
- 当前执行到第几步
- 用户确认的标题
- 用户的特殊要求或修改（如删除配图、修改工作流规则等）
- `articles/<YYYYMMDD-HHMMSS>/` 目录路径

---

## 双配置文件维护规则

本项目可能被 OpenCode 和 MimoCode 两个工具使用，因此必须同时保留：

- `opencode.json`
- `mimocode.json`

修改权限、MCP、外部目录或工具调用配置时，需要同步检查两个文件，避免一个工具可用而另一个工具失效。
