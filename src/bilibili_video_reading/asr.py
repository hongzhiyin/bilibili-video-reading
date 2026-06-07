from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .common import run_command


MODEL_CANDIDATES = [
    "assets/models/whisper/ggml-small.bin",
    "assets/models/whisper/ggml-base.bin",
    "assets/models/whisper/ggml-medium.bin",
    "assets/models/whisper/ggml-large-v3-turbo.bin",
    "models/whisper/ggml-small.bin",
    "models/whisper/ggml-base.bin",
    "models/whisper/ggml-medium.bin",
    "models/whisper/ggml-large-v3-turbo.bin",
]


@dataclass(slots=True)
class WhisperCppOptions:
    audio: Path
    output_dir: Path
    model: str | None = None
    lang: str = "zh"
    stem: str | None = None
    gpu: bool = False
    threads: int = 4


def model_search_roots() -> list[Path]:
    roots = []
    asset_dir = os.environ.get("BVR_ASSET_DIR")
    if asset_dir:
        roots.append(Path(asset_dir).expanduser())
    roots.extend(
        [
            Path.cwd(),
            Path.home() / ".codex" / "skills" / "bilibili-video-reading",
        ]
    )
    return roots


def find_model(explicit: str | None = None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        return path if path.exists() else None
    for env_name in ("WHISPER_CPP_MODEL", "BVR_WHISPER_MODEL"):
        if os.environ.get(env_name):
            path = Path(os.environ[env_name]).expanduser().resolve()
            if path.exists():
                return path
    for root in model_search_roots():
        for rel in MODEL_CANDIDATES:
            path = root / rel
            if path.exists():
                return path.resolve()
    return None


def transcribe_whisper_cpp(options: WhisperCppOptions) -> tuple[dict, int]:
    ffmpeg = shutil.which("ffmpeg")
    whisper_cli = shutil.which("whisper-cli")
    model = find_model(options.model)
    audio_path = options.audio.expanduser().resolve()
    output_dir = options.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = options.stem or audio_path.stem

    diagnostics = {
        "audio": str(audio_path),
        "output_dir": str(output_dir),
        "stem": stem,
        "ffmpeg": ffmpeg,
        "whisper_cli": whisper_cli,
        "model": str(model) if model else None,
        "lang": options.lang,
    }

    if not audio_path.exists():
        diagnostics["status"] = "missing_audio"
        return diagnostics, 2
    if not ffmpeg:
        diagnostics["status"] = "missing_ffmpeg"
        return diagnostics, 2
    if not whisper_cli:
        diagnostics["status"] = "missing_whisper_cli"
        return diagnostics, 2
    if not model:
        diagnostics["status"] = "missing_whisper_model"
        diagnostics["manual_next_step"] = (
            "Set WHISPER_CPP_MODEL or BVR_WHISPER_MODEL to a GGML model path, place a model under "
            "an external models/whisper directory, or keep using the installed skill asset directory."
        )
        return diagnostics, 2

    try:
        wav_path = output_dir / f"{stem}.wav"
        run_command([ffmpeg, "-y", "-i", str(audio_path), "-ar", "16000", "-ac", "1", str(wav_path)])
        output_stem = output_dir / stem
        cmd = [
            whisper_cli,
            "-m",
            str(model),
            "-l",
            options.lang,
            "-t",
            str(options.threads),
            "-osrt",
            "-otxt",
            "-of",
            str(output_stem),
            str(wav_path),
        ]
        if not options.gpu:
            cmd.insert(1, "-ng")
        completed = run_command(cmd)
    except RuntimeError as exc:
        diagnostics["status"] = "command_failed"
        try:
            diagnostics["error"] = json.loads(str(exc))
        except json.JSONDecodeError:
            diagnostics["error"] = str(exc)
        return diagnostics, 3

    diagnostics.update(
        {
            "status": "ok",
            "wav": str(wav_path),
            "txt": str(output_stem.with_suffix(".txt")),
            "srt": str(output_stem.with_suffix(".srt")),
            "whisper_stdout_tail": completed.stdout[-4000:],
            "whisper_stderr_tail": completed.stderr[-4000:],
        }
    )
    return diagnostics, 0
