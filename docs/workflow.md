# 文章生产工作流

收到字幕文件后，先在本地清洗字幕，再按以下步骤依次执行。

所有内容集中在 `articles/<YYYYMMDD-HHMMSS>/` 单一目录，不分散存放。

---

## 阶段文档路由

`AGENTS.md` 只常驻引用本工作流。执行到具体步骤时，必须按需读取对应文档，不要把所有阶段文档长期塞进上下文。

| 阶段 | 必读文档 | 用途 |
| --- | --- | --- |
| Step 1 | `docs/subtitle-guide.md` | 字幕清洗、读取和校验 |
| Step 2、Step 3 | `docs/writing-guide.md` | 文章生成、标题选择、免责声明、关注引导和终稿检查 |
| Step 2 真人化改写轮 | `docs/ai-humanizer-guide.md` | 逐段识别并去除 AI 写作痕迹、套话、机械结构和宣传腔 |
| Step 2 | `docs/image-prompt-guide.md` | `cover_prompt.md`、封面提示词和正文配图提示词 |
| Step 4 | `docs/markdown-guide.md` | Markdown 格式化、覆盖和中间文件清理 |
| Step 5 | `docs/image-generation-guide.md` | 图片生成、provider、失败处理、备份和清理 |
| Step 6 | `docs/html-guide.md` | 公众号 HTML 生成、主题参数、兼容性约束和图片硬检查 |
| Step 8 | `docs/wechat-guide.md` | 微信图片上传、封面素材和公众号草稿 |
| Step 9、Step 10 | `docs/xiaohongshu-guide.md` | 小红书卡片和发布文案 |
| Step 11 | `docs/final-cleanup-guide.md` | 发布前最终目录清理 |

---

## 目录结构

最终目录只保留可发布、可复用的正式资产。完整清理规则见 `docs/final-cleanup-guide.md`。

```
articles/<YYYYMMDD-HHMMSS>/
├── article.md
├── article.html
├── cover.png + 配图{1-N}.png
└── 小红书卡片-{01-N}.png + 小红书文案.txt
```

**文件关系说明：**

| 文件 | 来源步骤 | 用途 |
|------|---------|------|
| `source.srt` / `source.vtt` | 用户输入 | 原始字幕，仅用于必要时回查时间点或核对原文 |
| `source.cleaned.txt` | Step 1 | 移除时间轴和字幕元数据后的本地清洗文本 |
| `article.md` | Step 2 → Step 4 覆盖 | 格式化后的最终 Markdown，后续所有步骤基于此文件操作 |
| `article.html` | Step 6 | 公众号文章 HTML，用于上传微信草稿 |
| `cover_prompt.md` | Step 2 → Step 5 | 封面和正文配图提示词 |

---

## 流程

### 准备工作：定位字幕文件

用户触发工作流时，AI 必须主动扫描 `inputs/` 目录，查找字幕文件（`.srt`、`.vtt`、字幕 `.txt`）：

1. 扫描 `inputs/` 目录，列出所有字幕文件
2. 如果找到字幕文件，创建 `articles/<YYYYMMDD-HHMMSS>/` 目录（以日期+时间命名，如 `20260612-143052`，防止同一天多次生成覆盖），将字幕文件复制进去作为 `source.srt`（或 `source.vtt`）
3. 如果 `inputs/` 为空，提示用户先将字幕文件放入 `inputs/` 目录
4. 字幕文件就位后，进入 Step 1

### Step 1：本地清洗字幕（自动）

在 AI 读取字幕内容前，先用本地脚本移除字幕时间轴和格式元数据，输出压缩后的纯字幕文本。清洗命令、字幕读取、回查和校验规则见 `docs/subtitle-guide.md`。

### Step 2：生成文章和配图提示词

- **article.md** — 按 `docs/writing-guide.md` 生成文章、候选标题、免责声明和关注引导
- **cover_prompt.md** — 按 `docs/image-prompt-guide.md` 生成封面和正文配图提示词

Step 2 必须分两轮完成，不能一次性从字幕直接输出终稿：

1. **内容初稿轮**：提炼主线、取舍素材、选择开头方式，生成结构完整且忠实字幕的初稿
2. **真人化改写轮**：先按 `docs/writing-guide.md` 的“去 AI 味终稿检查”做硬检查，再按 `docs/ai-humanizer-guide.md` 逐段识别和改写 AI 写作痕迹。不新增事实、不改变结论，只优化开头、节奏、判断、细节、口语感和作者判断。

只有完成真人化改写后，才能把内容写入最终 `article.md`。

Step 2 完成后必须按 `docs/image-prompt-guide.md` 执行正文配图硬检查。检查失败不得进入 Step 4，必须先修复 `article.md` 或 `cover_prompt.md`。

### Step 3：选定标题（AI 自动）

AI 从候选标题中自动选择最优标题，写入 `article.md` frontmatter，并移除候选标题列表。标题选择规则见 `docs/writing-guide.md`。

### Step 4：格式化 Markdown（自动）

自动调用 `/baoyu-format-markdown` 检查并格式化 `article.md`，格式化后覆盖原文件。具体调用模式、覆盖和清理规则见 `docs/markdown-guide.md`。只负责排版和标点，不负责补救文章的 AI 味。

### Step 5：生成配图

使用 `/baoyu-image-gen` skill 从 `cover_prompt.md` 自动批量生成封面和正文配图。详细流程、provider、失败处理、备份规则和清理规则见 `docs/image-generation-guide.md`。

### Step 6：生成公众号 HTML（自动）

将 `article.md` 转为 `article.html`。工具随机选择、参数和 HTML 兼容性规则详见 `docs/html-guide.md`。

Step 6 完成后必须按 `docs/html-guide.md` 执行 HTML 图片硬检查。检查失败不得进入 Step 7，必须先修复 `article.html`。

### Step 7：预览确认

**用户打开 `article.html` 预览，确认：**

- 排版正确
- 图片位置和说明正常
- 内容无误

确认后进入下一步。如需修改，返回 Step 2-6 对应环节。

### Step 8：上传图片并创建公众号草稿

用户确认后，使用 `baoyu-post-to-wechat` 的 API 方法上传 `article.html` 和封面到微信草稿箱。

`baoyu-post-to-wechat` 在发布过程中自动完成：

- 上传正文 `<img src="配图N.png">` 本地图片，替换为微信 CDN URL
- 上传封面图为微信素材，获取草稿所需的 `thumb_media_id`
- 创建公众号草稿，设置标题、摘要和作者

本流程只关心最终草稿箱内容，不要求把 CDN URL 回写到本地 `article.html`。工具使用方式和草稿信息文件格式见 `docs/wechat-guide.md`。

### Step 9：生成小红书卡片

将 `article.md` 转为小红书图文笔记卡片。截图脚本和产物命名规则见 `docs/xiaohongshu-guide.md`。

### Step 10：生成小红书文案

基于 `article.md` 内容生成小红书发布文案，输出到 `articles/<YYYYMMDD-HHMMSS>/小红书文案.txt`。文案格式和写作规则见 `docs/xiaohongshu-guide.md`。

### Step 11：手动发布小红书

发布前执行最终目录清理，删除原始字幕、清洗字幕和所有中间文件，确保文章目录只保留正式发布资产。完整清理规则见 `docs/final-cleanup-guide.md`。

用户将 `小红书卡片-{01-N}.png` + `小红书文案.txt` 的内容手动发布到小红书平台。
