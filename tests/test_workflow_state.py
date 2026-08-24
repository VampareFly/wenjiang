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
        state["current_step"] = f"step_{min(step_number + 1, 12)}"
        workflow_state.save_state(self.root, state)

    def write_approval_artifacts(self) -> None:
        (self.root / "article.md").write_text(
            "---\ntitle: 久坐以后，身体为什么总觉得沉\n"
            "description: 相关研究解释了久坐后的身体感受。\n"
            "author: 食外\n---\n正文\n【配图1：久坐后的身体变化】\n",
            encoding="utf-8",
        )
        (self.root / "article.html").write_text(
            '<section style="max-width:677px;line-height:1.8;color:#52525B">'
            '<p>正文</p><img src="配图1.png" alt="久坐后的身体变化"></section>',
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
        (self.root / "wechat-layout-check.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "renderer": "gzh-design-skill",
                    "theme_id": "graphite-minimal",
                    "brand_config": "config/wechat-brand.json",
                    "gzh_errors": 0,
                    "gzh_warnings": 0,
                    "mobile_preview": {
                        "reviewed": True,
                        "viewport_width": 390,
                        "first_screen_clear": True,
                        "headings_wrap_cleanly": True,
                        "card_density_ok": True,
                        "images_balanced": True,
                        "spacing_consistent": True,
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.root / "xiaohongshu-strategy.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "mode": "evergreen",
                    "researched_at": None,
                    "primary_keyword": "久坐",
                    "secondary_keywords": ["身体沉", "生活方式"],
                    "search_intent": "久坐后为什么身体沉",
                    "content_angle": "解释久坐后的身体感受",
                    "trend_evidence": [],
                    "external_facts_used": False,
                    "fact_boundaries": ["不新增疗效"],
                    "cta_mode": "omit",
                    "cta_reason": "短文已经回答核心问题",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        card_data = (
            b"\x89PNG\r\n\x1a\n"
            + struct.pack(">I", 13)
            + b"IHDR"
            + struct.pack(">II", 1080, 1440)
        )
        (self.root / "小红书卡片-01.png").write_bytes(card_data)
        (self.root / "xiaohongshu-card-check.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "pages": [
                        {
                            "file": "小红书卡片-01.png",
                            "width": 1080,
                            "height": 1440,
                            "overflow": False,
                            "min_font_px": 28,
                            "footer_gap_px": 24,
                            "background_layer": True,
                        }
                    ],
                    "cover_review": {
                        "reviewed": True,
                        "thumbnail_clear": True,
                        "title_clear": True,
                        "meaningful_visual": True,
                        "no_dead_space": True,
                        "background_supports_reading": True,
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.root / "小红书文案.txt").write_text(
            "久坐后为什么身体沉\n久坐以后身体发沉，可以先从活动节奏看。\n#久坐 #身体健康 #生活方式",
            encoding="utf-8",
        )
        (self.root / "今日头条文章.md").write_text(
            "# 为什么久坐后身体总是发沉？3招找回充沛精力\n\n"
            "> 1. 《为什么久坐后身体总是发沉？3招找回充沛精力》（23字）\n\n"
            "正文\n\n## 标题候选\n1. 标题一\n",
            encoding="utf-8",
        )
        (self.root / "微头条.txt").write_text(
            "为什么久坐后身体总是发沉？\n\n"
            "分享 3 个简单调整：\n"
            "1. 每工作 45 分钟起身活动 2 分钟；\n"
            "2. 喝水并做简单拉伸；\n"
            "3. 保持深呼吸调动核心。\n\n"
            "你平时也有久坐发沉的感觉吗？欢迎评论区聊聊！\n\n"
            "#久坐健康# #健康科普#",
            encoding="utf-8",
        )
        for i in (1, 2, 3):
            data = (
                b"\x89PNG\r\n\x1a\n"
                + struct.pack(">I", 13)
                + b"IHDR"
                + struct.pack(">II", 160, 90)
                + f"toutiao-{i}".encode("utf-8")
            )
            (self.root / f"toutiao-cover-{i}.png").write_bytes(data)

    def test_init_creates_all_pending_steps(self):


        state = workflow_state.init_state(self.root)
        self.assertEqual("step_1", state["current_step"])
        self.assertEqual("pending", state["steps"]["step_12"]["status"])
        self.assertFalse(state["steps"]["step_10"]["approved"])

    def test_init_refuses_to_overwrite_existing_state(self):
        workflow_state.init_state(self.root)
        with self.assertRaisesRegex(FileExistsError, "workflow-state.json"):
            workflow_state.init_state(self.root)

    def test_schema_one_state_is_migrated_to_twelve_step_layout(self):
        legacy_steps = {
            f"step_{number}": workflow_state._new_step(number)
            for number in range(1, 12)
        }
        for number in range(1, 7):
            legacy_steps[f"step_{number}"]["status"] = "passed"
        legacy_steps["step_8"]["status"] = "passed"
        legacy_steps["step_9"]["status"] = "passed"
        legacy_steps["step_10"]["status"] = "pending"
        (self.root / "workflow-state.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "article_dir": str(self.root),
                    "current_step": "step_10",
                    "steps": legacy_steps,
                    "updated_at": "2026-08-19T00:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )

        state = workflow_state.load_state(self.root)

        self.assertEqual(2, state["schema_version"])
        self.assertEqual("passed", state["steps"]["step_8"]["status"])
        self.assertEqual("passed", state["steps"]["step_11"]["status"])
        self.assertEqual("pending", state["steps"]["step_12"]["status"])
        self.assertEqual("step_7", state["current_step"])

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
        self.assertEqual(["docs/steps/step1/subtitle-guide.md"], context["guides"])
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
                "docs/steps/step2/writing-guide.md",
                "docs/steps/step2/editorial-guide.md",
                "docs/steps/step2/final-review-guide.md",
                "docs/steps/step2/image-prompt-guide.md",
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

    def test_all_step_context_guide_paths_exist(self):
        project_root = Path(__file__).resolve().parents[1]
        for step, cfg in workflow_state.STEP_CONTEXT.items():
            for guide in cfg.get("guides", []):
                self.assertTrue(
                    (project_root / guide).is_file(),
                    f"{step} 的指南路径不存在：{guide}",
                )

    def test_step_seven_to_nine_route_to_split_xiaohongshu_guides(self):
        self.assertEqual(
            workflow_state.STEP_CONTEXT["step_7"]["guides"],
            ["docs/steps/step7/xiaohongshu-strategy-guide.md"],
        )
        self.assertEqual(
            workflow_state.STEP_CONTEXT["step_8"]["guides"],
            ["docs/steps/step8/xiaohongshu-card-guide.md"],
        )
        self.assertEqual(
            workflow_state.STEP_CONTEXT["step_9"]["guides"],
            [
                "docs/steps/step9/xiaohongshu-copy-guide.md",
                "docs/steps/step9/toutiao-guide.md",
            ],
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

    def test_step_ten_can_only_pass_through_approve(self):
        workflow_state.init_state(self.root)
        self.mark_passed_through(9)
        workflow_state.start_step(self.root, "step_10")
        with self.assertRaisesRegex(ValueError, "approve"):
            workflow_state.pass_step(self.root, "step_10")

    def test_approval_digest_becomes_stale_after_artifact_change(self):
        self.write_approval_artifacts()
        workflow_state.init_state(self.root)
        self.mark_passed_through(9)
        workflow_state.start_step(self.root, "step_10")
        workflow_state.approve(self.root)
        self.assertEqual([], workflow_state.validate_approval(self.root))
        (self.root / "article.html").write_text("changed", encoding="utf-8")
        self.assertTrue(workflow_state.validate_approval(self.root))

    def test_step_eleven_requires_fresh_approval(self):
        self.write_approval_artifacts()
        workflow_state.init_state(self.root)
        self.mark_passed_through(9)
        with self.assertRaisesRegex(ValueError, "Step 10"):
            workflow_state.start_step(self.root, "step_11", enforce_previous=False)
        workflow_state.start_step(self.root, "step_10")
        workflow_state.approve(self.root)
        state = workflow_state.start_step(self.root, "step_11")
        self.assertEqual("running", state["steps"]["step_11"]["status"])

    def test_step_eleven_cannot_pass_if_approval_becomes_stale(self):
        self.write_approval_artifacts()
        workflow_state.init_state(self.root)
        self.mark_passed_through(9)
        workflow_state.start_step(self.root, "step_10")
        workflow_state.approve(self.root)
        workflow_state.start_step(self.root, "step_11")
        (self.root / "article.html").write_text("changed", encoding="utf-8")
        (self.root / "公众号草稿信息.txt").write_text(
            "草稿 media_id：test-id",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "确认已失效"):
            workflow_state.pass_step(self.root, "step_11")

    def test_approval_requires_all_expected_artifacts(self):
        workflow_state.init_state(self.root)
        self.mark_passed_through(9)
        workflow_state.start_step(self.root, "step_10")
        with self.assertRaisesRegex(ValueError, "article.md"):
            workflow_state.approve(self.root)

    def test_approval_revalidates_current_article_images_and_html(self):
        self.write_approval_artifacts()
        (self.root / "article.md").write_text("invalid", encoding="utf-8")
        workflow_state.init_state(self.root)
        self.mark_passed_through(9)
        workflow_state.start_step(self.root, "step_10")
        with self.assertRaisesRegex(ValueError, "frontmatter"):
            workflow_state.approve(self.root)

    def test_reopen_resets_target_and_downstream_approval(self):
        self.write_approval_artifacts()
        workflow_state.init_state(self.root)
        self.mark_passed_through(9)
        workflow_state.start_step(self.root, "step_10")
        workflow_state.approve(self.root)

        state = workflow_state.reopen_step(self.root, "step_4", "用户要求调整排版")

        self.assertEqual("passed", state["steps"]["step_3"]["status"])
        for number in range(4, 13):
            self.assertEqual("pending", state["steps"][f"step_{number}"]["status"])
        self.assertFalse(state["steps"]["step_10"]["approved"])
        self.assertIsNone(state["steps"]["step_10"]["artifacts_sha256"])
        self.assertEqual("step_4", state["current_step"])
        self.assertEqual("用户要求调整排版", state["reopen_reason"])

    def test_step_twelve_revalidates_content_not_only_file_names(self):
        self.write_approval_artifacts()
        workflow_state.init_state(self.root)
        self.mark_passed_through(9)
        workflow_state.start_step(self.root, "step_10")
        workflow_state.approve(self.root)
        state = workflow_state.load_state(self.root)
        state["steps"]["step_11"]["status"] = "passed"
        state["current_step"] = "step_12"
        workflow_state.save_state(self.root, state)
        workflow_state.start_step(self.root, "step_12")
        (self.root / "article.md").write_text("invalid", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "frontmatter"):
            workflow_state.pass_step(self.root, "step_12")


if __name__ == "__main__":
    unittest.main()
