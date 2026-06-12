# 图片指南

本文件定义封面图、正文配图、小红书卡片相关的提示词格式、图片生成流程和临时文件清理要求。

---

## cover_prompt.md 格式规范

### 配图标记规范

正文中标记配图位置：

```
【配图1：光照抑制食欲通路】
【配图2：饥饿素节律】
```

- 编号与 `cover_prompt.md` 中的提示词 section 一一对应
- 封面不计入编号

### cover_prompt.md 文件格式

```
# 封面图提示词

## 英文提示词（Codex 文生图使用）
[英文提示词，适合封面横向 16:9，主体完整居中]

## 中文说明
[关键元素、风格、氛围说明]

---

## 【配图1：标题】

### 英文提示词（Codex 文生图使用）
[英文提示词]

### 中文说明
[内容描述、风格、配色建议]
```

- 封面+配图提示词在同一个文件
- 每个配图一个独立 section，用 `---` 分隔
- section 标题为 `【配图N：标题】`，与正文编号完全一致
- 封面始终横向 16:9

### 中文文字要求（强制）

图片面向中文读者，提示词中必须明确要求中文文字渲染：

- 如果图片包含文字标注、标题、数据标签、图例等，提示词中必须加 `all text labels in Simplified Chinese` 或 `Chinese text annotations`
- 封面图如果含标题文字，必须注明 `title text in Simplified Chinese`
- 信息图、图表类配图，必须注明 `all chart labels, legends, and annotations in Simplified Chinese`
- 如果图片不需要任何文字（纯视觉插图），则不需要加中文要求
- **禁止生成含英文标注的科普/信息图给中文读者看**

### 配图提示词安全规范

#### 明确禁止的词汇类
- 人体器官/解剖学写实描述 → 改为抽象/隐喻表达
- 医疗场景写实 → 改为 medical illustration / diagram / scientific visualization
- 真实人物姓名/肖像 → 改为泛化描述（a scientist in lab coat）
- 疾病症状写实 → 改为 cellular process / biological mechanism
- 血液/创伤/暴力暗示
- 药品/毒品/成瘾物质
- 年龄暗示的孤立描述 → 改为 diverse age group

#### 具体改写规则
- 科学内容统一加 safety modifier：medical illustration / diagram / infographic
- 解剖学概念使用 schematic / cross-section / abstract representation
- 人体部位使用 silhouette / outline / icon 风格
- 健康数据使用 chart / graph / data visualization
- 提示词偏 educational / textbook-style / classroom diagram
- 正文配图优先 isometric view / flat illustration

---

## 图片生成使用指南

### 工具

`baoyu-image-gen` skill，通过 batch 模式批量生成封面和配图。

Provider：`codex-cli`（使用 Codex 订阅，无需额外 API key）。

### 生成策略（强制）

- **唯一 provider：`codex-cli`**，禁止切换到其他图片生成方式（DALL-E、Midjourney、Stable Diffusion 等）
- 如果 codex 生图失败（超时、锁冲突、API 错误等），**不要自动降级到其他 provider**，应直接告知用户生图失败并输出错误信息
- 如果生成超时，可以增加 `--timeout` 参数延长等待时间重试，但仍然必须使用 `codex-cli`
- 如果重试后仍然失败，停止图片生成，向用户报告具体错误，由用户决定下一步操作

### 覆盖与备份规则

如果文章目录里已存在同名图片，先备份旧图再保存新文件（文件名追加 `.backup-YYYYMMDD-HHMMSS`）。

### 前提条件

- `codex` CLI 已安装且已登录（`codex login`）

### 完整流程

#### 0. codex-cli 锁文件预检

每次执行图片生成前，先检查 `codex-cli` 图片生成锁，避免上一次失败留下的陈旧锁阻断重新生图。

锁文件路径：

```bash
LOCK="$HOME/.cache/baoyu-codex-imagegen/codex-exec.lock"
```

预检规则：

1. 如果锁文件不存在，直接继续。
2. 如果锁文件存在，先检查是否有正在运行的图片生成进程：

   ```bash
   ps -axo pid,etime,command | rg 'codex-imagegen|codex exec|baoyu-image-gen|scripts/main.ts'
   ```

3. 如果只有当前检查命令本身，没有真实的 `codex-imagegen` / `codex exec` / `baoyu-image-gen` 进程，说明是陈旧锁，删除后再继续：

   ```bash
   rm "$LOCK"
   ```

4. 如果存在真实运行中的图片生成进程，不要删除锁；等待该进程结束，或先确认是否需要中断旧任务。
5. 如果检查进程或删除锁被沙箱拦截，按 Codex 权限流程申请沙箱外执行，不要直接重跑生成命令。

常见失败特征：

