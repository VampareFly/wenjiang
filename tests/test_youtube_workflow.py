#!/usr/bin/env python3
"""Unit tests for YouTube discovery and fetch workflow."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import fetch_youtube
import discover_youtube
import link_registry
import workflow_state


class TestYouTubeWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        (self.project_root / "articles").mkdir()
        (self.project_root / "inputs").mkdir()
        (self.project_root / "links").mkdir()
        (self.project_root / "config").mkdir()

        # Initialize empty registry
        (self.project_root / "link-registry.json").write_text(
            json.dumps({"schema_version": 1, "updated_at": None, "entries": []}),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normalize_youtube_url(self):
        cases = [
            ("dQw4w9WgXcQ", ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ")),
            ("https://youtu.be/dQw4w9WgXcQ?si=abcdef", ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ")),
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s", ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ")),
            ("https://www.youtube.com/shorts/dQw4w9WgXcQ", ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ")),
        ]
        for inp, expected in cases:
            with self.subTest(inp=inp):
                norm, vid = fetch_youtube.normalize_youtube_url(inp)
                self.assertEqual((norm, vid), expected)

    def test_format_duration(self):
        self.assertEqual(fetch_youtube.format_duration(65), "01:05")
        self.assertEqual(fetch_youtube.format_duration(3665), "01:01:05")
        self.assertEqual(fetch_youtube.format_duration(0), "00:00")
        self.assertEqual(fetch_youtube.format_duration(None), "00:00")

    def test_create_article_task_and_state(self):
        # Create a mock srt file
        mock_srt = self.project_root / "inputs" / "mock.srt"
        mock_srt.write_text(
            "1\n00:00:01,000 --> 00:00:03,000\nHello world\n\n2\n00:00:04,000 --> 00:00:06,000\nThis is a test\n",
            encoding="utf-8",
        )

        meta = {
            "title": "Agentic AI in 2026",
            "uploader": "Tech Radar",
            "duration": 185,
            "upload_date": "20260819",
            "view_count": 10000,
            "description": "A comprehensive deep dive into agents.",
        }

        target_article = self.project_root / "articles" / "20260819-120000"
        article_path = fetch_youtube.create_article_task(
            project_root=self.project_root,
            url="https://youtu.be/dQw4w9WgXcQ",
            meta=meta,
            srt_path=mock_srt,
            target_dir=target_article,
            keep_inputs=True,
            skip_clean=False,
        )

        self.assertTrue(article_path.exists())
        self.assertTrue((article_path / "source.srt").exists())
        self.assertTrue((article_path / "source-link.txt").exists())
        self.assertTrue((article_path / "source-map.json").exists())
        self.assertTrue((article_path / "source.cleaned.txt").exists())
        self.assertTrue((article_path / "workflow-state.json").exists())

        # Verify cleaned subtitle content
        cleaned_content = (article_path / "source.cleaned.txt").read_text(encoding="utf-8")
        self.assertIn("Hello world", cleaned_content)
        self.assertIn("This is a test", cleaned_content)
        self.assertNotIn("-->", cleaned_content)

        # Verify workflow state is passed at step_1
        state_data = json.loads((article_path / "workflow-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state_data["steps"]["step_1"]["status"], "passed")
        self.assertEqual(state_data["steps"]["step_2"]["status"], "pending")

        # Verify source-map.json
        map_data = json.loads((article_path / "source-map.json").read_text(encoding="utf-8"))
        self.assertEqual(map_data["url_normalized"], "https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual(map_data["video_metadata"]["title"], "Agentic AI in 2026")

    def test_markdown_report_generation(self):
        candidates = [
            {
                "source_type": "channel",
                "category": "AI前沿",
                "channel_name": "AI Explained",
                "video_id": "vid12345678",
                "title": "Anthropic New Model Breakdown",
                "url": "https://youtu.be/vid12345678",
                "published_at": "2026-08-18",
                "views": 54000,
                "duration": 720,
            }
        ]
        out_md = self.project_root / "candidates.md"
        discover_youtube.generate_markdown_report(candidates, out_md)

        self.assertTrue(out_md.exists())
        text = out_md.read_text(encoding="utf-8")
        self.assertIn("Anthropic New Model Breakdown", text)
        self.assertIn("AI Explained", text)
        self.assertIn("54,000 次播放", text)
        self.assertIn("12:00", text)
        self.assertIn("https://youtu.be/vid12345678", text)


if __name__ == "__main__":
    unittest.main()
