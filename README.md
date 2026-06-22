# 文匠 WenJiang

> 字幕进去，爆款出来。一条流水线，从视频字幕到公众号发布。

文匠是一个基于 Code Agent 的内容生产工作流。丢进一段字幕，Agent 自动完成内容分析、风格化写作、排版优化、配图生成、HTML 转换，直到上传微信草稿箱。

公众号草稿创建前的主体流程在 AI Code 内闭环完成；Step 7 需要用户预览确认，Step 11 仍由用户手动发布小红书。

## 它能做什么

| 能力 | 说明 |
|------|------|
| 内容类型识别 | 自动判断科普 / 财经 / 科技 / 成长等类型，匹配对应写法 |
| 去 AI 味写作 | 两轮写作：先重组内容，再逐段真人化改写，口语化、有立场、带细节 |
| 微信 SEO | 标题和正文覆盖搜一搜高频关键词 |
| 多格式输出 | 公众号 HTML、小红书图文卡片、封面和配图 |
| 一键发布 | 通过 baoyu-post-to-wechat API 自动上传正文图片和封面，推送到草稿箱 |

## 工作流

```
字幕文件 (.srt)
  │
  ▼
Step 1  本地清洗字幕 (source.cleaned.txt)
Step 2  两轮写作生成文章 (article.md) + 配图提示词 (cover_prompt.md)
Step 3  自动选定最优标题
Step 4  格式化 Markdown
Step 5  AI 生成封面和配图
Step 6  转换为公众号 HTML (article.html)
Step 7  预览确认
Step 8  上传图片并创建微信草稿箱
Step 9  生成小红书卡片
Step 10 生成小红书文案
Step 11 手动发布小红书
```

## 每篇文章产出

文章目录最终只保留正式发布资产。字幕、提示词、batch、截图脚本、调试文件等中间产物会在流程中清理。

```
articles/YYYYMMDD-HHMMSS/
├── article.md          # Markdown 文章
├── article.html        # 公众号 HTML
├── cover.png           # 封面 (16:9)
├── 配图1~N.png         # 正文配图
├── 小红书卡片-01~N.png  # 小红书图文
└── 小红书文案.txt       # 小红书发布文案
```

## 项目结构

```
.
├── AGENTS.md           # Agent 角色定义和文档入口
├── .agents/
│   └── skills/         # 项目级 Agent Skills，避免污染全局上下文
├── opencode.json       # OpenCode 权限配置
├── mimocode.json       # MimoCode 权限配置
├── scripts/
│   ├── clean_subtitle.py   # 本地字幕清洗脚本
│   └── package.json        # Playwright 依赖
├── docs/
│   ├── workflow.md              # 主流程和步骤
│   ├── subtitle-guide.md        # 字幕清洗规则
│   ├── writing-guide.md         # 内容类型、写作策略、去 AI 味规则
│   ├── image-prompt-guide.md     # 封面和正文配图提示词规则
│   ├── markdown-guide.md         # Markdown 格式化规则
│   ├── image-generation-guide.md # 图片生成执行规则
│   ├── html-guide.md             # 公众号 HTML 生成参数和兼容性规则
│   ├── wechat-guide.md           # 公众号草稿上传说明
│   ├── xiaohongshu-guide.md      # 小红书卡片和发布文案规则
│   └── final-cleanup-guide.md    # 发布前最终目录清理规则
└── inputs/             # 字幕文件输入目录
```

## 快速开始

### 前置依赖

- [OpenCode](https://github.com/anomalyco/opencode) — 驱动整个工作流的 Agent
- [md2wechat](https://github.com/geekjourneyx/md2wechat-skill) — 可选的公众号 HTML 生成工具
- [baoyu-post-to-wechat](https://github.com/JimLiu/baoyu-skills#baoyu-post-to-wechat) — 上传正文图片、封面素材并创建公众号草稿
- [Playwright](https://playwright.dev/) — 小红书卡片截图导出使用（依赖定义在 `scripts/package.json`，首次使用前在 `scripts/` 目录执行 `npm install && npx playwright install chromium`）

### 使用

1. 将字幕文件（.srt）放入 `inputs/` 目录
2. 在 OpenCode 中打开本项目
3. 对 Agent 说：「用 inputs/ 里的字幕写一篇文章」
4. Agent 先本地清洗字幕，再自动执行全流程，最终产出在 `articles/YYYYMMDD-HHMMSS/`
5. 流程结束前清理字幕、提示词、batch、截图脚本和调试文件，只保留正式发布资产

## 配置

### 项目 Skills

本项目使用 `.agents/skills/` 存放项目级 skill 替身。公众号生产相关 skill 只服务当前项目，不应放在全局 `~/.agents/skills/`，否则会让其他项目加载不必要的上下文，也会增加误触发概率。

`.agents/skills/` 是通用 Agent Skills 目录，不绑定某一个 AI Agent 工具。切换 OpenCode、MimoCode 或其他兼容 Agent Skills 的工具时，也可以继续复用这一套项目级入口。

当前项目需要以下 skills：

| Skill | 用途 |
|------|------|
| `baoyu-article-illustrator` | 分析文章结构，判断正文哪里需要配图 |
| `baoyu-format-markdown` | 格式化 `article.md`，优化公众号 Markdown 排版 |
| `baoyu-image-gen` | 根据 `cover_prompt.md` 生成封面和正文配图（codex-cli provider 要求 codex 版本 ≤ 0.139.0，更高版本会导致生图失败） |
| `baoyu-markdown-to-html` | 将 Markdown 转换为微信公众号兼容 HTML |
| `baoyu-post-to-wechat` | 上传正文图片和封面，创建微信公众号草稿 |
| `guizang-social-card-skill` | 生成小红书图文卡片、公众号封面等社交传播图片 |
| `md2wechat` | 使用 `md2wechat` CLI 做预览、转换、草稿等公众号流程 |

这些 skill 应保留在：

```text
.agents/skills/<skill-name>/SKILL.md
```

不要同时维护 `.opencode/skills/` 和 `.agents/skills/` 两套同名 skill，避免重复发现和触发混乱。

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | Agent 角色定义和文档入口 |
| `.agents/skills/` | 项目级 Agent Skills |
| `opencode.json` | OpenCode 权限配置 |
| `mimocode.json` | MimoCode 权限配置 |
| `docs/workflow.md` | 主流程和步骤 |
| `docs/subtitle-guide.md` | 字幕清洗规则 |
| `docs/writing-guide.md` | 内容类型、写作策略、去 AI 味规则 |
| `docs/image-prompt-guide.md` | 封面和正文配图提示词规则 |
| `docs/markdown-guide.md` | Markdown 格式化规则 |
| `docs/image-generation-guide.md` | 图片生成执行规则 |
| `docs/html-guide.md` | 公众号 HTML 生成参数和兼容性规则 |
| `docs/wechat-guide.md` | 公众号草稿上传说明 |
| `docs/xiaohongshu-guide.md` | 小红书卡片和发布文案规则 |
| `docs/final-cleanup-guide.md` | 发布前最终目录清理规则 |

本项目可能被 OpenCode 和 MimoCode 两个工具使用，因此保留 `opencode.json` 和 `mimocode.json` 两份配置文件。修改权限配置时，需要同步检查两份文件是否一致。

配置修改后立即生效，下次运行自动应用。

## License

MIT
