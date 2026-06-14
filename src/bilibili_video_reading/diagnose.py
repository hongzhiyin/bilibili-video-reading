from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from .bilibili import page_label, resolve_video
from .common import DEFAULT_MEDIA_FORMAT, DEFAULT_REFERER, DEFAULT_USER_AGENT, extract_bvid, safe_stem
from .media import MediaDownloadOptions, download_media
from .net import resolve_host_for_diagnostics
from .subtitles import SubtitleExportOptions, export_subtitles
from .tools import check_tools


DIAGNOSTIC_HOSTS = [
    "api.bilibili.com",
    "subtitle.bilibili.com",
    "aisubtitle.hdslb.com",
]


@dataclass(slots=True)
class DiagnoseOptions:
    source: str
    output_dir: Path
    lang: str = "zh"
    page: int = 1
    proxy: str | None = None
    try_media: bool = False
    save_full_urls: bool = False
    format: str = DEFAULT_MEDIA_FORMAT
    user_agent: str = DEFAULT_USER_AGENT
    referer: str = DEFAULT_REFERER


def dns_diagnostics(proxy: str | None = None) -> dict:
    result = {host: resolve_host_for_diagnostics(host) for host in DIAGNOSTIC_HOSTS}
    if proxy:
        result["_note"] = "Local DNS results may differ from the proxy's upstream resolution."
        result["_proxy"] = proxy
    return result


def selected_page(info: dict, page: int) -> dict | None:
    pages = info.get("pages") or []
    if page < 1 or page > len(pages):
        return None
    return pages[page - 1]


def summarize_video(info: dict, page: int) -> dict:
    pages = info.get("pages") or []
    chosen = selected_page(info, page)
    summary = {
        "status": "ok",
        "bvid": info.get("bvid"),
        "aid": info.get("aid"),
        "title": info.get("title"),
        "page_count": len(pages),
        "selected_page": page,
    }
    if chosen:
        summary["selected_page_label"] = page_label(chosen)
        summary["selected_cid"] = chosen.get("cid")
    return summary


def subtitle_diagnostic_state(subtitle_result: dict) -> str:
    return subtitle_result.get("diagnostic_state") or subtitle_result.get("status") or "unknown"


def media_diagnostic_state(media_result: dict | None) -> str | None:
    if not media_result:
        return None
    download = media_result.get("download") or {}
    return media_result.get("status") or download.get("status")


def diagnose(options: DiagnoseOptions) -> tuple[dict, int]:
    options.output_dir.mkdir(parents=True, exist_ok=True)
    bvid = extract_bvid(options.source)
    stem = safe_stem(bvid or "bilibili_video")
    result = {
        "source": options.source,
        "bvid": bvid,
        "time": int(time.time()),
        "output_dir": str(options.output_dir),
        "dns": dns_diagnostics(options.proxy),
        "tools": check_tools(),
        "content_source_order": ["subtitles", "logged_in_chrome", "media_asr", "visual_ocr"],
    }

    if not bvid:
        result["status"] = "no_bvid_found"
        result["manual_next_step"] = "Pass a Bilibili URL or BVID."
        return result, 2

    info = None
    aid = None
    cid = None
    try:
        info = resolve_video(options.source, proxy=options.proxy)
        result["video"] = summarize_video(info, options.page)
        aid = info.get("aid")
        page_info = selected_page(info, options.page)
        if page_info:
            cid = page_info.get("cid")
        else:
            result["video"]["status"] = "invalid_page"
            result["video"]["error"] = f"--page must be between 1 and {len(info.get('pages') or [])}"
    except Exception as exc:
        result["video"] = {
            "status": "video_resolve_failed",
            "error": str(exc),
            "manual_next_step": "If running in a sandbox, rerun with network approval, try --proxy, or pass aid/cid to subtitle export.",
        }

    subtitle_result, subtitle_status = export_subtitles(
        SubtitleExportOptions(
            source=options.source,
            output_dir=options.output_dir,
            aid=aid,
            cid=cid,
            page=options.page,
            lang=options.lang,
            stem=f"{stem}_diagnose",
            proxy=options.proxy,
            save_full_urls=options.save_full_urls,
        )
    )
    result["subtitles"] = subtitle_result
    result["subtitle_status_code"] = subtitle_status
    subtitle_state = subtitle_diagnostic_state(subtitle_result)
    result["subtitle_diagnostic_state"] = subtitle_state

    if subtitle_status == 0:
        result["status"] = "ok"
        result["transcript"] = subtitle_result.get("transcript")
        return result, 0

    if not options.try_media:
        result["media_fallback"] = {
            "status": "not_attempted",
            "manual_next_step": (
                "Rerun with --try-media to test the yt-dlp audio fallback and classify media download failures."
            ),
        }
        result["status"] = subtitle_state
        result["manual_next_step"] = subtitle_result.get("manual_next_step")
        return result, 3 if subtitle_status >= 3 else 2

    media_result, media_status = download_media(
        MediaDownloadOptions(
            source=options.source,
            output_dir=options.output_dir,
            stem=f"{stem}_diagnose_audio",
            format=options.format,
            user_agent=options.user_agent,
            referer=options.referer,
            audio_only=True,
        )
    )
    result["media_fallback"] = media_result
    result["media_status_code"] = media_status
    media_state = media_diagnostic_state(media_result)
    result["media_diagnostic_state"] = media_state

    if media_status == 0:
        result["status"] = "media_fallback_audio_downloaded"
        audio = media_result.get("audio")
        result["manual_next_step"] = (
            f"Run bvr asr whisper-cpp {audio} --lang {options.lang} --output-dir {options.output_dir}"
            if audio
            else "Run ASR on the downloaded audio."
        )
        return result, 0

    result["status"] = media_state or subtitle_state
    result["manual_next_step"] = media_result.get("manual_next_step") or subtitle_result.get("manual_next_step")
    return result, 3 if media_status >= 3 else 2
