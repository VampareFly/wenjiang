# 微信草稿指南

本文件定义 Step 8 上传图片并创建微信公众号草稿的规则。只有创建微信草稿时才需要读取本文件。

---

## baoyu-post-to-wechat 使用指南

Step 8 使用 `baoyu-post-to-wechat` 的 API 方法上传草稿到微信公众号，支持自动上传正文图片、上传封面素材，并设置标题、摘要、作者等元数据。

本项目传入 Step 7 已预览确认的 `article.html`，而不是重新传 `article.md` 让发布脚本渲染。这样可以保留 Step 6 生成并确认过的版式。`wechat-api.ts` 支持 HTML 输入，会读取同目录 `article.md` 的 frontmatter，并扫描 HTML 中的 `<img src="...">` 处理本地正文图片。

### 前置条件

- 微信公众号 API 凭据已配置（`~/.baoyu-skills/.env` 中设置 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`）。
- 本机 IP 已加入微信公众号后台的 IP 白名单。

### 使用方式

```bash
bun ~/.agents/skills/baoyu-post-to-wechat/scripts/wechat-api.ts \
  articles/<YYYYMMDD-HHMMSS>/article.html \
  --theme default \
  --title "文章标题" \
  --summary "文章摘要" \
  --author "作者名" \
  --cover articles/<YYYYMMDD-HHMMSS>/cover.png
```

### 图片上传与替换

发布脚本会在创建草稿前自动处理图片：

- 扫描 `article.html` 中的 `<img src="配图N.png">` 本地正文图片。
- 调用微信 `media/uploadimg` 上传正文图片，得到微信 CDN URL，并写入即将提交到草稿箱的 HTML 内容。
- 调用微信 `material/add_material` 上传封面图，得到草稿 `thumb_media_id`。
- 同一张本地图片只上传一次，正文图片和封面素材按用途分别处理。

本项目只关心最终草稿箱内容，因此不要求把 CDN URL 回写到本地 `article.html`。本地 `article.html` 可继续保留 `src="配图N.png"`，用于预览和复查。

### 元数据来源

| 字段 | 优先级 |
|------|--------|
| 标题 | CLI `--title` → frontmatter `title` → 自动生成 |
| 摘要 | CLI `--summary` → frontmatter `description` → 自动生成 |
| 作者 | CLI `--author` → EXTEND.md `default_author` |
| 封面 | CLI `--cover` → frontmatter `cover` → `imgs/cover.png` → 首张内联图 |

### 输出

草稿创建成功后返回草稿 `media_id`，需记录到 `公众号草稿信息.txt`。

---

## 公众号草稿信息文件格式

使用 `baoyu-post-to-wechat` API 方法上传草稿后，必须在文章目录输出 `公众号草稿信息.txt`，内容包括：

```text
草稿 media_id：{media_id}
标题：{从 frontmatter 提取}
作者：{作者名}
摘要：{摘要}
推荐话题：{3-5 个，基于文章内容和微信搜一搜高频词}

后台操作说明：
草稿已自动设置标题、作者和摘要，请在微信公众号后台「内容管理」→「草稿箱」中核对后发布。
```
