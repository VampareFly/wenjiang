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

最终目录只保留可发布、可复用的正式资产。完整清理规则见 `docs/runtime-rules.md`。

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

在 AI 读取字幕内容前，先用本地脚本移除字幕时间轴和格式元数据，输出压缩后的纯字幕文本。清洗命令、字幕读取、回查和校验规则见 `docs/runtime-rules.md`。

### Step 2：生成文章和配图提示词

- **article.md** — 按 `docs/writing-guide.md` 生成文章、候选标题、免责声明和关注引导
- **cover_prompt.md** — 按 `docs/image-guide.md` 生成封面和正文配图提示词

### Step 3：选定标题（AI 自动）

AI 从候选标题中自动选择最优标题，写入 `article.md` frontmatter，并移除候选标题列表。标题选择规则见 `docs/writing-guide.md`。

### Step 4：格式化 Markdown（自动）

自动调用 `/baoyu-format-markdown` 检查并格式化 `article.md`，格式化后覆盖原文件。具体调用模式、覆盖和清理规则见 `docs/tool-reference.md` 与 `docs/runtime-rules.md`。

### Step 5：生成配图

使用 `/baoyu-image-gen` skill 从 `cover_prompt.md` 自动批量生成封面和正文配图。详细流程、provider、失败处理、备份规则和清理规则见 `docs/image-guide.md`。

### Step 6：生成公众号 HTML（自动）

将 `article.md` 转为 `article.html`。工具随机选择、参数和 HTML 兼容性规则详见 `docs/tool-reference.md`。

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

使用 `baoyu-post-to-wechat` 的 API 方法上传 `article.html` 和封面到微信草稿箱，自动设置标题、摘要和作者。工具使用方式和草稿信息文件格式见 `docs/tool-reference.md`。

### Step 10：生成小红书卡片

使用 `guizang-social-card-skill` 将 `article.md` 转为小红书图文笔记卡片。截图脚本和产物命名规则见 `docs/image-guide.md`。

### Step 11：生成小红书文案

基于 `article.md` 内容生成小红书发布文案，输出到 `articles/<YYYYMMDD-HHMMSS>/小红书文案.txt`。文案格式和写作规则见 `docs/writing-guide.md`。

### Step 12：手动发布小红书

发布前执行最终目录清理，删除原始字幕、清洗字幕和所有中间文件，确保文章目录只保留正式发布资产。完整清理规则见 `docs/runtime-rules.md`。

用户将 `小红书卡片-{01-N}.png` + `小红书文案.txt` 的内容手动发布到小红书平台。
