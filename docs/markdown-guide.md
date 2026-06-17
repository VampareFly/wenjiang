# Markdown 格式化指南

本文件定义 Step 4 的 Markdown 格式化规则。只有格式化 `article.md` 时才需要读取本文件。

---

## baoyu-format-markdown 使用指南

Step 4 自动调用 `/baoyu-format-markdown` skill 检查并格式化 `article.md`：

- 无需用户确认，直接执行。
- 直接选择「优化格式」模式，跳过 skill 内的模式选择提问。
- 格式校验后，用格式化内容覆盖 `article.md`。
- 删除 `article-formatted.md` 中间文件，保持文章目录中唯一 `article.md`。
- 修复 CJK/英文间距、标点符号等排版问题。
- 后续步骤全部基于覆盖后的 `article.md` 操作。

格式化阶段只负责排版和标点，不负责补救文章的 AI 味。
