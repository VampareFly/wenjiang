#!/usr/bin/env python3
"""Publish Toutiao article and weitoutiao drafts to Toutiao Creator Platform using Chrome/Playwright."""

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

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
PUBLISHER_JS = SCRIPTS_DIR / "toutiao_publisher.js"
NODE_MODULES = PROJECT_ROOT / ".agents/skills/guizang-social-card-skill/node_modules"

DRAFT_RECORD_FILENAME = "今日头条草稿信息.txt"
TOUTIAO_ARTICLE_FILENAME = "今日头条文章.md"
WEITOUTIAO_FILENAME = "微头条.txt"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_node_publisher(cmd_args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run toutiao_publisher.js with proper NODE_PATH."""
    env = os.environ.copy()
    existing_node_path = env.get("NODE_PATH", "")
    env["NODE_PATH"] = f"{NODE_MODULES}:{existing_node_path}" if existing_node_path else str(NODE_MODULES)

    full_cmd = ["node", str(PUBLISHER_JS)] + cmd_args
    return subprocess.run(full_cmd, env=env, capture_output=False, text=True)


def check_toutiao_login() -> bool:
    """Check if Toutiao session is valid in headless Chrome."""
    env = os.environ.copy()
    existing_node_path = env.get("NODE_PATH", "")
    env["NODE_PATH"] = f"{NODE_MODULES}:{existing_node_path}" if existing_node_path else str(NODE_MODULES)

    res = subprocess.run(
        ["node", str(PUBLISHER_JS), "check-login"],
        env=env,
        capture_output=True,
        text=True,
    )
    return res.returncode == 0


def interactive_toutiao_login(force: bool = False) -> bool:
    """Launch non-headless Chrome for user to scan QR code."""
    cmd = ["login"]
    if force:
        cmd.append("--force")
    res = run_node_publisher(cmd)
    return res.returncode == 0


def parse_toutiao_article(article_dir: Path) -> dict[str, object]:
    """Parse 今日头条文章.md, extract main title (<=30 chars) and body."""
    article_path = article_dir / TOUTIAO_ARTICLE_FILENAME
    if not article_path.is_file():
        raise ValueError(f"未找到头条长文文件：{article_path.name}")

    text = article_path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"{TOUTIAO_ARTICLE_FILENAME} 为空")

    lines = [line.rstrip() for line in text.splitlines()]
    title = ""
    body_lines = []
    found_title = False

    # Extract first candidate title if present
    for line in lines:
        stripped = line.strip()
        if not title:
            # Check for candidate title block format: 1. 《标题》
            cand_match = re.search(r"[1-3]\.\s*《([^》]+)》", stripped)
            if cand_match:
                title = cand_match.group(1).strip()
            elif stripped.startswith("#"):
                title = re.sub(r"^#+\s*", "", stripped).strip()

        body_lines.append(line)

    if not title:
        # Fallback to first non-empty line
        for line in lines:
            if line.strip() and not line.strip().startswith(">"):
                title = re.sub(r"^#+\s*", "", line.strip())
                break

    if not title:
        raise ValueError(f"{TOUTIAO_ARTICLE_FILENAME} 缺少有效标题")

    # Clean body text
    body_text = "\n".join(body_lines).strip()
    split_candidates = re.split(r"\n##+\s*标题候选", body_text)
    clean_body = split_candidates[0].strip()

    # Collect cover images
    covers = [
        article_dir / "toutiao-cover-1.png",
        article_dir / "toutiao-cover-2.png",
        article_dir / "toutiao-cover-3.png",
    ]
    existing_covers = [c for c in covers if c.is_file()]

    # Collect article images
    body_images = sorted(list(article_dir.glob("配图*.png")))

    return {
        "title": title[:30],
        "full_title": title,
        "body": clean_body,
        "covers": [str(c.resolve()) for c in existing_covers],
        "has_three_covers": len(existing_covers) == 3,
        "images": [str(img.resolve()) for img in body_images],
    }


def parse_weitoutiao(article_dir: Path) -> dict[str, object]:
    """Parse 微头条.txt, extract text and hashtags."""
    wt_path = article_dir / WEITOUTIAO_FILENAME
    if not wt_path.is_file():
        raise ValueError(f"未找到微头条文件：{wt_path.name}")

    text = wt_path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"{WEITOUTIAO_FILENAME} 为空")

    # Extract hashtags like #话题#
    tags = re.findall(r"#([^#]+)#", text)

    # Collect body images (配图1.png ~ 配图3.png) as Weitoutiao attachments
    body_imgs = sorted(list(article_dir.glob("配图*.png")))
    if not body_imgs:
        body_imgs = sorted(list(article_dir.glob("小红书卡片-*.png")))

    return {
        "content": text,
        "length": len(text),
        "tags": tags,
        "attachments": [str(c.resolve()) for c in body_imgs[:9]],
    }



def write_draft_record(
    article_dir: Path,
    article_result: dict[str, object] | None = None,
    weitoutiao_result: dict[str, object] | None = None,
    automated_saved: bool = False,
) -> Path:
    """Write audit record to 今日头条草稿信息.txt."""
    record_path = article_dir / DRAFT_RECORD_FILENAME
    now_str = _now()

    lines = [
        "平台：今日头条 (头条号 mp.toutiao.com)",
        f"保存时间：{now_str}",
        f"草稿状态：{'已自动通过 Playwright Chrome 推送到头条号后台草稿箱' if automated_saved else '资产已就绪待推送'}",
    ]

    if article_result is None and (article_dir / TOUTIAO_ARTICLE_FILENAME).is_file():
        try:
            article_result = parse_toutiao_article(article_dir)
        except Exception:
            pass

    if weitoutiao_result is None and (article_dir / WEITOUTIAO_FILENAME).is_file():
        try:
            weitoutiao_result = parse_weitoutiao(article_dir)
        except Exception:
            pass

    if article_result:
        lines.extend([
            "",
            "--- 【今日头条深度长文】 ---",
            f"文章标题：{article_result.get('title')}",
            f"三图封面：{'已上传 (3张16:9写实封面)' if article_result.get('has_three_covers') else '单图/无'}",
            f"正文配图数：{len(article_result.get('images', []))} 张",
            "长文状态：已存入草稿箱 (可在头条号后台/今日头条App查看并一键发布)",
        ])

    if weitoutiao_result:
        lines.extend([
            "",
            "--- 【微头条短快讯】 ---",
            f"微头条字数：{weitoutiao_result.get('length')} 字",
            f"附带图片数：{len(weitoutiao_result.get('attachments', []))} 张",
            f"话题标签：{', '.join(['#' + t + '#' for t in weitoutiao_result.get('tags', [])]) if weitoutiao_result.get('tags') else '无'}",
            "微头条状态：已存入微头条草稿箱 (可一键发布)",
        ])

    lines.append("")
    record_path.write_text("\n".join(lines), encoding="utf-8")
    return record_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-publish Toutiao article and weitoutiao drafts to Toutiao creator platform via Playwright."
    )
    parser.add_argument(
        "article_dir",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the article directory, e.g. articles/YYYYMMDD-HHMMSS",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Open Chrome window to scan QR code and save persistent Toutiao login session.",
    )
    parser.add_argument(
        "--check-login",
        action="store_true",
        help="Check whether the stored Toutiao session is valid in headless Chrome.",
    )
    parser.add_argument(
        "--type",
        choices=["all", "article", "weitoutiao"],
        default="all",
        help="Type of draft to save: all (both article & weitoutiao), article, or weitoutiao. Default: all",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in visible mode for debugging.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate assets and parse contents without launching browser.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force clear existing session and re-scan QR code.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    # Handle direct login commands
    if args.login:
        ok = interactive_toutiao_login(force=args.force)
        return 0 if ok else 1

    if args.check_login:
        ok = check_toutiao_login()
        return 0 if ok else 1

    if not args.article_dir:
        print("ERROR: 请指定文章目录路径，例如: python3 scripts/post_to_toutiao.py articles/20260824-162147", file=sys.stderr)
        return 1

    article_dir = args.article_dir.resolve()
    if not article_dir.is_dir():
        print(f"ERROR: 目标目录不存在：{article_dir}", file=sys.stderr)
        return 1

    print(f"==> 正在准备今日头条自动化草稿推送: {article_dir.name}")

    article_data = None
    weitoutiao_data = None

    if args.type in {"all", "article"}:
        try:
            article_data = parse_toutiao_article(article_dir)
            print(f"✓ 今日头条长文已就绪: 《{article_data['title']}》")
            print(f"  - 封面素材: {len(article_data['covers'])} 张 (三图模式: {article_data['has_three_covers']})")
            print(f"  - 正文插图: {len(article_data['images'])} 张")
        except Exception as exc:
            print(f"ERROR: 长文解析失败: {exc}", file=sys.stderr)
            return 1

    if args.type in {"all", "weitoutiao"}:
        try:
            weitoutiao_data = parse_weitoutiao(article_dir)
            print(f"✓ 微头条已就绪: {weitoutiao_data['length']} 字，附图 {len(weitoutiao_data['attachments'])} 张")
        except Exception as exc:
            print(f"ERROR: 微头条解析失败: {exc}", file=sys.stderr)
            return 1

    if args.dry_run:
        print("\n==> [Dry Run] 资产与格式校验完全通过，跳过浏览器上传操作。")
        write_draft_record(article_dir, article_data, weitoutiao_data, automated_saved=False)
        return 0

    # Check login session before posting
    print("\n==> 正在检查今日头条登录状态...")
    if not check_toutiao_login():
        print("\n⚠️ 检测到今日头条尚未登录或登录态已过期。")
        print("==> 正在为您唤起 Chrome 扫码窗口，请完成一次扫码登录...")
        if not interactive_toutiao_login():
            print("ERROR: 扫码登录未完成，草稿推送中止。", file=sys.stderr)
            return 1

    # Execute automated publishing via Playwright
    has_error = False
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        if article_data:
            art_payload_path = tmp_path / "article_payload.json"
            art_payload_path.write_text(json.dumps(article_data, ensure_ascii=False), encoding="utf-8")
            cmd = ["post-article", str(art_payload_path)]
            if args.headed:
                cmd.append("--headed")
            res = run_node_publisher(cmd)
            if res.returncode != 0:
                print("ERROR: 长文自动化推送失败，请检查控制台输出。", file=sys.stderr)
                has_error = True

        if weitoutiao_data:
            wt_payload_path = tmp_path / "weitoutiao_payload.json"
            wt_payload_path.write_text(json.dumps(weitoutiao_data, ensure_ascii=False), encoding="utf-8")
            cmd = ["post-weitoutiao", str(wt_payload_path)]
            if args.headed:
                cmd.append("--headed")
            res = run_node_publisher(cmd)
            if res.returncode != 0:
                print("ERROR: 微头条自动化推送失败，请检查控制台输出。", file=sys.stderr)
                has_error = True

    if has_error:
        print("\n❌ 今日头条草稿自动推送未完全成功，请根据错误信息排查。", file=sys.stderr)
        return 1

    # Write draft record
    record_path = write_draft_record(
        article_dir=article_dir,
        article_result=article_data,
        weitoutiao_result=weitoutiao_data,
        automated_saved=True,
    )

    print(f"\n🎉 今日头条草稿自动推送流程完成！")
    print(f"✓ 审计记录已写入: {record_path.name}")
    print(f"💡 打开手机「今日头条 App」或「头条号后台」草稿箱即可查看并一键群发。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
