# 图片生成指南

本文件定义 Step 5 使用 `cover_prompt.md` 生成公众号封面、正文配图与今日头条专属三图封面的执行规则。只有实际调用图片生成工具时才需要读取本文件。

---

## 生图优先级与路由规则（强制）

按 **“首选 Gemini，GPT 兜底”** 的原则选择生图路径：

1. **第一优先级（首选：Gemini 路径）**：
   - 当前会话明确暴露且可调用环境原生生图工具（如 `generate_image`）或 Gemini Imagen 接口时，**必须优先使用 Gemini 逐张生成**。
   - 仅列出 `imagegen` skill 不足以证明原生工具可用；必须同时确认当前会话实际暴露了可调用的原生生图工具。
2. **第二优先级（兜底：GPT 路径）**：
   - 仅当 Gemini 路径出现工具未暴露、不可调用、报错、配额耗尽、网络异常或单张生成失败时，才自动切换使用 **GPT**（OpenAI / GPT-Image-2 / `baoyu-image-gen --provider openai` 或 `codex-cli`）进行兜底补全。
3. **不可用**：
   - 若 Gemini 与 GPT 均无法生成时，停止并向用户报告，由用户决定后续处理。

无论使用哪种后端，生成的图片必须严格符合尺寸与比例规范，并通过 `validate_workflow.py images` 客观门禁。

---

## 前提条件

- 两条路径共同要求 `python3 scripts/validate_workflow.py skills skills.lock.json` 返回 `OK`，`cover_prompt.md` 已通过提示词校验，输出目录可写，并且同名旧图已按备份规则处理。
- Gemini 路径优先检测当前会话中原生生图工具是否可调用，或 Gemini 接口可用性。
- GPT 兜底路径在 Gemini 失败或不可用时触发，使用 OpenAI / GPT-Image-2 / codex-cli 渠道。

---

## 核心生成策略

- 调用任何外部 Skill 或图片工具前，先运行公共兼容性检查 `python3 scripts/validate_workflow.py skills skills.lock.json`。
- **逐张生成**：每次调用只传当前图片的 prompt 和目标比例，按公众号封面、正文配图（1~N）、头条三图封面（1~3）的顺序依次生成。
- **失败重试策略**：若某张图片在 Gemini 路径生成失败，针对该图片切换到 GPT 兜底生成，已成功的图片无需重复生成。
- **只做客观门禁**：生成后通过程序检查文件存在、PNG 可识别、编号匹配、尺寸和比例正确。不得使用 AI 读图、`view_image`、截图目检或主观审美判断来重复生成图片。

---

## 资产与文件契约

读取 `articles/<YYYYMMDD-HHMMSS>/cover_prompt.md` 中的英文提示词，严格输出以下文件：

| 资产名称 | 文件路径 | 目标比例 | 说明 |
| :--- | :--- | :--- | :--- |
| **公众号主封面** | `articles/<YYYYMMDD-HHMMSS>/cover.png` | `2.35:1` | 公众号大图封面 |
| **正文插图** | `articles/<YYYYMMDD-HHMMSS>/配图1.png` ~ `配图N.png` | `16:9` | 对应文章内各配图点位 |
| **头条封面 1** | `articles/<YYYYMMDD-HHMMSS>/toutiao-cover-1.png` | `16:9` | 痛点共鸣 / 场景人物写实摄影 |
| **头条封面 2** | `articles/<YYYYMMDD-HHMMSS>/toutiao-cover-2.png` | `16:9` | 食物反差 / 饮食细节微距特写 |
| **头条封面 3** | `articles/<YYYYMMDD-HHMMSS>/toutiao-cover-3.png` | `16:9` | 科学赋能 / 健康生活饱满特写 |

---

## 覆盖与备份规则

如果文章目录里已存在同名图片，先备份旧图再保存新文件（文件名追加 `.backup-YYYYMMDD-HHMMSS`）。

备份必须保留到 Step 7 用户确认当前文章、HTML 和图片后。确认前不得因为新图片已经存在而删除备份；确认后才能删除。若确认后再次修改任何资产，原确认自动失效。

---

## 完整执行流程

### 0. 兼容性检查

```bash
python3 scripts/validate_workflow.py skills skills.lock.json
```

### 1. 提取提示词

读取 `articles/<YYYYMMDD-HHMMSS>/cover_prompt.md`，提取公众号封面、正文配图和头条三图封面的完整英文 Prompt。

### 2. 执行生图（Gemini 优先 ➔ GPT 兜底）

#### 步骤 2A：优先使用 Gemini
- 调用可调用的原生 `generate_image` 工具或 Gemini 生图通道，逐张传入 prompt 与 `AspectRatio`（如 `16:9`）。
- 将生成的图片移入文章目录对应文件名。

#### 步骤 2B：若 Gemini 失败，使用 GPT 兜底
- 自动切换到 GPT 渠道（如 `baoyu-image-gen` 或 OpenAI 接口），补齐未成功生成的图片。

### 3. 运行客观校验

生成完成后运行客观门禁检查：

```bash
python3 scripts/validate_workflow.py images articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_5
```

校验器会严格核对 `cover.png`（2.35:1）、全部 `配图N.png`（16:9）与 `toutiao-cover-1~3.png`（16:9）是否存在、比例是否精准、格式是否有效。

### 4. 清理临时文件

图片客观检查通过后，删除临时文件（如 `batch.json`、临时生成的缓存等），进入 Step 6 生成公众号 HTML。
