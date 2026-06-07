from __future__ import annotations

import argparse
from pathlib import Path

from .asr import WhisperCppOptions, transcribe_whisper_cpp
from .common import (
    DEFAULT_MEDIA_FORMAT,
    DEFAULT_REFERER,
    DEFAULT_USER_AGENT,
    ensure_output_dir,
    extract_bvid,
    is_url,
    print_json,
    safe_stem,
)
from .manifest import write_manifest
from .media import MediaDownloadOptions, VisualSampleOptions, download_media, sample_visuals
from .net import redact_for_output
from .subtitles import SubtitleExportOptions, convert_subtitle_json, export_subtitles
from .tools import check_tools, doctor


def add_manifest_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-manifest", action="store_true", help="Do not write manifest.json in the output directory.")


def emit_result(
    result: dict,
    status: int,
    *,
    output_dir: Path | None = None,
    command: str,
    source: str | None = None,
    no_manifest: bool = False,
) -> int:
    if output_dir and not no_manifest:
        manifest_path = write_manifest(output_dir, command=command, result=result, status_code=status, source=source)
        result["manifest"] = str(manifest_path)
    print_json(redact_for_output(result))
    return status


def cmd_parse(args: argparse.Namespace) -> int:
    bvid = extract_bvid(args.source)
    result = {
        "source": args.source,
        "bvid": bvid,
        "canonical_url": f"https://www.bilibili.com/video/{bvid}/" if bvid else None,
        "status": "ok" if bvid else "no_bvid_found",
    }
    print_json(result)
    return 0 if bvid else 2


def cmd_subtitles_export(args: argparse.Namespace) -> int:
    stem = args.stem or (f"bilibili_{extract_bvid(args.source or '')}" if extract_bvid(args.source or "") else None)
    output_dir = ensure_output_dir(args.output_dir, args.source, stem)
    options = SubtitleExportOptions(
        source=args.source,
        output_dir=output_dir,
        aid=args.aid,
        cid=args.cid,
        page=args.page,
        all_pages=args.all_pages,
        lang=args.lang,
        stem=args.stem,
        subtitle_index_url=args.subtitle_index_url,
        subtitle_url=args.subtitle_url,
        proxy=args.proxy,
        save_full_urls=args.save_full_urls,
    )
    result, status = export_subtitles(options)
    return emit_result(
        result,
        status,
        output_dir=output_dir,
        command="subtitles export",
        source=args.source,
        no_manifest=args.no_manifest,
    )


def cmd_subtitles_convert(args: argparse.Namespace) -> int:
    json_path = Path(args.json).expanduser().resolve()
    output_dir = Path(args.output_dir or ".").expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.stem or json_path.stem
    result = convert_subtitle_json(json_path, output_dir, stem)
    result["status"] = "ok"
    result["raw_json"] = str(json_path)
    return emit_result(
        result,
        0,
        output_dir=output_dir,
        command="subtitles convert",
        source=str(json_path),
        no_manifest=args.no_manifest,
    )


def media_stem(source: str, explicit: str | None) -> str:
    if explicit:
        return safe_stem(explicit)
    source_path = Path(source).expanduser() if not is_url(source) else None
    return safe_stem(extract_bvid(source) or (source_path.stem if source_path else "bilibili_video"))


def cmd_media_download(args: argparse.Namespace) -> int:
    stem = media_stem(args.source, args.stem)
    output_dir = ensure_output_dir(args.output_dir, args.source, stem)
    result, status = download_media(
        MediaDownloadOptions(
            source=args.source,
            output_dir=output_dir,
            stem=stem,
            format=args.format,
            user_agent=args.user_agent,
            referer=args.referer,
            audio_only=args.audio_only,
        )
    )
    return emit_result(
        result,
        status,
        output_dir=output_dir,
        command="media download",
        source=args.source,
        no_manifest=args.no_manifest,
    )


def cmd_media_sample(args: argparse.Namespace) -> int:
    stem = media_stem(args.source, args.stem)
    output_dir = ensure_output_dir(args.output_dir, args.source, stem)
    result, status = sample_visuals(
        VisualSampleOptions(
            source=args.source,
            output_dir=output_dir,
            stem=stem,
            format=args.format,
            user_agent=args.user_agent,
            referer=args.referer,
            sample_every=args.sample_every,
            max_frames=args.max_frames,
            frame_width=args.frame_width,
            tile_cols=args.tile_cols,
        )
    )
    return emit_result(
        result,
        status,
        output_dir=output_dir,
        command="media sample",
        source=args.source,
        no_manifest=args.no_manifest,
    )


def cmd_asr_whisper_cpp(args: argparse.Namespace) -> int:
    audio_path = Path(args.audio).expanduser()
    output_dir = Path(args.output_dir or ".").expanduser().resolve()
    result, status = transcribe_whisper_cpp(
        WhisperCppOptions(
            audio=audio_path,
            output_dir=output_dir,
            model=args.model,
            lang=args.lang,
            stem=args.stem,
            gpu=args.gpu,
            threads=args.threads,
        )
    )
    return emit_result(
        result,
        status,
        output_dir=output_dir,
        command="asr whisper-cpp",
        source=str(audio_path),
        no_manifest=args.no_manifest,
    )


