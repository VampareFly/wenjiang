#!/usr/bin/env python3
"""Clean subtitle files before sending them into AI article workflows."""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


TIMECODE_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}(?:[,.]\d{1,3})?)\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}(?:[,.]\d{1,3})?)(?:\s+.*)?$"
)
SIMPLE_TIMESTAMP_RE = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?(?:[,.]\d{1,3})?$")
SRT_INDEX_RE = re.compile(r"^\d+$")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9:-]*(?:\s+[^<>]*)?/?>")
WHITESPACE_RE = re.compile(r"[ \t]+")
WEBVTT_SKIP_BLOCKS = {"NOTE", "STYLE", "REGION"}


INLINE_TAG_RE = re.compile(r"<[^>]+>")


def is_timecode_line(line: str) -> bool:
    return bool(TIMECODE_RE.match(line.strip()))


def is_simple_timestamp_line(line: str) -> bool:
    return bool(SIMPLE_TIMESTAMP_RE.match(line.strip()))


def normalize_caption_line(line: str) -> str:
    text = line.strip().lstrip("\ufeff")
    text = html.unescape(text)
    text = HTML_TAG_RE.sub("", text)
    text = INLINE_TAG_RE.sub("", text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def next_nonempty_line(lines: list[str], start_index: int) -> str:
    for raw_line in lines[start_index:]:
        line = raw_line.strip().lstrip("\ufeff")
        if line:
            return line
    return ""


def clean_subtitle_text(source: str) -> str:
    """Return compact subtitle text with cue metadata and timecodes removed."""
    cleaned: list[str] = []
    previous = ""
    skip_block = False

    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    for line_index, raw_line in enumerate(lines):
        line = raw_line.strip().lstrip("\ufeff")
        upper = line.upper()

        if not line:
            skip_block = False
            continue

        if upper == "WEBVTT" or upper.startswith("WEBVTT "):
            continue

        if upper.startswith(("KIND:", "LANGUAGE:")):
            continue

        first_word = upper.split(maxsplit=1)[0]
        if first_word in WEBVTT_SKIP_BLOCKS:
            skip_block = True
            continue
        if skip_block:
            continue

        if is_timecode_line(line):
            continue

        if SRT_INDEX_RE.match(line) and is_timecode_line(next_nonempty_line(lines, line_index + 1)):
            continue

        if is_simple_timestamp_line(line):
            continue

        next_line = lines[line_index + 1].strip() if line_index + 1 < len(lines) else ""
        if next_line and is_timecode_line(next_line):
            continue

        normalized = normalize_caption_line(line)
        if not normalized:
            continue

        if normalized == previous:
            continue

        cleaned.append(normalized)
        previous = normalized

    return "\n".join(cleaned).rstrip() + ("\n" if cleaned else "")


def find_timecode_residue(output: str) -> list[tuple[int, str]]:
    residue: list[tuple[int, str]] = []
    for index, line in enumerate(output.splitlines(), start=1):
        stripped = line.strip()
        if is_timecode_line(stripped) or is_simple_timestamp_line(stripped):
            residue.append((index, stripped))
    return residue


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}.cleaned.txt")


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4)) if text else 0


def print_stats(source: str, cleaned: str) -> None:
    source_lines = len(source.splitlines())
    cleaned_lines = len(cleaned.splitlines())
    source_tokens = estimate_tokens(source)
    cleaned_tokens = estimate_tokens(cleaned)
    saved_tokens = source_tokens - cleaned_tokens
    saved_percent = (1 - len(cleaned) / len(source)) * 100 if source else 0

    print(f"Original: {len(source)} chars, {source_lines} lines, ~{source_tokens} tokens")
    print(f"Cleaned:  {len(cleaned)} chars, {cleaned_lines} lines, ~{cleaned_tokens} tokens")
    print(f"Saved:    {saved_tokens} tokens estimated, {saved_percent:.1f}% chars")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove subtitle timecodes and metadata while preserving caption text."
    )
    parser.add_argument("input", type=Path, help="Subtitle file: .srt, .vtt, or caption .txt")
    parser.add_argument("-o", "--output", type=Path, help="Output path. Defaults to *.cleaned.txt")
    parser.add_argument("--stats", action="store_true", help="Print compression statistics")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Fail if cleaned output still contains subtitle timecode patterns",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=0,
        metavar="N",
        help="Print the first N cleaned lines after writing the output",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    input_path: Path = args.input
    output_path: Path = args.output or default_output_path(input_path)

    source = input_path.read_text(encoding="utf-8-sig")
    cleaned = clean_subtitle_text(source)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(cleaned, encoding="utf-8")

    if args.stats:
        print_stats(source, cleaned)

    if args.preview > 0:
        preview_lines = cleaned.splitlines()[: args.preview]
        print("\n".join(preview_lines))

    if args.verify:
        residue = find_timecode_residue(cleaned)
        if residue:
            print("Timecode residue found:", file=sys.stderr)
            for line_number, line in residue:
                print(f"{line_number}: {line}", file=sys.stderr)
            return 1
        print("Verification passed: no subtitle timecode residue found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
