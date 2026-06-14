from __future__ import annotations

import importlib.util
import os
import filecmp
import shutil
import sys
from pathlib import Path

from .asr import MODEL_CANDIDATES, model_search_roots


MODULES = [
    "yt_dlp",
    "whisper",
    "faster_whisper",
    "mlx_whisper",
    "speech_recognition",
    "vosk",
    "torch",
    "transformers",
]

COMMANDS = [
    "yt-dlp",
    "ffmpeg",
    "ffprobe",
    "afconvert",
    "sips",
    "whisper",
    "whisper-cli",
    "mlx_whisper",
    "faster-whisper",
]


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def skill_source_dir() -> Path:
    return project_root() / "skill"


def installed_skill_dir() -> Path:
    return Path(os.environ.get("BVR_SKILL_DIR", codex_home() / "skills" / "bilibili-video-reading")).expanduser()


def compare_skill_files(source_dir: Path, target_dir: Path) -> dict:
    rel_paths = [
        Path("SKILL.md"),
        Path("agents/openai.yaml"),
        Path("references/asr-ocr-fallback.md"),
        Path("references/manual-devtools-fallback.md"),
    ]
    files = {}
    all_match = True
    for rel_path in rel_paths:
        source = source_dir / rel_path
        target = target_dir / rel_path
        source_exists = source.exists()
        target_exists = target.exists()
        matches = source_exists and target_exists and filecmp.cmp(source, target, shallow=False)
        files[str(rel_path)] = {
            "source_exists": source_exists,
            "installed_exists": target_exists,
            "matches": matches,
        }
        all_match = all_match and matches
    return {"files": files, "all_match": all_match}


def model_paths() -> list[str]:
    paths = []
    for env_name in ("WHISPER_CPP_MODEL", "BVR_WHISPER_MODEL"):
        if os.environ.get(env_name):
            candidate = os.path.expanduser(os.environ[env_name])
            if os.path.exists(candidate):
                paths.append(os.path.abspath(candidate))
    for root in model_search_roots():
        for rel in MODEL_CANDIDATES:
            candidate = root / rel
            if candidate.exists():
                paths.append(str(candidate.resolve()))
    return sorted(set(paths))


def check_tools() -> dict:
    modules = {name: module_available(name) for name in MODULES}
    commands = {name: shutil.which(name) for name in COMMANDS}
    models = model_paths()
    yt_dlp_available = modules["yt_dlp"] or bool(commands["yt-dlp"])
    whisper_available = any(
        [
            modules["whisper"],
            modules["faster_whisper"],
            modules["mlx_whisper"],
            modules["speech_recognition"],
            modules["vosk"],
            bool(commands["whisper"]),
            bool(commands["whisper-cli"]),
            bool(commands["mlx_whisper"]),
            bool(commands["faster-whisper"]),
        ]
    )
    capabilities = {
        "can_use_yt_dlp_module": modules["yt_dlp"],
        "can_download_public_media": yt_dlp_available,
        "can_convert_or_sample_media": bool(commands["ffmpeg"]),
        "can_sample_public_video_visuals": yt_dlp_available and bool(commands["ffmpeg"]),
        "can_sample_local_video_visuals": bool(commands["ffmpeg"]),
        "can_transcribe_locally": whisper_available and bool(models),
        "has_local_asr_command": whisper_available,
        "has_local_asr_model": bool(models),
        "can_use_macos_audio_tools": bool(commands["afconvert"]),
        "can_use_macos_image_tools": bool(commands["sips"]),
    }
    recommendations = []
    if not capabilities["can_download_public_media"]:
        recommendations.append("Install yt-dlp for public media fallback, for example: brew install yt-dlp.")
    if not capabilities["can_convert_or_sample_media"]:
        recommendations.append("Install ffmpeg for audio conversion, frame sampling, and visual contact sheets.")
    if whisper_available and not models:
        recommendations.append("Set WHISPER_CPP_MODEL or BVR_WHISPER_MODEL to a multilingual GGML Whisper model.")
    if not whisper_available:
        recommendations.append(
            "Install a local ASR tool such as whisper.cpp, mlx-whisper, faster-whisper, or openai-whisper."
        )
    return {
        "python": sys.executable,
        "modules": modules,
        "commands": commands,
        "model_search_roots": [str(path) for path in model_search_roots()],
        "models": models,
        "capabilities": capabilities,
        "recommendations": recommendations,
    }


def doctor() -> dict:
    result = check_tools()
    root = project_root()
    source_skill = skill_source_dir()
    target_skill = installed_skill_dir()
    bvr_command = shutil.which("bvr")
    project_venv_bvr = root / ".venv" / "bin" / "bvr"
    project_venv_bvr_exists = project_venv_bvr.exists()
    bvr_project_dir_env = os.environ.get("BVR_PROJECT_DIR")
    skill_compare = compare_skill_files(source_skill, target_skill) if source_skill.exists() else {
        "files": {},
        "all_match": False,
    }
    installed_scripts_dir = target_skill / "scripts"
    installed_bin = target_skill / "bin" / "bvr"
    installation = {
        "project_root": str(root),
        "bvr_project_dir_env": bvr_project_dir_env,
        "bvr_command": bvr_command,
        "project_venv_bvr": str(project_venv_bvr),
        "project_venv_bvr_exists": project_venv_bvr_exists,
        "cli_package_source_exists": (root / "pyproject.toml").exists(),
        "skill_source_dir": str(source_skill),
        "skill_source_exists": source_skill.exists(),
        "installed_skill_dir": str(target_skill),
        "installed_skill_exists": target_skill.exists(),
        "installed_skill_matches_source": skill_compare["all_match"],
        "installed_skill_file_compare": skill_compare["files"],
        "installed_legacy_scripts_dir_exists": installed_scripts_dir.exists(),
        "installed_skill_bin": str(installed_bin),
        "installed_skill_bin_exists": installed_bin.exists(),
    }
    recommendations = list(result.get("recommendations", []))
    if not bvr_command and not project_venv_bvr_exists:
        recommendations.append("Install the CLI in the project venv: ./scripts/install_cli.sh")
    elif not bvr_command and not bvr_project_dir_env:
        recommendations.append(
            f"Make the CLI discoverable: export PATH={project_venv_bvr.parent}:$PATH or export BVR_PROJECT_DIR={root}"
        )
    if not target_skill.exists():
        recommendations.append("Install the Codex skill: ./scripts/sync_skill.sh")
    elif not skill_compare["all_match"]:
        recommendations.append("Installed skill differs from repo source: ./scripts/sync_skill.sh")
    if installed_scripts_dir.exists():
        recommendations.append("Remove legacy installed scripts: ./scripts/sync_skill.sh")
    if target_skill.exists() and not installed_bin.exists():
        recommendations.append("Installed skill is missing bin/bvr: ./scripts/sync_skill.sh --force")
    result["installation"] = installation
    result["recommendations"] = recommendations
    result["status"] = "ok" if not recommendations else "needs_action"
    return result
