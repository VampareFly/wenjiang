# 文匠 WenJiang

> 字幕进去，爆款出来。一条流水线，从视频字幕到公众号发布。

文匠是一个基于 Code Agent 的内容生产工作流。丢进一段字幕，Agent 以字幕为唯一事实基准，依次完成内容分析、分轮写作、排版、配图、HTML 和平台资产生成。

公众号草稿创建前的主体流程在 AI Code 内闭环完成；Step 10 统一预览公众号与小红书资产，最终仍由用户手动发布小红书。

## 它能做什么

| 能力 | 说明 |
|------|------|
| 选题雷达 | 自动扫描海外优质博主频道与关键词，输出 `candidates.md` 选题看板 |
| 秒级字幕抓取 | 基于 `yt-dlp` 秒级提取原声/自动字幕与元数据，自动清洗建档过 Step 1 |
| 内容类型识别 | 自动判断科普 / 财经 / 科技 / 成长等类型，匹配对应写法 |
| 去 AI 味写作 | 三轮写作：内容初稿、编辑终稿、独立质检与配图提示词 |
| 微信 SEO | 标题和正文覆盖搜一搜高频关键词 |
| 头条算法适配 | 生成痛点前置、大白话、超短段落的头条长文（含 3 个三段式标题）与微头条 |
| 多格式输出 | 公众号 HTML、小红书图文卡片、今日头条长文与微头条、封面和配图 |
| 一键发布 | 通过 baoyu-post-to-wechat API 自动上传正文图片和封面，推送到草稿箱 |

## 工作流

```
YouTube 链接 (或 inputs/ 本地字幕)
  │
  ▼
Step 0  [可选] 选题雷达扫描 (candidates.md) ➔ 一键抓取建档 (fetch_youtube.py)
Step 1  本地清洗字幕 (source.cleaned.txt)
Step 2  三轮生成文章 (article.md) + 配图提示词 (cover_prompt.md)
Step 3  确定性回归校验
Step 4  格式化 Markdown
Step 5  AI 生成封面和配图
Step 6  固定品牌主题生成公众号 HTML + 移动端视觉复查
Step 7  小红书搜索意图与热点策略
Step 8  生成小红书卡片 + 全页程序检查
Step 9  生成多平台文案 (小红书文案 + 今日头条长文/微头条) + 独立健康表达/去 AI 质检
Step 10 统一预览确认公众号、小红书与今日头条资产
Step 11 上传图片并创建微信草稿箱
Step 12 最终清理；随后手动发布小红书与今日头条
```

每个任务使用 `workflow-state.json` 记录步骤和校验状态。Step 10 是统一用户确认硬门禁；确认后的公众号、小红书或头条资产发生变化时，必须重新确认才能创建微信草稿。

## 每篇文章产出

文章目录最终保留正式发布资产、本篇源字幕和来源链接映射。只有微信公众号草稿创建成功并取得 `media_id` 后，才会精确删除 `inputs/` 和 `links/` 中对应的一对输入；清洗字幕、提示词、batch、截图脚本和调试文件等中间产物会在流程中清理。

```
articles/YYYYMMDD-HHMMSS/
├── source.srt          # 本篇文章对应的源字幕（也可能是 .vtt/.txt）
├── source-link.txt     # 本篇文章的原始来源链接
├── source-map.json     # 输入文件、链接、文章和微信草稿映射
├── article.md          # Markdown 文章
├── article.html        # 公众号 HTML
├── cover.png           # 公众号封面 (2.35:1)
├── 配图1~N.png         # 正文配图
├── 公众号草稿信息.txt   # 微信草稿 media_id 和后台核对信息
├── 小红书卡片-01~N.png  # 小红书图文
├── 小红书文案.txt       # 小红书发布文案
├── 今日头条文章.md      # 今日头条长文（大白话、超短段落、三段式标题候选）
├── 微头条.txt           # 今日头条 300~500 字短平快动态文案
├── toutiao-cover-1~3.png # 今日头条专属爆款三图封面（16:9 高反差叙事）
└── workflow-state.json # 步骤、校验和确认摘要审计记录
```



## 项目结构

