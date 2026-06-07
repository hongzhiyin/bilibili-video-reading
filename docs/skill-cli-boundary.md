# Skill and CLI Boundary

This project is the deterministic CLI side of the Bilibili video-reading workflow. The installed Codex skill should stay concise and use the CLI output, especially `manifest.json`, as evidence for the next decision.

## Project Shape

```text
bilibili-video-reading/
├── pyproject.toml
├── skill/
│   ├── SKILL.md       # installed skill source; decision layer
│   ├── agents/
│   └── references/
├── src/bilibili_video_reading/
│   ├── cli.py          # argparse entrypoint; console script: bvr
│   ├── bilibili.py     # BVID/video metadata, WBI signing, subtitle index parsing
│   ├── subtitles.py    # subtitle export and JSON -> SRT/transcript conversion
│   ├── media.py        # public yt-dlp download, ffprobe, ffmpeg frames/contact sheet
│   ├── asr.py          # whisper.cpp invocation and external model discovery
│   ├── tools.py        # local capability checks
│   ├── net.py          # HTTP helpers and redaction
│   ├── manifest.py     # manifest.json writer
│   └── common.py       # shared parsing/path/process helpers
└── tests/
```

## CLI Responsibilities

- `bvr parse <source>`: extract BVID and canonical URL without network access.
- `bvr subtitles export <source>`: public subtitle lookup, WBI fallback, subtitle index parsing, direct subtitle URL download, SRT/transcript conversion.
- `bvr subtitles convert <json>`: convert manually copied subtitle JSON response bodies.
- `bvr media download <source>`: download public audio/video with `yt-dlp`.
- `bvr media sample <source>`: download or accept a local video, sample frames, write `frames_index.csv`, `contact_sheet.jpg`, and visual notes template.
- `bvr asr whisper-cpp <audio>`: convert audio to 16 kHz mono WAV and run local `whisper-cli`.
- `bvr tools check`: report external commands, Python modules, and model availability.
- `bvr tools doctor`: check CLI installation, skill sync status, external tools, and model portability.

## Skill Responsibilities

- Choose whether the user's task needs subtitles, ASR, sampled visuals, or a mixture.
- Use Chrome fallback when CLI diagnostics report `need_login_subtitle`, `no_subtitle_url_found`, `subtitle_download_failed`, or `subtitle_download_failed_fake_ip`.
- Avoid cookie extraction and browser profile inspection.
- Decide whether ASR output is trustworthy enough, especially for music/MMD/gameplay clips.
- Interpret transcripts, frames, OCR/vision notes, and limitations for the user.

## Manifest Contract

Most commands write `manifest.json` in the output directory unless `--no-manifest` is passed. The manifest is redacted and contains:

- `schema_version`
- `source`, `bvid`, `title` when known
- `runs[]` with command, status, status code, timestamp, and redacted result
- `artifacts[]` with important generated paths

The manifest is intentionally evidence-like. It records what happened; it does not encode agent policy.

## Asset Policy

This source tree must not depend on `/Users/chihoyo/Project/Idea` and must not contain Whisper model binaries. Model discovery checks:

- explicit `--model`
- `WHISPER_CPP_MODEL`
- `BVR_WHISPER_MODEL`
- `BVR_ASSET_DIR`
- current working directory external `models/whisper/...`
- installed skill assets under `~/.codex/skills/bilibili-video-reading/assets/models/whisper/...`

## Portability

The installed skill should call `bvr` rather than a hard-coded source checkout path. If `bvr` is unavailable, `BVR_PROJECT_DIR` may point to a checkout and the module form can be used:

```bash
PYTHONPATH="$BVR_PROJECT_DIR/src" python3 -m bilibili_video_reading.cli <command>
```

Use `docs/install.md` and `scripts/sync_skill.sh` when migrating to another machine.
