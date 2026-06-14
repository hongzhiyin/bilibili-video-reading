---
name: bilibili-video-reading
description: Read, summarize, analyze, translate, or archive Bilibili video content by turning Bilibili video links into AI-readable transcript, ASR, OCR, or visual artifacts. Use for requests like "read this Bilibili video", "summarize this B站 link", "analyze this BV video", or "extract subtitles"; subtitles are preferred, with logged-in Chrome triggering, ASR, and visual/OCR fallback when needed.
metadata:
  requires:
    bins: ["bvr"]
  cliHelp: "bvr --help"
---

# Bilibili Video Reading

## Goal

Read the content of a Bilibili video and produce useful AI-readable evidence:

- Raw subtitle JSON: `<stem>_<lang>.json`
- SRT subtitle file: `<stem>_<lang>.srt`
- Timestamped transcript: `<stem>_transcript.txt`
- ASR transcript when subtitles are unavailable: `<stem>_asr.txt` and `<stem>_asr.srt`
- Visual fallback artifacts: `frames/`, `frames_index.csv`, `contact_sheet.jpg`, and `<stem>_visual_notes.md`
- Run manifest: `manifest.json`

Default `stem` is `bilibili_<BVID>`, default language is `zh`. If the user asked for a summary, analysis, translation, or answer about the video, use the transcript/artifacts to answer the task instead of stopping at file export.

## CLI

Run deterministic helper commands with:

```bash
bvr <command>
```

If `bvr` is not on PATH, try the installed skill-local wrapper when this skill
directory is visible:

```bash
bin/bvr <command>
```

If neither command works but `BVR_PROJECT_DIR` points to a source checkout or
native release, use:

```bash
PYTHONPATH="$BVR_PROJECT_DIR/src" python3 -m bilibili_video_reading.cli <command>
```

If none of these works, ask the user to install or update the native release:

```bash
curl -fsSL https://github.com/hongzhiyin/bilibili-video-reading/releases/latest/download/install_remote.sh | sh
```

The installed skill delegates deterministic work to the current `bvr` CLI.

Unless the user asks to save artifacts elsewhere, put run artifacts under:

```text
./bilibili-video-reading-tmp/<BVID>/
```

## Safety Rules

- Do not read, export, copy, print, or ask for browser cookies.
- Do not inspect browser local storage, profile files, saved passwords, or session stores.
- Do not use `Copy as cURL` from DevTools, because it may include cookies.
- Prefer public APIs, WBI-signed public requests, signed short-lived subtitle URLs, and browser UI-triggered page resources.
- If Bilibili is not logged in, ask the user to log in in Chrome. The user should handle passwords, QR scans, 2FA, SMS codes, and CAPTCHAs directly in the browser.
- If a login wall remains, ask the user to log in or to copy only the `Response` body of the subtitle JSON request.
- Do not copy Whisper model binaries into the project source. Use `WHISPER_CPP_MODEL`, `BVR_WHISPER_MODEL`, `BVR_ASSET_DIR`, or installed skill assets.

## Default Workflow

When the user asks to read a Bilibili video, do not require them to say "use my logged-in Chrome." Assume their normal browser may already have login state and use it only when public subtitle retrieval fails.

If another agent or project reports a brittle Bilibili failure, collect a single structured report first:

```bash
bvr diagnose "https://www.bilibili.com/video/BV..." --output-dir ./bilibili-video-reading-tmp/BV...
```

Use `--try-media` only when it is acceptable to test `yt-dlp` audio fallback. The diagnostic report merges DNS, tool capability, video resolution, subtitle index/body status, and media failure classification without reading browser cookies.

1. Run subtitle export first:

```bash
bvr subtitles export "https://www.bilibili.com/video/BV..." --output-dir ./bilibili-video-reading-tmp/BV...
```

The CLI resolves video metadata, checks public subtitle data, tries WBI-signed subtitle data, parses `x/v2/subtitle/web/view`, downloads the chosen subtitle URL, writes JSON/SRT/transcript files, redacts short-lived authorization parameters, and writes `manifest.json`.

2. If the CLI status is `ok`, read the generated transcript and complete the user's content task.

3. If the CLI reports `need_login_subtitle`, `no_subtitle_url_found`, `subtitle_download_failed`, `subtitle_download_failed_fake_ip`, `diagnostic_state=subtitle_index_ok_body_blocked`, or an empty subtitle list, use logged-in Chrome automatically:

- Use the `chrome:control-chrome` skill.
- Open or claim the Bilibili video page.
- Verify from the visible page whether the user is logged in. Do not inspect cookies or storage.
- If logged out, ask the user to log in in Chrome and then continue.
- Play/seek enough for player controls to load.
- Open the subtitle menu and select the desired language, usually `中文`.
- Verify subtitles visibly appear when possible.
- Collect the page-triggered final subtitle JSON URL, preferring `https://aisubtitle.hdslb.com/bfs/ai_subtitle/prod/...?...auth_key=...`.