```
.
├── AGENTS.md           # Agent 角色定义和文档入口
├── .agents/
│   └── skills/         # 项目级 Agent Skills，避免污染全局上下文
├── opencode.json       # OpenCode 可选权限配置（其他 Agent 可忽略）
├── skills.lock.json    # 已验证 Skill 版本、入口和关键能力
├── config/
│   └── sources.json        # YouTube 频道订阅、关键词雷达与过滤配置
├── scripts/
│   ├── discover_youtube.py # YouTube 选题雷达扫描与 candidates.md 生成
│   ├── fetch_youtube.py    # YouTube 字幕提取、清洗与任务初始化
│   ├── clean_subtitle.py   # 本地字幕清洗脚本
│   ├── link_registry.py    # 链接查重与输入/草稿映射
│   ├── validate_workflow.py # 文章、图片、HTML、发布和最终资产校验
│   └── workflow_state.py   # 工作流状态与用户确认门禁
├── docs/
│   ├── workflow.md         # 主流程和步骤
│   ├── youtube-workflow.md # YouTube 选题雷达与全自动工作流说明
│   ├── steps/              # 按工作流阶段组织的指南
│   │   ├── step1/
│   │   │   └── subtitle-guide.md        # 字幕清洗规则
│   │   ├── step2/              # Step 2 多轮专属目录
│   │   │   ├── writing-guide.md         # 第一轮内容初稿规则
│   │   │   ├── editorial-guide.md       # 第二轮标题、真人化和收尾规则
│   │   │   ├── title-guide.md           # 标题生成与去模板盲选
│   │   │   ├── ai-humanizer-guide.md    # 真人化改写规则
│   │   │   ├── final-review-guide.md    # 第三轮独立质检规则
│   │   │   └── image-prompt-guide.md    # 封面和正文配图提示词规则
│   │   ├── step4/
│   │   │   └── markdown-guide.md        # Markdown 格式化规则
│   │   ├── step5/
│   │   │   └── image-generation-guide.md # 图片生成执行规则
│   │   ├── step6/
│   │   │   ├── html-guide.md            # 公众号 HTML 生成参数和兼容性规则
│   │   │   └── html-tools/gzh-design.md # 固定品牌渲染细则
│   │   ├── step7/xiaohongshu-strategy-guide.md # 小红书搜索意图与热点策略
│   │   ├── step8/xiaohongshu-card-guide.md     # 小红书卡片与程序检查
│   │   ├── step9/xiaohongshu-copy-guide.md     # 文案、健康表达与去 AI 质检
│   │   ├── step10/unified-approval-guide.md    # 统一预览确认
│   │   ├── step11/wechat-guide.md              # 公众号草稿上传说明
│   │   └── step12/final-cleanup-guide.md       # 发布前最终目录清理规则
│   └── exceptions/             # 条件触发/异常参考
│       ├── ending-guide.md             # 特殊免责声明或关注引导
│       └── final-writing-check.md      # 独立质检未覆盖问题的输出规范
├── inputs/             # 字幕文件输入目录
├── links/              # 与字幕同主文件名的链接文件输入目录
└── link-registry.json  # 所有成功处理链接的永久汇总索引
```

## 快速开始

### 前置依赖

