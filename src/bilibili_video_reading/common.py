from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/148.0.0.0 Safari/537.36"
)
DEFAULT_REFERER = "https://www.bilibili.com/"
DEFAULT_MEDIA_FORMAT = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def extract_bvid(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\b(BV[0-9A-Za-z]+)\b", value)
    return match.group(1) if match else None


def normalize_bvid_or_value(value: str | None) -> str | None:
    if not value:
        return None
    return extract_bvid(value) or value


def safe_stem(value: str) -> str:
    stem = re.sub(r"[^0-9A-Za-z._-]+", "_", value).strip("._-")
    return stem or "bilibili_video"


def default_output_dir(source: str | None, stem: str | None = None) -> Path:
    folder = extract_bvid(source) if source else None
    folder = folder or stem or "bilibili_video"
    return Path("bilibili-video-reading-tmp") / safe_stem(folder)


def ensure_output_dir(path: str | Path | None, source: str | None = None, stem: str | None = None) -> Path:
    output_dir = Path(path).expanduser() if path else default_output_dir(source, stem)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            json.dumps(
                {
                    "command": cmd,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-4000:],
                    "stderr": completed.stderr[-4000:],
                },
                ensure_ascii=False,
            )
        )
    return completed


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))
