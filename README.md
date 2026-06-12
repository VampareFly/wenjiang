# 文匠 WenJiang

> 字幕进去，爆款出来。一条流水线，从视频字幕到公众号发布。

文匠是一个基于 Code Agent 的内容生产工作流。丢进一段字幕，Agent 自动完成内容分析、风格化写作、排版优化、配图生成、HTML 转换，直到上传微信草稿箱。

整个流程在 AI Code 内闭环完成，不需要手动干预。

## 它能做什么

| 能力 | 说明 |
|------|------|
| 内容类型识别 | 自动判断科普 / 财经 / 科技 / 成长等类型，匹配对应写法 |
| 去 AI 味写作 | 口语化、有立场、带细节，读起来像真人写的公众号文章 |
| 微信 SEO | 标题和正文覆盖搜一搜高频关键词 |
| 多格式输出 | 公众号 HTML、小红书图文卡片、封面和配图 |
| 一键发布 | 通过 md2wechat 上传图片到微信素材库，推送到草稿箱 |

## 工作流

```
字幕文件 (.srt)
  │
  ▼
Step 1  本地清洗字幕 (source.cleaned.txt)
Step 2  生成文章 (article.md) + 配图提示词 (cover_prompt.md)
Step 3  自动选定最优标题
Step 4  格式化 Markdown
Step 5  转换为公众号 HTML (article.html)
Step 6  AI 生成封面和配图
Step 7  预览确认
Step 8  上传图片，替换 CDN 地址
Step 9  上传微信草稿箱
Step 10 生成小红书卡片
Step 11 生成小红书文案
Step 12 手动发布小红书
```

## 每篇文章产出

文章目录最终只保留正式发布资产。字幕、提示词、batch、截图脚本、调试文件等中间产物会在流程中清理。

```
articles/YYYYMMDD/
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
├── opencode.json       # OpenCode 权限配置
├── mimocode.json       # MimoCode 权限配置
├── scripts/
│   ├── clean_subtitle.py   # 本地字幕清洗脚本
│   └── package.json        # Playwright 依赖
├── docs/
│   ├── workflow.md     # 主流程和步骤
│   ├── writing-guide.md    # 内容类型、写作策略、去 AI 味规则
│   ├── tool-reference.md   # md2wechat 和 baoyu-markdown-to-html 使用说明
│   ├── image-guide.md      # 封面、配图、图片生成规则
│   └── runtime-rules.md    # 临时文件清理、上下文压缩、Agent 执行约束
└── inputs/             # 字幕文件输入目录
```

## 快速开始

### 前置依赖

- [OpenCode](https://github.com/anomalyco/opencode) — 驱动整个工作流的 Agent
- [md2wechat](https://github.com/geekjourneyx/md2wechat-skill) — Markdown 转公众号 HTML + 图片上传 + 草稿推送
- [Playwright](https://playwright.dev/) — 小红书卡片截图（依赖定义在 `scripts/package.json`，首次使用前在 `scripts/` 目录执行 `npm install && npx playwright install chromium`）

### 使用

1. 将字幕文件（.srt）放入 `inputs/` 目录
2. 在 OpenCode 中打开本项目
3. 对 Agent 说：「用 inputs/ 里的字幕写一篇文章」
4. Agent 先本地清洗字幕，再自动执行全流程，最终产出在 `articles/YYYYMMDD/`
5. 流程结束前清理字幕、提示词、batch、截图脚本和调试文件，只保留正式发布资产

## 配置

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | Agent 角色定义和文档入口 |
| `opencode.json` | OpenCode 权限配置 |
| `mimocode.json` | MimoCode 权限配置 |
| `docs/workflow.md` | 主流程和步骤 |
| `docs/writing-guide.md` | 内容类型、写作策略、去 AI 味规则 |
| `docs/tool-reference.md` | md2wechat 和 baoyu-markdown-to-html 使用说明 |
| `docs/image-guide.md` | 封面、配图、图片生成规则 |
| `docs/runtime-rules.md` | 临时文件清理、上下文压缩、Agent 执行约束 |

本项目可能被 OpenCode 和 MimoCode 两个工具使用，因此保留 `opencode.json` 和 `mimocode.json` 两份配置文件。修改权限配置时，需要同步检查两份文件是否一致。

配置修改后立即生效，下次运行自动应用。

## License

MIT
