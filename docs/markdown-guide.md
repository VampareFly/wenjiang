# Markdown 格式化指南

本文件定义 Step 4 的 Markdown 格式化规则。只有格式化 `article.md` 时才需要读取本文件。

---

## baoyu-format-markdown 使用指南

Step 4 自动调用 `/baoyu-format-markdown` skill 检查并格式化 `article.md`：

- 本项目已明确选择「优化格式」模式；调用 Skill 时把该选择作为当前任务的显式输入，无需再次询问用户。
- 若当前 Skill 版本不接受显式模式或仍强制要求选择，停止并报告兼容性冲突，不自行换用其他模式。
- 格式校验后，用格式化内容覆盖 `article.md`。
- 删除 `article-formatted.md` 中间文件，保持文章目录中唯一 `article.md`。
- 修复 CJK/英文间距、标点符号等排版问题。
- 后续步骤全部基于覆盖后的 `article.md` 操作。

格式化阶段只负责排版和标点，不负责补救文章的 AI 味。

## 格式化后回归门禁

格式化可能改变 frontmatter、标题或配图标记。覆盖完成后必须运行：

```bash
python3 scripts/validate_workflow.py article articles/<YYYYMMDD-HHMMSS>
python3 scripts/validate_workflow.py prompts articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_4
```

任何检查失败都必须修复 `article.md` 或 `cover_prompt.md` 后重跑，不得直接进入图片生成。
