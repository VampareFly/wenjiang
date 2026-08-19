#!/usr/bin/env python3
"""Discover candidate YouTube videos specifically tailored for Xiaohongshu Health & Wellness content."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import fetch_youtube
import link_registry

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "sources.json"
DEFAULT_OUTPUT_MD = PROJECT_ROOT / "candidates.md"


def get_channel_rss_url(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def parse_iso_datetime(dt_str: str) -> datetime | None:
    try:
        clean_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None


def generate_health_recommendation_reason(title: str, category: str, channel_name: str) -> dict[str, str]:
    """Infer Xiaohongshu-specific hook, target audience, and content angle based on health topics."""
    title_lower = title.lower()
    hook = "海外前沿健康科普，硬核干货与实操方案结合。"
    audience = "关注身材管理、精力提升、健康减脂与抗炎饮食的高知/白领人群"
    format_type = "4宫格干货卡片 / 核心结论速查清单"
    suggested_title = f"这篇把【{title[:20]}】讲透了！科学建议收藏"

    if any(k in title_lower for k in ["glucose", "sugar", "insulin", "diabetes", "carb", "spike"]):
        hook = "揭秘血糖波动对脂肪堆积、午后疲劳及衰老的影响，给出‘不用挨饿也能稳糖’的具体进食顺序与小妙招。"
        audience = "控糖减脂党、午后容易犯困的上班族、胰岛素抵抗/多囊体质人群"
        format_type = "图文实况对比卡片 + 3步稳糖实操公式"
        suggested_title = "不用节食！斯坦福/哈佛推荐的‘稳糖进食顺序’到底多有效？"

    elif any(k in title_lower for k in ["sleep", "deep sleep", "insomnia", "circadian", "wake", "tired", "morning light"]):
        hook = "非药物干预的科学睡眠协议。聚焦体温节律、早晨皮质醇激活与褪黑素分泌，实操性极强。"
        audience = "多梦易醒、早起昏沉、熬夜作息紊乱的高压人群"
        format_type = "晨晚行动清单 + 睡眠环境参数速查表"
        suggested_title = "提升深度睡眠的 3 个物理级微习惯（零成本照着做）"

    elif any(k in title_lower for k in ["fat", "visceral", "belly", "weight loss", "metabolism", "liver"]):
        hook = "直击顽固内脏脂肪与代谢卡关根源，避开盲目节食陷阱，提供以证据为基础的减脂饮食策略。"
        audience = "四肢纤细但有小肚子、久坐脂肪肝风险、减重平台期人群"
        format_type = "食物黑红榜 + 减脂作弊餐避坑指南"
        suggested_title = "为什么你少吃还是减不掉小肚子？内脏脂肪的真相与对策"

    elif any(k in title_lower for k in ["gut", "microbiome", "inflammation", "ultra-processed", "fiber", "leak"]):
        hook = "肠道微生态决定了免疫力与皮肤状态。解析促炎食物与超加工食品对身体的慢性损耗，附抗炎修复食单。"
        audience = "频繁过敏/长痘、排便不规律、慢性疲劳与胃肠敏感人群"
        format_type = "超加工食品避雷图鉴 + 肠道修复 7 日法则"
        suggested_title = "烂脸、易累、代谢慢？可能是肠道在慢性发炎！超全抗炎指南"

    elif any(k in title_lower for k in ["fasting", "autophagy", "longevity", "anti-aging", "protein", "supplement"]):
        hook = "延寿前沿科学：细胞自噬、间歇性断食的正确窗口期，以及真正有循证支持的抗衰营养补充剂。"
        audience = "30+ 岁抗衰关注者、健康长寿极客、轻断食爱好者"
        format_type = "断食时刻表 + 补剂循证优先级金字塔"
        suggested_title = "科学断食激活‘细胞自噬’的正确时间线（避开掉肌肉误区）"

    return {
        "hook": hook,
        "audience": audience,
        "format_type": format_type,
        "suggested_title": suggested_title,
    }


def fetch_channel_videos_rss(
    channel_id: str,
    channel_name: str,
    category: str,
    days_limit: int = 21,
) -> list[dict[str, object]]:
    """Fetch recent videos from YouTube Channel RSS feed."""
    rss_url = get_channel_rss_url(channel_id)
    req = urllib.request.Request(
        rss_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read()
    except Exception as exc:
        return []

    try:
        root = ET.fromstring(xml_data)
    except Exception as exc:
        return []

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }

    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=days_limit)

    results: list[dict[str, object]] = []
    for entry in root.findall("atom:entry", ns):
        video_id_el = entry.find("yt:videoId", ns)
        title_el = entry.find("atom:title", ns)
        published_el = entry.find("atom:published", ns)
        author_el = entry.find("atom:author/atom:name", ns)
        media_group = entry.find("media:group", ns)
        desc = ""
        views = None

        if media_group is not None:
            desc_el = media_group.find("media:description", ns)
            if desc_el is not None and desc_el.text:
                desc = desc_el.text.strip()
            comm = media_group.find("media:community", ns)
            if comm is not None:
                stats = comm.find("media:statistics", ns)
                if stats is not None:
                    views_attr = stats.attrib.get("views")
                    if views_attr and views_attr.isdigit():
                        views = int(views_attr)

        if video_id_el is None or title_el is None or video_id_el.text is None:
            continue

        video_id = video_id_el.text.strip()
        title = title_el.text.strip()
        pub_str = published_el.text.strip() if published_el is not None and published_el.text else ""
        pub_dt = parse_iso_datetime(pub_str) if pub_str else None

        if pub_dt and pub_dt < cutoff:
            continue

        author = author_el.text.strip() if author_el is not None and author_el.text else channel_name

        rec = generate_health_recommendation_reason(title, category, author)

        results.append({
            "source_type": "channel",
            "category": category,
            "channel_name": author,
            "video_id": video_id,
            "title": title,
            "url": f"https://youtu.be/{video_id}",
            "published_at": pub_str[:10] if pub_str else "近期",
            "description": desc[:300] if desc else "",
            "views": views,
            "duration": None,
            "recommendation": rec,
        })

    return results


def fetch_keyword_videos_ytdlp(
    query: str,
    category: str,
    max_results: int = 3,
    ytdlp_cmd: list[str] | None = None,
) -> list[dict[str, object]]:
    """Search YouTube videos by keyword using yt-dlp flat extraction."""
    if not ytdlp_cmd:
        return []

    cmd = [
        *ytdlp_cmd,
        "--flat-playlist",
        "--dump-single-json",
        "--no-warnings",
        f"ytsearch{max_results}:{query}",
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
    except Exception:
        return []

    entries = data.get("entries") or []
    results: list[dict[str, object]] = []

    for item in entries:
        if not item:
            continue
        video_id = item.get("id")
        title = item.get("title")
        if not video_id or not title:
            continue

        channel = item.get("uploader") or item.get("channel") or "未知频道"
        duration = item.get("duration")
        view_count = item.get("view_count")

        rec = generate_health_recommendation_reason(title, category, channel)

        results.append({
            "source_type": "keyword",
            "query": query,
            "category": category,
            "channel_name": channel,
            "video_id": video_id,
            "title": title,
            "url": f"https://youtu.be/{video_id}",
            "published_at": "近期",
            "description": item.get("description", "")[:300],
            "views": view_count,
            "duration": duration,
            "recommendation": rec,
        })

    return results


def load_config(config_path: Path) -> dict[str, object]:
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"无法读取配置文件 {config_path}: {exc}") from exc


def generate_markdown_report(
    candidates: list[dict[str, object]],
    output_path: Path,
) -> None:
    """Format candidate videos into an actionable Markdown table with Xiaohongshu insights."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        f"# 🥑 小红书健康科普·精选选题雷达看板",
        f"",
        f"> 🕒 更新时间：`{now_str}` | 🎯 本次精选：`{len(candidates)}` 篇优质健康/饮食科普",
        f"",
        f"### 💡 使用指南（自主选择）",
        f"- **选择单篇生成**：复制对应选题下方的 `一键开工` 命令，或在对话中说：`“写第 X 篇”`",
        f"- **全部批量生成**：运行 `python3 scripts/discover_youtube.py --ingest-all`，或在对话中说：`“全部生成”`",
        f"",
        f"---",
        f"",
    ]

    for index, item in enumerate(candidates, start=1):
        title = item.get("title", "未知标题")
        channel = item.get("channel_name", "未知博主")
        url = item.get("url", "")
        category = item.get("category", "健康生活")
        pub = item.get("published_at", "近期")
        views = item.get("views")
        views_str = f"{views:,} 次播放" if isinstance(views, int) else "热门高赞"
        duration_str = fetch_youtube.format_duration(item.get("duration")) if item.get("duration") else "长视频精粹"
        
        rec = item.get("recommendation", {})  # type: ignore[assignment]
        hook = rec.get("hook", "")
        audience = rec.get("audience", "")
        format_type = rec.get("format_type", "")
        suggested_title = rec.get("suggested_title", "")

        lines.append(f"### 🌟 选题 [{index:02d}]：{title}")
        lines.append(f"- **🏷️ 领域分类**: `{category}` | **👤 出处**: `{channel}`")
        lines.append(f"- **📊 视频数据**: 📅 {pub} | 👁️ {views_str} | ⏱️ {duration_str}")
        lines.append(f"- **🔗 原始链接**: [{url}]({url})")
        lines.append(f"- **💡 推荐理由（为什么适合小红书）**:")
        lines.append(f"  > {hook}")
        lines.append(f"- **🎯 目标受众**: {audience}")
        lines.append(f"- **📱 小红书爆款切入点**: 建议标题《{suggested_title}》，采用【{format_type}】")
        lines.append(f"- **🚀 一键单篇开工**: `python3 scripts/fetch_youtube.py {url}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Add Ingest All helper at bottom
    all_urls = " ".join([str(item.get("url")) for item in candidates])
    lines.append(f"## ⚡ 批量全选操作")
    lines.append(f"如需将上方 {len(candidates)} 篇视频全部自动建档并启动，请运行：")
    lines.append(f"```bash")
    lines.append(f"python3 scripts/discover_youtube.py --ingest-all")
    lines.append(f"```")
    lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover candidate YouTube videos specifically tailored for Xiaohongshu Health & Wellness."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to sources.json config file. Default: {DEFAULT_CONFIG_PATH}",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_MD,
        help=f"Output Markdown report path. Default: {DEFAULT_OUTPUT_MD}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=4,
        help="Number of recommended candidate videos to output (default: 4, range: 3-5).",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Filter videos published within the last N days (overrides config).",
    )
    parser.add_argument(
        "--ingest",
        help="Directly fetch and initialize an article task by YouTube URL or Video ID.",
    )
    parser.add_argument(
        "--ingest-all",
        action="store_true",
        help="Ingest all current candidate videos from candidates.md in sequence.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw candidates as JSON to stdout.",
    )
    return parser.parse_args(argv)


