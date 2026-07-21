#!/usr/bin/env python3
"""Pair subtitle/link inputs, archive their mapping, and query processed URLs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


MAP_FILENAME = "source-map.json"
SOURCE_LINK_FILENAME = "source-link.txt"
REGISTRY_FILENAME = "link-registry.json"
SUBTITLE_SUFFIXES = {".srt", ".vtt", ".txt"}
LINK_SUFFIXES = {".txt", ".url"}
DEFAULT_LINK_FILE = "links.txt"
TRACKING_KEYS = {
    "fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "spm", "from",
    "ref", "ref_src", "share_source", "share_token", "source",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)


def normalize_url(url: str) -> str:
    """Normalize a URL for local duplicate checks without network expansion."""
    raw = url.strip()
    parts = urlsplit(raw)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise ValueError(f"链接必须是完整的 http/https URL：{url}")
    host = (parts.hostname or "").lower()
    port = parts.port
    if port and not ((parts.scheme.lower() == "http" and port == 80) or (parts.scheme.lower() == "https" and port == 443)):
        host = f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    # YouTube share tokens change on every share; the video ID is the stable key.
    if host in {"youtu.be", "www.youtu.be"}:
        video_id = path.strip("/").split("/")[0]
        if video_id:
            return f"https://youtu.be/{video_id}"
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        query_pairs = dict(parse_qsl(parts.query, keep_blank_values=True))
        video_id = query_pairs.get("v")
        if not video_id and path.startswith("/shorts/"):
            video_id = path.split("/", 2)[2].split("/", 1)[0]
        if not video_id and path.startswith("/embed/"):
            video_id = path.split("/", 2)[2].split("/", 1)[0]
        if video_id:
            return f"https://youtu.be/{video_id}"
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in TRACKING_KEYS:
            continue
        query.append((key, value))
    query.sort(key=lambda item: (item[0], item[1]))
    return urlunsplit((parts.scheme.lower(), host, path, urlencode(query), ""))


def _read_link_text_raw(path: Path) -> str:
    if not path.is_file() or path.suffix.lower() not in LINK_SUFFIXES:
        raise ValueError(f"链接文件必须是非空 .txt/.url 文件：{path}")
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"链接文件为空：{path}")
    return text


def read_link_file(path: Path) -> str:
    text = _read_link_text_raw(path)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    urls = [line for line in lines if re.match(r"^https?://", line, re.IGNORECASE)]
    if len(urls) != 1:
        raise ValueError(f"每个链接文件必须且只能包含一个 http/https 链接：{path}")
    return urls[0]


def read_link_file_full(path: Path) -> str:
    _read_link_text_raw(path)
    read_link_file(path)
    return path.read_text(encoding="utf-8-sig").rstrip("\n")


def project_root_for(article_dir: Path) -> Path:
    article_dir = article_dir.resolve()
    if article_dir.parent.name != "articles":
        raise ValueError(f"文章目录必须位于 articles/ 下：{article_dir}")
    return article_dir.parent.parent


def load_registry(project_root: Path) -> dict[str, object]:
    path = project_root / REGISTRY_FILENAME
    if not path.exists():
        return {"schema_version": 1, "updated_at": None, "entries": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{REGISTRY_FILENAME} 无效：{exc}") from exc
    if payload.get("schema_version") != 1 or not isinstance(payload.get("entries"), list):
        raise ValueError(f"{REGISTRY_FILENAME} 结构无效")
    return payload


def find_url(project_root: Path, url: str) -> list[dict[str, object]]:
    normalized = normalize_url(url)
    entries = load_registry(project_root)["entries"]
    matches = []
    for entry in entries:  # type: ignore[union-attr]
        candidate = entry.get("url_original") or entry.get("url_normalized")
        try:
            candidate_normalized = normalize_url(str(candidate))
        except ValueError:
            candidate_normalized = str(entry.get("url_normalized", ""))
        if candidate_normalized == normalized:
            matches.append(entry)
    return matches


def prepare_mapping(article_dir: Path | str, subtitle: Path | str, link_file: Path | str) -> dict[str, object]:
    article_path = Path(article_dir).resolve()
    subtitle_path = Path(subtitle).resolve()
    link_path = Path(link_file).resolve()
    project_root = project_root_for(article_path)
    if not subtitle_path.is_file() or subtitle_path.suffix.lower() not in SUBTITLE_SUFFIXES:
        raise ValueError(f"字幕必须是非空 .srt/.vtt/.txt 文件：{subtitle_path}")
    if subtitle_path.stat().st_size == 0:
        raise ValueError(f"字幕文件为空：{subtitle_path}")
    if subtitle_path.parent != (project_root / "inputs").resolve():
        raise ValueError("字幕文件必须直接位于 inputs/ 目录")
    if link_path.parent != (project_root / "links").resolve():
        raise ValueError("链接文件必须直接位于 links/ 目录")
    original_url = read_link_file(link_path)
    normalized_url = normalize_url(original_url)
    duplicates = find_url(project_root, original_url)
    if duplicates:
        article = duplicates[0].get("article_dir", "未知文章")
        raise ValueError(
            "该视频已经成功处理过："
            f"{article}。当前输入未删除：字幕={subtitle_path.name}，链接文件={link_path.name}。"
            "请先确认是否删除这两个输入文件；未明确确认前不会删除。"
        )
    article_path.mkdir(parents=True, exist_ok=True)
    existing_sources = [p for p in article_path.glob("source.*") if p.suffix.lower() in SUBTITLE_SUFFIXES]
    if existing_sources:
        raise ValueError("文章目录已存在 source.*，拒绝覆盖")
    source_name = f"source{subtitle_path.suffix.lower()}"
    source_path = article_path / source_name
    source_path.write_bytes(subtitle_path.read_bytes())
    (article_path / SOURCE_LINK_FILENAME).write_text(read_link_file_full(link_path) + "\n", encoding="utf-8")
    payload: dict[str, object] = {
        "schema_version": 1,
        "status": "prepared",
        "article_dir": article_path.relative_to(project_root).as_posix(),
        "prepared_at": _now(),
        "input_subtitle": {"filename": subtitle_path.name, "sha256": _sha256(subtitle_path)},
        "input_link_file": {"filename": link_path.name, "sha256": _sha256(link_path)},
        "source_subtitle": source_name,
        "source_link_file": SOURCE_LINK_FILENAME,
        "url_original": original_url,
        "url_normalized": normalized_url,
        "wechat_draft": None,
    }
    _write_json(article_path / MAP_FILENAME, payload)
    return payload


def _draft_fields(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    fields: dict[str, str] = {}
    for label, key in (("media_id", "media_id"), ("标题", "title")):
        match = re.search(rf"{label}\s*[：:]\s*(\S[^\n]*)", text)
        if match:
            fields[key] = match.group(1).strip()
    if not fields.get("media_id"):
        raise ValueError("公众号草稿信息.txt 缺少有效 media_id")
    return fields


def _validate_exact_input(path: Path, expected_sha256: str, expected_parent: Path) -> bool:
    if not path.exists():
        return False
    if path.parent.resolve() != expected_parent.resolve():
        raise ValueError(f"拒绝清理目录外文件：{path}")
    if _sha256(path) != expected_sha256:
        raise ValueError(f"输入文件内容已变化，拒绝删除：{path.name}")
    return True


def _remove_validated_input(path: Path, exists: bool) -> bool:
    if not exists:
        return False
    path.unlink()
    return True


def finalize_mapping(article_dir: Path | str) -> dict[str, object] | None:
    """Finalize a prepared mapping after WeChat draft success and clean exact inputs.

    Old article tasks without source-map.json are left untouched for compatibility.
    """
    article_path = Path(article_dir).resolve()
    project_root = project_root_for(article_path)
    map_path = article_path / MAP_FILENAME
    if not map_path.is_file():
        return None
    payload = json.loads(map_path.read_text(encoding="utf-8"))
    original_url = str(payload["url_original"])
    normalized_url = normalize_url(original_url)
    source_link_path = article_path / SOURCE_LINK_FILENAME
    if not source_link_path.is_file() or normalize_url(read_link_file(source_link_path)) != normalized_url:
        raise ValueError(f"{SOURCE_LINK_FILENAME} 缺失或与映射不一致")
    source_path = article_path / str(payload["source_subtitle"])
    if not source_path.is_file():
        raise ValueError(f"归档源字幕缺失：{source_path.name}")
    subtitle_info = payload["input_subtitle"]  # type: ignore[assignment]
    link_info = payload["input_link_file"]  # type: ignore[assignment]
    input_subtitle = project_root / "inputs" / subtitle_info["filename"]  # type: ignore[index]
    input_link = project_root / "links" / link_info["filename"]  # type: ignore[index]
    subtitle_exists = _validate_exact_input(
        input_subtitle, subtitle_info["sha256"], project_root / "inputs"  # type: ignore[index]
    )
    draft = _draft_fields(article_path / "公众号草稿信息.txt")
    finalized_at = _now()
    payload["status"] = "wechat_draft_created"
    payload["finalized_at"] = finalized_at
    payload["url_normalized"] = normalized_url
    payload["wechat_draft"] = draft
    registry = load_registry(project_root)
    entries: list[dict[str, object]] = registry["entries"]  # type: ignore[assignment]
    entry: dict[str, object] = {
        "url_original": original_url,
        "url_normalized": normalized_url,
        "article_dir": payload["article_dir"],
        "subtitle_file": payload["input_subtitle"]["filename"],  # type: ignore[index]
        "link_file": payload["input_link_file"]["filename"],  # type: ignore[index]
        "media_id": draft["media_id"],
        "title": draft.get("title"),
        "processed_at": finalized_at,
    }
    matches = []
    for i, item in enumerate(entries):
        candidate = item.get("url_original") or item.get("url_normalized")
        try:
            candidate_normalized = normalize_url(str(candidate))
        except ValueError:
            candidate_normalized = str(item.get("url_normalized", ""))
        if candidate_normalized == normalized_url:
            matches.append(i)
    if matches:
        current = entries[matches[0]]
        if current.get("article_dir") != payload["article_dir"]:
            raise ValueError(f"全局链接索引已存在其他文章映射：{current.get('article_dir')}")
        entries[matches[0]] = entry
    else:
        entries.append(entry)
    entries.sort(key=lambda item: (str(item.get("processed_at", "")), str(item.get("url_normalized", ""))))
    registry["updated_at"] = finalized_at
    _write_json(project_root / REGISTRY_FILENAME, registry)
    _write_json(map_path, payload)
    link_exists = input_link.is_file() and input_link.parent.resolve() == (project_root / "links").resolve()
    if link_exists:
        input_link.write_text("", encoding="utf-8")
    removed = {
        "subtitle": _remove_validated_input(input_subtitle, subtitle_exists),
        "link_cleared": link_exists,
    }
    return {"mapping": payload, "removed": removed}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="archive a subtitle/link pair into an article task")
    prepare.add_argument("article_dir", type=Path)
    prepare.add_argument("subtitle", type=Path)
    prepare.add_argument("link_file", type=Path)
    check = sub.add_parser("check", help="check whether a URL was successfully processed")
    check.add_argument("url")
    check.add_argument("--project-root", type=Path, default=Path.cwd())
    finalize = sub.add_parser("finalize", help="register a successful WeChat draft and clean inputs")
    finalize.add_argument("article_dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_mapping(args.article_dir, args.subtitle, args.link_file)
        elif args.command == "finalize":
            result = finalize_mapping(args.article_dir)
        else:
            matches = find_url(args.project_root.resolve(), args.url)
            result = {"found": bool(matches), "normalized_url": normalize_url(args.url), "matches": matches}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if matches else 1
    except (KeyError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
