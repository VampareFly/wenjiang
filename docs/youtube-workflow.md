# YouTube 自动化工作流与选题雷达指南

本文档介绍如何使用本项目内置的 **YouTube 自动化工具链**，实现从“全网找视频（选题雷达） ➔ 爆款潜质初筛 ➔ 自动提取字幕与建档 ➔ 无缝衔接文章创作”的全流程自动化。

---

## 核心特性

1. **自动选题雷达（Discovery Radar）**：通过 YouTube 频道 RSS 与关键词搜索，自动扫描优质海外博主最新视频，输出可视化 Markdown 选题看板 `candidates.md`。
2. **秒级字幕提取（Zero-Video Download）**：基于 `yt-dlp` 的 `--skip-download` 模式，不下载大体积视频本体，仅需 2~5 秒即可提取官方中/英字幕或自动字幕（Auto-captions）及完整视频元数据。
3. **一步建档与清洗（Auto Step 1）**：自动创建时间戳文章目录 `articles/YYYYMMDD-HHMMSS/`，归档 `source.srt`、`source-link.txt`，自动调用 `clean_subtitle.py` 进行压缩清洗并标记 Step 1 状态通过。
4. **全自动全局防重（Deduplication）**：与 `link-registry.json` 深度集成，自动识别并拦截已处理过的视频 URL。

---

## 快速上手

### 1. 前置依赖准备

本工具链推荐安装 `yt-dlp`（工业级视频元数据与字幕提取工具）：

```bash
# 使用 pip 安装
pip install yt-dlp

# 或在 macOS 上使用 Homebrew
brew install yt-dlp
```

> [!TIP]
> 频道 RSS 扫描功能使用 Python 内置库，无需任何外部依赖即可独立运行；关键词深度搜索与字幕提取需要 `yt-dlp`。

---

### 2. 模式一：直接抓取单个视频并开工（推荐）

当你已有 YouTube 视频链接时，只需在终端执行一行命令：

```bash
python3 scripts/fetch_youtube.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**执行效果：**
1. 校验链接是否处理过；
2. 秒级抓取最佳字幕与标题、频道名、时长、发布时间；
3. 创建文章目录（如 `articles/20260819-110000/`）；
4. 自动运行清洗脚本输出 `source.cleaned.txt`；
5. 初始化 `workflow-state.json` 并通过 `step_1`；
6. 提示直接开始 Step 2 写作：

```bash
# 接着运行 Step 2 即可开始写作：
python3 scripts/workflow_state.py start articles/20260819-110000 step_2
```

#### 常用参数

| 参数 | 说明 | 示例 |
| :--- | :--- | :--- |
| `url` | 视频 URL 或 11 位 Video ID（必填） | `"https://youtu.be/xxx"` 或 `"xxx"` |
| `-o`, `--output-dir` | 指定目标文章目录（默认按当前时间戳生成） | `-o articles/my-custom-dir` |
| `--languages` | 优先字幕语言列表（逗号分隔，默认 `en,zh-Hans,zh,zh-CN,zh-TW,ja`） | `--languages en,zh` |
| `--force` | 忽略 `link-registry.json` 防重检查，强制重新抓取 | `--force` |
| `--dry-run` | 仅抓取元数据并预览，不写入文件和初始化状态 | `--dry-run` |
| `--keep-inputs` | 同时在 `inputs/` 和 `links/links.txt` 中备份一份输入 | `--keep-inputs` |

---

### 3. 模式二：自动化选题雷达（小红书健康科普·精选推荐）

不想手动去 YouTube 翻视频？使用选题雷达一键扫描健康/饮食/长寿领域的顶尖博主与高频关键词：

```bash
# 默认每次精选 3~5 个高价值选题，并输出小红书推荐理由
python3 scripts/discover_youtube.py --limit 4
```

**执行结果：**
- 自动扫描关注的顶尖健康博主（Huberman Lab, Glucose Goddess, Dr. Eric Berg, Peter Attia, ZOE 等）；
- 自动过滤最近 21 天内的视频，并剔除已处理过的历史链接；
- 在项目根目录生成 `candidates.md` 选题看板，包含：
  - 📺 **视频标题与博主出处**
  - 📊 **播放数据与视频时长**
  - 💡 **推荐理由**（揭示受众痛点与核心机制，如控糖稳糖、改善深睡眠、内脏脂肪逆转、肠道抗炎）
  - 🎯 **目标受众画像**（减脂卡关、高压白领、抗衰极客、失眠人群等）
  - 📱 **小红书爆款切入点与建议标题**
  - 🚀 **一键单篇开工命令**

#### 自主选择：单篇生成 vs 全部生成

- **方案 A（单篇生成）**：
  在 `candidates.md` 中查看后，复制对应选题下方的命令，或在对话框中告诉我：
  ```bash
  python3 scripts/fetch_youtube.py "<选中的URL>"
  # 或在对话中说：“写第 1 篇”
  ```
- **方案 B（全部批量生成）**：
  如果看板中的选题都很满意，希望一次性全部排队建档并清洗，运行：
  ```bash
  python3 scripts/discover_youtube.py --ingest-all
  # 或在对话中说：“全部生成”
  ```
  系统将依次拉取看板中的所有选题，在 `articles/` 下创建对应目录，自动完成字幕清洗与 Step 1 校验。

---

## 配置文件说明 (`config/sources.json`)

你可以根据自己的内容领域（如健康科普、饮食控糖、抗衰长寿等）自由定制 `config/sources.json`：

```json
{
  "channels": [
    {
      "name": "Huberman Lab (Andrew Huberman)",
      "channel_id": "UC2D2197645-_dcG6KETOQcA",
      "custom_url": "https://www.youtube.com/@hubermanlab",
      "category": "神经科学与睡眠精力"
    },
    {
      "name": "Peter Attia MD (The Drive)",
      "channel_id": "UC8kGsMa0LygSX9nkBcBH1Sg",
      "custom_url": "https://www.youtube.com/@PeterAttiaMD",
      "category": "长寿医学与代谢抗衰"
    },
    {
      "name": "Glucose Goddess (Jessie Inchauspé)",
      "channel_id": "UCwkd2LpZqG1lC0k_a2jUv-w",
      "custom_url": "https://www.youtube.com/@GlucoseGoddess",
      "category": "控糖曲线与饮食顺序"
    }
  ],
  "keywords": [
    {
      "query": "glucose spike hacks diet science",
      "category": "控糖曲线与饮食顺序",
      "max_results": 3
    },
    {
      "query": "deep sleep optimization science protocol",
      "category": "睡眠改善与精力管理",
      "max_results": 3
    }
  ],
  "filters": {
    "min_duration_seconds": 180,
    "max_duration_seconds": 5400,
    "published_within_days": 21,
    "preferred_languages": ["en", "zh-Hans", "zh"],
    "default_recommend_count": 4
  }
}
```

> **如何获取 YouTube 频道的 `channel_id`？**
> 1. 打开博主主页，查看网页源代码，搜索 `channelId` 或 `itemprop="channelId"`；
> 2. 或在频道 URL 末尾添加 `/videos`，复制频道 ID（通常为 `UC` 开头的 24 位字符串）。

---

## 对话式 Agent 极简交互

在 Antigravity 对话中，你可以直接发送：

- **选题推荐**：*“帮我找 4 个最新的小红书健康/饮食科普选题”*（系统自动扫描并呈送带理由的精选看板）
- **单篇开工**：*“写第 1 篇”* 或 *“帮我把这个视频写成文章：https://youtu.be/xxxxx”*
- **批量开工**：*“全部生成”*（系统自动批量建档清洗并依次进入写稿阶段）

