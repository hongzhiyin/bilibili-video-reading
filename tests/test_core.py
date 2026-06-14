from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from bilibili_video_reading import __version__
from bilibili_video_reading.bilibili import choose_subtitle, parse_binary_subtitle_index
from bilibili_video_reading.cli import main
from bilibili_video_reading.common import extract_bvid, safe_stem
from bilibili_video_reading.media import classify_yt_dlp_failure
from bilibili_video_reading.net import redact_url
from bilibili_video_reading.release import launcher_is_bvr_owned, plan_native_uninstall
from bilibili_video_reading.subtitles import convert_subtitle_json, timestamp_short, timestamp_srt


class CoreHelpersTest(unittest.TestCase):
    def test_cli_version_flag_prints_package_version(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as raised:
                main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), f"bvr {__version__}")

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

    def test_classify_ytdlp_http_412(self) -> None:
        result = classify_yt_dlp_failure(
            returncode=1,
            stdout="[BiliBili] Extracting formats",
            stderr="ERROR: HTTP Error 412: Precondition Failed",
        )
        self.assertEqual(result["status"], "download_failed_http_412")
        self.assertIn("likely_causes", result)
        self.assertIn("yt-dlp", result["manual_next_step"])

    def test_classify_ytdlp_dns_failure(self) -> None:
        result = classify_yt_dlp_failure(
            returncode=1,
            stdout="",
            stderr="<urlopen error [Errno 8] nodename nor servname provided, or not known>",
        )
        self.assertEqual(result["status"], "download_failed_dns")
        self.assertEqual(result["failure_stage"], "media_download")

    def test_launcher_ownership_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            launcher = Path(tmp) / "bvr"
            launcher.write_text(
                '#!/bin/sh\nBVR_PROJECT_DIR="/x" PYTHONPATH="/x/src" exec python3 -m bilibili_video_reading.cli "$@"\n',
                encoding="utf-8",
            )
            self.assertTrue(launcher_is_bvr_owned(launcher))

            other = Path(tmp) / "other"
            other.write_text("#!/bin/sh\necho nope\n", encoding="utf-8")
            self.assertFalse(launcher_is_bvr_owned(other))

    def test_uninstall_plan_skips_unmarked_skill_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install_root = root / "install"
            bin_dir = root / "bin"
            skill_dir = root / "codex" / "skills" / "bilibili-video-reading"
            install_root.mkdir()
            bin_dir.mkdir()
            skill_dir.mkdir(parents=True)
            actions = plan_native_uninstall(
                install_root,
                bin_dir,
                keep_skills=False,
                targets=(),
            )
            self.assertIn("remove", {item.action for item in actions})


if __name__ == "__main__":
    unittest.main()
