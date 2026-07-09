# 文匠 WenJiang

> 字幕进去，爆款出来。一条流水线，从视频字幕到公众号发布。

文匠是一个基于 Code Agent 的内容生产工作流。丢进一段字幕，Agent 以字幕为唯一事实基准，依次完成内容分析、分轮写作、排版、配图、HTML 和平台资产生成。

公众号草稿创建前的主体流程在 AI Code 内闭环完成；Step 7 需要用户预览确认，Step 11 仍由用户手动发布小红书。

## 它能做什么

| 能力 | 说明 |
|------|------|
| 内容类型识别 | 自动判断科普 / 财经 / 科技 / 成长等类型，匹配对应写法 |
| 去 AI 味写作 | 三轮写作：内容初稿、编辑终稿、独立质检与配图提示词 |
| 微信 SEO | 标题和正文覆盖搜一搜高频关键词 |
| 多格式输出 | 公众号 HTML、小红书图文卡片、封面和配图 |
| 一键发布 | 通过 baoyu-post-to-wechat API 自动上传正文图片和封面，推送到草稿箱 |

## 工作流

```
字幕文件 (.srt)
  │
  ▼
Step 1  本地清洗字幕 (source.cleaned.txt)
Step 2  三轮生成文章 (article.md) + 配图提示词 (cover_prompt.md)
Step 3  确定性回归校验
Step 4  格式化 Markdown
Step 5  AI 生成封面和配图
Step 6  转换为公众号 HTML (article.html，3 个工具随机选主)
Step 7  预览确认
Step 8  上传图片并创建微信草稿箱
Step 9  生成小红书卡片
Step 10 生成小红书文案
Step 11 手动发布小红书
```

每个任务使用 `workflow-state.json` 记录步骤和校验状态。Step 7 是用户确认硬门禁；确认后的文章、HTML 或图片发生变化时，必须重新确认才能创建微信草稿。

## 每篇文章产出

文章目录最终只保留正式发布资产。字幕、提示词、batch、截图脚本、调试文件等中间产物会在流程中清理。

```
articles/YYYYMMDD-HHMMSS/
├── article.md          # Markdown 文章
├── article.html        # 公众号 HTML
├── cover.png           # 公众号封面 (2.35:1)
├── 配图1~N.png         # 正文配图
├── 公众号草稿信息.txt   # 微信草稿 media_id 和后台核对信息
├── 小红书卡片-01~N.png  # 小红书图文
├── 小红书文案.txt       # 小红书发布文案
└── workflow-state.json # 步骤、校验和确认摘要审计记录
```

## 项目结构

```
.
├── AGENTS.md           # Agent 角色定义和文档入口
├── .agents/
│   └── skills/         # 项目级 Agent Skills，避免污染全局上下文
├── opencode.json       # OpenCode 权限配置
├── skills.lock.json    # 已验证 Skill 版本、入口和关键能力
├── scripts/
│   ├── clean_subtitle.py   # 本地字幕清洗脚本
│   ├── validate_workflow.py # 文章、图片、HTML、发布和最终资产校验
│   └── workflow_state.py    # 工作流状态与用户确认门禁
├── docs/
│   ├── workflow.md              # 主流程和步骤
│   ├── steps/                  # 按工作流阶段组织的指南
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
│   │   │   └── html-tools/             # 三个 HTML 生成工具细则
│   │   │       ├── md2wechat.md
│   │   │       ├── baoyu-markdown-to-html.md
│   │   │       └── gzh-design.md
│   │   ├── step8/
│   │   │   └── wechat-guide.md          # 公众号草稿上传说明
│   │   ├── step9/
│   │   │   └── xiaohongshu-guide.md    # 小红书卡片生成规则
│   │   ├── step10/
│   │   │   └── xiaohongshu-guide.md    # 小红书发布文案规则
│   │   └── step11/
│   │       └── final-cleanup-guide.md   # 发布前最终目录清理规则
│   └── exceptions/             # 条件触发/异常参考
│       ├── ending-guide.md             # 特殊免责声明或关注引导
│       └── final-writing-check.md      # 独立质检未覆盖问题的输出规范
└── inputs/             # 字幕文件输入目录
```

## 快速开始

### 前置依赖

- [OpenCode](https://github.com/anomalyco/opencode) — 驱动整个工作流的 Agent
- [md2wechat](https://github.com/geekjourneyx/md2wechat-skill) — 可选的公众号 HTML 生成工具
- [baoyu-post-to-wechat](https://github.com/JimLiu/baoyu-skills#baoyu-post-to-wechat) — 上传正文图片、封面素材并创建公众号草稿
- [Playwright](https://playwright.dev/) — 小红书卡片截图导出使用，依赖由 `guizang-social-card-skill` 提供（位于 `.agents/skills/guizang-social-card-skill/node_modules/`，截图脚本通过 `NODE_PATH` 指向该目录）

### 使用

1. 将字幕文件（.srt）放入 `inputs/` 目录
2. 在 OpenCode 中打开本项目
3. 对 Agent 说：「用 inputs/ 里的字幕写一篇文章」
4. Agent 先本地清洗字幕，再按 `workflow-state.json` 顺序执行；Step 7 等待用户明确预览确认
5. 流程结束前清理字幕、提示词、batch、截图脚本和调试文件，只保留正式发布资产

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
| `baoyu-markdown-to-html` | 将 Markdown 转换为微信公众号兼容 HTML |
| `gzh-design-skill` | 将 Markdown 转为不掉样式的公众号 HTML（Step 6 随机主工具之一） |
| `baoyu-post-to-wechat` | 上传正文图片和封面，创建微信公众号草稿 |
| `guizang-social-card-skill` | 生成小红书图文卡片、公众号封面等社交传播图片 |
| `md2wechat` | 使用 `md2wechat` CLI 做预览、转换、草稿等公众号流程 |


| 文件 | 用途 |
|------|------|
| `AGENTS.md` | Agent 角色定义和文档入口 |
| `.agents/skills/` | 项目级 Agent Skills |
| `opencode.json` | OpenCode 权限配置 |
| `docs/workflow.md` | 主流程和步骤 |
| `docs/steps/step1/subtitle-guide.md` | 字幕清洗规则 |
| `docs/steps/step2/writing-guide.md` | 第一轮内容初稿规则 |
| `docs/steps/step2/editorial-guide.md` | 第二轮标题、真人化和收尾规则 |
| `docs/steps/step2/final-review-guide.md` | 第三轮独立质检规则 |
| `docs/steps/step2/image-prompt-guide.md` | 封面和正文配图提示词规则 |
| `docs/steps/step4/markdown-guide.md` | Markdown 格式化规则 |
| `docs/steps/step5/image-generation-guide.md` | 图片生成执行规则 |
| `docs/steps/step6/html-guide.md` | 公众号 HTML 生成参数和兼容性规则 |
| `docs/steps/step8/wechat-guide.md` | 公众号草稿上传说明 |
| `docs/steps/step9/xiaohongshu-guide.md` | 小红书卡片生成规则 |
| `docs/steps/step10/xiaohongshu-guide.md` | 小红书发布文案规则 |
| `docs/steps/step11/final-cleanup-guide.md` | 发布前最终目录清理规则 |


配置修改后立即生效，下次运行自动应用。

## License

MIT
