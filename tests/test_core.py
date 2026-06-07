from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bilibili_video_reading.bilibili import choose_subtitle, parse_binary_subtitle_index
from bilibili_video_reading.common import extract_bvid, safe_stem
from bilibili_video_reading.net import redact_url
from bilibili_video_reading.subtitles import convert_subtitle_json, timestamp_short, timestamp_srt


class CoreHelpersTest(unittest.TestCase):
    def test_extract_bvid_from_url_or_raw_value(self) -> None:
        self.assertEqual(extract_bvid("https://www.bilibili.com/video/BV1NyVr6hEsh/"), "BV1NyVr6hEsh")
        self.assertEqual(extract_bvid("BV1NyVr6hEsh"), "BV1NyVr6hEsh")
        self.assertIsNone(extract_bvid("https://example.com/nope"))

    def test_safe_stem(self) -> None:
        self.assertEqual(safe_stem("BV1NyVr6hEsh 中文 标题"), "BV1NyVr6hEsh")
        self.assertEqual(safe_stem("中文标题"), "bilibili_video")

    def test_redact_url_masks_short_lived_auth(self) -> None:
        url = "https://aisubtitle.hdslb.com/a.json?auth_key=123-secret&foo=bar&token=abc"
        redacted = redact_url(url)
        self.assertIn("auth_key=REDACTED", redacted)
        self.assertIn("token=REDACTED", redacted)
        self.assertIn("foo=bar", redacted)

    def test_subtitle_index_parsing_and_choice_prefers_ai_subtitle(self) -> None:
        blob = (
            b"prefix ai-zh data //subtitle.bilibili.com/path/a.json?auth_key=123-aabb-0-ccdd"
            b"\x00 prefix ai-zh data //aisubtitle.hdslb.com/bfs/a.json?auth_key=456-bbcc-0-ddee"
        )
        items = parse_binary_subtitle_index(blob)
        self.assertEqual(len(items), 2)
        chosen = choose_subtitle(items, "zh")
        self.assertIsNotNone(chosen)
        self.assertIn("aisubtitle.hdslb.com", chosen["url"])

    def test_timestamp_helpers(self) -> None:
        self.assertEqual(timestamp_srt(65.4321), "00:01:05,432")
        self.assertEqual(timestamp_short(65.4321), "01:05")

    def test_convert_subtitle_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            json_path = tmp_path / "sub.json"
            json_path.write_text(
                json.dumps(
                    {
                        "body": [
                            {"from": 0, "to": 1.5, "content": "hello"},
                            {"from": 2, "to": 3, "content": "world"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = convert_subtitle_json(json_path, tmp_path, "demo")
            self.assertEqual(result["segments"], 2)
            self.assertTrue((tmp_path / "demo.srt").exists())
            transcript = (tmp_path / "demo_transcript.txt").read_text(encoding="utf-8")
            self.assertIn("[00:00] hello", transcript)
            self.assertIn("连续文本", transcript)


if __name__ == "__main__":
    unittest.main()
