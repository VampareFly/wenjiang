import struct
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts import workflow_state


class WorkflowStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def mark_passed_through(self, step_number: int) -> None:
        state = workflow_state.load_state(self.root)
        for number in range(1, step_number + 1):
            state["steps"][f"step_{number}"]["status"] = "passed"
        state["current_step"] = f"step_{min(step_number + 1, 11)}"
        workflow_state.save_state(self.root, state)

    def write_approval_artifacts(self) -> None:
        (self.root / "article.md").write_text(
            "---\ntitle: 久坐以后，身体为什么总觉得沉\n"
            "description: 相关研究解释了久坐后的身体感受。\n"
            "author: 身心漫游\n---\n正文\n【配图1：久坐后的身体变化】\n",
            encoding="utf-8",
        )
        (self.root / "article.html").write_text(
            '<p>正文</p><img src="配图1.png" alt="久坐后的身体变化">',
            encoding="utf-8",
        )
        for name, width, height in (("cover.png", 235, 100), ("配图1.png", 16, 9)):
            data = (
                b"\x89PNG\r\n\x1a\n"
                + struct.pack(">I", 13)
                + b"IHDR"
                + struct.pack(">II", width, height)
            )
            (self.root / name).write_bytes(data)

    def test_init_creates_all_pending_steps(self):
        state = workflow_state.init_state(self.root)
        self.assertEqual("step_1", state["current_step"])
        self.assertEqual("pending", state["steps"]["step_11"]["status"])
        self.assertFalse(state["steps"]["step_7"]["approved"])

    def test_init_refuses_to_overwrite_existing_state(self):
        workflow_state.init_state(self.root)
        with self.assertRaisesRegex(FileExistsError, "workflow-state.json"):
            workflow_state.init_state(self.root)

    def test_cannot_start_step_before_previous_passes(self):
        workflow_state.init_state(self.root)
        with self.assertRaisesRegex(ValueError, "step_1"):
            workflow_state.start_step(self.root, "step_2")

    def test_start_and_block_step_records_reason(self):
        workflow_state.init_state(self.root)
        workflow_state.start_step(self.root, "step_1")
        state = workflow_state.block_step(self.root, "step_1", "清洗失败")
        self.assertEqual("blocked", state["steps"]["step_1"]["status"])
        self.assertEqual("清洗失败", state["steps"]["step_1"]["reason"])

    def test_step_one_cannot_pass_without_valid_cleaned_subtitle(self):
        workflow_state.init_state(self.root)
        workflow_state.start_step(self.root, "step_1")
        with self.assertRaisesRegex(ValueError, "清洗字幕"):
            workflow_state.pass_step(self.root, "step_1")

    def test_step_one_passes_after_subtitle_validation(self):
        (self.root / "source.cleaned.txt").write_text("有效字幕正文", encoding="utf-8")
        workflow_state.init_state(self.root)
        workflow_state.start_step(self.root, "step_1")
        state = workflow_state.pass_step(self.root, "step_1")
        self.assertEqual("passed", state["steps"]["step_1"]["status"])
        self.assertEqual("step_2", state["current_step"])
        self.assertIsNotNone(state["steps"]["step_1"]["validated_at"])

    def test_context_routes_step_one_without_mutating_state(self):
        workflow_state.init_state(self.root)

        context = workflow_state.workflow_context(self.root)

        self.assertEqual("step_1", context["current_step"])
        self.assertEqual("pending", context["status"])
        self.assertEqual("deterministic", context["mode"])
        self.assertEqual(["docs/subtitle-guide.md"], context["guides"])
        self.assertIn("source.cleaned.txt", context["outputs"])
        self.assertEqual("pending", workflow_state.load_state(self.root)["steps"]["step_1"]["status"])

    def test_context_routes_step_two_to_three_normal_passes(self):
        workflow_state.init_state(self.root)
        self.mark_passed_through(1)

        context = workflow_state.workflow_context(self.root)

        self.assertEqual("step_2", context["current_step"])
        self.assertEqual("three_pass_ai", context["mode"])
        self.assertEqual(
            ["内容初稿轮", "编辑终稿轮", "独立质检与配图提示词轮"],
            context["rounds"],
        )
        self.assertEqual(
            [
                "docs/writing-guide.md",
                "docs/editorial-guide.md",
                "docs/final-review-guide.md",
                "docs/image-prompt-guide.md",
            ],
            context["guides"],
        )
        self.assertEqual(["article.md", "cover_prompt.md"], context["outputs"])

    def test_context_routes_step_three_to_deterministic_validation(self):
        workflow_state.init_state(self.root)
        self.mark_passed_through(2)

        context = workflow_state.workflow_context(self.root)

        self.assertEqual("step_3", context["current_step"])
        self.assertEqual("deterministic", context["mode"])
        self.assertEqual([], context["guides"])
        self.assertEqual(
            [
                f"python3 scripts/validate_workflow.py article {self.root.resolve()}",
                f"python3 scripts/validate_workflow.py prompts {self.root.resolve()}",
            ],
            context["commands"],
        )

    def test_context_cli_prints_json_without_ok_suffix(self):
        workflow_state.init_state(self.root)
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = workflow_state.main(["context", str(self.root)])

        self.assertEqual(0, exit_code)
        payload = json.loads(output.getvalue())
        self.assertEqual("step_1", payload["current_step"])
        self.assertNotIn("OK", output.getvalue())

    def test_step_seven_can_only_pass_through_approve(self):
        workflow_state.init_state(self.root)
        self.mark_passed_through(6)
        workflow_state.start_step(self.root, "step_7")
        with self.assertRaisesRegex(ValueError, "approve"):
            workflow_state.pass_step(self.root, "step_7")

    def test_approval_digest_becomes_stale_after_artifact_change(self):
        self.write_approval_artifacts()
        workflow_state.init_state(self.root)
        self.mark_passed_through(6)
        workflow_state.start_step(self.root, "step_7")
        workflow_state.approve(self.root)
        self.assertEqual([], workflow_state.validate_approval(self.root))
        (self.root / "article.html").write_text("changed", encoding="utf-8")
        self.assertTrue(workflow_state.validate_approval(self.root))

    def test_step_eight_requires_fresh_approval(self):
        self.write_approval_artifacts()
        workflow_state.init_state(self.root)
        self.mark_passed_through(6)
        with self.assertRaisesRegex(ValueError, "Step 7"):
            workflow_state.start_step(self.root, "step_8", enforce_previous=False)
        workflow_state.start_step(self.root, "step_7")
        workflow_state.approve(self.root)
        state = workflow_state.start_step(self.root, "step_8")
        self.assertEqual("running", state["steps"]["step_8"]["status"])

    def test_step_eight_cannot_pass_if_approval_becomes_stale(self):
        self.write_approval_artifacts()
        workflow_state.init_state(self.root)
        self.mark_passed_through(6)
        workflow_state.start_step(self.root, "step_7")
        workflow_state.approve(self.root)
        workflow_state.start_step(self.root, "step_8")
        (self.root / "article.html").write_text("changed", encoding="utf-8")
        (self.root / "公众号草稿信息.txt").write_text(
            "草稿 media_id：test-id",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "确认已失效"):
            workflow_state.pass_step(self.root, "step_8")

    def test_approval_requires_all_expected_artifacts(self):
        workflow_state.init_state(self.root)
        self.mark_passed_through(6)
        workflow_state.start_step(self.root, "step_7")
        with self.assertRaisesRegex(ValueError, "article.md"):
            workflow_state.approve(self.root)

    def test_approval_revalidates_current_article_images_and_html(self):
        self.write_approval_artifacts()
        (self.root / "article.md").write_text("invalid", encoding="utf-8")
        workflow_state.init_state(self.root)
        self.mark_passed_through(6)
        workflow_state.start_step(self.root, "step_7")
        with self.assertRaisesRegex(ValueError, "frontmatter"):
            workflow_state.approve(self.root)

    def test_reopen_resets_target_and_downstream_approval(self):
        self.write_approval_artifacts()
        workflow_state.init_state(self.root)
        self.mark_passed_through(6)
        workflow_state.start_step(self.root, "step_7")
        workflow_state.approve(self.root)

        state = workflow_state.reopen_step(self.root, "step_4", "用户要求调整排版")

        self.assertEqual("passed", state["steps"]["step_3"]["status"])
        for number in range(4, 12):
            self.assertEqual("pending", state["steps"][f"step_{number}"]["status"])
        self.assertFalse(state["steps"]["step_7"]["approved"])
        self.assertIsNone(state["steps"]["step_7"]["artifacts_sha256"])
        self.assertEqual("step_4", state["current_step"])
        self.assertEqual("用户要求调整排版", state["reopen_reason"])

    def test_step_eleven_revalidates_content_not_only_file_names(self):
        workflow_state.init_state(self.root)
        for name in (
            "article.md",
            "article.html",
            "cover.png",
            "配图1.png",
            "公众号草稿信息.txt",
            "小红书卡片-01.png",
            "小红书文案.txt",
        ):
            (self.root / name).write_bytes(b"x")
        self.mark_passed_through(10)
        workflow_state.start_step(self.root, "step_11")
        with self.assertRaisesRegex(ValueError, "frontmatter"):
            workflow_state.pass_step(self.root, "step_11")


if __name__ == "__main__":
    unittest.main()
