# 图片生成使用指南

## 工具

`baoyu-image-gen` skill，通过 batch 模式批量生成封面和配图。

Provider：`codex-cli`（使用 Codex 订阅，无需额外 API key）。

## 前提条件

- `codex` CLI 已安装且已登录（`codex login`）
- Reasonix 沙箱允许写入当前项目、`/tmp`、`/private/tmp`、`/Users/weak/.codex` 和 `/Users/weak/.cache/baoyu-codex-imagegen`。当前项目使用根目录的 `reasonix.toml` 配置。

## 完整流程

### 0. codex-cli 锁文件预检

每次执行 Step 6 前，先检查 `codex-cli` 图片生成锁，避免上一次失败留下的陈旧锁阻断重新生图。

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

### 1. 从 cover_prompt.md 提取提示词

读取 `articles/<YYYYMMDD>/cover_prompt.md`，提取每个 section 的英文 prompt。

### 2. 组装临时 batch.json

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

### 3. 调用生成

```bash
bun ~/.agents/skills/baoyu-image-gen/scripts/main.ts \
  --batchfile articles/<YYYYMMDD>/batch.json \
  --provider codex-cli --jobs 2
```

### 4. 验证输出

生成完成后检查：
- 文件是否存在：`ls articles/<YYYYMMDD>/*.png`
- 尺寸是否合理（公众号配图建议 > 800px 宽）

### 5. 替换 HTML 中的占位路径

将 `article.html` 中的图片占位符（如 `配图1.jpg`）替换为实际文件名（如 `配图1.png`）。

### 6. 清理临时文件

确认图片文件存在、尺寸合理，且 `article.html` 中的图片路径已经替换完成后，删除：

- `articles/<YYYYMMDD>/batch.json`
- `articles/<YYYYMMDD>/cover_prompt.md`
- `articles/<YYYYMMDD>/prompts/`
- `articles/<YYYYMMDD>/*.backup-*`

## batch.json 模板

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

## 注意事项

- batch.json 中的 `image` 路径使用项目相对路径（如 `articles/20260612/cover.png`），不要用绝对路径
- 如果图片被保存到嵌套目录（如 `articles/20260612/articles/20260612/`），需要手动移动到正确位置
- batch.json、cover_prompt.md、prompts/ 和图片备份文件都是临时文件，确认图片生成和 HTML 替换完成后必须删除
