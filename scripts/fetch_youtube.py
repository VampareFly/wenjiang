#!/usr/bin/env python3
"""Fetch YouTube subtitles, extract metadata, clean captions, and initialize article workflows."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Import existing workflow helpers from the same directory
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import clean_subtitle
import link_registry
import workflow_state


def get_ytdlp_command() -> list[str] | None:
    """Find available yt-dlp executable or python module."""
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    # Check if python3 -m yt_dlp is available
    try:
        res = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return [sys.executable, "-m", "yt_dlp"]
    except Exception:
        pass
    return None


def format_duration(seconds: int | float | None) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds:
        return "00:00"
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def normalize_youtube_url(url_or_id: str) -> tuple[str, str]:
    """Return (normalized_url, video_id)."""
    raw = url_or_id.strip()
    if re.match(r"^[A-Za-z0-9_-]{11}$", raw):
        return f"https://youtu.be/{raw}", raw
    try:
        norm = link_registry.normalize_url(raw)
        # Extract video ID from normalized youtu.be url
        m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", norm)
        video_id = m.group(1) if m else raw
        return norm, video_id
    except ValueError:
        # Fallback if raw string contains a youtube ID
        m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", raw)
        if m:
            vid = m.group(1)
            return f"https://youtu.be/{vid}", vid
        raise ValueError(f"无法识别的 YouTube 链接或视频 ID：{url_or_id}")


def download_subtitles_and_meta(
    url: str,
    ytdlp_cmd: list[str],
    preferred_languages: list[str],
    work_dir: Path,
) -> tuple[dict[str, object], Path]:
    """Download best matching subtitle file and video metadata JSON using yt-dlp."""
    # Expand languages to include -orig variants (e.g. en-orig to avoid YouTube 429 auto-translation errors)
    expanded_languages = []
    for lang in preferred_languages:
        orig_variant = f"{lang}-orig"
        if orig_variant not in expanded_languages:
            expanded_languages.append(orig_variant)
        if lang not in expanded_languages:
            expanded_languages.append(lang)
    lang_arg = ",".join(expanded_languages)
    output_tmpl = str(work_dir / "%(id)s")

    # 1. Fetch metadata JSON
    meta_cmd = [
        *ytdlp_cmd,
        "--dump-single-json",
        "--no-warnings",
        url,
    ]
    try:
        proc = subprocess.run(meta_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        err_msg = exc.stderr.strip() or exc.stdout.strip()
        if "confirm you’re not a bot" in err_msg or "Sign in" in err_msg or "cookies" in err_msg:
            print("💡 检测到 YouTube 机器人验证，正在使用 Chrome Cookies 获取元数据...")
            retry_meta_cmd = meta_cmd[:-1] + [
                "--cookies-from-browser", "chrome",
                "--extractor-args", "youtube:player_client=web_embedded",
                url,
            ]
            proc = subprocess.run(retry_meta_cmd, capture_output=True, text=True, check=True)
        else:
            raise RuntimeError(f"yt-dlp 提取元数据失败：{err_msg}") from exc

    try:
        meta = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"无法解析 yt-dlp 返回的视频元数据 JSON：{exc}") from exc

    # 2. Fetch subtitles (without convert-subs to avoid requiring ffmpeg)
    sub_cmd = [
        *ytdlp_cmd,
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-lang",
        lang_arg,
        "--no-warnings",
        "-o",
        output_tmpl,
        url,
    ]
    subprocess.run(sub_cmd, capture_output=True, text=True)

    sub_files = list(work_dir.glob("*.srt")) + list(work_dir.glob("*.vtt"))
    if not sub_files:
        print("💡 标准通道未获取到字幕，正在尝试使用 web_embedded 客户端与 Chrome Cookies 重试...")
        retry_sub_cmd = sub_cmd[:-1] + [
            "--cookies-from-browser", "chrome",
            "--extractor-args", "youtube:player_client=web_embedded",
            url,
        ]
        subprocess.run(retry_sub_cmd, capture_output=True, text=True)
        sub_files = list(work_dir.glob("*.srt")) + list(work_dir.glob("*.vtt"))

    if not sub_files:
        raise RuntimeError(
            f"未找到视频 '{meta.get('title', url)}' 的可用字幕。\n"
            f"该视频可能未开启任何官方字幕或自动字幕。"
        )

    # Sort files by language priority
    def lang_score(sub_path: Path) -> int:
        filename = sub_path.name.lower()
        is_auto = "orig" in filename or "auto" in filename
        for idx, lang in enumerate(preferred_languages):
            lang_low = lang.lower()
            if (
                f".{lang_low}." in filename
                or f".{lang_low}-" in filename
                or filename.endswith(f".{lang_low}.srt")
                or filename.endswith(f".{lang_low}.vtt")
                or filename.endswith(f".{lang_low}-orig.srt")
                or filename.endswith(f".{lang_low}-orig.vtt")
            ):
                return idx * 2 + (1 if is_auto else 0)
        return 999

    sub_files.sort(key=lang_score)
    chosen_sub = sub_files[0]
    return meta, chosen_sub


def create_article_task(
    project_root: Path,
    url: str,
    meta: dict[str, object],
    srt_path: Path,
    target_dir: Path | None = None,
    keep_inputs: bool = False,
    skip_clean: bool = False,
) -> Path:
    """Create timestamped article directory, archive source files, clean captions, and init state."""
    project_root = project_root.resolve()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if target_dir:
        article_path = target_dir.resolve()
    else:
        article_path = (project_root / "articles" / timestamp).resolve()

    if article_path.exists() and any(article_path.iterdir()):
        raise ValueError(f"目标文章目录已存在且非空：{article_path}")

    article_path.mkdir(parents=True, exist_ok=True)

    title = str(meta.get("title", "")).strip()
    uploader = str(meta.get("uploader", "")).strip() or str(meta.get("channel", "")).strip()
    duration_str = format_duration(meta.get("duration"))
    upload_date = str(meta.get("upload_date", ""))
    if len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

    # 1. Copy source subtitle
    sub_ext = srt_path.suffix.lower()
    target_source_sub = article_path / f"source{sub_ext}"
    shutil.copy2(srt_path, target_source_sub)

    # 2. Write source-link.txt
    norm_url, video_id = normalize_youtube_url(url)
    source_link_content = (
        f"{norm_url}\n"
        f"标题：{title}\n"
        f"频道：{uploader}\n"
        f"时长：{duration_str}\n"
        f"发布时间：{upload_date}\n"
    )
    (article_path / link_registry.SOURCE_LINK_FILENAME).write_text(source_link_content, encoding="utf-8")

    # 3. Write source-map.json for link_registry compatibility
    subtitle_sha256 = link_registry._sha256(target_source_sub)
    map_payload = {
        "schema_version": 1,
        "status": "prepared",
        "article_dir": article_path.relative_to(project_root).as_posix(),
        "prepared_at": link_registry._now(),
        "input_subtitle": {
            "filename": f"youtube_{video_id}{sub_ext}",
            "sha256": subtitle_sha256,
        },
        "input_link_file": {
            "filename": "links.txt",
            "sha256": link_registry._sha256(article_path / link_registry.SOURCE_LINK_FILENAME),
        },
        "source_subtitle": target_source_sub.name,
        "source_link_file": link_registry.SOURCE_LINK_FILENAME,
        "url_original": url,
        "url_normalized": norm_url,
        "video_metadata": {
            "id": video_id,
            "title": title,
            "uploader": uploader,
            "duration": meta.get("duration"),
            "upload_date": upload_date,
            "view_count": meta.get("view_count"),
            "description": meta.get("description", ""),
        },
        "wechat_draft": None,
    }
    link_registry._write_json(article_path / link_registry.MAP_FILENAME, map_payload)

    # 4. Optional backup into inputs/ and links/
    if keep_inputs:
        inputs_dir = project_root / "inputs"
        links_dir = project_root / "links"
        inputs_dir.mkdir(exist_ok=True)
        links_dir.mkdir(exist_ok=True)
        shutil.copy2(target_source_sub, inputs_dir / f"youtube_{video_id}{sub_ext}")
        (links_dir / link_registry.DEFAULT_LINK_FILE).write_text(source_link_content, encoding="utf-8")

    # 5. Clean subtitle and initialize workflow state
    if not skip_clean:
        source_text = target_source_sub.read_text(encoding="utf-8-sig")
        cleaned_text = clean_subtitle.clean_subtitle_text(source_text)
        cleaned_path = article_path / "source.cleaned.txt"
        cleaned_path.write_text(cleaned_text, encoding="utf-8")

        # Verify residue
        residue = clean_subtitle.find_timecode_residue(cleaned_text)
        if residue:
            print(f"警告：清洗结果中可能存在残留时间轴 ({len(residue)} 处)", file=sys.stderr)

        # Initialize workflow state and pass step_1
        workflow_state.init_state(article_path)
        workflow_state.start_step(article_path, "step_1")
        workflow_state.pass_step(article_path, "step_1")

    return article_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube video subtitles, clean them, and initialize article workflows."
    )
    parser.add_argument(
        "url",
        help="YouTube video URL or 11-char Video ID (e.g. https://youtu.be/xxx or xxx)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Target article directory. Defaults to articles/<YYYYMMDD-HHMMSS>",
    )
    parser.add_argument(
        "--languages",
        default="en,zh-Hans,zh,zh-CN,zh-TW,ja",
        help="Comma-separated language codes in priority order. Default: en,zh-Hans,zh,zh-CN,zh-TW,ja",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow fetching even if the URL is already registered in link-registry.json",
    )
    parser.add_argument(
        "--keep-inputs",
        action="store_true",
        help="Also write copies to inputs/ and links/links.txt",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip clean_subtitle.py and workflow state initialization",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch metadata only and print info without creating files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    ytdlp_cmd = get_ytdlp_command()
    if not ytdlp_cmd:
        print(
            "ERROR: 未找到 yt-dlp 工具！\n"
            "请先在终端安装 yt-dlp：\n"
            "  pip install yt-dlp\n"
            "或使用 Homebrew：\n"
            "  brew install yt-dlp",
            file=sys.stderr,
        )
        return 1

    try:
        norm_url, video_id = normalize_youtube_url(args.url)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Check duplicates in registry
    if not args.force:
        duplicates = link_registry.find_url(PROJECT_ROOT, norm_url)
        if duplicates:
            article = duplicates[0].get("article_dir", "未知文章")
            print(
                f"ERROR: 该视频已经成功处理过：{article}\n"
                f"URL: {norm_url}\n"
                f"若需强制重新处理，请使用 --force 参数。",
                file=sys.stderr,
            )
            return 1

    preferred_languages = [lang.strip() for lang in args.languages.split(",") if lang.strip()]

    print(f"==> 正在分析并提取视频字幕与信息: {norm_url}")
    with tempfile.TemporaryDirectory(prefix="yt_fetch_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        try:
            meta, chosen_srt = download_subtitles_and_meta(
                norm_url, ytdlp_cmd, preferred_languages, tmp_dir
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        title = meta.get("title", "未知标题")
        uploader = meta.get("uploader") or meta.get("channel") or "未知频道"
        duration_str = format_duration(meta.get("duration"))
        print(f"✓ 视频标题: {title}")
        print(f"✓ 频道作者: {uploader} (时长: {duration_str})")
        print(f"✓ 抓取字幕: {chosen_srt.name}")

        if args.dry_run:
            print("==> --dry-run 模式：跳过文件写入与工作流初始化。")
            return 0

        try:
            article_dir = create_article_task(
                project_root=PROJECT_ROOT,
                url=norm_url,
                meta=meta,
                srt_path=chosen_srt,
                target_dir=args.output_dir,
                keep_inputs=args.keep_inputs,
                skip_clean=args.skip_clean,
            )
        except Exception as exc:
            print(f"ERROR: 创建任务失败: {exc}", file=sys.stderr)
            return 1

    print(f"✓ 任务目录已创建: {article_dir.relative_to(PROJECT_ROOT)}")
    if not args.skip_clean:
        cleaned_file = article_dir / "source.cleaned.txt"
        if cleaned_file.exists():
            cleaned_len = len(cleaned_file.read_text(encoding="utf-8"))
            print(f"✓ 字幕清洗完成 (source.cleaned.txt, {cleaned_len} 字符)")
        print(f"✓ Step 1 状态已标记通过 (passed)")
        print(f"\n🎉 准备就绪！下一步可直接开始 Step 2 文章生成：")
        print(f"   python3 scripts/workflow_state.py start {article_dir.relative_to(PROJECT_ROOT)} step_2")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
