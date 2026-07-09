# 公众号 HTML 指南

本文件定义 Step 6 生成公众号 HTML 时的通用生成原则、微信兼容性约束和图片硬检查门禁。三个工具的**细则**拆到 `docs/html-tools/` 下独立文件，确定使用哪个工具后再按需读取，避免一次性加载全部上下文。

---

## 生成原则

Step 6 只负责把 `article.md` 转为可预览、可上传的 `article.html`：

- 只使用 HTML 生成所需参数，不触发上传、草稿创建等发布副作用。
- 等待用户在 Step 7 预览确认后，才进入 Step 8 创建微信草稿。
- 图片已在 Step 5 生成完毕，HTML 中必须用 `<img src="配图N.png" alt="标题">` 标签插入正文配图，不能只输出图片文件名文本。
- 标题不放在卡片内，单独作为顶部元素或由公众号后台自动处理。
- 正文列表在 HTML 中优先转为独立段落，避免微信编辑器剥离 `<ul>` / `<li>` 后破坏换行。

Step 6 从 3 个工具中等概率随机选一个主工具：`baoyu-markdown-to-html`、`gzh-design-skill`、`md2wechat`。文章已在 Step 4 完成格式化并通过回归校验，因此调用时明确使用当前 `article.md`，不重复触发格式化轮。每次 Step 6 独立随机，重开可能换工具；工具选择不写入状态文件。

选中工具后按其流程生成 `article.html`；若生成或校验失败，排除已失败工具后重新随机选工具再生成。3 个工具均已失败时，调用 `python3 scripts/workflow_state.py block articles/<YYYYMMDD-HHMMSS> step_6 --reason "3 个 HTML 生成工具均失败"` 并停止，向用户报告具体原因。不设固定降级链路，不在工具间随机切换之外另行回退。

### 工具细则路由

确定主工具后，读取对应细则文件再执行生成流程：

| 主工具 | 细则文件 |
|--------|----------|
| `md2wechat` | `docs/html-tools/md2wechat.md` |
| `baoyu-markdown-to-html` | `docs/html-tools/baoyu-markdown-to-html.md` |
| `gzh-design-skill` | `docs/html-tools/gzh-design.md` |

细则文件包含主题/色系选择、参数表、调用示例、配图标记转换、跳过项（如 fix-html-images）等工具专属规定；本文件不重复这些细节。

---

## 微信 HTML 兼容性约束

公众号 HTML 必须遵守以下约束：

- 禁止使用 `<style>` 标签，所有样式必须为 inline style。
- 禁止使用 flex `gap` 属性，卡片间距用 `margin-bottom` 实现。
- 微信编辑器会剥掉 `<ul>` / `<li>` 标签，导致列表换行失效。正文中的列举内容统一使用独立 `<p>` 段落 + `margin-bottom` 控制间距，不用 `<ul><li>`。

---

## HTML 图片硬检查

> **fix-html-images 执行差异**：`baoyu-markdown-to-html` 与 `md2wechat` 路径在下方门禁前先运行 `validate_workflow.py fix-html-images`；`gzh-design-skill` 路径跳过此步（其图片组件样式由主题库决定，fix-html-images 会覆盖破坏，详见 `docs/html-tools/gzh-design.md`）。

生成后必须执行 HTML 图片硬检查，失败即停止，不得进入预览确认：

- `article.html` 中 `<img` 数量必须等于 `article.md` 中 `【配图N：...】` 数量。
- `article.html` 中不得残留 `【配图`。
- 每个正文图片必须使用本地相对路径：`src="配图N.png"`。
- 每个正文图片必须包含 `alt`。
- 如果 `<img` 数量为 0，且 `article.md` 中存在配图标记，必须停止并修复。

推荐检查命令：

```bash
rg -n "【配图[0-9]+：" articles/<YYYYMMDD-HHMMSS>/article.md
rg -n "<img" articles/<YYYYMMDD-HHMMSS>/article.html
rg -n "【配图" articles/<YYYYMMDD-HHMMSS>/article.html
```

以上人工命令只用于定位问题，阶段门禁统一执行：

```bash
python3 scripts/validate_workflow.py html articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_6
```

校验失败不得进入 Step 7。