- 支持读取项目指令和调用项目 Skills 的 Code Agent — 例如 [Codex](https://openai.com/codex/) 或 [OpenCode](https://github.com/anomalyco/opencode)，用于执行工作流
- [baoyu-post-to-wechat](https://github.com/JimLiu/baoyu-skills#baoyu-post-to-wechat) — 上传正文图片、封面素材并创建公众号草稿
- [Playwright](https://playwright.dev/) — 小红书卡片截图导出使用，依赖由 `guizang-social-card-skill` 提供（位于 `.agents/skills/guizang-social-card-skill/node_modules/`，截图脚本通过 `NODE_PATH` 指向该目录）

不要求安装 OpenCode。使用其他 Agent 时，请按该工具的项目指令与 Skills 配置方式加载本仓库的 `AGENTS.md` 和 `.agents/skills/`；`opencode.json` 仅对 OpenCode 生效。

### 使用

#### 方式 A：YouTube 一键抓取开工（推荐）
1. **自动找视频（选题雷达）**：运行 `python3 scripts/discover_youtube.py`，查看生成的 `candidates.md` 选题看板。
2. **一键建档与清洗**：运行 `python3 scripts/fetch_youtube.py "<YouTube链接>"`（或在对话框直接发链接：“写这篇视频：<链接>”）。
3. 脚本自动完成查重、秒级提取字幕、本地清洗，并自动通过 Step 1。
4. 随后直接运行 Step 2 启动文章生成。

#### 方式 B：本地字幕手动输入
1. 将字幕放入 `inputs/`，并把只含一个来源链接的同名 `.txt/.url` 文件放入 `links/`，例如 `video.srt` + `video.txt`
2. 在你使用的 Code Agent 中打开本项目（例如 Codex 或 OpenCode）
3. 对 Agent 说：「用 inputs/ 里的字幕写一篇文章」
4. Agent 先本地清洗字幕，再按 `workflow-state.json` 顺序执行；Step 10 等待用户统一预览确认
5. 微信草稿成功后自动登记链接并清理对应输入；流程结束前再清理提示词、batch、截图脚本和调试文件

随时可检查一个链接是否处理过；命中时会返回文章目录、原字幕、`media_id` 和处理时间：

```bash
python3 scripts/link_registry.py check "https://example.com/video"
```

## 配置

### 项目 Skills

本项目使用 `.agents/skills/` 作为项目级 Skill 入口；当前入口可能链接到用户目录中的已安装 Skill。`skills.lock.json` 记录已验证版本、入口和关键能力，执行外部 Skill 前必须运行兼容性检查，避免全局升级后静默漂移。

`.agents/skills/` 不绑定某一个 AI Agent 工具，但换机器或升级 Skill 后必须重新建立入口并验证 `skills.lock.json`；符号链接本身不等于依赖已经随仓库分发。

当前项目需要以下 skills：

Step 5 会先运行项目 Skill 兼容性检查，再确认当前会话是否暴露可调用的 Codex 原生图片工具；可调用时按 `imagegen` skill 的规则逐张生成。只有当前会话没有可调用的原生图片工具时，才使用下表中的 `baoyu-image-gen` 通过 `codex-cli` 回退生成。

| Skill | 用途 |
|------|------|
| `baoyu-article-illustrator` | 分析文章结构，判断正文哪里需要配图 |
| `baoyu-format-markdown` | 格式化 `article.md`，优化公众号 Markdown 排版 |
| `baoyu-image-gen` | 当前会话无可调用的原生图片工具时，通过 `codex-cli` 生成封面和正文配图（回退路径） |
| `gzh-design-skill` | 按固定“石墨极简”品牌配置生成公众号 HTML |
| `baoyu-post-to-wechat` | 上传正文图片和封面，创建微信公众号草稿 |
| `guizang-social-card-skill` | 生成小红书图文卡片、公众号封面等社交传播图片 |


| 文件 | 用途 |
|------|------|
| `AGENTS.md` | Agent 角色定义和文档入口 |
| `.agents/skills/` | 项目级 Agent Skills |
| `opencode.json` | OpenCode 的可选权限配置；使用其他 Agent 时可忽略 |
| `docs/workflow.md` | 主流程和步骤 |
| `docs/steps/step1/subtitle-guide.md` | 字幕清洗规则 |
| `docs/steps/step2/writing-guide.md` | 第一轮内容初稿规则 |
| `docs/steps/step2/editorial-guide.md` | 第二轮标题、真人化和收尾规则 |
| `docs/steps/step2/final-review-guide.md` | 第三轮独立质检规则 |
| `docs/steps/step2/image-prompt-guide.md` | 封面和正文配图提示词规则 |
| `docs/steps/step4/markdown-guide.md` | Markdown 格式化规则 |
| `docs/steps/step5/image-generation-guide.md` | 图片生成执行规则 |
| `docs/steps/step6/html-guide.md` | 公众号 HTML 生成参数和兼容性规则 |
| `docs/steps/step7/xiaohongshu-strategy-guide.md` | 小红书搜索意图与热点策略 |
| `docs/steps/step8/xiaohongshu-card-guide.md` | 小红书卡片生成与程序检查 |
| `docs/steps/step9/xiaohongshu-copy-guide.md` | 小红书文案、健康表达与去 AI 质检 |
| `docs/steps/step10/unified-approval-guide.md` | 公众号与小红书统一预览确认 |
| `docs/steps/step11/wechat-guide.md` | 公众号草稿上传说明 |
| `docs/steps/step12/final-cleanup-guide.md` | 发布前最终目录清理规则 |


配置修改后立即生效，下次运行自动应用。

## License

MIT
