# 图片生成指南

本文件定义 Step 5 使用 `cover_prompt.md` 生成公众号封面和正文配图的执行规则。只有实际调用图片生成工具时才需要读取本文件。

---

## 工具

`baoyu-image-gen` skill，通过 batch 模式批量生成封面和配图。

Provider：`codex-cli`（使用 Codex 订阅，无需额外 API key）。

---

## 生成策略（强制）

- 唯一 provider：`codex-cli`，禁止降级到 DALL-E、Midjourney 等其他方式。超时时通过 `BAOYU_CODEX_IMAGEGEN_TIMEOUT_MS` 调整单次时限后重试；仍失败则停止并报告错误，由用户决定。
- 调用前必须运行 `python3 scripts/validate_workflow.py skills skills.lock.json`。关键入口、参数或强制前置行为不兼容时停止，不使用记忆中的旧命令。
- 当前 `baoyu-image-gen` Skill 要求先读取有效的 `EXTEND.md`；该前置步骤不可跳过。缺少配置时按 Skill 指引完成配置后再继续。
- 本项目显式固定 `--provider codex-cli`，因此不进入 provider 自动选择；若当前 Skill 声明该项目级选择不可用，停止并报告，不静默切换后端。

---

## 覆盖与备份规则

如果文章目录里已存在同名图片，先备份旧图再保存新文件（文件名追加 `.backup-YYYYMMDD-HHMMSS`）。

备份必须保留到 Step 7 用户确认当前文章、HTML 和图片后。确认前不得因为新图片已经存在而删除备份；确认后才能删除。若确认后再次修改任何资产，原确认自动失效。

---

## 前提条件

- `codex` CLI 已安装且已登录（`codex login`）。
- `python3 scripts/validate_workflow.py skills skills.lock.json` 返回 `OK`。
- `baoyu-image-gen` 的 `EXTEND.md` 已存在且能解析；命令行的 `--provider codex-cli` 优先于默认 provider。

---

## 完整流程

### 0. codex-cli 锁文件预检

先执行项目兼容性预检：

```bash
python3 scripts/validate_workflow.py skills skills.lock.json
```

每次执行图片生成前，先检查 `codex-cli` 图片生成锁，避免上一次失败留下的陈旧锁阻断重新生图。

锁文件路径：

```bash
LOCK="$HOME/.cache/baoyu-codex-imagegen/codex-exec.lock"
```

预检规则：

1. 如果锁文件不存在，直接继续。
2. 如果锁文件存在，不要扫描系统进程列表。只检查锁文件本身：

   ```bash
   ls -l "$LOCK"
   stat "$LOCK"
   ```

3. 如果锁文件内容是明确的 PID，只允许检查这个 PID 是否仍然存在，不要使用 `ps -axo` 这类全局进程扫描命令：

   ```bash
   read -r PID < "$LOCK"
   case "$PID" in
     ''|*[!0-9]*) exit 2 ;;
     *) kill -0 "$PID" ;;
   esac
   ```

4. 如果能确认锁文件对应的 PID 已不存在，或用户确认这是上一次失败留下的陈旧锁，删除后再继续：

   ```bash
   rm "$LOCK"
   ```

5. 如果无法从锁文件确认是否陈旧，不要自动删除锁；向用户报告 `lock_busy`，由用户决定等待、删除锁，或中断旧任务。
6. 如果检查锁文件或删除锁被沙箱拦截，按 Codex 权限流程申请对锁文件路径的沙箱外执行，不要直接重跑生成命令。

常见失败特征：

```text
Invalid codex-cli result (lock_busy)
Failed to acquire lock at ~/.cache/baoyu-codex-imagegen/codex-exec.lock
EPERM: operation not permitted, open '~/.cache/baoyu-codex-imagegen/codex-exec.lock'
```

遇到以上错误时，按本节预检规则处理后，用 `--jobs 1` 重跑，避免并发调度再次等待锁。

### 1. 从 cover_prompt.md 提取提示词

读取 `articles/<YYYYMMDD-HHMMSS>/cover_prompt.md`，提取每个 section 的英文 prompt。

### 2. 组装临时 batch.json

在 `articles/<YYYYMMDD-HHMMSS>/` 目录下创建 `batch.json`，结构见下方模板。

字段说明：

- `id`：任务标识，与 cover_prompt.md 中的 section 对应。
- `prompt`：英文提示词，直接从 cover_prompt.md 复制。
- `image`：输出路径，使用项目相对路径。
- `ar`：宽高比，封面使用 `2.35:1`；正文配图默认使用 `16:9`。
- `quality`：`2k`（默认，适合公众号）。

### 3. 调用生成

```bash
bun ~/.agents/skills/baoyu-image-gen/scripts/main.ts \
  --batchfile articles/<YYYYMMDD-HHMMSS>/batch.json \
  --provider codex-cli --jobs 1
```

### 4. 验证输出

生成完成后运行硬检查：

```bash
python3 scripts/validate_workflow.py images articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_5
```

校验器会检查封面和全部正文配图是否存在、是否为可识别 PNG、编号是否匹配，以及封面 `2.35:1`、正文图 `16:9` 的比例。只运行 `ls` 不能证明 Step 5 完成。

### 5. 清理临时文件

图片硬检查通过后立即删除：

- `articles/<YYYYMMDD-HHMMSS>/batch.json`

以下文件保留到 Step 7 用户确认后再删除：

- `articles/<YYYYMMDD-HHMMSS>/cover_prompt.md`
- `articles/<YYYYMMDD-HHMMSS>/prompts/`
- `articles/<YYYYMMDD-HHMMSS>/*.backup-*`

图片生成完成后，下一步由 `docs/workflow.md` 的 Step 6 生成公众号 HTML，直接使用已生成的图片文件名。

---

## batch.json 模板

每次生成图片时，按以下结构创建 batch.json，将 prompt 替换为 cover_prompt.md 中的实际内容：

```json
{
  "jobs": 1,
  "tasks": [
    {
      "id": "cover",
      "prompt": "<Cover section prompt>",
      "image": "articles/<YYYYMMDD-HHMMSS>/cover.png",
      "ar": "2.35:1",
      "quality": "2k"
    },
    {
      "id": "img1",
      "prompt": "<配图1 section prompt>",
      "image": "articles/<YYYYMMDD-HHMMSS>/配图1.png",
      "ar": "16:9",
      "quality": "2k"
    },
    {
      "id": "img2",
      "prompt": "<配图2 section prompt>",
      "image": "articles/<YYYYMMDD-HHMMSS>/配图2.png",
      "ar": "16:9",
      "quality": "2k"
    }
  ]
}
```

---

## 注意事项

- 如果图片被保存到嵌套目录（如 `articles/20260612-143052/articles/20260612-143052/`），需要手动移动到正确位置。