Then rerun:

```bash
bvr subtitles export "BV..." --subtitle-url "<observed aisubtitle URL>" --output-dir ./bilibili-video-reading-tmp/BV...
```

4. If Chrome shows subtitles but browser automation cannot collect the URL, use the DevTools Response-only fallback in `references/manual-devtools-fallback.md`, then run:

```bash
bvr subtitles convert <stem>_<lang>.json --output-dir ./bilibili-video-reading-tmp/BV...
```

5. If no subtitles exist, switch to ASR/OCR/visual fallback. Read `references/asr-ocr-fallback.md` only at that point.

For speech-heavy videos, use public audio download plus local ASR when available:

```bash
bvr media download "https://www.bilibili.com/video/BV..." --audio-only --output-dir ./bilibili-video-reading-tmp/BV...
bvr asr whisper-cpp ./bilibili-video-reading-tmp/BV.../<audio-file> --lang zh --stem bilibili_BV..._asr --output-dir ./bilibili-video-reading-tmp/BV...
```

For purely visual videos, music videos, MMD clips, gameplay clips without narration, or videos where ASR looks like unreliable song lyrics, generate visual artifacts:

```bash
bvr media sample "https://www.bilibili.com/video/BV..." --output-dir ./bilibili-video-reading-tmp/BV...
```

Then inspect `contact_sheet.jpg`, key frames in `frames/`, and `frames_index.csv`. Fill or use `<stem>_visual_notes.md` as the source for the answer, and clearly say the result is visual/OCR-derived rather than a full transcript.

## Multi-P Videos

For a specific page:

```bash
bvr subtitles export "BV..." --page 2 --output-dir ./bilibili-video-reading-tmp/BV...
```

For every page:

```bash
bvr subtitles export "BV..." --all-pages --output-dir ./bilibili-video-reading-tmp/BV...
```

If the user's request asks about the whole video/course/playlist-like Bilibili page, prefer `--all-pages` after checking that the page count is reasonable.

## Useful Commands

```bash
bvr parse "https://www.bilibili.com/video/BV..."
bvr subtitles export "BV..." --lang zh --output-dir ./bilibili-video-reading-tmp/BV...
bvr subtitles export "BV..." --aid <aid> --cid <cid> --output-dir ./bilibili-video-reading-tmp/BV...
bvr subtitles export "BV..." --subtitle-index-url "<observed web/view URL>" --output-dir ./bilibili-video-reading-tmp/BV...
bvr subtitles export "BV..." --proxy http://127.0.0.1:7897 --output-dir ./bilibili-video-reading-tmp/BV...
bvr diagnose "BV..." --try-media --output-dir ./bilibili-video-reading-tmp/BV...
bvr tools doctor
```

Use `--save-full-urls` only when the full short-lived subtitle URLs are needed locally for debugging or reruns. Do not paste those URLs into public places, and delete full-URL debug files after use.

## Common Findings

- `need_login_subtitle: true` with empty subtitles means public `x/player/v2` is not enough; logged-in Chrome is the next normal step.
- Bilibili may expose language choices only after the video player has loaded and the subtitle menu has been opened.
- `x/v2/subtitle/web/view` may return a binary/protobuf-like payload containing language codes such as `ai-zh`, `ai-en`, and `subtitle.bilibili.com` URLs.
- After selecting a language in Chrome, the player may request a more directly downloadable `aisubtitle.hdslb.com/bfs/ai_subtitle/prod/...` URL. Prefer that final JSON URL over `subtitle.bilibili.com`.
- `subtitle.bilibili.com` and `aisubtitle.hdslb.com` URLs are short-lived because they contain `auth_key`; if download fails due to expiry, refresh the page or re-run the Chrome trigger.
- If `subtitle.bilibili.com` resolves to a fake IP such as `198.18.x.x` or TLS fails, prefer collecting the final `aisubtitle.hdslb.com` URL. Try a local proxy only once; if CONNECT succeeds but TLS still fails, move on to Response-only fallback or ASR/OCR.
- `diagnostic_state=subtitle_index_ok_body_blocked` means the subtitle index was reachable and yielded candidates, but the direct subtitle JSON body fetch was blocked. Do not repeat the same direct URL; move to Chrome-triggered `aisubtitle.hdslb.com`, Response-only fallback, or ASR/OCR.
- If `yt-dlp` returns HTTP 412, retry once with the CLI's Chrome-like User-Agent and referer defaults; do not spend turns retrying the same bare command.
- If Chrome auto-plays to the next collection item, navigate back to the original BVID before sampling frames or reading page text.
- If Whisper output looks like garbled lyrics or background music, do not treat it as a reliable transcript. Use visual notes as the primary source and mention the limitation.
