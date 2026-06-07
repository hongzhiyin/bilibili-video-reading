from __future__ import annotations

import csv
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

from .common import (
    DEFAULT_MEDIA_FORMAT,
    DEFAULT_REFERER,
    DEFAULT_USER_AGENT,
    extract_bvid,
    is_url,
    run_command,
    safe_stem,
)


@dataclass(slots=True)
class MediaDownloadOptions:
    source: str
    output_dir: Path
    stem: str | None = None
    format: str = DEFAULT_MEDIA_FORMAT
    user_agent: str = DEFAULT_USER_AGENT
    referer: str = DEFAULT_REFERER
    audio_only: bool = False


@dataclass(slots=True)
class VisualSampleOptions:
    source: str
    output_dir: Path
    stem: str | None = None
    format: str = DEFAULT_MEDIA_FORMAT
    user_agent: str = DEFAULT_USER_AGENT
    referer: str = DEFAULT_REFERER
    sample_every: float | None = None
    max_frames: int = 60
    frame_width: int = 480
    tile_cols: int = 5


VIDEO_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
AUDIO_SUFFIXES = {".m4a", ".mp3", ".opus", ".ogg", ".wav", ".webm"}


def find_downloaded_media(output_dir: Path, stem: str, *, audio_only: bool = False) -> Path | None:
    suffixes = AUDIO_SUFFIXES if audio_only else VIDEO_SUFFIXES
    candidates = sorted(
        [
            path
            for path in output_dir.glob(f"{stem}.*")
            if path.suffix.lower() in suffixes and not path.name.endswith(".info.json")
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def download_public_media(options: MediaDownloadOptions) -> tuple[Path | None, dict]:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        return None, {
            "status": "missing_yt_dlp",
            "manual_next_step": "Install yt-dlp, for example: brew install yt-dlp.",
        }
    if not is_url(options.source):
        return None, {"status": "source_is_not_url", "manual_next_step": "Pass a public Bilibili URL."}

    stem = safe_stem(options.stem or extract_bvid(options.source) or "bilibili_video")
    fmt = "ba/bestaudio" if options.audio_only and options.format == DEFAULT_MEDIA_FORMAT else options.format
    cmd = [yt_dlp, "--user-agent", options.user_agent, "--referer", options.referer, "-f", fmt]
    if not options.audio_only:
        cmd.extend(["--merge-output-format", "mp4"])
    cmd.extend(
        [
            "--write-info-json",
            "--no-clean-info-json",
            "--output",
            str(options.output_dir / f"{stem}.%(ext)s"),
            options.source,
        ]
    )

    completed = run_command(cmd)
    media = find_downloaded_media(options.output_dir, stem, audio_only=options.audio_only)
    if not media:
        return None, {
            "status": "download_completed_but_media_not_found",
            "yt_dlp_stdout_tail": completed.stdout[-4000:],
            "yt_dlp_stderr_tail": completed.stderr[-4000:],
        }
    return media, {
        "status": "downloaded",
        "media": str(media),
        "audio_only": options.audio_only,
        "yt_dlp_stdout_tail": completed.stdout[-4000:],
        "yt_dlp_stderr_tail": completed.stderr[-4000:],
    }


def download_media(options: MediaDownloadOptions) -> tuple[dict, int]:
    options.output_dir.mkdir(parents=True, exist_ok=True)
    bvid = extract_bvid(options.source)
    stem = safe_stem(options.stem or bvid or "bilibili_video")
    diagnostics = {
        "source": options.source,
        "bvid": bvid,
        "output_dir": str(options.output_dir),
        "stem": stem,
        "audio_only": options.audio_only,
    }
    try:
        media_path, download_diag = download_public_media(
            MediaDownloadOptions(
                source=options.source,
                output_dir=options.output_dir,
                stem=stem,
                format=options.format,
                user_agent=options.user_agent,
                referer=options.referer,
                audio_only=options.audio_only,
            )
        )
    except RuntimeError as exc:
        diagnostics["status"] = "command_failed"
        try:
            diagnostics["error"] = json.loads(str(exc))
        except json.JSONDecodeError:
            diagnostics["error"] = str(exc)
        return diagnostics, 3
    diagnostics["download"] = download_diag
    if not media_path:
        diagnostics["status"] = download_diag.get("status", "download_failed")
        return diagnostics, 2
    diagnostics["status"] = "ok"
    if options.audio_only:
        diagnostics["audio"] = str(media_path)
    else:
        diagnostics["video"] = str(media_path)
    info_path, info = find_info_json(options.output_dir, stem)
    diagnostics["info_json"] = str(info_path) if info_path else None
    if info:
        diagnostics["title"] = info.get("title")
        diagnostics["uploader"] = info.get("uploader")
    return diagnostics, 0


def ffprobe_json(video_path: Path) -> dict | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    completed = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
    )
    return json.loads(completed.stdout)


def duration_from_probe(probe: dict | None) -> float | None:
    if not probe:
        return None
    value = (probe.get("format") or {}).get("duration")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def video_stream_from_probe(probe: dict | None) -> dict:
    if not probe:
        return {}
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    return {}


def auto_sample_every(duration: float | None) -> float:
    if duration is None:
        return 10.0
    if duration <= 30:
        return 1.0
    if duration <= 180:
        return 5.0
    if duration <= 900:
        return 10.0
    if duration <= 3600:
        return 30.0
    return 60.0


def bounded_sample_every(duration: float | None, sample_every: float, max_frames: int) -> float:
    if not duration or not max_frames:
        return sample_every
    expected = math.ceil(duration / sample_every) + 1
    if expected <= max_frames:
        return sample_every
    return max(sample_every, duration / max(max_frames - 1, 1))


def ffmpeg_fps_value(sample_every: float) -> str:
    if abs(sample_every - 1.0) < 0.0001:
        return "1"
    return f"1/{sample_every:.6g}"


def clear_old_frames(frames_dir: Path) -> None:
    for path in frames_dir.glob("frame_*.jpg"):
        path.unlink()


def sample_frames(video_path: Path, output_dir: Path, sample_every: float, frame_width: int) -> tuple[list[Path] | None, dict]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None, {
            "status": "missing_ffmpeg",
            "manual_next_step": "Install ffmpeg, for example: brew install ffmpeg.",
        }
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    clear_old_frames(frames_dir)
    fps = ffmpeg_fps_value(sample_every)
    vf = f"fps={fps},scale={frame_width}:-1"
    pattern = frames_dir / "frame_%03d.jpg"
    completed = run_command([ffmpeg, "-y", "-i", str(video_path), "-vf", vf, str(pattern)])
    frames = sorted(frames_dir.glob("frame_*.jpg"))
    return frames, {
        "status": "sampled",
        "frames_dir": str(frames_dir),
        "frame_count": len(frames),
        "sample_every_seconds": sample_every,
        "ffmpeg_stdout_tail": completed.stdout[-4000:],
        "ffmpeg_stderr_tail": completed.stderr[-4000:],
    }


def write_frame_index(output_dir: Path, frames: list[Path], sample_every: float, duration: float | None) -> Path:
    path = output_dir / "frames_index.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame", "approx_time_seconds", "approx_timestamp"])
        for index, frame in enumerate(frames):
            seconds = index * sample_every
            if duration is not None:
                seconds = min(seconds, duration)
            minutes = int(seconds // 60)
            secs = seconds - minutes * 60
            writer.writerow([str(frame.relative_to(output_dir)), f"{seconds:.3f}", f"{minutes:02d}:{secs:05.2f}"])
    return path


def make_contact_sheet(output_dir: Path, frames: list[Path], tile_cols: int) -> Path | None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not frames:
        return None
    rows = max(1, math.ceil(len(frames) / tile_cols))
    sheet = output_dir / "contact_sheet.jpg"
    pattern = output_dir / "frames" / "frame_%03d.jpg"
    vf = f"tile={tile_cols}x{rows}:padding=8:margin=8"
    run_command(
        [
            ffmpeg,
            "-y",
            "-framerate",
            "1",
            "-i",
            str(pattern),
            "-vf",
            vf,
            "-frames:v",
            "1",
            "-update",
            "1",
            str(sheet),
        ]
    )
    return sheet


def find_info_json(output_dir: Path, stem: str) -> tuple[Path | None, dict | None]:
    candidates = sorted(output_dir.glob(f"{stem}.info.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return None, None
    try:
        return candidates[0], json.loads(candidates[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return candidates[0], None


def write_notes_template(
    output_dir: Path,
    source: str,
    stem: str,
    info: dict | None,
    probe: dict | None,
    frames: list[Path],
    sample_every: float,
    contact_sheet: Path | None,
    index_path: Path,
) -> Path:
    video_stream = video_stream_from_probe(probe)
    duration = duration_from_probe(probe)
    path = output_dir / f"{stem}_visual_notes.md"
    title = (info or {}).get("title") or ""
    uploader = (info or {}).get("uploader") or ""
    lines = [
        f"# {stem} Visual Notes",
        "",
        f"Source: {source}",
    ]
    if title:
        lines.append(f"Title: {title}")
    if uploader:
        lines.append(f"Uploader: {uploader}")
    if duration is not None:
        lines.append(f"Duration: {duration:.3f}s")
    if video_stream:
        width = video_stream.get("width")
        height = video_stream.get("height")
        codec = video_stream.get("codec_name")
        if width and height:
            lines.append(f"Video: {width}x{height}" + (f", {codec}" if codec else ""))
    contact_sheet_ref = contact_sheet.relative_to(output_dir) if contact_sheet else ""
    lines.extend(
        [
            f"Sample every: {sample_every:.3f}s",
            f"Frame count: {len(frames)}",
            "",
            "## Sources To Inspect",
            "",
            f"- Contact sheet: `{contact_sheet_ref}`",
            f"- Frame index: `{index_path.relative_to(output_dir)}`",
            "- Frames: `frames/frame_*.jpg`",
            "",
            "## Visual Reading",
            "",
            "- Main subjects:",
            "- Setting/background:",
            "- Visible text or UI:",
            "- Actions and changes:",
            "- Likely intent or joke:",
            "",
            "## Approximate Timeline",
            "",
            "- 00:00-00:??:",
            "",
            "## Confidence Notes",
            "",
            "- Mark this as visual/OCR-derived if there is no reliable transcript.",
            "- Mention any missed details caused by sparse sampling, fast cuts, or unclear frames.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def sample_visuals(options: VisualSampleOptions) -> tuple[dict, int]:
    bvid = extract_bvid(options.source)
    source_path = Path(options.source).expanduser() if not is_url(options.source) else None
    stem = safe_stem(options.stem or bvid or (source_path.stem if source_path else "bilibili_video"))
    options.output_dir.mkdir(parents=True, exist_ok=True)
    diagnostics = {
        "source": options.source,
        "bvid": bvid,
        "output_dir": str(options.output_dir),
        "stem": stem,
        "mode": "url" if is_url(options.source) else "local_file",
    }

    try:
        if is_url(options.source):
            video_path, download_diag = download_public_media(
                MediaDownloadOptions(
                    source=options.source,
                    output_dir=options.output_dir,
                    stem=stem,
                    format=options.format,
                    user_agent=options.user_agent,
                    referer=options.referer,
                )
            )
            diagnostics["download"] = download_diag
            if not video_path:
                diagnostics["status"] = download_diag.get("status", "download_failed")
                return diagnostics, 2
        else:
            if not source_path or not source_path.exists():
                diagnostics["status"] = "missing_local_video"
                return diagnostics, 2
            video_path = source_path.resolve()
            diagnostics["video"] = str(video_path)

        probe = ffprobe_json(video_path)
        duration = duration_from_probe(probe)
        sample_every = options.sample_every or auto_sample_every(duration)
        sample_every = bounded_sample_every(duration, sample_every, options.max_frames)
        frames, sample_diag = sample_frames(video_path, options.output_dir, sample_every, options.frame_width)
        diagnostics["sample"] = sample_diag
        if frames is None:
            diagnostics["status"] = sample_diag.get("status", "sampling_failed")
            return diagnostics, 2

        index_path = write_frame_index(options.output_dir, frames, sample_every, duration)
        contact_sheet = make_contact_sheet(options.output_dir, frames, options.tile_cols)
        info_path, info = find_info_json(options.output_dir, stem)
        notes_path = write_notes_template(
            options.output_dir,
            options.source,
            stem,
            info,
            probe,
            frames,
            sample_every,
            contact_sheet,
            index_path,
        )

        diagnostics.update(
            {
                "status": "ok",
                "video": str(video_path),
                "duration_seconds": duration,
                "sample_every_seconds": sample_every,
                "frame_count": len(frames),
                "frames_dir": str(options.output_dir / "frames"),
                "frames_index": str(index_path),
                "contact_sheet": str(contact_sheet) if contact_sheet else None,
                "visual_notes_template": str(notes_path),
                "info_json": str(info_path) if info_path else None,
            }
        )
        if info:
            diagnostics["title"] = info.get("title")
            diagnostics["uploader"] = info.get("uploader")
        return diagnostics, 0
    except RuntimeError as exc:
        diagnostics["status"] = "command_failed"
        try:
            diagnostics["error"] = json.loads(str(exc))
        except json.JSONDecodeError:
            diagnostics["error"] = str(exc)
        return diagnostics, 3