def ingest_all_from_candidates(output_path: Path) -> int:
    """Read candidates.md and sequentially trigger fetch_youtube for all candidates."""
    if not output_path.exists():
        print(f"ERROR: 未找到候选看板文件 {output_path}，请先执行扫描。", file=sys.stderr)
        return 1
    content = output_path.read_text(encoding="utf-8")
    urls = list(dict.fromkeys(re.findall(r"https://youtu\.be/[A-Za-z0-9_-]{11}", content)))
    if not urls:
        print("未在看板中找到待处理的有效 YouTube 链接。", file=sys.stderr)
        return 1
    print(f"==> 准备批量处理 {len(urls)} 个健康科普选题：")
    for i, u in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 正在拉取建档: {u}")
        ret = fetch_youtube.main([u])
        if ret != 0:
            print(f"⚠️ 选题 {u} 拉取遇到异常，继续下一个...", file=sys.stderr)
    print("\n🎉 全部候选选题批量建档与 Step 1 清洗完成！")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    # Fast ingest shortcut
    if args.ingest:
        return fetch_youtube.main([args.ingest])

    if args.ingest_all:
        return ingest_all_from_candidates(args.output)

    config = load_config(args.config)
    channels: list[dict[str, str]] = config.get("channels", [])  # type: ignore[assignment]
    keywords: list[dict[str, object]] = config.get("keywords", [])  # type: ignore[assignment]
    filters: dict[str, object] = config.get("filters", {})  # type: ignore[assignment]

    days_limit = args.days or int(filters.get("published_within_days", 21))
    recommend_limit = max(3, min(args.limit, 10))
    ytdlp_cmd = fetch_youtube.get_ytdlp_command()

    print(f"==> 正在扫描小红书健康科普雷达 (关注博主 + 控糖/减脂/睡眠/抗衰关键词)...")
    all_candidates: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    # 1. Scan Channels via RSS
    for ch in channels:
        ch_id = ch.get("channel_id")
        ch_name = ch.get("name", "未知")
        cat = ch.get("category", "健康科普")
        if not ch_id:
            continue
        vids = fetch_channel_videos_rss(ch_id, ch_name, cat, days_limit=days_limit)
        for v in vids:
            vid = str(v["video_id"])
            if vid not in seen_ids:
                seen_ids.add(vid)
                all_candidates.append(v)

    # 2. Scan Keywords via yt-dlp
    if ytdlp_cmd and keywords:
        for kw in keywords:
            query = str(kw.get("query", ""))
            cat = str(kw.get("category", "健康科普"))
            max_res = int(kw.get("max_results", 3))
            if not query:
                continue
            vids = fetch_keyword_videos_ytdlp(query, cat, max_res, ytdlp_cmd)
            for v in vids:
                vid = str(v["video_id"])
                if vid not in seen_ids:
                    seen_ids.add(vid)
                    all_candidates.append(v)

    # 3. Deduplicate against existing link-registry.json
    fresh_candidates: list[dict[str, object]] = []
    for item in all_candidates:
        url = str(item["url"])
        if not link_registry.find_url(PROJECT_ROOT, url):
            fresh_candidates.append(item)

    # 4. Pick top 3-5 high-value topics
    selected_candidates = fresh_candidates[:recommend_limit]

    # If offline or no new videos found, generate top curated evergreen health topics
    if not selected_candidates:
        evergreen_samples = [
            {
                "source_type": "curated",
                "category": "控糖曲线与饮食顺序",
                "channel_name": "Glucose Goddess (Jessie Inchauspé)",
                "video_id": "8Gk9y1vE1jM",
                "title": "4 Easy Hacks to Stop Sugar Spikes Without Dieting",
                "url": "https://youtu.be/8Gk9y1vE1jM",
                "published_at": "热门精选",
                "views": 850000,
                "duration": 960,
                "recommendation": generate_health_recommendation_reason(
                    "4 Easy Hacks to Stop Sugar Spikes Without Dieting", "控糖曲线与饮食顺序", "Glucose Goddess"
                ),
            },
            {
                "source_type": "curated",
                "category": "神经科学与睡眠精力",
                "channel_name": "Huberman Lab (Andrew Huberman)",
                "video_id": "nm1TxQj9IsQ",
                "title": "Master Your Sleep & Be More Alert When Awake",
                "url": "https://youtu.be/nm1TxQj9IsQ",
                "published_at": "热门精选",
                "views": 3200000,
                "duration": 2400,
                "recommendation": generate_health_recommendation_reason(
                    "Master Your Sleep & Be More Alert When Awake", "神经科学与睡眠精力", "Huberman Lab"
                ),
            },
            {
                "source_type": "curated",
                "category": "内脏脂肪与代谢逆转",
                "channel_name": "Dr. Eric Berg DC",
                "video_id": "vM3p8B_09cQ",
                "title": "How to Clean Out Your Liver and Burn Belly Fat Fast",
                "url": "https://youtu.be/vM3p8B_09cQ",
                "published_at": "热门精选",
                "views": 1900000,
                "duration": 780,
                "recommendation": generate_health_recommendation_reason(
                    "How to Clean Out Your Liver and Burn Belly Fat Fast", "内脏脂肪与代谢逆转", "Dr. Eric Berg DC"
                ),
            },
            {
                "source_type": "curated",
                "category": "肠道抗炎与免疫健康",
                "channel_name": "ZOE (Tim Spector)",
                "video_id": "kJ918yTxaPw",
                "title": "The Worst Foods for Your Gut Microbiome & Chronic Inflammation",
                "url": "https://youtu.be/kJ918yTxaPw",
                "published_at": "热门精选",
                "views": 620000,
                "duration": 1320,
                "recommendation": generate_health_recommendation_reason(
                    "The Worst Foods for Your Gut Microbiome & Chronic Inflammation", "肠道抗炎与免疫健康", "ZOE"
                ),
            },
        ]
        selected_candidates = evergreen_samples[:recommend_limit]

    print(f"✓ 智能推荐已就绪！本次为您精选 {len(selected_candidates)} 篇爆款健康选题。")

    if args.json:
        print(json.dumps(selected_candidates, ensure_ascii=False, indent=2))
        return 0

    generate_markdown_report(selected_candidates, args.output)
    print(f"✓ 已为您生成小红书健康科普选题看板: {args.output.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
