# 文匠 WenJiang

> 字幕进去，爆款出来。一条流水线，从视频字幕到公众号发布。

文匠是一个基于 Claude Code Agent 的内容生产工作流。丢进一段字幕，Agent 自动完成内容分析、风格化写作、排版优化、配图生成、HTML 转换，直到上传微信草稿箱。

整个流程在 Claude Code 内闭环完成，不需要手动干预。

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
Step 1  生成文章 (article.md) + 配图提示词 (cover_prompt.md)
Step 2  自动选定最优标题
Step 3  格式化 Markdown
Step 4  转换为公众号 HTML (article.html)
Step 5  AI 生成封面和配图
Step 6  预览确认
Step 7  上传图片，替换 CDN 地址
Step 8  上传微信草稿箱
Step 9  生成小红书卡片
Step 10 生成小红书文案
```

## 每篇文章产出

```
articles/YYYYMMDD/
├── article.md          # Markdown 文章
├── cover_prompt.md     # 配图提示词
├── article.html        # 公众号 HTML
├── cover.png           # 封面 (16:9)
├── 配图1~N.png         # 正文配图
├── 小红书卡片-01~N.png  # 小红书图文
└── 小红书文案.txt       # 小红书发布文案
```

## 项目结构

```
.
├── AGENTS.md           # Agent 核心配置（写作规则、工作流定义）
├── .claude/
│   └── CLAUDE.md       # Claude Code 角色与引用配置
├── docs/
│   ├── workflow.md     # 完整工作流文档
│   ├── writing-style.md    # 写作风格准则
│   ├── content-types.md    # 内容类型识别
│   ├── md2wechat-usage.md  # md2wechat 工具指南
│   ├── baoyu-markdown-to-html-usage.md
│   ├── cover-prompt-format.md
│   └── image-gen-usage.md
└── inputs/             # 字幕文件输入目录
```

## 快速开始

### 前置依赖

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — 驱动整个工作流的 Agent
- [md2wechat](https://github.com/geekjourneyx/md2wechat-skill) — Markdown 转公众号 HTML + 图片上传 + 草稿推送
- [Playwright](https://playwright.dev/) — 小红书卡片截图

### 使用

1. 将字幕文件（.srt）放入 `inputs/` 目录
2. 在 Claude Code 中打开本项目
3. 对 Agent 说：「用 inputs/ 里的字幕写一篇文章」
4. Agent 自动执行全流程，最终产出在 `articles/YYYYMMDD/`

## 配置

所有写作规则和工作流定义都在 `AGENTS.md` 中。如果你想调整：

- **写作风格** — 修改 `docs/writing-style.md`
- **内容类型判断** — 修改 `docs/content-types.md`
- **工作流步骤** — 修改 `docs/workflow.md`
- **公众号主题** — 修改 `docs/md2wechat-usage.md`

配置修改后立即生效，下次运行自动应用。

## License

MIT
