import json
import tempfile
import unittest
from pathlib import Path

from scripts import link_registry


class LinkRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        self.inputs = self.project / "inputs"
        self.links = self.project / "links"
        self.article = self.project / "articles" / "task-1"
        self.inputs.mkdir()
        self.links.mkdir()
        self.article.mkdir(parents=True)
        self.subtitle = self.inputs / "video.srt"
        self.link_file = self.links / "video.txt"
        self.subtitle.write_text("subtitle facts", encoding="utf-8")
        self.link_file.write_text(
            "https://Example.com/watch/?utm_source=x&v=2#part\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self):
        return link_registry.prepare_mapping(self.article, self.subtitle, self.link_file)

    def test_normalize_url_removes_tracking_fragment_and_trailing_slash(self):
        self.assertEqual(
            "https://example.com/watch?v=2",
            link_registry.normalize_url("https://Example.com/watch/?v=2&utm_source=x#part"),
        )

    def test_prepare_archives_pair_without_removing_inputs(self):
        payload = self.prepare()
        self.assertEqual("prepared", payload["status"])
        self.assertTrue((self.article / "source.srt").is_file())
        self.assertTrue((self.article / "source-link.txt").is_file())
        self.assertTrue((self.article / "source-map.json").is_file())
        self.assertTrue(self.subtitle.exists())
        self.assertTrue(self.link_file.exists())

    def test_prepare_allows_different_stems(self):
        other = self.links / "other.txt"
        other.write_text("https://example.com/other", encoding="utf-8")
        payload = link_registry.prepare_mapping(self.article, self.subtitle, other)
        self.assertEqual("prepared", payload["status"])

    def test_finalize_registers_url_and_clears_link(self):
        self.prepare()
        (self.article / "公众号草稿信息.txt").write_text(
            "草稿 media_id：draft-123\n标题：测试标题\n",
            encoding="utf-8",
        )
        result = link_registry.finalize_mapping(self.article)
        registry = json.loads((self.project / "link-registry.json").read_text(encoding="utf-8"))
        mapping = json.loads((self.article / "source-map.json").read_text(encoding="utf-8"))
        self.assertEqual({"subtitle": True, "link_cleared": True}, result["removed"])
        self.assertFalse(self.subtitle.exists())
        self.assertTrue(self.link_file.exists())
        self.assertEqual("", self.link_file.read_text(encoding="utf-8"))
        self.assertEqual("draft-123", registry["entries"][0]["media_id"])
        self.assertEqual("wechat_draft_created", mapping["status"])
        self.assertEqual(1, len(link_registry.find_url(self.project, "https://example.com/watch?v=2")))

    def test_finalize_refuses_changed_subtitle_before_writing_registry(self):
        self.prepare()
        self.subtitle.write_text("changed", encoding="utf-8")
        (self.article / "公众号草稿信息.txt").write_text(
            "草稿 media_id：draft-123\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "内容已变化"):
            link_registry.finalize_mapping(self.article)
        self.assertFalse((self.project / "link-registry.json").exists())
        self.assertTrue(self.subtitle.exists())
        self.assertTrue(self.link_file.exists())
        self.assertNotEqual("", self.link_file.read_text(encoding="utf-8"))

    def test_prepare_rejects_url_already_in_success_registry(self):
        registry = {
            "schema_version": 1,
            "updated_at": "2026-07-17T00:00:00+00:00",
            "entries": [{
                "url_normalized": "https://example.com/watch?v=2",
                "article_dir": "articles/old",
            }],
        }
        (self.project / "link-registry.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "已经成功处理"):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
