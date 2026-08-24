# 图片生成指南

本文件定义 Step 5 使用 `cover_prompt.md` 生成公众号封面和正文配图的执行规则。只有实际调用图片生成工具时才需要读取本文件。

---

## 工具路由

按当前会话实际暴露的能力选择路径，不根据 Agent 名称、客户端名称或主观推测判断：

1. **Codex 原生路径（优先）**：当前会话明确暴露可调用的原生图片工具时，读取 `imagegen` skill 的使用规则，并逐张生成。
2. **codex-cli 回退路径**：当前会话没有可调用的原生图片工具时，使用 `baoyu-image-gen --provider codex-cli --jobs 1`。
3. **不可用**：既没有原生能力，也无法使用已登录的 `codex` CLI 时，停止并报告，由用户决定后续处理。

仅列出 `imagegen` skill 不足以证明原生工具可用；skill 是使用说明，必须同时确认当前会话实际暴露了可调用的原生图片工具。工具名称可能带运行时命名空间，不要求字面值恰好等于 `image_gen`。

两条可用路径都使用 Codex 图片生成能力和用户的 Codex 订阅，不需要额外的 OpenAI API key。

---

## 生成策略（强制）

- 调用任何外部 Skill 或图片工具前，必须先运行公共兼容性检查 `python3 scripts/validate_workflow.py skills skills.lock.json`。该门禁覆盖整个项目的外部 Skills，不属于某一个图片 provider。
- 必须确认当前会话实际暴露可调用的原生图片工具。确认可调用时不得再通过 `baoyu-image-gen` 启动嵌套的 `codex exec`。
- 原生路径必须逐张调用，一次只生成封面或一张正文配图。不得用同一调用生成拼图后再裁切。
- 只有原生能力不存在时才进入 codex-cli 回退。回退路径必须显式固定 `--provider codex-cli --jobs 1`，不进入 provider 自动选择。
- 禁止静默降级到 OpenAI Images API、DALL-E、Midjourney 或其他 provider。所选路径失败时按对应错误规则处理；仍失败则停止并报告，由用户决定。
- `EXTEND.md`、batch 模式和 codex-cli 锁文件只属于回退路径，不得作为原生路径的前置条件。
- 默认只生成一次。生成后的检查只允许客观门禁：文件存在、PNG 可识别、编号匹配、尺寸和比例正确。不得使用 AI 读图、`view_image`、截图目检或主观审美判断来检查图片内容，也不得因此重生成。图片内容、中文标签、安全表达和风格质量必须在 Step 2 的 `cover_prompt.md` 阶段前置解决。

---

## 覆盖与备份规则

如果文章目录里已存在同名图片，先备份旧图再保存新文件（文件名追加 `.backup-YYYYMMDD-HHMMSS`）。

备份必须保留到 Step 7 用户确认当前文章、HTML 和图片后。确认前不得因为新图片已经存在而删除备份；确认后才能删除。若确认后再次修改任何资产，原确认自动失效。

---

## 前提条件

- 两条路径共同要求 `python3 scripts/validate_workflow.py skills skills.lock.json` 返回 `OK`，`cover_prompt.md` 已通过提示词校验，输出目录可写，并且同名旧图已按备份规则处理。
- 原生路径要求当前会话明确暴露可调用的原生图片工具，并读取 `imagegen` skill 的使用规则。
- codex-cli 回退路径要求：
  - `codex` CLI 已安装且已完成 `codex login`。
  - `baoyu-image-gen` 的 `EXTEND.md` 已存在且能解析；命令行的 `--provider codex-cli` 优先于默认 provider。

---

## 完整流程

### 0. 检测并固定本次生成路径

先运行项目公共兼容性检查：

```bash
python3 scripts/validate_workflow.py skills skills.lock.json
```

通过后检查当前会话的 skills 和 tools 清单，并确认底层原生图片工具是否可调用：

- 存在 `imagegen` 使用说明，且底层原生图片工具可调用：本次 Step 5 固定使用原生路径，继续执行第 1、2A、3 节。
- 原生图片工具未暴露或不可调用：本次 Step 5 固定使用 codex-cli 回退路径，继续执行第 1、2B、3 节。

一旦开始生成，不得在没有报告的情况下为剩余图片切换后端。某张图片失败时，只重试失败项，不重新生成已经成功并通过客观检查的图片。

### 1. 从 cover_prompt.md 提取提示词

读取 `articles/<YYYYMMDD-HHMMSS>/cover_prompt.md`，为封面、正文配图和今日头条专属三图封面分别提取完整英文 prompt。保持 section 与输出文件一一对应：

