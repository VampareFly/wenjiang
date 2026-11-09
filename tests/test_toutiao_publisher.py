#!/usr/bin/env python3
"""Unit tests for Toutiao publisher script."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import post_to_toutiao


class TestToutiaoPublisher(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.article_dir = Path(self.temp_dir.name)

        # Create dummy Toutiao article
        (self.article_dir / "今日头条文章.md").write_text(
            "# 为什么一觉醒来浑身酸痛？斯坦福教授揭秘深睡眠真相：做对这3点很关键\n\n"
            "很多人以为只要睡够8小时就行，其实深度睡眠才是决定精力的关键。\n\n"
            "**第一点：睡前降低体温。**\n\n"
            "**第二点：拉开窗帘见晨光。**\n\n"
            "## 标题候选\n"
            "1. 标题候选一\n"
            "2. 标题候选二\n",
            encoding="utf-8",
        )

        # Create dummy weitoutiao
        (self.article_dir / "微头条.txt").write_text(
            "为什么你明明睡够了8小时，早上起来还是像没睡一样？\n\n"
            "其实决定疲劳恢复的不是睡眠时长，而是‘深度睡眠’的比例。\n"
            "分享 3 个零成本提升深睡眠的物理级小技巧：\n"
            "1. 睡前 90 分钟热水澡\n"
            "2. 早晨起床先见 10 分钟太阳\n"
            "3. 卧室温度控制在 19 度左右\n\n"
            "大家平时有早起昏沉的困扰吗？评论区聊聊👇\n"
            "#深度睡眠# #健康生活# #睡眠优化#\n",
            encoding="utf-8",
        )

        # Create dummy covers and images
        (self.article_dir / "toutiao-cover-1.png").write_bytes(b"dummy1")
        (self.article_dir / "toutiao-cover-2.png").write_bytes(b"dummy2")
        (self.article_dir / "toutiao-cover-3.png").write_bytes(b"dummy3")
        (self.article_dir / "配图1.png").write_bytes(b"dummy_img1")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_toutiao_article(self):
        result = post_to_toutiao.parse_toutiao_article(self.article_dir)
        self.assertTrue(len(result["title"]) <= 30)
        self.assertIn("斯坦福教授揭秘深睡眠真相", result["full_title"])
        self.assertTrue(result["has_three_covers"])
        self.assertEqual(len(result["covers"]), 3)
        self.assertEqual(len(result["images"]), 1)
        self.assertNotIn("## 标题候选", result["body"])

    def test_parse_weitoutiao(self):
        result = post_to_toutiao.parse_weitoutiao(self.article_dir)
        self.assertTrue(result["length"] > 100)
        self.assertIn("深度睡眠", result["tags"])
        self.assertIn("健康生活", result["tags"])
        self.assertEqual(len(result["attachments"]), 1)

    def test_write_draft_record(self):
        art_res = post_to_toutiao.parse_toutiao_article(self.article_dir)
        wt_res = post_to_toutiao.parse_weitoutiao(self.article_dir)
        rec_path = post_to_toutiao.write_draft_record(self.article_dir, art_res, wt_res)

        self.assertTrue(rec_path.is_file())
        text = rec_path.read_text(encoding="utf-8")
        self.assertIn("今日头条", text)
        self.assertIn("今日头条深度长文", text)
        self.assertIn("微头条短快讯", text)
        self.assertIn("已上传 (3张16:9写实封面)", text)

    def test_main_dry_run(self):
        ret = post_to_toutiao.main([str(self.article_dir), "--dry-run"])
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
