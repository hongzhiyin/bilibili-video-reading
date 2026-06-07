from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .net import redact_for_output


MANIFEST_NAME = "manifest.json"
ARTIFACT_KEYS = {
    "audio",
    "contact_sheet",
    "frames_dir",
    "frames_index",
    "info_json",
    "raw_json",
    "srt",
    "subtitle_index_bin",
    "subtitle_urls_json",
    "transcript",
    "txt",
    "video",
    "visual_notes_template",
    "wav",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_manifest(output_dir: Path) -> dict:
    path = output_dir / MANIFEST_NAME
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    now = utc_now()
    return {
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
        "runs": [],
        "artifacts": [],
    }


def collect_artifacts(value) -> list[dict]:
    artifacts = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ARTIFACT_KEYS and isinstance(item, str):
                artifacts.append({"kind": key, "path": item})
            else:
                artifacts.extend(collect_artifacts(item))
    elif isinstance(value, list):
        for item in value:
            artifacts.extend(collect_artifacts(item))
    return artifacts


def merge_artifacts(existing: list[dict], new_items: list[dict]) -> list[dict]:
    by_key = {(item.get("kind"), item.get("path")): item for item in existing}
    for item in new_items:
        by_key[(item.get("kind"), item.get("path"))] = item
    return sorted(by_key.values(), key=lambda item: (item.get("kind") or "", item.get("path") or ""))


def write_manifest(
    output_dir: Path,
    *,
    command: str,
    result: dict,
    status_code: int,
    source: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(output_dir)
    now = utc_now()
    manifest["updated_at"] = now
    if source:
        manifest["source"] = source
    if result.get("bvid"):
        manifest["bvid"] = result["bvid"]
    if result.get("title"):
        manifest["title"] = result["title"]
    redacted = redact_for_output(result)
    manifest["runs"].append(
        {
            "command": command,
            "status": redacted.get("status"),
            "status_code": status_code,
            "created_at": now,
            "result": redacted,
        }
    )
    manifest["artifacts"] = merge_artifacts(manifest.get("artifacts", []), collect_artifacts(redacted))
    path = output_dir / MANIFEST_NAME
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
