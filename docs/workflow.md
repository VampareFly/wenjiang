# 文章生产工作流

收到字幕文件后，先在本地清洗字幕，再按以下步骤依次执行。

所有内容集中在 `articles/<YYYYMMDD-HHMMSS>/` 单一目录，不分散存放。

---

## 相关文档

- 写作规则：`docs/writing-guide.md`
- HTML 和微信工具：`docs/tool-reference.md`
- 图片提示词和生成：`docs/image-guide.md`
- Agent 运行规则：`docs/runtime-rules.md`

---

## 目录结构

最终目录只保留可发布、可复用的正式资产。原始字幕、清洗字幕、提示词、batch、截图脚本和调试文件都属于临时文件，完成对应步骤后删除。完整清理规则见 `docs/runtime-rules.md`。

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
| `source.srt` / `source.vtt` | 用户输入 | 原始字幕，仅用于必要时回查时间点或核对原文，流程结束前删除 |
| `source.cleaned.txt` | Step 1 | 移除时间轴和字幕元数据后的本地清洗文本，**AI 默认只读取此文件生成文章**，流程结束前删除 |
| `article.md` | Step 2 → Step 4 覆盖 | 原始 markdown → 经 `/baoyu-format-markdown` 排版优化后覆盖自身。**后续所有步骤基于此文件操作** |
| `article.html` | Step 6 | 公众号文章 HTML，用于上传微信草稿 |
| `cover_prompt.md` | Step 2 → Step 5 | 配图提示词，图片生成完成后删除 |

---

## 流程

### 准备工作：定位字幕文件

用户触发工作流时，AI 必须主动扫描 `inputs/` 目录，查找字幕文件（`.srt`、`.vtt`、字幕 `.txt`）：

1. 扫描 `inputs/` 目录，列出所有字幕文件
2. 如果找到字幕文件，创建 `articles/<YYYYMMDD-HHMMSS>/` 目录（以日期+时间命名，如 `20260612-143052`，防止同一天多次生成覆盖），将字幕文件复制进去作为 `source.srt`（或 `source.vtt`）
3. 如果 `inputs/` 为空，提示用户先将字幕文件放入 `inputs/` 目录
4. 字幕文件就位后，进入 Step 1

### Step 1：本地清洗字幕（自动）

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

**强制规则：**
- AI 生成文章时默认只读取 `*.cleaned.txt`，不要把原始 `.srt` / `.vtt` 全量贴入对话。
- 原始字幕只在需要定位视频时间点、核对争议句或排查清洗异常时回查。
- 清洗脚本在本地运行，目标是尽量减少 AI 对话上下文占用和 token 消耗。
- `--verify` 必须通过；如果发现残留时间轴，先修正清洗结果或回查原字幕，不要直接进入 Step 2。
- `--preview 20` 用于人工快速抽查前 20 行，确认真实字幕内容没有被误删。

### Step 2：生成文章和配图提示词

- **article.md** — 按 `docs/writing-guide.md` 的内容类型识别和写作策略生成，正文尾部含：
  1. 5个爆款标题（备选）
  2. 正文内容
  3. 免责声明（`>` 引用格式，2句以内）
  4. 关注引导（50-80字，独立段落）
- **cover_prompt.md** — 封面 + 配图提示词（格式见 `docs/image-guide.md`），属于临时文件，Step 5 完成后删除

### Step 3：选定标题（AI 自动）

AI 根据引流、曝光量和搜索量目标，从 5 个候选标题中自动选择最优标题：
- 放入 frontmatter 的 `title` 字段
- **从正文中删除候选标题列表**
- 选择标准：微信搜一搜关键词覆盖 > 认知冲突感 > 具体结论或数字 > 社交传播性
- 不向用户展示候选列表，不要求用户选择

### Step 4：格式化 Markdown（自动）

**自动调用** `/baoyu-format-markdown` skill 检查并格式化 article.md：
- 无需用户确认，直接执行
- **直接选择「优化格式」模式，跳过 skill 内的模式选择提问**
- **格式校验后，用格式化内容覆盖 `article.md`**（删除 `article-formatted.md` 中间文件，保持目录中唯一 `article.md`）
- 修复 CJK/英文间距、标点符号等排版问题
- 后续步骤基于 `article.md` 操作

### Step 5：生成配图

使用 `/baoyu-image-gen` skill 从 `cover_prompt.md` 自动批量出图，provider 为 `codex-cli`。**禁止降级到其他图片生成方式**，codex 失败则直接告知用户。

详细流程、备份规则和清理规则见 `docs/image-guide.md`。

### Step 6：生成公众号 HTML（自动）

随机选择 `baoyu-markdown-to-html`（60%）或 `md2wechat --mode ai`（40%）将 `article.md` 转为 `article.html`。图片已在 Step 5 生成完毕，HTML 中直接使用实际图片文件名。

工具参数、方案选择和 HTML 兼容性规则详见 `docs/tool-reference.md`。

### Step 7：预览确认

**用户打开 `article.html` 预览，确认：**

- 排版正确
- 图片位置和说明正常
- 内容无误

确认后进入下一步。如需修改，返回 Step 2-6 对应环节。

### Step 8：上传图片并替换 CDN 地址

用户确认后，用 `md2wechat upload_image` 逐张上传封面和配图，将 HTML 中的本地路径替换为返回的 CDN 地址。

详细命令见 `docs/tool-reference.md`。

### Step 9：上传公众号草稿

使用 `md2wechat test-draft` 上传 `article.html` 和封面到微信草稿箱。草稿信息文件格式见 `docs/tool-reference.md`。

让用户在微信公众号后台手动设置标题/作者/摘要后发布。

### Step 10：生成小红书卡片

使用 `guizang-social-card-skill` 将 `article.md` 内容转为小红书图文笔记卡片（1080×1440，3:4）。主题/色系由 AI 根据内容类型自动匹配，不需要用户指定。

截图脚本规则和临时文件清理规则见 `docs/image-guide.md`。

### Step 11：生成小红书文案

基于 `article.md` 内容生成小红书发布文案：
- 标题（第一行，小红书自动识别为标题，**≤20字**）
- 正文（短句、emoji 点缀、话题标签）
- 输出到 `articles/<YYYYMMDD-HHMMSS>/小红书文案.txt`

### Step 12：手动发布小红书

发布前执行最终目录清理，删除原始字幕、清洗字幕和所有中间文件，确保文章目录只保留正式发布资产。完整清理规则见 `docs/runtime-rules.md`。

用户将 `小红书卡片-{01-N}.png` + `小红书文案.txt` 的内容手动发布到小红书平台。
