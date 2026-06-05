# baoyu-markdown-to-html 使用指南

## 角色定位

baoyu-markdown-to-html 是备选 HTML 生成工具，当 `md2wechat` 不可用时（配置/网络问题）使用。

AI 根据内容类型自动匹配主题和色系，无需用户指定。

## 主题 & 色系选择（根据内容类型自动匹配）

| 内容类型 | 推荐主题 | 推荐色系 |
|---------|---------|---------|
| 健康科普 | modern | green / blue |
| 科技前沿 | modern | blue / sky |
| 财经商业 | default | blue / black |
| 个人成长 | grace | orange / rose |
| 访谈对话 | grace | purple / orange |
| 生活技能 | simple | green / orange |
| 教育学习方法 | grace | purple / blue |
| 心理健康情绪管理 | grace | rose / purple |

## 主题说明

| 主题 | 描述 |
|------|------|
| `default` | 经典布局，居中标题带底边，H2 白字彩色背景 |
| `grace` | 优雅风格，文字阴影、圆角卡片、精致引用 |
| `simple` | 简约现代，非对称圆角，干净留白 |
| `modern` | 现代风格，大圆角、药丸标题、宽松行高（配 `--color red` 即传统红金风格） |

## 色系预设

| 名称 | Hex | 说明 |
|------|-----|------|
| blue | #0F4C81 | 经典蓝 |
| green | #009874 | 翡翠绿 |
| vermilion | #FA5151 | 朱红 |
| purple | #92617E | 薰衣草紫 |
| sky | #55C9EA | 天蓝 |
| rose | #B76E79 | 玫瑰金 |
| orange | #D97757 | 暖橙（modern 默认） |
| red | #A93226 | 中国红 |
| black | #333333 | 石墨黑 |

## 输出规则

- **输出文件名**与输入文件名一致（`article.md` → `article.html`）
- **输出目录**与输入文件同级
- 如果 HTML 已存在，自动备份：`article.html.bak-YYYYMMDDHHMMSS`
- HTML 中图片先用本地路径占位（`配图1.jpg`），后续上传后替换为 CDN 地址

## 使用示例

```bash
# 基本转换（当前目录）
bun <skill-path>/scripts/main.ts article.md

# 指定主题和色系
bun <skill-path>/scripts/main.ts article.md --theme modern --color blue

# 指定主题、色系、标题
bun <skill-path>/scripts/main.ts article.md --theme grace --color orange --title "文章标题"

# 微信外链转底部引用
bun <skill-path>/scripts/main.ts article.md --cite
```

## 详细参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--theme <name>` | 主题：default, grace, simple, modern | default |
| `--color <name\|hex>` | 主色：预设名或 hex | 主题默认 |
| `--font-size <N>` | 字号：14-18px | 16px |
| `--title <title>` | 覆盖 frontmatter 标题 | - |
| `--cite` | 外链转底部引用 | false |
| `--keep-title` | 保留内容中的第一个标题 | false（删除） |