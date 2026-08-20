# gzh-design 固定品牌路径细则

本文件补充 Step 6 的固定执行细节。主规则以 `docs/steps/step6/html-guide.md` 和 `config/wechat-brand.json` 为准。

## 固定选择

- 渲染器固定为 `gzh-design-skill`。
- 主题固定为石墨极简风 `graphite-minimal`。
- 不再向用户逐篇询问主题，不随机切换，不失败后换风格。
- 每次生成都读取主题文件与通用组件文件，不能凭记忆手写组件。

## 标题、签名与内容保护

- 跳过主题库正文标题组件，公众号后台已设置标题。
- 不凭 frontmatter 自动扩写“我是食外……”等作者简介。
- 原文已有关注引导时按主题组件转换；没有时不自动补三连文案。
- 不改写、删减或新增文章实质内容。

## 配图标记转换

用临时 Markdown 把 `【配图N：标题】` 转换为 `![标题](配图N.png)`，正式 `article.md` 保持不变。生成后逐张确认 `src`、`alt`、数量与顺序一致。

## 文件处理

在 `articles/<YYYYMMDD-HHMMSS>/` 内执行，原生主题输出重命名为 `article.html`。如果旧 HTML 存在，按原流程保留带时间戳备份，直到 Step 6 新稿通过；随后清理备份。

不生成长期保留的预览外壳，不运行 `fix-html-images`。正式产物必须是纯 `<section>…</section>` 正文片段。

## 校验

运行：

```bash
python3 .agents/skills/gzh-design-skill/scripts/validate_gzh_html.py articles/<YYYYMMDD-HHMMSS>/article.html
```

ERROR 与半角标点 WARNING 都清零后，再完成移动端视觉复查并写入 `wechat-layout-check.json`。
