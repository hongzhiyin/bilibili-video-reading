from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError

from .bilibili import (
    choose_subtitle,
    normalize_subtitle_url,
    page_label,
    page_stem,
    parse_binary_subtitle_index,
    public_player_subtitles,
    resolve_video,
    subtitle_index_url,
    wbi_player_subtitles,
)
from .common import extract_bvid
from .net import fetch, redact_for_output, subtitle_endpoint_diagnostics


@dataclass(slots=True)
class SubtitleExportOptions:
    source: str | None
    output_dir: Path
    aid: int | None = None
    cid: int | None = None
    page: int = 1
    all_pages: bool = False
    lang: str = "zh"
    stem: str | None = None
    subtitle_index_url: str | None = None
    subtitle_url: str | None = None
    proxy: str | None = None
    save_full_urls: bool = False


def load_json_file(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def timestamp_srt(seconds: float | int | str | None) -> str:
    ms = round(float(seconds or 0) * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def timestamp_short(seconds: float | int | str | None) -> str:
    total = int(float(seconds or 0))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:02}:{minutes:02}:{secs:02}"
    return f"{minutes:02}:{secs:02}"


def convert_subtitle_json(json_path: str | Path, out_dir: str | Path, stem: str) -> dict:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    data = load_json_file(json_path)
    body = data.get("body") or []
    srt_parts = []
    transcript_lines = []
    plain_lines = []
    segment_number = 1
    for item in body:
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        start = item.get("from", 0)
        end = item.get("to", start)
        srt_parts.append(f"{segment_number}\n{timestamp_srt(start)} --> {timestamp_srt(end)}\n{content}\n")
        transcript_lines.append(f"[{timestamp_short(start)}] {content}")
        plain_lines.append(content)
        segment_number += 1

    srt_path = out_path / f"{stem}.srt"
    transcript_path = out_path / f"{stem}_transcript.txt"
    srt_path.write_text("\n".join(srt_parts), encoding="utf-8")
    transcript_path.write_text(
        "\n".join(transcript_lines) + "\n\n--- 连续文本 ---\n" + "\n".join(plain_lines) + "\n",
        encoding="utf-8",
    )
    return {"segments": segment_number - 1, "srt": str(srt_path), "transcript": str(transcript_path)}


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def save_subtitle_url_listing(
    out_dir: Path,
    stem_base: str,
    subtitle_items: list[dict],
    options: SubtitleExportOptions,
    diagnostics: dict,
) -> None:
    urls_path = out_dir / f"{stem_base}_subtitle_urls.json"
    save_json(urls_path, redact_for_output(subtitle_items))
    diagnostics["subtitle_urls_json"] = str(urls_path)
    if options.save_full_urls:
        full_urls_path = out_dir / f"{stem_base}_subtitle_urls_full.json"
        save_json(full_urls_path, subtitle_items)
        diagnostics["subtitle_urls_full_json"] = str(full_urls_path)


def export_page(
    options: SubtitleExportOptions,
    *,
    bvid: str | None,
    aid: int | None,
    cid: int | None,
    stem_base: str,
    page_info: dict | None = None,
    include_page: bool = False,
) -> tuple[dict, int]:
    page_stem_base = page_stem(stem_base, page_info, include_page=include_page)
    diagnostics = {
        "bvid": bvid,
        "time": int(time.time()),
        "aid": aid,
        "cid": cid,
        "lang": options.lang,
        "content_source_order": ["public_subtitle", "wbi_subtitle", "subtitle_index", "logged_in_chrome", "asr_ocr"],
    }
    if page_info:
        diagnostics["page"] = page_info.get("page")
        diagnostics["page_label"] = page_label(page_info)

    subtitle_items: list[dict] = []
    if options.subtitle_url:
        subtitle_items = [
            {
                "code": options.lang,
                "label": options.lang,
                "url": normalize_subtitle_url(options.subtitle_url),
            }
        ]
        diagnostics["subtitle_url_source"] = "direct"
    else:
        if bvid and cid:
            try:
                subtitle_items, player_data = public_player_subtitles(bvid, cid, proxy=options.proxy)
                diagnostics["need_login_subtitle"] = (player_data.get("data") or {}).get("need_login_subtitle")
                diagnostics["player_v2_subtitle_count"] = len(subtitle_items)
            except Exception as exc:
                diagnostics["player_v2_error"] = str(exc)

        if not subtitle_items and bvid and cid:
            try:
                subtitle_items, player_wbi_data = wbi_player_subtitles(bvid, aid, cid, proxy=options.proxy)
                diagnostics["player_wbi_v2_subtitle_count"] = len(subtitle_items)
                if (player_wbi_data.get("data") or {}).get("v_voucher"):
                    diagnostics["player_wbi_v2_voucher"] = True
            except Exception as exc:
                diagnostics["player_wbi_v2_error"] = str(exc)

        if not subtitle_items:
            if options.subtitle_index_url:
                index_url = options.subtitle_index_url
            elif aid and cid:
                index_url = subtitle_index_url(aid, cid)
            else:
                diagnostics["status"] = "missing_subtitle_index_inputs"
                diagnostics["manual_next_step"] = (
                    "Pass a BVID or --aid/--cid, or open the video in logged-in Chrome so the "
                    "page can trigger a short-lived subtitle JSON URL."
                )
                save_subtitle_url_listing(options.output_dir, page_stem_base, subtitle_items, options, diagnostics)
                return diagnostics, 2

            diagnostics["subtitle_index_url"] = index_url
            try:
                raw = fetch(index_url, binary=True, proxy=options.proxy)
            except Exception as exc:
                diagnostics["status"] = "subtitle_index_fetch_failed"
                diagnostics["error"] = str(exc)
                diagnostics["manual_next_step"] = (
                    "Use logged-in Chrome automatically if available: open the video, trigger/select "
                    "subtitles, collect the observed aisubtitle.hdslb.com URL, then rerun with "
                    "--subtitle-url. If no subtitle exists, fall back to ASR/OCR."
                )
                save_subtitle_url_listing(options.output_dir, page_stem_base, subtitle_items, options, diagnostics)
                return diagnostics, 3
            raw_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8", errors="replace")
            raw_path = options.output_dir / f"{page_stem_base}_subtitle_view.bin"
            raw_path.write_bytes(raw_bytes)
            diagnostics["subtitle_index_bin"] = str(raw_path)
            diagnostics["subtitle_index_bytes"] = len(raw_bytes)
            subtitle_items = parse_binary_subtitle_index(raw_bytes)

    diagnostics["subtitle_count"] = len(subtitle_items)
    save_subtitle_url_listing(options.output_dir, page_stem_base, subtitle_items, options, diagnostics)

    chosen = choose_subtitle(subtitle_items, options.lang)
    if not chosen:
        diagnostics["status"] = "no_subtitle_url_found"
        diagnostics["manual_next_step"] = (
            "If the user likely has Bilibili logged in, use Chrome as the next automatic fallback. "
            "Open the video, select a subtitle language if available, and pass the observed "
            "aisubtitle.hdslb.com URL with --subtitle-url. If the page has no subtitles, use ASR/OCR."
        )
        return diagnostics, 2

    json_path = options.output_dir / f"{page_stem_base}_{options.lang}.json"
    diagnostics["chosen"] = redact_for_output(chosen)
    try:
        sub_text = fetch(
            chosen["url"],
            referer=f"https://www.bilibili.com/video/{bvid}/" if bvid else "https://www.bilibili.com/",
            proxy=options.proxy,
        )
        if not isinstance(sub_text, str):
            sub_text = sub_text.decode("utf-8", errors="replace")
        json.loads(sub_text)
        json_path.write_text(sub_text, encoding="utf-8")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        endpoint = subtitle_endpoint_diagnostics(chosen["url"])
        error_text = str(exc)
        diagnostics["status"] = "subtitle_download_failed"
        diagnostics["error"] = error_text
        diagnostics["error_type"] = exc.__class__.__name__
        diagnostics["subtitle_endpoint"] = endpoint
        host = endpoint.get("host")
        resolution = endpoint.get("host_resolution") or {}
        if host == "subtitle.bilibili.com" and resolution.get("fake_ip"):
            diagnostics["status"] = "subtitle_download_failed_fake_ip"
            diagnostics["manual_next_step"] = (
                "Do not keep retrying the same subtitle.bilibili.com URL: this environment resolves "
                "the host to a 198.18.* fake IP, so direct TLS download is expected to fail. Use "
                "logged-in Chrome to trigger and collect a final aisubtitle.hdslb.com JSON URL, use "
                "the DevTools Response-only fallback, or switch to ASR/OCR."
            )
        elif host == "subtitle.bilibili.com" and ("SSL" in error_text or "EOF" in error_text):
            diagnostics["manual_next_step"] = (
                "Avoid repeated direct retries of the same subtitle.bilibili.com short URL after TLS "
                "EOF/SSL failure. Prefer a Chrome-triggered aisubtitle.hdslb.com JSON URL. If that "
                "cannot be collected, use the DevTools Response-only fallback or ASR/OCR."
            )
        else:
            diagnostics["manual_next_step"] = (
                "Refresh/trigger subtitles in logged-in Chrome, select the desired language, collect the "
                "observed aisubtitle.hdslb.com URL, then rerun with --subtitle-url. If the URL is only "
                "reachable through a local proxy, pass --proxy such as http://127.0.0.1:7897. As a last "
                "resort, copy only the Response body from DevTools and rerun with --convert-json."
            )
        diagnostics["target_json_path"] = str(json_path)
        return diagnostics, 3

    converted = convert_subtitle_json(json_path, options.output_dir, f"{page_stem_base}_{options.lang}")
    diagnostics["status"] = "ok"
    diagnostics["raw_json"] = str(json_path)
    diagnostics.update(converted)
    return diagnostics, 0


def export_subtitles(options: SubtitleExportOptions) -> tuple[dict, int]:
    if options.subtitle_url and options.all_pages:
        return {"status": "invalid_arguments", "error": "--subtitle-url can only be used for one page at a time"}, 2
    if options.subtitle_index_url and options.all_pages:
        return {"status": "invalid_arguments", "error": "--subtitle-index-url can only be used for one page at a time"}, 2

    bvid = extract_bvid(options.source or "")
    if not bvid and not options.subtitle_index_url and not options.subtitle_url:
        return {
            "status": "invalid_arguments",
            "error": "Provide a Bilibili URL/BVID, --subtitle-index-url, or --subtitle-url",
        }, 2

    info = None
    if bvid and not options.subtitle_url and not (options.aid and options.cid):
        try:
            info = resolve_video(bvid, proxy=options.proxy)
        except Exception as exc:
            return {
                "bvid": bvid,
                "time": int(time.time()),
                "status": "video_resolve_failed",
                "error": str(exc),
                "manual_next_step": (
                    "Network resolution failed before aid/cid could be fetched. If running in a sandbox, "
                    "rerun with network approval, try --proxy, pass --aid and --cid, or use logged-in "
                    "Chrome to trigger a subtitle JSON URL."
                ),
            }, 3

    aid = options.aid or (info and info["aid"])
    stem_base = options.stem or f"bilibili_{bvid or 'subtitle'}"

    if options.all_pages:
        if not info:
            return {"status": "invalid_arguments", "error": "--all-pages requires a resolvable BVID"}, 2
        page_results = []
        worst_status = 0
        for page_info in info["pages"]:
            diagnostics, status = export_page(
                options,
                bvid=bvid,
                aid=aid,
                cid=page_info["cid"],
                stem_base=stem_base,
                page_info=page_info,
                include_page=True,
            )
            worst_status = max(worst_status, status)
            page_results.append(diagnostics)
        return {
            "bvid": bvid,
            "aid": aid,
            "title": info.get("title") if info else None,
            "status": "ok" if worst_status == 0 else "partial_or_failed",
            "pages": page_results,
        }, worst_status

    page_info = None
    cid = options.cid
    include_page = False
    if info and not cid:
        if options.page < 1 or options.page > len(info["pages"]):
            return {"status": "invalid_arguments", "error": f"--page must be between 1 and {len(info['pages'])}"}, 2
        page_info = info["pages"][options.page - 1]
        cid = page_info["cid"]
        include_page = options.page != 1
    elif info and cid:
        for candidate in info["pages"]:
            if candidate.get("cid") == cid:
                page_info = candidate
                include_page = (candidate.get("page") or 1) != 1
                break

    diagnostics, status = export_page(
        options,
        bvid=bvid,
        aid=aid,
        cid=cid,
        stem_base=stem_base,
        page_info=page_info,
        include_page=include_page,
    )
    if info and info.get("title"):
        diagnostics["title"] = info["title"]
    return diagnostics, status
