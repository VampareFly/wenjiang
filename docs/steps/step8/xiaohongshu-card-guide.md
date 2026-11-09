# 小红书卡片指南

本文件定义 Step 8。使用 `guizang-social-card-skill`，基于 `article.md`、`xiaohongshu-strategy.json`、公众号封面和正文配图生成 1080×1440（3:4）卡片。

正式输出：

```text
小红书卡片-{01-N}.png
```

检查记录：

```text
xiaohongshu-card-check.json
```

## 内容一致性与爆款首图

- 封面必须围绕策略中的 `primary_keyword` 和 `content_angle`，但不得复制公众号标题。
- **首图大标题必须采用小红书爆款标题 5 大公式之一**（反直觉冲突/扎心痛点/避坑警告/权威背书/极简自救），字号醒目、带有强烈情绪反差或疑问冲击力，自动选取契合模式，不需向用户过问。
- 卡片只使用字幕、`article.md` 和 `article.plan.md` 中已有事实，不使用热点搜索结果补充事实。
- `小红书卡片-01.png` 固定为首图，**强制执行“首图必须含图”与“自然杂志美学”铁律，严禁交付任何纯文字/纯数字封面，严禁使用科幻发光浮夸插图**。
- **首图统一采用【画报三段流（方案 A 标准）】**：
  - **顶部**：领域胶囊标签 + 爆款扎心反问大标题；
  - **中部（核心视觉区）**：置入高度 480~540px 的自然质感视觉大图（优先复用正文最精彩的自然光食材特写、生活方式抓拍或极简科学图解；亦可在生图阶段专门针对**真实生活静物、自然光食材、舒适生活场景**重新生成专属大图，严禁发光器官/霓虹光效/夸张惊悚表情），带 20px 圆角、微光阴影与底部结论浮层；
  - **底部**：3 组结构化数据柱 + 底部行动提示条，全幅纵向撑满；
- 备选版式仅允许【全屏杂志画报流】（生成自然质感艺术大图铺满全屏背景并压衬线大标题），现有素材不适合 3:4 构图时才新增竖版素材。

## 视觉系统

- 默认使用 `Editorial Magazine x E-ink`，一套卡片只用一种色盘与视觉系统。
- 每页必须有可感知的纸张底色、纸纹和弱墨晕/等高线层，不得交付纯白或单一扁平底色。
- 首图背景强于正文；正文页降低背景对比度，不能干扰数字和小字。
- 健康研究/数据类优先 `Indigo Porcelain`，饮食/生活方式优先 `Forest Ink`，中性科普优先 `Ink Classic`。
- 正文信息图用 `object-fit:contain`，不得为了塞进单页把字体缩小到手机不可读。

## 固定画布门禁

- 所有 PNG 必须为 1080×1440。
- 文件从 `01` 连续编号，不得重复图片。
- 主体内容必须为 footer 预留至少 24px 安全间距。
- 正文最小字号、溢出、背景层、标题间距和画布密度必须在截图前用程序测量。
- 首图另做一次 AI 视觉复查：缩略图醒目、标题一眼读懂、无无意义大空白、主视觉支持标题、背景不影响阅读。

## 检查记录契约

`xiaohongshu-card-check.json` 必须记录全部页面：

```json
{
  "schema_version": 1,
  "pages": [
    {
      "file": "小红书卡片-01.png",
      "width": 1080,
      "height": 1440,
      "overflow": false,
      "min_font_px": 28,
      "footer_gap_px": 24,
      "background_layer": true
    }
  ],
  "cover_review": {
    "reviewed": true,
    "thumbnail_clear": true,
    "title_clear": true,
    "meaningful_visual": true,
    "no_dead_space": true,
    "background_supports_reading": true
  }
}
```

程序报告与实际 PNG 文件名、尺寸必须完全一致。不得手工填写通过结果来替代真实测量。

完成后运行：

```bash
python3 scripts/validate_workflow.py cards articles/<YYYYMMDD-HHMMSS>
python3 scripts/validate_workflow.py xhs-card-check articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_8
```

临时 HTML、JS、截图脚本和 debug 文件在本步骤完成后删除。
