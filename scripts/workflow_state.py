#!/usr/bin/env python3
"""Create and update the machine-readable article workflow state."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

try:
    from scripts import validate_workflow as validator
    from scripts import link_registry
except ImportError:  # Direct execution: python3 scripts/workflow_state.py
    import validate_workflow as validator  # type: ignore[no-redef]
    import link_registry  # type: ignore[no-redef]


SCHEMA_VERSION = 2
ALLOWED_STATUSES = {"pending", "running", "passed", "blocked"}
STEP_NAMES = tuple(f"step_{number}" for number in range(1, 13))
STATE_FILENAME = "workflow-state.json"

STEP_CONTEXT: dict[str, dict[str, object]] = {
    "step_1": {
        "mode": "deterministic",
        "guides": ["docs/steps/step1/subtitle-guide.md"],
        "inputs": ["source.srt|source.vtt|source.txt"],
        "outputs": ["source.cleaned.txt"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_1",
    },
    "step_2": {
        "mode": "three_pass_ai",
        "guides": [
            "docs/steps/step2/writing-guide.md",
            "docs/steps/step2/editorial-guide.md",
            "docs/steps/step2/final-review-guide.md",
            "docs/steps/step2/image-prompt-guide.md",
        ],
        "rounds": ["内容初稿轮", "编辑终稿轮", "独立质检与配图提示词轮"],
        "inputs": ["source.cleaned.txt"],
        "outputs": ["article.md", "cover_prompt.md"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_2",
    },
    "step_3": {
        "mode": "deterministic",
        "guides": [],
        "inputs": ["article.md", "cover_prompt.md"],
        "outputs": ["article.md", "cover_prompt.md"],
        "commands": [
            "python3 scripts/validate_workflow.py article {article_dir}",
            "python3 scripts/validate_workflow.py prompts {article_dir}",
        ],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_3",
    },
    "step_4": {
        "mode": "deterministic_skill",
        "guides": ["docs/steps/step4/markdown-guide.md"],
        "inputs": ["article.md", "cover_prompt.md"],
        "outputs": ["article.md"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_4",
    },
    "step_5": {
        "mode": "skill",
        "guides": ["docs/steps/step5/image-generation-guide.md"],
        "inputs": ["article.md", "cover_prompt.md"],
        "outputs": ["cover.png", "配图{1-N}.png"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_5",
    },
    "step_6": {
        "mode": "deterministic_skill",
        "guides": ["docs/steps/step6/html-guide.md"],
        "inputs": ["article.md", "cover.png", "配图{1-N}.png"],
        "outputs": ["article.html", "wechat-layout-check.json"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_6",
    },
    "step_7": {
        "mode": "ai_with_optional_readonly_discovery",
        "guides": ["docs/steps/step7/xiaohongshu-strategy-guide.md"],
        "inputs": ["article.md", "article.plan.md", "source.cleaned.txt"],
        "outputs": ["xiaohongshu-strategy.json"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_7",
    },
    "step_8": {
        "mode": "skill",
        "guides": ["docs/steps/step8/xiaohongshu-card-guide.md"],
        "inputs": ["article.md", "xiaohongshu-strategy.json", "cover.png", "配图{1-N}.png"],
        "outputs": ["小红书卡片-{01-N}.png", "xiaohongshu-card-check.json"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_8",
    },
    "step_9": {
        "mode": "two_pass_ai",
        "guides": ["docs/steps/step9/xiaohongshu-copy-guide.md"],
        "rounds": ["平台文案轮", "独立健康表达与去 AI 质检轮"],
        "inputs": ["article.md", "article.plan.md", "source.cleaned.txt", "xiaohongshu-strategy.json"],
        "outputs": ["小红书文案.txt"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_9",
    },
    "step_10": {
        "mode": "user_gate",
        "guides": ["docs/steps/step10/unified-approval-guide.md"],
        "inputs": [
            "article.md",
            "article.html",
            "cover.png",
            "配图{1-N}.png",
            "xiaohongshu-strategy.json",
            "小红书卡片-{01-N}.png",
            "小红书文案.txt",
        ],
        "outputs": ["workflow-state.json approval digest"],
        "completion_command": "python3 scripts/workflow_state.py approve {article_dir}",
    },
    "step_11": {
        "mode": "external_side_effect",
        "guides": ["docs/steps/step11/wechat-guide.md"],
        "inputs": ["article.html", "cover.png", "Step 10 approval"],
        "outputs": ["公众号草稿信息.txt", "source-map.json", "link-registry.json"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_11",
    },
    "step_12": {
        "mode": "deterministic",
        "guides": ["docs/steps/step12/final-cleanup-guide.md"],
        "inputs": ["all workflow artifacts"],
        "outputs": ["final asset whitelist"],
        "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_12",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _state_path(article_dir: Path | str) -> Path:
    return Path(article_dir) / STATE_FILENAME


def _new_step(number: int) -> dict[str, object]:
    step: dict[str, object] = {
        "status": "pending",
        "started_at": None,
        "validated_at": None,
        "completed_at": None,
        "reason": None,
    }
    if number == 10:
        step.update(
            {
                "approved": False,
                "approved_at": None,
                "artifacts_sha256": None,
            }
        )
    return step


def init_state(article_dir: Path | str) -> dict[str, object]:
    article_dir = Path(article_dir)
    article_dir.mkdir(parents=True, exist_ok=True)
    path = _state_path(article_dir)
    if path.exists():
        raise FileExistsError(f"{STATE_FILENAME} 已存在：{path}")
    state: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "article_dir": str(article_dir.resolve()),
        "current_step": "step_1",
        "steps": {
            f"step_{number}": _new_step(number) for number in range(1, 13)
        },
        "updated_at": _now(),
    }
    save_state(article_dir, state)
    return state


def _migrate_v1_state(state: dict[str, object]) -> dict[str, object]:
    """Map the former 11-step layout to schema v2 without replaying side effects."""
    old_steps = state.get("steps")
    if not isinstance(old_steps, dict):
        raise ValueError(f"{STATE_FILENAME} 缺少完整步骤")
    migrated = copy.deepcopy(state)
    new_steps = {f"step_{number}": _new_step(number) for number in range(1, 13)}
    for number in range(1, 7):
        if isinstance(old_steps.get(f"step_{number}"), dict):
            new_steps[f"step_{number}"] = copy.deepcopy(old_steps[f"step_{number}"])

    # Old Step 9/10 were cards/copy; old Step 8 was the WeChat side effect.
    if isinstance(old_steps.get("step_9"), dict):
        new_steps["step_8"] = copy.deepcopy(old_steps["step_9"])
    if isinstance(old_steps.get("step_10"), dict):
        new_steps["step_9"] = copy.deepcopy(old_steps["step_10"])
    if isinstance(old_steps.get("step_8"), dict):
        new_steps["step_11"] = copy.deepcopy(old_steps["step_8"])
    if isinstance(old_steps.get("step_11"), dict):
        new_steps["step_12"] = copy.deepcopy(old_steps["step_11"])

    # A fully completed legacy task remains historical-complete. Active tasks must
    # produce the new strategy/check artifacts and receive unified approval.
    legacy_complete = old_steps.get("step_11", {}).get("status") == "passed"
    if legacy_complete:
        new_steps["step_7"].update(
            {"status": "passed", "completed_at": state.get("updated_at")}
        )
        old_approval = old_steps.get("step_7", {})
        new_steps["step_10"].update(
            {
                "status": "passed",
                "approved": bool(old_approval.get("approved")),
                "approved_at": old_approval.get("approved_at"),
                "artifacts_sha256": old_approval.get("artifacts_sha256"),
                "completed_at": old_approval.get("completed_at"),
            }
        )

    migrated["schema_version"] = SCHEMA_VERSION
    migrated["steps"] = new_steps
    migrated["migrated_from_schema"] = 1
    if legacy_complete:
        migrated["current_step"] = "step_12"
    else:
        migrated["current_step"] = next(
            (
                name
                for name in STEP_NAMES
                if new_steps[name].get("status") != "passed"
            ),
            "step_12",
        )
    return migrated


def load_state(article_dir: Path | str) -> dict[str, object]:
    path = _state_path(article_dir)
    if not path.is_file():
        raise FileNotFoundError(f"缺少 {STATE_FILENAME}：{path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{STATE_FILENAME} 无效：{exc}") from exc
    if state.get("schema_version") == 1:
        state = _migrate_v1_state(state)
    elif state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"不支持的状态版本：{state.get('schema_version')}，需要 {SCHEMA_VERSION}"
        )
    steps = state.get("steps")
    if not isinstance(steps, dict) or any(name not in steps for name in STEP_NAMES):
        raise ValueError(f"{STATE_FILENAME} 缺少完整步骤")
    for name in STEP_NAMES:
        status = steps[name].get("status")
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"{name} 状态无效：{status}")
    return state


def save_state(article_dir: Path | str, state: dict[str, object]) -> None:
    article_dir = Path(article_dir)
    article_dir.mkdir(parents=True, exist_ok=True)
    state["schema_version"] = SCHEMA_VERSION
    state["updated_at"] = _now()
    path = _state_path(article_dir)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def workflow_context(article_dir: Path | str) -> dict[str, object]:
    """Return the minimal instructions needed to resume the current step."""
    article_path = Path(article_dir).resolve()
    state = load_state(article_path)
    current_step = str(state["current_step"])
    context = copy.deepcopy(STEP_CONTEXT[current_step])
    for key in ("commands",):
        if key in context:
            context[key] = [
                str(command).format(article_dir=article_path)
                for command in context[key]  # type: ignore[union-attr]
            ]
    if "completion_command" in context:
        context["completion_command"] = str(context["completion_command"]).format(
            article_dir=article_path
        )
    context.update(
        {
            "current_step": current_step,
            "status": _steps(state)[current_step]["status"],
            "article_dir": str(article_path),
        }
    )
    return context


def _steps(state: dict[str, object]) -> dict[str, dict[str, object]]:
    return state["steps"]  # type: ignore[return-value]


def _step_number(step: str) -> int:
    if step not in STEP_NAMES:
        raise ValueError(f"未知步骤：{step}")
    return int(step.split("_", 1)[1])


def start_step(
    article_dir: Path | str,
    step: str,
    *,
    enforce_previous: bool = True,
) -> dict[str, object]:
    number = _step_number(step)
    state = load_state(article_dir)
    steps = _steps(state)
    if enforce_previous and number > 1:
        previous = f"step_{number - 1}"
        if steps[previous]["status"] != "passed":
            raise ValueError(f"不能开始 {step}：前置步骤 {previous} 尚未通过")
    if step in {"step_11", "step_12"}:
        approval_errors = validate_approval(article_dir)
        if approval_errors:
            raise ValueError("Step 10 用户确认无效：" + "；".join(approval_errors))
    current_status = steps[step]["status"]
    if current_status == "passed":
        raise ValueError(f"{step} 已通过，不能重复开始")
    if current_status == "running":
        raise ValueError(f"{step} 已在运行")
    steps[step].update(
        {
            "status": "running",
            "started_at": _now(),
            "validated_at": None,
            "completed_at": None,
            "reason": None,
        }
    )
    state["current_step"] = step
    save_state(article_dir, state)
    return state


def _validate_step(article_dir: Path | str, step: str) -> list[str]:
    checks: dict[str, tuple[Callable[[Path | str], list[str]], ...]] = {
        "step_1": (validator.validate_cleaned_subtitle,),
        "step_2": (validator.validate_article, validator.validate_prompts),
        "step_3": (validator.validate_article, validator.validate_prompts),
        "step_4": (validator.validate_article, validator.validate_prompts),
        "step_5": (validator.validate_images,),
        "step_6": (validator.validate_html, validator.validate_wechat_layout),
        "step_7": (validator.validate_xiaohongshu_strategy,),
        "step_8": (validator.validate_cards, validator.validate_xiaohongshu_card_check),
        "step_9": (validator.validate_xiaohongshu_copy,),
        "step_11": (validator.validate_draft_record,),
        "step_12": (
            validator.validate_article,
            validator.validate_images,
            validator.validate_html,
            validator.validate_draft_record,
            validator.validate_cards,
            validator.validate_xiaohongshu_copy,
            validator.validate_final,
        ),
    }
    errors: list[str] = []
    if step == "step_11":
        errors.extend(validate_approval(article_dir))
    for check in checks.get(step, ()):
        errors.extend(check(article_dir))
    return errors


def pass_step(article_dir: Path | str, step: str) -> dict[str, object]:
    number = _step_number(step)
    if step == "step_10":
        raise ValueError("step_10 只能通过 approve 命令完成")
    state = load_state(article_dir)
    steps = _steps(state)
    if steps[step]["status"] != "running":
        raise ValueError(f"{step} 必须处于 running 才能通过")
    errors = _validate_step(article_dir, step)
    if errors:
        raise ValueError(f"{step} 校验失败：" + "；".join(errors))
    if step == "step_11":
        link_registry.finalize_mapping(article_dir)
    timestamp = _now()
    steps[step].update(
        {
            "status": "passed",
            "validated_at": timestamp,
            "completed_at": timestamp,
            "reason": None,
        }
    )
    state["current_step"] = f"step_{number + 1}" if number < 12 else "step_12"
    save_state(article_dir, state)
    return state


def block_step(article_dir: Path | str, step: str, reason: str) -> dict[str, object]:
    _step_number(step)
    if not reason.strip():
        raise ValueError("阻塞原因不能为空")
    state = load_state(article_dir)
    steps = _steps(state)
    if steps[step]["status"] != "running":
        raise ValueError(f"{step} 必须处于 running 才能标记 blocked")
    steps[step].update(
        {
            "status": "blocked",
            "completed_at": _now(),
            "reason": reason.strip(),
        }
    )
    state["current_step"] = step
    save_state(article_dir, state)
    return state


def reopen_step(
    article_dir: Path | str,
    step: str,
    reason: str,
) -> dict[str, object]:
    number = _step_number(step)
    if number > 10:
        raise ValueError("reopen 仅用于返回 Step 1-10 修改内容；发布后步骤应按失败重试规则处理")
    if not reason.strip():
        raise ValueError("重开原因不能为空")
    state = load_state(article_dir)
    steps = _steps(state)
    for reset_number in range(number, 13):
        steps[f"step_{reset_number}"] = _new_step(reset_number)
    state["current_step"] = step
    state["reopen_reason"] = reason.strip()
    state["reopened_at"] = _now()
    save_state(article_dir, state)
    return state


def _approval_artifacts(article_dir: Path | str) -> list[Path]:
    article_dir = Path(article_dir)
    fixed = [
        article_dir / "article.md",
        article_dir / "article.html",
        article_dir / "cover.png",
        article_dir / "小红书文案.txt",
    ]
    body_images = sorted(
        article_dir.glob("配图*.png"),
        key=lambda path: int(re.search(r"\d+", path.name).group()),  # type: ignore[union-attr]
    )
    cards = sorted(article_dir.glob("小红书卡片-*.png"))
    missing = [path.name for path in fixed if not path.is_file()]
    if not body_images:
        missing.append("配图1.png")
    if not cards:
        missing.append("小红书卡片-01.png")
    if missing:
        raise ValueError("缺少 Step 10 确认资产：" + "、".join(missing))
    return fixed + body_images + cards


def artifact_digest(article_dir: Path | str) -> str:
    article_dir = Path(article_dir)
    digest = hashlib.sha256()
    for path in _approval_artifacts(article_dir):
        digest.update(path.relative_to(article_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def approve(article_dir: Path | str) -> dict[str, object]:
    state = load_state(article_dir)
    steps = _steps(state)
    if steps["step_9"]["status"] != "passed":
        raise ValueError("Step 9 尚未通过，不能确认统一预览")
    if steps["step_10"]["status"] != "running":
        raise ValueError("Step 10 必须处于 running 才能记录用户确认")
    validation_errors: list[str] = []
    for check in (
        validator.validate_article,
        validator.validate_images,
        validator.validate_html,
        validator.validate_wechat_layout,
        validator.validate_xiaohongshu_strategy,
        validator.validate_cards,
        validator.validate_xiaohongshu_card_check,
        validator.validate_xiaohongshu_copy,
    ):
        validation_errors.extend(check(article_dir))
    if validation_errors:
        raise ValueError("Step 10 当前资产校验失败：" + "；".join(validation_errors))
    digest = artifact_digest(article_dir)
    timestamp = _now()
    steps["step_10"].update(
        {
            "status": "passed",
            "approved": True,
            "approved_at": timestamp,
            "artifacts_sha256": digest,
            "validated_at": timestamp,
            "completed_at": timestamp,
            "reason": None,
        }
    )
    state["current_step"] = "step_11"
    save_state(article_dir, state)
    return state


def validate_approval(article_dir: Path | str) -> list[str]:
    try:
        state = load_state(article_dir)
    except (FileNotFoundError, ValueError) as exc:
        return [str(exc)]
    step = _steps(state)["step_10"]
    if step.get("status") != "passed" or not step.get("approved"):
        return ["Step 10 尚未获得用户明确确认"]
    expected = step.get("artifacts_sha256")
    try:
        actual = artifact_digest(article_dir)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    if expected != actual:
        return ["Step 10 确认已失效：公众号或小红书资产在确认后发生变化"]
    return []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("article_dir", type=Path)

    for command in ("start", "pass"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("article_dir", type=Path)
        command_parser.add_argument("step", choices=STEP_NAMES)

    block_parser = subparsers.add_parser("block")
    block_parser.add_argument("article_dir", type=Path)
    block_parser.add_argument("step", choices=STEP_NAMES)
    block_parser.add_argument("--reason", required=True)

    reopen_parser = subparsers.add_parser("reopen")
    reopen_parser.add_argument("article_dir", type=Path)
    reopen_parser.add_argument("step", choices=STEP_NAMES[:10])
    reopen_parser.add_argument("--reason", required=True)

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("article_dir", type=Path)

    check_parser = subparsers.add_parser("check-approval")
    check_parser.add_argument("article_dir", type=Path)

    context_parser = subparsers.add_parser("context")
    context_parser.add_argument("article_dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            init_state(args.article_dir)
        elif args.command == "start":
            start_step(args.article_dir, args.step)
        elif args.command == "pass":
            pass_step(args.article_dir, args.step)
        elif args.command == "block":
            block_step(args.article_dir, args.step, args.reason)
        elif args.command == "reopen":
            reopen_step(args.article_dir, args.step, args.reason)
        elif args.command == "approve":
            approve(args.article_dir)
        elif args.command == "check-approval":
            errors = validate_approval(args.article_dir)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
        elif args.command == "context":
            print(json.dumps(workflow_context(args.article_dir), ensure_ascii=False, indent=2))
            return 0
    except (FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