- 公众号主封面：`cover.png`，目标比例 `2.35:1`。
- 正文插图：`配图N.png`，目标比例 `16:9`。
- 今日头条三图封面：`toutiao-cover-1.png`、`toutiao-cover-2.png`、`toutiao-cover-3.png`，目标比例 `16:9`（分别对应痛点场景、食物对比与科学赋能）。

无论原生接口是否提供独立的比例参数，都必须在传入的 prompt 中明确写出目标比例和用途。

### 2A. Codex 原生路径

1. 按当前 `imagegen` skill 的说明调用原生 `image_gen`，每个 section 单独调用一次，按公众号封面、正文配图（1~N）、头条三图封面（1~3）的顺序依次生成。
2. 每次调用只传当前图片的 prompt、目标比例和必要参考图，不传其他 section 的内容。
3. 原生工具生成完成后，使用该次调用返回的文件路径或输出提示定位新图；不要事先扫描或猜测 `$CODEX_HOME/generated_images/` 中的旧文件。
4. 将该次生成的图片移动或复制到对应文章目录：

   ```text
   articles/<YYYYMMDD-HHMMSS>/cover.png
   articles/<YYYYMMDD-HHMMSS>/配图1.png
   articles/<YYYYMMDD-HHMMSS>/配图2.png
   articles/<YYYYMMDD-HHMMSS>/toutiao-cover-1.png
   articles/<YYYYMMDD-HHMMSS>/toutiao-cover-2.png
   articles/<YYYYMMDD-HHMMSS>/toutiao-cover-3.png
   ```

5. 原生路径不创建 `batch.json`，不读取 `baoyu-image-gen` 的 `EXTEND.md`，也不执行 codex-cli 锁文件预检。

项目的“生成后只做客观检查”规则优先：即使原生 `imagegen` skill 的通用流程建议目检，本阶段也不得调用 `view_image` 或根据主观画面质量重生成。


### 2B. codex-cli 回退路径

仅当当前会话没有可调用的原生图片工具时执行本节。

#### 2B.1 EXTEND.md 与锁文件预检

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

#### 2B.2 组装临时 batch.json

在 `articles/<YYYYMMDD-HHMMSS>/` 目录下创建 `batch.json`，结构见下方模板。

字段说明：

- `id`：任务标识，与 cover_prompt.md 中的 section 对应。
- `prompt`：英文提示词，直接从 cover_prompt.md 复制。
- `image`：输出路径，使用项目相对路径。
- `ar`：宽高比，封面使用 `2.35:1`；正文配图默认使用 `16:9`。
- `quality`：`2k`（默认，适合公众号）。

#### 2B.3 调用生成

```bash
bun .agents/skills/baoyu-image-gen/scripts/main.ts \
  --batchfile articles/<YYYYMMDD-HHMMSS>/batch.json \
  --provider codex-cli --jobs 1
```

### 3. 验证输出

生成完成后运行硬检查：

```bash
python3 scripts/validate_workflow.py images articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_5
```

校验器会检查封面和全部正文配图是否存在、是否为可识别 PNG、编号是否匹配，以及封面 `2.35:1`、正文图 `16:9` 的比例。只运行 `ls` 不能证明 Step 5 完成。

本阶段不得增加视觉内容检查。以下行为默认禁止：

- 打开图片让 AI 判断构图、中文字、风格或是否“更好”。
- 因发现图片中英文、标签不够理想、画面不够美观等主观内容问题而重生成。
- 生成后再改提示词补救内容质量。

只有以下情况才允许重新生成或移动图片：

- `validate_workflow.py images` 失败。
- 图片被保存到嵌套目录等错误位置，需要移动到正确目录。
- 生成命令失败、锁冲突、超时或输出文件损坏。
- 用户明确要求修改或重生成某张图片。

### 4. 清理临时文件

图片硬检查通过后，删除本次实际创建的临时文件。原生路径通常没有 batch 临时文件；codex-cli 回退路径应立即删除：

- `articles/<YYYYMMDD-HHMMSS>/batch.json`

以下文件保留到 Step 7 用户确认后再删除：

- `articles/<YYYYMMDD-HHMMSS>/cover_prompt.md`
- `articles/<YYYYMMDD-HHMMSS>/prompts/`
- `articles/<YYYYMMDD-HHMMSS>/*.backup-*`

图片生成完成后，下一步由 `docs/workflow.md` 的 Step 6 生成公众号 HTML，直接使用已生成的图片文件名。

---

## batch.json 模板

本模板只用于 codex-cli 回退路径。按以下结构创建 batch.json，将 prompt 替换为 cover_prompt.md 中的实际内容：

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

- codex-cli 回退路径如果把图片保存到嵌套目录（如 `articles/20260612-143052/articles/20260612-143052/`），需要手动移动到正确位置。
- 原生路径不得把项目要引用的最终图片只留在 `$CODEX_HOME/generated_images/` 中。
