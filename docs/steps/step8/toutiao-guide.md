# 今日头条草稿发布指南

本文件定义 Step 8 执行今日头条长文与微头条**全自动存草稿**的规则与操作指南。只有实际推送头条草稿时才需要读取本文件。

---

## 核心定位

今日头条发布采用与微信公众号完全相同的**“全自动存入草稿箱（Draft）”**模式：
- 脚本全自动处理标题提取、正文富文本排版、正文插图上传、16:9 专属三图封面上传、微头条短快讯排版与话题挂载；
- 全自动存入今日头条创作者后台的【草稿箱】；
- 绝不直接向公域群发，由创作者在手机「今日头条 App」或电脑端扫一眼后一键发布。

---

## 前置要求与资产清单

执行发布前，确保目标文章目录 `articles/<YYYYMMDD-HHMMSS>/` 中已具备以下完整资产：

1. **`今日头条文章.md`**：长文终稿，包含第一行 `# 三段式标题`（≤30 字）、短段落与加粗。
2. **`微头条.txt`**：300~500 字短动态，包含前三行抓人悬念、3 点干货清单与 `#话题标签#`。
3. **`toutiao-cover-1.png`、`toutiao-cover-2.png`、`toutiao-cover-3.png`**：16:9 写实三图封面。
4. **`配图1~N.png`**：正文高清插图。

---

## 快速使用命令

### 1. 一键全自动推送（长文草稿 + 微头条草稿）

```bash
python3 scripts/post_to_toutiao.py articles/<YYYYMMDD-HHMMSS>
```

### 2. 仅推送长文草稿

```bash
python3 scripts/post_to_toutiao.py articles/<YYYYMMDD-HHMMSS> --type article
```

### 3. 仅推送微头条草稿

```bash
python3 scripts/post_to_toutiao.py articles/<YYYYMMDD-HHMMSS> --type weitoutiao
```

### 4. 仅校验资产与格式（不启动浏览器）

```bash
python3 scripts/post_to_toutiao.py articles/<YYYYMMDD-HHMMSS> --dry-run
```

---

## 产物与审计记录

执行完成后，文章目录下将自动生成：

```text
articles/<YYYYMMDD-HHMMSS>/今日头条草稿信息.txt
```

记录了长文草稿与微头条草稿的保存时间、标题、封面模式与状态凭据。

---

## 手机/电脑端一键发布

- **电脑端**：登录 [头条号创作者平台 (mp.toutiao.com)](https://mp.toutiao.com/) ➔ 进入【作品管理】➔【草稿箱】➔ 点击【发布】。
- **手机端**：打开【今日头条 App】➔ 点击底部【+ 发布】➔ 进入【草稿箱】➔ 点击【发布】。
