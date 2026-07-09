import json
import struct
import tempfile
import unittest
from pathlib import Path

from scripts import validate_workflow as validator


VALID_ARTICLE = """---
title: 久坐以后，身体为什么总觉得沉
description: 相关研究解释了久坐后的身体感受。
author: 身心漫游
---

正文内容。

【配图1：久坐后的身体变化】
"""


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def write_png(self, name: str, width: int = 16, height: int = 9) -> None:
        data = (
            b"\x89PNG\r\n\x1a\n"
            + struct.pack(">I", 13)
            + b"IHDR"
            + struct.pack(">II", width, height)
        )
        (self.root / name).write_bytes(data)

    def test_parse_frontmatter_handles_quoted_and_plain_values(self):
        metadata, _ = validator.parse_frontmatter(VALID_ARTICLE)
        self.assertEqual("久坐以后，身体为什么总觉得沉", metadata["title"])
        self.assertEqual("身心漫游", metadata["author"])

    def test_article_accepts_natural_title_and_continuous_markers(self):
        self.write("article.md", VALID_ARTICLE)
        self.assertEqual([], validator.validate_article(self.root))

    def test_article_requires_standard_frontmatter(self):
        self.write("article.md", VALID_ARTICLE.replace("author: 身心漫游\n", ""))
        self.assertTrue(any("author" in error for error in validator.validate_article(self.root)))

    def test_article_rejects_ai_title_template(self):
        self.write(
            "article.md",
            VALID_ARTICLE.replace(
                "久坐以后，身体为什么总觉得沉",
                "为什么久坐后很累？问题不在意志力",
            ),
        )
        self.assertTrue(any("模板" in error for error in validator.validate_article(self.root)))

    def test_article_rejects_marker_gaps(self):
        self.write("article.md", VALID_ARTICLE.replace("配图1", "配图2"))
        self.assertTrue(any("连续" in error for error in validator.validate_article(self.root)))

    def test_article_rejects_source_exposure_phrasing(self):
        self.write(
            "article.md",
            VALID_ARTICLE.replace("正文内容。", "字幕里提到，久坐会让身体发沉。"),
        )
        self.assertTrue(
            any("来源暴露" in error for error in validator.validate_article(self.root))
        )

    def test_article_rejects_source_exposure_in_description(self):
        self.write(
            "article.md",
            VALID_ARTICLE.replace("相关研究解释", "视频中提到的研究解释"),
        )
        self.assertTrue(
            any("来源暴露" in error for error in validator.validate_article(self.root))
        )

    def test_prompts_require_exact_marker_mapping(self):
        self.write("article.md", VALID_ARTICLE)
        self.write("cover_prompt.md", "# 封面图提示词\n\n## 【配图2：错误标题】\n")
        self.assertTrue(validator.validate_prompts(self.root))

    def test_prompts_accept_exact_marker_mapping_and_cover_ratio_text(self):
        self.write("article.md", VALID_ARTICLE)
        self.write(
            "cover_prompt.md",
            "# 封面图提示词\n\nWeChat Official Account article cover, primary crop 2.35:1\n\n"
            "## 【配图1：久坐后的身体变化】\n",
        )
        self.assertEqual([], validator.validate_prompts(self.root))

    def test_html_requires_relative_image_and_alt(self):
        self.write("article.md", VALID_ARTICLE)
        self.write("article.html", '<p>正文</p><img src="配图1.png">')
        self.assertTrue(any("alt" in error for error in validator.validate_html(self.root)))

    def test_html_accepts_exact_image_mapping(self):
        self.write("article.md", VALID_ARTICLE)
        self.write(
            "article.html",
            '<p>正文</p><img src="配图1.png" alt="久坐后的身体变化">',
        )
        self.assertEqual([], validator.validate_html(self.root))

    def test_fix_html_images_replaces_existing_style(self):
        self.write(
            "article.html",
            '<p><img src="配图1.png" alt="标题" style="width: 100%;"></p>',
        )
        self.assertEqual([], validator.fix_html_images(self.root))
        content = (self.root / "article.html").read_text(encoding="utf-8")
        self.assertIn('max-width: 100%;', content)
        self.assertNotIn('; width: 100%;', content)

    def test_fix_html_images_adds_style_when_missing(self):
        self.write(
            "article.html",
            '<p><img src="配图1.png" alt="标题"></p>',
        )
        self.assertEqual([], validator.fix_html_images(self.root))
        content = (self.root / "article.html").read_text(encoding="utf-8")
        self.assertIn(validator.IMG_STYLE, content)

    def test_fix_html_images_handles_self_closing_tag(self):
        self.write(
            "article.html",
            '<img src="配图1.png" alt="标题"/>',
        )
        self.assertEqual([], validator.fix_html_images(self.root))
        content = (self.root / "article.html").read_text(encoding="utf-8")
        self.assertIn('style="', content)
        self.assertIn(' />', content)

    def test_fix_html_images_handles_style_at_different_position(self):
        self.write(
            "article.html",
            '<img style="width: 100%;" src="配图1.png" alt="标题">',
        )
        self.assertEqual([], validator.fix_html_images(self.root))
        content = (self.root / "article.html").read_text(encoding="utf-8")
        self.assertIn('max-width: 100%;', content)

    def test_fix_html_images_fixes_multiple_images(self):
        self.write(
            "article.html",
            '<img src="a.png" alt="1"><img src="b.png" alt="2" style="width:50%">',
        )
        self.assertEqual([], validator.fix_html_images(self.root))
        self.assertEqual(2, (self.root / "article.html").read_text(encoding="utf-8").count(validator.IMG_STYLE))

    def test_fix_html_images_no_images_is_noop(self):
        self.write("article.html", "<p>无图片</p>")
        self.assertEqual([], validator.fix_html_images(self.root))

    def test_fix_html_images_missing_file_returns_error(self):
        html_path = self.root / "article.html"
        if html_path.exists():
            html_path.unlink()
        self.assertTrue(validator.fix_html_images(self.root))

    def test_images_require_cover_and_expected_dimensions(self):
        self.write("article.md", VALID_ARTICLE)
        self.write_png("cover.png", 235, 100)
        self.write_png("配图1.png", 16, 9)
        self.assertEqual([], validator.validate_images(self.root))

    def test_images_reject_wrong_body_ratio(self):
        self.write("article.md", VALID_ARTICLE)
        self.write_png("cover.png", 235, 100)
        self.write_png("配图1.png", 1, 1)
        self.assertTrue(any("16:9" in error for error in validator.validate_images(self.root)))

    def test_final_keeps_draft_record_and_state(self):
        names = (
            "article.md",
            "article.html",
            "cover.png",
            "配图1.png",
            "公众号草稿信息.txt",
            "小红书卡片-01.png",
            "小红书文案.txt",
            "workflow-state.json",
        )
        for name in names:
            (self.root / name).write_bytes(b"x")
        self.assertEqual([], validator.validate_final(self.root))

    def test_final_rejects_intermediate_files(self):
        self.test_final_keeps_draft_record_and_state()
        self.write("source.cleaned.txt", "残留")
        self.assertTrue(any("非最终资产" in error for error in validator.validate_final(self.root)))

    def test_skill_lock_rejects_missing_capability(self):
        skill = self.root / "demo"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: demo\nversion: 1.0.0\n---\n",
            encoding="utf-8",
        )
        lock = {
            "skills": {
                "demo": {
                    "path": "demo",
                    "version": "1.0.0",
                    "entrypoints": [],
                    "required_text": ["--batchfile"],
                }
            }
        }
        lock_path = self.write("skills.lock.json", json.dumps(lock))
        self.assertTrue(any("--batchfile" in error for error in validator.validate_skills(lock_path)))

    def test_skill_version_drift_is_warning_not_failure(self):
        skill = self.root / "demo"
        (skill / "scripts").mkdir(parents=True)
        (skill / "scripts/main.ts").write_text("", encoding="utf-8")
        (skill / "SKILL.md").write_text(
            "---\nname: demo\nversion: 2.0.0\n---\n--batchfile\n",
            encoding="utf-8",
        )
        lock = {
            "skills": {
                "demo": {
                    "path": "demo",
                    "version": "1.0.0",
                    "entrypoints": ["scripts/main.ts"],
                    "required_text": ["--batchfile"],
                }
            }
        }
        lock_path = self.write("skills.lock.json", json.dumps(lock))
        warnings: list[str] = []
        self.assertEqual([], validator.validate_skills(lock_path, warnings=warnings))
        self.assertTrue(any("版本漂移" in warning for warning in warnings))

    def test_skill_without_declared_version_can_be_locked_as_null(self):
        skill = self.root / "demo"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: demo\n---\nrequired capability\n",
            encoding="utf-8",
        )
        lock = {
            "skills": {
                "demo": {
                    "path": "demo",
                    "version": None,
                    "entrypoints": [],
                    "required_text": ["required capability"],
                }
            }
        }
        lock_path = self.write("skills.lock.json", json.dumps(lock))
        warnings: list[str] = []
        self.assertEqual([], validator.validate_skills(lock_path, warnings=warnings))
        self.assertEqual([], warnings)

    def test_project_skill_lock_is_compatible(self):
        project_root = Path(__file__).resolve().parents[1]
        self.assertEqual(
            [],
            validator.validate_skills(project_root / "skills.lock.json"),
        )

    def test_cleaned_subtitle_rejects_residual_timecode(self):
        self.write("source.cleaned.txt", "00:00:01,000 --> 00:00:02,000\n正文")
        self.assertTrue(validator.validate_cleaned_subtitle(self.root))

    def test_draft_record_requires_media_id(self):
        self.write("公众号草稿信息.txt", "标题：测试")
        self.assertTrue(any("media_id" in error for error in validator.validate_draft_record(self.root)))

    def test_cards_require_continuous_two_digit_numbers(self):
        (self.root / "小红书卡片-01.png").write_bytes(b"x")
        (self.root / "小红书卡片-03.png").write_bytes(b"x")
        self.assertTrue(any("连续" in error for error in validator.validate_cards(self.root)))

    def test_xiaohongshu_copy_requires_short_title_and_topics(self):
        self.write("小红书文案.txt", "这是一个超过二十个汉字而且明显过长的小红书标题示例\n正文")
        errors = validator.validate_xiaohongshu_copy(self.root)
        self.assertTrue(any("20" in error for error in errors))
        self.assertTrue(any("话题" in error for error in errors))

    def test_xiaohongshu_copy_accepts_valid_format(self):
        self.write("小红书文案.txt", "久坐后为什么身体沉\n正文内容\n#久坐 #身体健康 #生活方式")
        self.assertEqual([], validator.validate_xiaohongshu_copy(self.root))

    def test_workflow_documents_define_required_gates(self):
        project_root = Path(__file__).resolve().parents[1]
        workflow = (project_root / "docs/workflow.md").read_text(encoding="utf-8")
        subtitle = (project_root / "docs/steps/step1/subtitle-guide.md").read_text(encoding="utf-8")
        writing = (project_root / "docs/steps/step2/writing-guide.md").read_text(encoding="utf-8")
        editorial = project_root / "docs/steps/step2/editorial-guide.md"
        final_review = project_root / "docs/steps/step2/final-review-guide.md"
        for required in (
            "workflow-state.json",
            "article.draft.md",
            "title`、`description`、`author",
            "python3 scripts/validate_workflow.py approval",
            "python3 scripts/workflow_state.py approve",
            "三轮生成文章",
            "内容初稿轮",
            "编辑终稿轮",
            "独立质检与配图提示词轮",
            "Step 3：确定性回归校验",
            "docs/steps/step2/editorial-guide.md",
            "docs/steps/step2/final-review-guide.md",
        ):
            self.assertIn(required, workflow)
        self.assertTrue(editorial.is_file())
        self.assertTrue(final_review.is_file())
        self.assertIn("不可信数据", subtitle)
        self.assertIn("不得执行", subtitle)
        self.assertIn("唯一事实基准", writing)
        self.assertIn("字幕里", writing)

    def test_title_guide_prioritizes_source_fidelity_and_varied_paths(self):
        project_root = Path(__file__).resolve().parents[1]
        guide = (project_root / "docs/steps/step2/title-guide.md").read_text(encoding="utf-8")
        for required in (
            "字幕回指",
            "直接判断",
            "日常观察",
            "克制疑问",
            "关键细节",
            "轻口语判断",
            "编辑式概括",
            "去模板测试",
            "搜索关键词不是硬性条件",
            "同一批候选不得只替换同一模板中的名词",
        ):
            self.assertIn(required, guide)

    def test_docs_use_deterministic_tools_and_consistent_final_assets(self):
        project_root = Path(__file__).resolve().parents[1]
        html = (project_root / "docs/steps/step6/html-guide.md").read_text(encoding="utf-8")
        markdown = (project_root / "docs/steps/step4/markdown-guide.md").read_text(encoding="utf-8")
        images = (project_root / "docs/steps/step5/image-generation-guide.md").read_text(encoding="utf-8")
        wechat = (project_root / "docs/steps/step8/wechat-guide.md").read_text(encoding="utf-8")
        cleanup = (project_root / "docs/steps/step11/final-cleanup-guide.md").read_text(encoding="utf-8")
        readme = (project_root / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("60%", html)
        self.assertNotIn("40%", html)
        self.assertIn("3 个工具中等概率随机选一个主工具", html)
        self.assertIn("`gzh-design-skill`", html)
        self.assertIn("validate_workflow.py article", markdown)
        self.assertIn("validate_workflow.py skills", images)
        self.assertIn("validate_workflow.py approval", wechat)
        for filename in ("公众号草稿信息.txt", "workflow-state.json"):
            self.assertIn(filename, cleanup)
            self.assertIn(filename, readme)
        self.assertIn("三轮写作", readme)
        self.assertIn("确定性回归校验", readme)
        self.assertNotIn("五轮写作", readme)

    def test_step_five_keeps_skill_compatibility_check_as_common_gate(self):
        project_root = Path(__file__).resolve().parents[1]
        workflow = (project_root / "docs/workflow.md").read_text(encoding="utf-8")
        images = (project_root / "docs/steps/step5/image-generation-guide.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "python3 scripts/workflow_state.py start articles/<YYYYMMDD-HHMMSS> step_5\n"
            "python3 scripts/validate_workflow.py skills skills.lock.json",
            workflow,
        )
        self.assertNotIn(
            "# python3 scripts/validate_workflow.py skills skills.lock.json",
            workflow,
        )
        self.assertIn("两条路径共同要求", images)
        self.assertIn("skills.lock.json", images)
        self.assertNotIn("skills.lock.json`、`EXTEND.md`", images)

    def test_native_image_route_requires_a_callable_native_tool(self):
        project_root = Path(__file__).resolve().parents[1]
        workflow = (project_root / "docs/workflow.md").read_text(encoding="utf-8")
        images = (project_root / "docs/steps/step5/image-generation-guide.md").read_text(
            encoding="utf-8"
        )
        readme = (project_root / "README.md").read_text(encoding="utf-8")
        for text in (workflow, images, readme):
            self.assertIn("可调用", text)
        self.assertIn("仅列出 `imagegen` skill 不足以证明原生工具可用", images)


if __name__ == "__main__":
    unittest.main()