def cmd_tools_check(args: argparse.Namespace) -> int:
    result = check_tools()
    result["status"] = "ok"
    print_json(result)
    return 0


def cmd_tools_doctor(args: argparse.Namespace) -> int:
    result = doctor()
    print_json(result)
    return 0 if result["status"] == "ok" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bvr", description="Deterministic helpers for Bilibili video reading.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser("parse", help="Parse a Bilibili URL or BVID without network access.")
    parse_parser.add_argument("source")
    parse_parser.set_defaults(func=cmd_parse)

    subtitles_parser = subparsers.add_parser("subtitles", help="Subtitle export and conversion commands.")
    subtitles_sub = subtitles_parser.add_subparsers(dest="subcommand", required=True)

    export_parser = subtitles_sub.add_parser("export", help="Export Bilibili subtitles as JSON, SRT, and transcript.")
    export_parser.add_argument("source", nargs="?", help="Bilibili video URL or BVID")
    export_parser.add_argument("--aid", type=int)
    export_parser.add_argument("--cid", type=int)
    export_parser.add_argument("--page", type=int, default=1, help="1-based page number for multi-P videos.")
    export_parser.add_argument("--all-pages", action="store_true", help="Export subtitles for every page in a multi-P video.")
    export_parser.add_argument("--lang", default="zh")
    export_parser.add_argument("--output-dir")
    export_parser.add_argument("--stem")
    export_parser.add_argument("--subtitle-index-url")
    export_parser.add_argument("--subtitle-url", help="Final subtitle JSON URL observed in Chrome/page resources.")
    export_parser.add_argument("--proxy", help="Optional HTTP proxy URL, for example http://127.0.0.1:7897.")
    export_parser.add_argument("--save-full-urls", action="store_true", help="Also save unredacted subtitle URLs locally.")
    add_manifest_flag(export_parser)
    export_parser.set_defaults(func=cmd_subtitles_export)

    convert_parser = subtitles_sub.add_parser("convert", help="Convert a subtitle JSON Response body to SRT/transcript.")
    convert_parser.add_argument("json")
    convert_parser.add_argument("--output-dir", default=".")
    convert_parser.add_argument("--stem")
    add_manifest_flag(convert_parser)
    convert_parser.set_defaults(func=cmd_subtitles_convert)

    media_parser = subparsers.add_parser("media", help="Public media download and visual sampling commands.")
    media_sub = media_parser.add_subparsers(dest="subcommand", required=True)

    download_parser = media_sub.add_parser("download", help="Download public Bilibili audio/video with yt-dlp.")
    download_parser.add_argument("source")
    download_parser.add_argument("--output-dir")
    download_parser.add_argument("--stem")
    download_parser.add_argument("--format", default=DEFAULT_MEDIA_FORMAT)
    download_parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    download_parser.add_argument("--referer", default=DEFAULT_REFERER)
    download_parser.add_argument("--audio-only", action="store_true")
    add_manifest_flag(download_parser)
    download_parser.set_defaults(func=cmd_media_download)

    sample_parser = media_sub.add_parser("sample", help="Sample video frames and create a contact sheet.")
    sample_parser.add_argument("source", help="Bilibili URL or local video file path.")
    sample_parser.add_argument("--output-dir")
    sample_parser.add_argument("--stem")
    sample_parser.add_argument("--format", default=DEFAULT_MEDIA_FORMAT)
    sample_parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    sample_parser.add_argument("--referer", default=DEFAULT_REFERER)
    sample_parser.add_argument("--sample-every", type=float)
    sample_parser.add_argument("--max-frames", type=int, default=60)
    sample_parser.add_argument("--frame-width", type=int, default=480)
    sample_parser.add_argument("--tile-cols", type=int, default=5)
    add_manifest_flag(sample_parser)
    sample_parser.set_defaults(func=cmd_media_sample)

    asr_parser = subparsers.add_parser("asr", help="Local ASR commands.")
    asr_sub = asr_parser.add_subparsers(dest="subcommand", required=True)
    whisper_parser = asr_sub.add_parser("whisper-cpp", help="Transcribe audio with local whisper.cpp.")
    whisper_parser.add_argument("audio")
    whisper_parser.add_argument("--model", help="GGML Whisper model path.")
    whisper_parser.add_argument("--lang", default="zh", help="Spoken language, or auto.")
    whisper_parser.add_argument("--output-dir", default=".")
    whisper_parser.add_argument("--stem", help="Output stem without extension.")
    whisper_parser.add_argument("--gpu", action="store_true", help="Use GPU/Metal. Default is CPU.")
    whisper_parser.add_argument("--threads", type=int, default=4)
    add_manifest_flag(whisper_parser)
    whisper_parser.set_defaults(func=cmd_asr_whisper_cpp)

    tools_parser = subparsers.add_parser("tools", help="Tool and model availability commands.")
    tools_sub = tools_parser.add_subparsers(dest="subcommand", required=True)
    check_parser = tools_sub.add_parser("check", help="Report available download, ffmpeg, ASR, and model capabilities.")
    check_parser.set_defaults(func=cmd_tools_check)
    doctor_parser = tools_sub.add_parser("doctor", help="Check CLI, skill sync, external tools, and model portability.")
    doctor_parser.set_defaults(func=cmd_tools_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