```text
Invalid codex-cli result (lock_busy)
Failed to acquire lock at ~/.cache/baoyu-codex-imagegen/codex-exec.lock
EPERM: operation not permitted, open '~/.cache/baoyu-codex-imagegen/codex-exec.lock'
```

遇到以上错误时，按本节预检规则处理后，用 `--jobs 1` 重跑，避免并发调度再次等待锁。

#### 1. 从 cover_prompt.md 提取提示词

读取 `articles/<YYYYMMDD>/cover_prompt.md`，提取每个 section 的英文 prompt。

#### 2. 组装临时 batch.json

在 `articles/<YYYYMMDD>/` 目录下创建 `batch.json`：

```json
{
  "jobs": 4,
  "tasks": [
    {
      "id": "cover",
      "prompt": "从 cover_prompt.md Cover section 提取的英文提示词",
      "image": "articles/<YYYYMMDD>/cover.png",
      "ar": "16:9",
      "quality": "2k"
    },
    {
      "id": "img1",
      "prompt": "从 cover_prompt.md 配图1 section 提取的英文提示词",
      "image": "articles/<YYYYMMDD>/配图1.png",
      "ar": "16:9",
      "quality": "2k"
    }
  ]
}
```

字段说明：
- `id`：任务标识，与 cover_prompt.md 中的 section 对应
- `prompt`：英文提示词，直接从 cover_prompt.md 复制
- `image`：输出路径，使用项目相对路径
- `ar`：宽高比，封面和正文配图统一用 `16:9`
- `quality`：`2k`（默认，适合公众号）

#### 3. 调用生成

```bash
bun ~/.agents/skills/baoyu-image-gen/scripts/main.ts \
  --batchfile articles/<YYYYMMDD>/batch.json \
  --provider codex-cli --jobs 2
```

#### 4. 验证输出

生成完成后检查：
- 文件是否存在：`ls articles/<YYYYMMDD>/*.png`
- 尺寸是否合理（公众号配图建议 > 800px 宽）

#### 5. 清理临时文件

确认图片文件存在、尺寸合理后，删除：

- `articles/<YYYYMMDD>/batch.json`
- `articles/<YYYYMMDD>/cover_prompt.md`
- `articles/<YYYYMMDD>/prompts/`
- `articles/<YYYYMMDD>/*.backup-*`

图片生成完成后，下一步由 `docs/workflow.md` 的 Step 6 生成公众号 HTML，直接使用已生成的图片文件名。

### batch.json 模板

每次生成图片时，按以下结构创建 batch.json，将 prompt 替换为 cover_prompt.md 中的实际内容：

```json
{
  "jobs": 4,
  "tasks": [
    {
      "id": "cover",
      "prompt": "<Cover section prompt>",
      "image": "articles/<YYYYMMDD>/cover.png",
      "ar": "16:9",
      "quality": "2k"
    },
    {
      "id": "img1",
      "prompt": "<配图1 section prompt>",
      "image": "articles/<YYYYMMDD>/配图1.png",
      "ar": "16:9",
      "quality": "2k"
    },
    {
      "id": "img2",
      "prompt": "<配图2 section prompt>",
      "image": "articles/<YYYYMMDD>/配图2.png",
      "ar": "16:9",
      "quality": "2k"
    }
  ]
}
```

### 注意事项

- batch.json 中的 `image` 路径使用项目相对路径（如 `articles/20260612/cover.png`），不要用绝对路径
- 如果图片被保存到嵌套目录（如 `articles/20260612/articles/20260612/`），需要手动移动到正确位置
- batch.json、cover_prompt.md、prompts/ 和图片备份文件都是临时文件，确认图片生成和 HTML 替换完成后必须删除

---

## 小红书卡片截图规则

小红书卡片使用 `guizang-social-card-skill` 生成，格式为 1080×1440（3:4）。

### 截图脚本规则

- Playwright 依赖在 `scripts/node_modules/`，截图脚本必须设置 `NODE_PATH` 指向该目录，否则 `require('playwright')` 会报 `MODULE_NOT_FOUND`：
  ```bash
  NODE_PATH=scripts/node_modules node screenshot.js
  ```
- 使用 `element.screenshot()` 而非 `page.screenshot({clip})` — 自动将目标元素滚入视口
- 脚本文件先用 Write 工具创建，再用 Bash 执行（避免 sandbox 拦截）
- viewport 高度设大（≥所有卡片高度总和 + 间距）
- `names` 数组和选择器根据实际卡片动态调整

### 临时文件清理

生成小红书卡片和文案后，删除截图脚本、临时 HTML、preview/debug 文件，只保留 `小红书卡片-{01-N}.png` 和 `小红书文案.txt`
