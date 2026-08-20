# 微信公众号草稿创建指南

本文件定义 Step 11。只有 Step 10 获得当前对话中的统一确认后，才能创建微信公众号草稿。

执行前：

```bash
python3 scripts/validate_workflow.py approval articles/<YYYYMMDD-HHMMSS>
python3 scripts/workflow_state.py start articles/<YYYYMMDD-HHMMSS> step_11
```

固定使用 `baoyu-post-to-wechat` 的文章 API 路径，上传 `article.html` 中的本地正文图片与 `cover.png`，只创建草稿，不直接发布。成功后写入：

```text
公众号草稿信息.txt
```

文件必须包含非空 `media_id`。随后运行：

```bash
python3 scripts/workflow_state.py pass articles/<YYYYMMDD-HHMMSS> step_11
```

通过时更新 `source-map.json` 和根目录 `link-registry.json`，再按映射中的文件名、目录和 SHA-256 精确删除原始输入字幕、清空 `links/links.txt`。任何校验失败时保留输入并标记 blocked。
