# Bilibili Video Reading

Small "skill + CLI" project for Bilibili video reading.

The CLI handles repeatable operations:

- Parse Bilibili URLs and BVIDs.
- Export subtitle JSON/SRT/transcripts.
- Download public audio/video with `yt-dlp`.
- Run local `whisper-cli` ASR.
- Sample frames with `ffmpeg` and create contact sheets.
- Write `manifest.json` artifacts for the skill to inspect.

The skill remains responsible for decisions and interpretation: when to trust subtitles, when to trigger logged-in Chrome, when ASR is reliable enough, and when the answer should be visual/OCR-derived.

The skill source lives in `skill/` and can be synced to:

```text
~/.codex/skills/bilibili-video-reading
```

```bash
./scripts/install.sh
./.venv/bin/bvr tools doctor
./.venv/bin/bvr subtitles export "https://www.bilibili.com/video/BV..."
./.venv/bin/bvr media sample "https://www.bilibili.com/video/BV..."
```

Whisper models are external assets. Set `WHISPER_CPP_MODEL` or `BVR_WHISPER_MODEL`, or keep a model in the installed skill asset directory. Do not commit model binaries to this source tree.

See [docs/install.md](docs/install.md) for portable setup and migration notes.
