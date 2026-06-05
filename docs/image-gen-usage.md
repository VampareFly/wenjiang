# 图片生成使用指南

## 工具

`baoyu-image-gen` skill，通过 batch 模式批量生成封面和配图。

Provider：`codex-cli`（使用 Codex 订阅，无需额外 API key）。

## 前提条件

- `codex` CLI 已安装且已登录（`codex login`）
- Reasonix 沙箱允许写入当前项目、`/tmp`、`/private/tmp`、`/Users/weak/.codex` 和 `/Users/weak/.cache/baoyu-codex-imagegen`。当前项目使用根目录的 `reasonix.toml` 配置。

## 完整流程

### 1. 从 cover_prompt.md 提取提示词

读取 `articles/<YYYYMMDD>/cover_prompt.md`，提取每个 section 的英文 prompt。

### 2. 组装 batch.json

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
- 生成后清理 batch.json 不是必须的，但建议保留以便排查问题
