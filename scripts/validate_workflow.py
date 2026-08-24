#!/usr/bin/env python3
"""Validate objective gates in the article production workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


REQUIRED_FRONTMATTER = ("title", "description", "author")
TITLE_MAX_LENGTH = 32
TITLE_BANNED_WORDS = (
    "一文读懂",
    "揭秘",
    "真相",
    "密码",
    "底层逻辑",
    "颠覆认知",
    "权威解读",
    "终极指南",
    "原来",
    "竟然",
    "没想到",
    "悄悄",
    "比你想象中",
)
TITLE_BANNED_PATTERNS = (
    re.compile(r"为什么.+[？?].*(问题不在|靠的是)"),
    re.compile(r"真正的?.+[，,:：]?(是|在于|不是|并非)"),
    re.compile(r"真正.+不是"),
    re.compile(r".+骗不了你的.+"),
    re.compile(r"身体比你更懂"),
    re.compile(r"你的.+正在"),
    re.compile(r"不是.+而是"),
    re.compile(r"从.+到.+"),
    re.compile(r"重新(理解|认识|定义|看待|思考)"),
    re.compile(r"被偷走|被毁掉|正在被"),
)
XHS_COPY_BANNED_TERMS = (
    "公众号",
    "二维码",
    "微信",
    "加V",
    "底层逻辑",
    "完整真相",
    "颠覆认知",
    "完全安全",
    "保证有效",
    "根治",
    "科学清除",
    "坚决截止",
    "修复窗口",
    "暴击受体",
)
XHS_COPY_BANNED_PATTERNS = (
    re.compile(r"今天我们(?:先)?抛开.{0,12}情绪"),
    re.compile(r"这篇只是把.{0,40}拎了出来"),
    re.compile(r"完整版我写在同名主页那篇长文里了"),
    re.compile(r"想.{0,20}底层逻辑.{0,10}去翻一下"),
)
SOURCE_EXPOSURE_PATTERNS = (
    re.compile(r"字幕(?:里|中)"),
    re.compile(r"字幕(?:提到|显示|写到|给出)"),
    re.compile(r"(?:视频|播客|节目|访谈)(?:里|中)(?:提到|讲到|说到|指出|给出)?"),
    re.compile(r"今天的节目"),
)
MARKER_RE = re.compile(r"【配图(\d+)：([^】]+)】")
PROMPT_MARKER_RE = re.compile(r"^##\s+【配图(\d+)：([^】]+)】\s*$", re.MULTILINE)
FINAL_FIXED = {
    "article.md",
    "article.html",
    "cover.png",
    "公众号草稿信息.txt",
    "小红书文案.txt",
    "workflow-state.json",
}
SOURCE_MAPPING_OPTIONAL = {"source-link.txt", "source-map.json"}
TOUTIAO_OPTIONAL = {"今日头条文章.md", "微头条.txt"}
FINAL_OPTIONAL = SOURCE_MAPPING_OPTIONAL | TOUTIAO_OPTIONAL
FINAL_PATTERNS = (
    re.compile(r"配图\d+\.png"),
    re.compile(r"小红书卡片-\d{2}\.png"),
    re.compile(r"toutiao-cover-[1-3]\.png"),
    re.compile(r"source\.(?:srt|vtt|txt)"),
)


TOUTIAO_BANNED_TERMS = (
    "公众号",
    "二维码",
    "微信",
    "加V",
    "扫码关注",
    "私信回复",
    "底层逻辑",
    "颠覆认知",
    "完全安全",
    "保证有效",
    "根治",
    "科学清除",
)



def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse the flat YAML subset used by article frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return {}, text

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        metadata[key.strip()] = value
    return metadata, "\n".join(lines[end + 1 :])


def extract_markers(text: str) -> list[tuple[int, str]]:
    return [(int(number), title.strip()) for number, title in MARKER_RE.findall(text)]


def _read_text(path: Path, label: str) -> tuple[str | None, list[str]]:
    if not path.is_file():
        return None, [f"缺少{label}：{path.name}"]
    try:
        return path.read_text(encoding="utf-8"), []
    except UnicodeDecodeError:
        return None, [f"{label}不是有效 UTF-8：{path.name}"]


def _read_json(path: Path, label: str) -> tuple[dict[str, object] | None, list[str]]:
    text, errors = _read_text(path, label)
    if text is None:
        return None, errors
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [f"{label}不是有效 JSON：{exc}"]
    if not isinstance(payload, dict):
        return None, [f"{label}顶层必须是对象"]
    return payload, errors


def validate_article(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    text, errors = _read_text(article_dir / "article.md", "终稿")
    if text is None:
        return errors

    metadata, body = parse_frontmatter(text)
    for field in REQUIRED_FRONTMATTER:
        if not metadata.get(field, "").strip():
            errors.append(f"article.md frontmatter 缺少 {field}")

    title = metadata.get("title", "").strip()
    if len(title) > TITLE_MAX_LENGTH:
        errors.append(f"标题超过 {TITLE_MAX_LENGTH} 字：{len(title)}")
    for word in TITLE_BANNED_WORDS:
        if word in title:
            errors.append(f"标题包含 AI/营销高风险词：{word}")
    if any(pattern.search(title) for pattern in TITLE_BANNED_PATTERNS):
        errors.append("标题命中高频 AI 模板，必须重新生成")
    if "候选标题" in body:
        errors.append("正文残留候选标题列表")

    visible_text = "\n".join(
        (metadata.get("title", ""), metadata.get("description", ""), body)
    )
    if any(pattern.search(visible_text) for pattern in SOURCE_EXPOSURE_PATTERNS):
        errors.append("article.md 存在‘字幕里/视频中提到’等来源暴露表达")

    markers = extract_markers(body)
    if not markers:
        errors.append("article.md 缺少正文配图标记")
    else:
        numbers = [number for number, _ in markers]
        expected = list(range(1, len(markers) + 1))
        if numbers != expected:
            errors.append(f"配图编号必须从 1 连续递增，当前为 {numbers}")
        if len(set(markers)) != len(markers):
            errors.append("article.md 存在重复配图标记")
    return errors


def validate_prompts(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    article_text, errors = _read_text(article_dir / "article.md", "终稿")
    prompt_text, prompt_errors = _read_text(article_dir / "cover_prompt.md", "配图提示词")
    errors.extend(prompt_errors)
    if article_text is None or prompt_text is None:
        return errors

    _, body = parse_frontmatter(article_text)
    article_markers = extract_markers(body)
    prompt_markers = [
        (int(number), title.strip())
        for number, title in PROMPT_MARKER_RE.findall(prompt_text)
    ]
    if article_markers != prompt_markers:
        errors.append(
            "article.md 与 cover_prompt.md 的配图编号或标题不一致："
            f"article={article_markers}, prompts={prompt_markers}"
        )
    if "WeChat Official Account article cover, primary crop 2.35:1" not in prompt_text:
        errors.append("封面提示词缺少公众号 2.35:1 主裁剪要求")
    for i in (1, 2, 3):
        if f"头条封面{i}" not in prompt_text and f"toutiao-cover-{i}" not in prompt_text:
            errors.append(f"cover_prompt.md 缺少今日头条专属三图封面提示词【头条封面{i}】")
    return errors


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()[:24]
    except OSError:
        return None
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def _validate_png(path: Path, target_ratio: float, ratio_label: str) -> list[str]:
    if not path.is_file():
        return [f"缺少图片：{path.name}"]
    dimensions = _png_dimensions(path)
    if dimensions is None:
        return [f"图片不是可识别的 PNG：{path.name}"]
    width, height = dimensions
    if width <= 0 or height <= 0:
        return [f"图片尺寸无效：{path.name} ({width}×{height})"]
    if abs(width / height - target_ratio) > 0.08:
        return [f"图片比例不是 {ratio_label}：{path.name} ({width}×{height})"]
    return []


def validate_images(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    article_text, errors = _read_text(article_dir / "article.md", "终稿")
    if article_text is None:
        return errors
    _, body = parse_frontmatter(article_text)
    markers = extract_markers(body)

    errors.extend(_validate_png(article_dir / "cover.png", 2.35, "2.35:1"))
    for number, _ in markers:
        errors.extend(
            _validate_png(article_dir / f"配图{number}.png", 16 / 9, "16:9")
        )
    actual_numbers = sorted(
        int(match.group(1))
        for path in article_dir.glob("配图*.png")
        if (match := re.fullmatch(r"配图(\d+)\.png", path.name))
    )
    expected_numbers = [number for number, _ in markers]
    if actual_numbers != expected_numbers:
        errors.append(
            f"正文图片文件与配图标记不一致：expected={expected_numbers}, actual={actual_numbers}"
        )
    image_paths = [article_dir / "cover.png"] + [
        article_dir / f"配图{number}.png" for number, _ in markers
    ]
    toutiao_covers = [article_dir / f"toutiao-cover-{i}.png" for i in (1, 2, 3)]
    for i, path in enumerate(toutiao_covers, start=1):
        if not path.is_file():
            errors.append(f"缺少今日头条专属封面：toutiao-cover-{i}.png")
        else:
            errors.extend(_validate_png(path, 16 / 9, "16:9"))
            image_paths.append(path)

    hashes: dict[str, list[str]] = {}
    for path in image_paths:
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            hashes.setdefault(digest, []).append(path.name)
    for duplicate_names in hashes.values():
        if len(duplicate_names) > 1:
            errors.append(
                "图片内容重复，禁止用同一张图代替多张配图/封面："
                + "、".join(duplicate_names)
            )
    return errors




class _ImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "img":
            self.images.append({key.lower(): value or "" for key, value in attrs})


def validate_html(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    article_text, errors = _read_text(article_dir / "article.md", "终稿")
    html_text, html_errors = _read_text(article_dir / "article.html", "公众号 HTML")
    errors.extend(html_errors)
    if article_text is None or html_text is None:
        return errors

    _, body = parse_frontmatter(article_text)
    markers = extract_markers(body)
    if "【配图" in html_text:
        errors.append("article.html 残留配图占位符")

    parser = _ImageParser()
    try:
        parser.feed(html_text)
    except Exception as exc:  # HTMLParser may expose malformed entity errors.
        errors.append(f"article.html 无法解析：{exc}")
        return errors
    if len(parser.images) != len(markers):
        errors.append(
            f"HTML 图片数量与正文标记不一致：expected={len(markers)}, actual={len(parser.images)}"
        )

    for index, (number, title) in enumerate(markers):
        if index >= len(parser.images):
            break
        image = parser.images[index]
        expected_src = f"配图{number}.png"
        if image.get("src") != expected_src:
            errors.append(f"HTML 图片必须使用相对路径 {expected_src}")
        if not image.get("alt", "").strip():
            errors.append(f"HTML 图片 {expected_src} 缺少 alt")
        elif image["alt"].strip() != title:
            errors.append(
                f"HTML 图片 {expected_src} 的 alt 与配图标题不一致：{image['alt']}"
            )
    return errors


IMG_STYLE = 'display: block; max-width: 100%; height: auto; margin: 1.5em auto;'


def fix_html_images(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    html_path = article_dir / "article.html"
    text, errors = _read_text(html_path, "公众号 HTML")
    if text is None:
        return errors

    fixed_count = 0

    def _fix_img_style(m: re.Match[str]) -> str:
        nonlocal fixed_count
        fixed_count += 1
        tag = m[0]
        tag = re.sub(r'\s+style=["\'][^"\']*["\']', "", tag)
        if tag.rstrip().endswith("/>"):
            tag = tag.rstrip()[:-2] + f' style="{IMG_STYLE}" />'
        else:
            tag = tag.rstrip()[:-1] + f' style="{IMG_STYLE}">'
        return tag

    updated = re.sub(r'<img\b[^>]*/?>', _fix_img_style, text, flags=re.IGNORECASE)
    if fixed_count == 0:
        if "<img" in text:
            errors.append("article.html 存在 <img 标签但正则未能匹配")
        return errors

    html_path.write_text(updated, encoding="utf-8")
    print(f"[fix-html-images] 已修正 {fixed_count} 个 <img> 标签的 style", file=sys.stderr)
    return errors


def _is_final_asset(name: str) -> bool:
    return name in FINAL_FIXED or name in FINAL_OPTIONAL or any(pattern.fullmatch(name) for pattern in FINAL_PATTERNS)


def validate_final(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    errors: list[str] = []
    for name in sorted(FINAL_FIXED):
        path = article_dir / name
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"缺少或为空的最终资产：{name}")

    body_images = sorted(article_dir.glob("配图*.png"))
    cards = sorted(article_dir.glob("小红书卡片-*.png"))
    source_subtitles = [
        path for path in article_dir.glob("source.*")
        if path.suffix.lower() in {".srt", ".vtt", ".txt"}
    ]
    if not body_images:
        errors.append("缺少正文配图最终资产")
    if not cards:
        errors.append("缺少小红书卡片最终资产")
    if len(source_subtitles) != 1 or source_subtitles[0].stat().st_size == 0:
        errors.append("必须保留且只能保留一个非空源字幕：source.srt/source.vtt/source.txt")
    mapping_assets = [name for name in SOURCE_MAPPING_OPTIONAL if (article_dir / name).is_file()]
    if mapping_assets and len(mapping_assets) != len(SOURCE_MAPPING_OPTIONAL):
        errors.append("来源链接归档必须同时保留 source-link.txt 和 source-map.json")


    for path in article_dir.iterdir() if article_dir.is_dir() else ():
        if not path.is_file() or not _is_final_asset(path.name):
            errors.append(f"发现非最终资产：{path.name}")
    return errors


def validate_cleaned_subtitle(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    text, errors = _read_text(article_dir / "source.cleaned.txt", "清洗字幕")
    if text is None:
        return errors
    if not text.strip():
        errors.append("source.cleaned.txt 为空")
    timecode = re.compile(
        r"(?:\d{1,2}:)?\d{2}:\d{2}[,.]\d{3}\s*-->\s*"
        r"(?:\d{1,2}:)?\d{2}:\d{2}[,.]\d{3}"
    )
    if timecode.search(text):
        errors.append("source.cleaned.txt 仍包含字幕时间轴")
    return errors


def validate_draft_record(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    text, errors = _read_text(article_dir / "公众号草稿信息.txt", "公众号草稿信息")
    if text is None:
        return errors
    if not re.search(r"media_id\s*[：:]\s*\S+", text):
        errors.append("公众号草稿信息.txt 缺少有效 media_id")
    return errors


def validate_cards(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    cards = sorted(article_dir.glob("小红书卡片-*.png"))
    if not cards:
        return ["缺少小红书卡片"]
    errors: list[str] = []
    numbers: list[int] = []
    for path in cards:
        match = re.fullmatch(r"小红书卡片-(\d{2})\.png", path.name)
        if not match:
            errors.append(f"小红书卡片命名不符合两位编号规则：{path.name}")
            continue
        numbers.append(int(match.group(1)))
        if path.stat().st_size == 0:
            errors.append(f"小红书卡片为空：{path.name}")
            continue
        dimensions = _png_dimensions(path)
        if dimensions != (1080, 1440):
            rendered = "无法识别" if dimensions is None else f"{dimensions[0]}×{dimensions[1]}"
            errors.append(f"小红书卡片必须为 1080×1440：{path.name} ({rendered})")
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        errors.append(f"小红书卡片编号必须从 01 连续递增，当前为 {numbers}")
    hashes: dict[str, list[str]] = {}
    for path in cards:
        if path.is_file() and path.stat().st_size > 0:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            hashes.setdefault(digest, []).append(path.name)
    for duplicate_names in hashes.values():
        if len(duplicate_names) > 1:
            errors.append(
                "小红书卡片内容重复，禁止复制同一张图片充当多张卡片："
                + "、".join(duplicate_names)
            )
    return errors


def validate_wechat_layout(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    payload, errors = _read_json(article_dir / "wechat-layout-check.json", "公众号排版检查记录")
    if payload is None:
        return errors
    expected = {
        "schema_version": 1,
        "renderer": "gzh-design-skill",
        "theme_id": "graphite-minimal",
        "brand_config": "config/wechat-brand.json",
        "gzh_errors": 0,
        "gzh_warnings": 0,
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            errors.append(f"公众号排版检查记录 {field} 必须为 {value!r}")
    preview = payload.get("mobile_preview")
    if not isinstance(preview, dict):
        errors.append("公众号排版检查记录缺少 mobile_preview")
        return errors
    if preview.get("viewport_width") not in range(360, 431):
        errors.append("公众号移动端预览宽度必须在 360-430px")
    for field in (
        "reviewed",
        "first_screen_clear",
        "headings_wrap_cleanly",
        "card_density_ok",
        "images_balanced",
        "spacing_consistent",
    ):
        if preview.get(field) is not True:
            errors.append(f"公众号移动端视觉检查未通过：{field}")
    html_text, html_errors = _read_text(article_dir / "article.html", "公众号 HTML")
    errors.extend(html_errors)
    if html_text is not None:
        for forbidden in ("<style", "<script", "<div", " class=", " id="):
            if forbidden in html_text.lower():
                errors.append(f"固定品牌 HTML 包含禁用结构：{forbidden.strip()}")
        for signature in ("max-width:677px", "line-height:1.8", "#52525B"):
            if signature not in html_text:
                errors.append(f"固定品牌 HTML 缺少石墨极简主题签名：{signature}")
    return errors


def validate_xiaohongshu_strategy(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    payload, errors = _read_json(
        article_dir / "xiaohongshu-strategy.json", "小红书策略"
    )
    if payload is None:
        return errors
    if payload.get("schema_version") != 1:
        errors.append("小红书策略 schema_version 必须为 1")
    mode = payload.get("mode")
    if mode not in {"live", "evergreen"}:
        errors.append("小红书策略 mode 必须为 live 或 evergreen")
    for field in ("primary_keyword", "search_intent", "content_angle", "cta_reason"):
        if not isinstance(payload.get(field), str) or not str(payload[field]).strip():
            errors.append(f"小红书策略缺少非空字段：{field}")
    secondary = payload.get("secondary_keywords")
    if not isinstance(secondary, list) or not 2 <= len(secondary) <= 5 or any(
        not isinstance(item, str) or not item.strip() for item in secondary
    ):
        errors.append("小红书策略 secondary_keywords 必须包含 2-5 个非空关键词")
    boundaries = payload.get("fact_boundaries")
    if not isinstance(boundaries, list) or not boundaries:
        errors.append("小红书策略必须记录 fact_boundaries")
    if payload.get("external_facts_used") is not False:
        errors.append("小红书策略 external_facts_used 必须为 false")
    cta_mode = payload.get("cta_mode")
    if cta_mode not in {"include", "omit"}:
        errors.append("小红书策略 cta_mode 必须为 include 或 omit")
    evidence = payload.get("trend_evidence")
    if not isinstance(evidence, list):
        errors.append("小红书策略 trend_evidence 必须为数组")
    elif mode == "live":
        if not isinstance(payload.get("researched_at"), str) or not payload["researched_at"]:
            errors.append("live 模式必须记录 researched_at")
        if len(evidence) < 2:
            errors.append("live 模式至少需要 2 条公开搜索趋势证据")
        for item in evidence:
            if not isinstance(item, dict) or not all(
                isinstance(item.get(field), str) and item.get(field)
                for field in ("title", "url", "observed_at")
            ):
                errors.append("live 模式趋势证据必须包含 title、url、observed_at")
                break
            if not re.match(r"https?://", str(item["url"])):
                errors.append("live 模式趋势证据 url 必须是完整 HTTP/HTTPS 链接")
                break
    elif mode == "evergreen":
        if payload.get("researched_at") is not None or evidence:
            errors.append("evergreen 模式不得伪造 researched_at 或 trend_evidence")
    return errors


def validate_xiaohongshu_card_check(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    payload, errors = _read_json(
        article_dir / "xiaohongshu-card-check.json", "小红书卡片检查记录"
    )
    if payload is None:
        return errors
    if payload.get("schema_version") != 1:
        errors.append("小红书卡片检查记录 schema_version 必须为 1")
    cards = sorted(article_dir.glob("小红书卡片-*.png"))
    expected_names = [path.name for path in cards]
    pages = payload.get("pages")
    if not isinstance(pages, list):
        errors.append("小红书卡片检查记录 pages 必须为数组")
    else:
        reported_names = [page.get("file") for page in pages if isinstance(page, dict)]
        if reported_names != expected_names:
            errors.append(
                "小红书卡片检查记录与实际文件不一致："
                f"expected={expected_names}, reported={reported_names}"
            )
        for page in pages:
            if not isinstance(page, dict):
                errors.append("小红书卡片检查记录包含无效页面")
                continue
            if page.get("width") != 1080 or page.get("height") != 1440:
                errors.append(f"卡片检查记录尺寸无效：{page.get('file')}")
            if page.get("overflow") is not False:
                errors.append(f"卡片存在文字溢出：{page.get('file')}")
            if not isinstance(page.get("min_font_px"), (int, float)) or page["min_font_px"] < 24:
                errors.append(f"卡片最小字号低于 24px：{page.get('file')}")
            if not isinstance(page.get("footer_gap_px"), (int, float)) or page["footer_gap_px"] < 24:
                errors.append(f"卡片 footer 安全间距不足：{page.get('file')}")
            if page.get("background_layer") is not True:
                errors.append(f"卡片缺少背景层：{page.get('file')}")
    review = payload.get("cover_review")
    if not isinstance(review, dict):
        errors.append("小红书卡片检查记录缺少 cover_review")
    else:
        for field in (
            "reviewed",
            "thumbnail_clear",
            "title_clear",
            "meaningful_visual",
            "no_dead_space",
            "background_supports_reading",
        ):
            if review.get(field) is not True:
                errors.append(f"小红书首图视觉复查未通过：{field}")
    return errors


def validate_xiaohongshu_copy(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    text, errors = _read_text(article_dir / "小红书文案.txt", "小红书文案")
    if text is None:
        return errors
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ["小红书文案.txt 为空"]
    if len(lines[0]) > 20:
        errors.append(f"小红书标题超过 20 字：{len(lines[0])}")
    topics = re.findall(r"(?<!\w)#[^\s#]+", text)
    if not 3 <= len(topics) <= 6:
        errors.append(f"小红书文案应包含 3-6 个话题，当前为 {len(topics)}")
    for term in XHS_COPY_BANNED_TERMS:
        if term in text:
            errors.append(f"小红书文案包含高风险/AI 模板词：{term}")
    for pattern in XHS_COPY_BANNED_PATTERNS:
        if pattern.search(text):
            errors.append(f"小红书文案命中固定 AI/引流模板：{pattern.pattern}")

    strategy_path = article_dir / "xiaohongshu-strategy.json"
    strategy: dict[str, object] | None = None
    if strategy_path.is_file():
        strategy, strategy_errors = _read_json(strategy_path, "小红书策略")
        errors.extend(strategy_errors)
    if strategy is not None:
        primary = strategy.get("primary_keyword")
        searchable_prefix = "".join(lines)[:120]
        if isinstance(primary, str) and primary not in searchable_prefix:
            errors.append("小红书主关键词必须自然出现在标题或正文前 120 字")
        cta_mode = strategy.get("cta_mode")
        has_cta = "主页" in text or "长文" in text or "完整版" in text or "去翻一下" in text
        if cta_mode == "include":
            if "主页" not in text or "长文" not in text:
                errors.append("策略要求长文引导时，文案需自然提到主页里的长文")
            cta_lines = [line for line in lines if "主页" in line or "长文" in line]
            if sum(len(line) for line in cta_lines) > 60:
                errors.append("小红书长文引导超过 60 字")
        elif cta_mode == "omit" and has_cta:
            errors.append("策略要求省略长文引导，但文案仍包含主页/长文引流")
    return errors


def validate_toutiao_article(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    path = article_dir / "今日头条文章.md"
    text, errors = _read_text(path, "今日头条文章")
    if text is None:
        return errors
    if not text.strip():
        return ["今日头条文章.md 为空"]
    for term in TOUTIAO_BANNED_TERMS:
        if term in text:
            errors.append(f"今日头条文章包含违规/AI词：{term}")
    if "标题候选" not in text and "候选标题" not in text:
        errors.append("今日头条文章需包含三段式标题候选")

    # 校验主标题长度不超过 30 字
    h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if h1_match:
        main_title = h1_match.group(1).strip().strip("《》")
        if len(main_title) > 30:
            errors.append(f"今日头条主标题超过 30 字（当前为 {len(main_title)} 字）：{main_title}")

    # 校验标题候选长度均不超过 30 字
    cand_lines = re.findall(r"(?:^|\n)\s*(?:>\s*)?(?:[1-9]\.|\d+、)\s*《?([^》\r\n]+)》?", text)
    for cand in cand_lines:
        cand_clean = cand.strip().strip("《》")
        if len(cand_clean) > 30:
            errors.append(f"今日头条标题候选超过 30 字（当前为 {len(cand_clean)} 字）：{cand_clean}")
    return errors



def validate_toutiao_micro(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    path = article_dir / "微头条.txt"
    text, errors = _read_text(path, "微头条文案")
    if text is None:
        return errors
    clean_text = text.strip()
    if not clean_text:
        return ["微头条.txt 为空"]
    if len(clean_text) < 100:
        errors.append(f"微头条字数过少（少于 100 字）：当前为 {len(clean_text)} 字")
    if len(clean_text) > 1000:
        errors.append(f"微头条字数过多（超过 1000 字）：当前为 {len(clean_text)} 字")
    topics = re.findall(r"(?<!\w)#[^\s#]+", text)
    if len(topics) < 1:
        errors.append("微头条文案应包含至少 1 个话题标签（如 #健康#）")
    for term in TOUTIAO_BANNED_TERMS:
        if term in text:
            errors.append(f"微头条包含违规/AI词：{term}")
    return errors



def validate_toutiao_covers(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    errors: list[str] = []
    covers = [article_dir / f"toutiao-cover-{i}.png" for i in (1, 2, 3)]
    for path in covers:
        if path.exists():
            errors.extend(_validate_png(path, 16 / 9, "16:9"))
    return errors


def validate_toutiao(article_dir: Path | str) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_toutiao_article(article_dir))
    errors.extend(validate_toutiao_micro(article_dir))
    errors.extend(validate_toutiao_covers(article_dir))
    return errors



def _frontmatter_version(text: str) -> str | None:
    metadata, _ = parse_frontmatter(text)
    return metadata.get("version")


def validate_skills(
    lock_path: Path | str,
    *,
    warnings: list[str] | None = None,
) -> list[str]:
    lock_path = Path(lock_path)
    warnings = warnings if warnings is not None else []
    if not lock_path.is_file():
        return [f"缺少 Skill 锁文件：{lock_path}"]
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"Skill 锁文件无效：{exc}"]

    errors: list[str] = []
    for name, expected in lock.get("skills", {}).items():
        skill_dir = Path(expected.get("path", ""))
        if not skill_dir.is_absolute():
            skill_dir = lock_path.parent / skill_dir
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"Skill {name} 缺少 SKILL.md：{skill_file}")
            continue
        try:
            text = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"Skill {name} 无法读取：{exc}")
            continue

        actual_version = _frontmatter_version(text)
        expected_version = expected.get("version")
        if expected_version is None and actual_version is not None:
            warnings.append(
                f"Skill {name} 版本漂移：verified=unversioned, actual={actual_version}"
            )
        elif expected_version is not None and actual_version != str(expected_version):
            warnings.append(
                f"Skill {name} 版本漂移：verified={expected_version}, actual={actual_version or 'unknown'}"
            )
        for entrypoint in expected.get("entrypoints", []):
            if not (skill_dir / entrypoint).is_file():
                errors.append(f"Skill {name} 缺少入口：{entrypoint}")
        for required_text in expected.get("required_text", []):
            if required_text not in text:
                errors.append(f"Skill {name} 缺少关键能力文本：{required_text}")
    return errors


def run_checks(article_dir: Path | str) -> list[str]:
    article_dir = Path(article_dir)
    errors = validate_article(article_dir)
    if (article_dir / "cover_prompt.md").exists():
        errors.extend(validate_prompts(article_dir))
    if (article_dir / "cover.png").exists():
        errors.extend(validate_images(article_dir))
    if (article_dir / "article.html").exists():
        errors.extend(validate_html(article_dir))
    if (article_dir / "wechat-layout-check.json").exists():
        errors.extend(validate_wechat_layout(article_dir))
    if (article_dir / "xiaohongshu-strategy.json").exists():
        errors.extend(validate_xiaohongshu_strategy(article_dir))
    if (article_dir / "xiaohongshu-card-check.json").exists():
        errors.extend(validate_cards(article_dir))
        errors.extend(validate_xiaohongshu_card_check(article_dir))
    if (article_dir / "小红书文案.txt").exists():
        errors.extend(validate_xiaohongshu_copy(article_dir))
    if (article_dir / "今日头条文章.md").exists() or (article_dir / "微头条.txt").exists():
        errors.extend(validate_toutiao(article_dir))
    state_path = article_dir / "workflow-state.json"
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            errors.append("workflow-state.json 无效")
        else:
            if state.get("steps", {}).get("step_12", {}).get("status") in {"running", "passed"}:
                errors.extend(validate_final(article_dir))
    return errors


def _print_result(errors: Iterable[str], warnings: Iterable[str] = ()) -> int:
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    errors = list(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "check",
        choices=(
            "article",
            "prompts",
            "images",
            "html",
            "wechat-layout",
            "xhs-strategy",
            "cards",
            "xhs-card-check",
            "xhs-copy",
            "toutiao-article",
            "toutiao-micro",
            "toutiao",
            "fix-html-images",
            "skills",
            "approval",
            "final",
            "all",
        ),
    )
    parser.add_argument("path", type=Path, help="Article directory or skills.lock.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check == "skills":
        warnings: list[str] = []
        return _print_result(validate_skills(args.path, warnings=warnings), warnings)
    if args.check == "approval":
        try:
            from scripts.workflow_state import validate_approval
        except ImportError:
            try:
                from workflow_state import validate_approval  # type: ignore[no-redef]
            except ImportError:
                return _print_result(["工作流状态模块尚未安装"])
        return _print_result(validate_approval(args.path))
    checks = {
        "article": validate_article,
        "prompts": validate_prompts,
        "images": validate_images,
        "html": validate_html,
        "wechat-layout": validate_wechat_layout,
        "xhs-strategy": validate_xiaohongshu_strategy,
        "cards": validate_cards,
        "xhs-card-check": validate_xiaohongshu_card_check,
        "xhs-copy": validate_xiaohongshu_copy,
        "toutiao-article": validate_toutiao_article,
        "toutiao-micro": validate_toutiao_micro,
        "toutiao": validate_toutiao,
        "fix-html-images": fix_html_images,
        "final": validate_final,
        "all": run_checks,
    }
    return _print_result(checks[args.check](args.path))


if __name__ == "__main__":
    raise SystemExit(main())

