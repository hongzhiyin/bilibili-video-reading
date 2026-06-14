# Bilibili Video Reading

Small "skill + CLI" project for Bilibili video reading.

The CLI handles repeatable operations:

- Parse Bilibili URLs and BVIDs.
- Create issue-ready diagnostic reports across DNS, subtitle lookup, subtitle body download, and optional media fallback.
- Export subtitle JSON/SRT/transcripts.
- Download public audio/video with `yt-dlp`.
- Run local `whisper-cli` ASR.
- Sample frames with `ffmpeg` and create contact sheets.
- Write `manifest.json` artifacts for the skill to inspect.

The skill remains responsible for decisions and interpretation: when to trust subtitles, when to trigger logged-in Chrome, when ASR is reliable enough, and when the answer should be visual/OCR-derived.

## Install

Recommended native install:

```bash
curl -fsSL https://github.com/hongzhiyin/bilibili-video-reading/releases/latest/download/install_remote.sh | sh
```

This installs versioned releases under `~/.local/share/bvr`, writes the launcher
to `~/.local/bin/bvr`, and syncs the skill into agent skill homes. If
`~/.local/bin` is not on PATH, run `~/.local/bin/bvr` directly or add that
directory yourself.

For source checkout development:

```bash
make install
```

The skill source lives in `skill/` and can be synced to:

```text
~/.codex/skills/bilibili-video-reading
```

```bash
make install
bvr --version
bvr sync-skill --targets codex,cursor,agents,claude --force
bvr tools doctor
bvr update
bvr diagnose "https://www.bilibili.com/video/BV..." --try-media
bvr subtitles export "https://www.bilibili.com/video/BV..."
bvr media sample "https://www.bilibili.com/video/BV..."
```

Whisper models are external assets. Set `WHISPER_CPP_MODEL` or `BVR_WHISPER_MODEL`, or keep a model in the installed skill asset directory. Do not commit model binaries to this source tree.

## Documentation Map

- [docs/SPEC.md](docs/SPEC.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)
- [docs/DECISIONS.md](docs/DECISIONS.md)
- [Install and Migration](docs/install.md)
- [Skill and CLI Boundary](docs/skill-cli-boundary.md)
