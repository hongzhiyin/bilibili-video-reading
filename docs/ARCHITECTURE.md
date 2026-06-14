# ARCHITECTURE - Bilibili Video Reading

> Source of truth for what currently exists. Behaviour rules live in SPEC.md;
> progress lives in ROADMAP.md; rationale lives in DECISIONS.md.

## 1. Layer View

```text
User / Agent
  -> skill/SKILL.md decision workflow
  -> bvr CLI argparse entrypoint
  -> deterministic modules for Bilibili metadata, subtitles, media, ASR, tools
  -> public HTTP endpoints and optional external commands
  -> output artifacts + redacted manifest.json
```

## 2. Module Table

| Module | Path | Responsibility | Does not depend on |
|---|---|---|---|
| Skill workflow | `skill/SKILL.md` | Agent decision layer, safety rules, fallback ordering, and artifact interpretation | Python internals or hard-coded source paths |
| CLI entrypoint | `src/bilibili_video_reading/cli.py` | Argparse commands, result emission, and manifest writes | Browser cookies or agent policy decisions |
| Bilibili metadata | `src/bilibili_video_reading/bilibili.py` | BVID parsing, public metadata resolution, subtitle index support, WBI signing | Browser profiles |
| Subtitle export | `src/bilibili_video_reading/subtitles.py` | Subtitle lookup/download/conversion and status classification | User-facing interpretation |
| Diagnostic flow | `src/bilibili_video_reading/diagnose.py` | DNS/tool/video/subtitle/media readiness report | Credential stores |
| Media fallback | `src/bilibili_video_reading/media.py` | `yt-dlp`, `ffprobe`, `ffmpeg`, frames, contact sheets | Cookie extraction |
| ASR fallback | `src/bilibili_video_reading/asr.py` | whisper.cpp invocation and model discovery | Committed model binaries |
| Tool checks | `src/bilibili_video_reading/tools.py` | Local command/module/model and skill-sync status checks | Network APIs |
| Native release lifecycle | `src/bilibili_video_reading/release.py` | Native update/uninstall planning and safe removal checks | Browser or media APIs |
| Install scripts | `scripts/*.sh` | Source checkout install, PATH command entry, skill sync, install check | GitHub visibility changes |
| Tests | `tests/` | Core parser/redaction/subtitle/media behaviours | External Bilibili network |

## 3. Data Flow

```text
bvr subtitles export / diagnose / media / asr
  -> parse source and options
  -> perform deterministic local/public-network work
  -> classify status and next-step fields
  -> redact sensitive URL query parameters
  -> write artifacts under output_dir
  -> append manifest.json unless disabled
  -> print JSON for the skill to inspect
```

## 4. Data Model

### 4.1 Manifest

```text
manifest.json
  schema_version
  source / bvid / title when known
  runs[]: command, status, status_code, timestamp, redacted result
  artifacts[]: important generated paths
```

Persistence:
- Caller-selected output directory, usually `./bilibili-video-reading-tmp/<BVID>/`.
- Generated reports belong under `docs/_generated/` only when produced by docs
  or audit tooling.

## 5. Configuration

| Field | Default | Meaning | Required |
|---|---|---|---|
| `BVR_PROJECT_DIR` | unset | Source checkout fallback for module-form CLI execution | no |
| `BVR_VENV_DIR` | `<repo>/.venv` | Source checkout virtualenv/wrapper location | no |
| `BVR_BIN_DIR` | `~/.local/bin` for native install; first writable PATH dir for source command install | Destination for command launcher/symlink | no |
| `BVR_PROFILE_FILE` | `~/.zprofile` | Shell profile modified by current command installer | no |
| `BVR_SKIP_PROFILE` | `0` | Skip shell profile edits when set to `1` | no |
| `BVR_SKILL_DIR` | `${CODEX_HOME:-~/.codex}/skills/bilibili-video-reading` | Installed skill target override for checks | no |
| `BVR_INSTALL_ROOT` | `~/.local/share/bvr` | Native release install root | no |
| `BVR_RELEASE_BASE_URL` | GitHub latest release assets | Alternate release asset base URL or `file://` smoke test path | no |
| `BVR_RELEASE_REPO` | `hongzhiyin/bilibili-video-reading` | GitHub release repo for remote installer | no |
| `WHISPER_CPP_MODEL` / `BVR_WHISPER_MODEL` | unset | External whisper.cpp model path | no |
| `BVR_ASSET_DIR` | unset | External asset search root | no |

## 6. Process Model

- Entry: one-shot CLI commands or skill-guided workflows.
- Shutdown: CLI exits after printing JSON and writing requested artifacts.
- Background work: none owned by this project.
- External processes: optional `yt-dlp`, `ffmpeg`, `ffprobe`, `whisper-cli`, and
  platform media/image tools.

## 7. Known Constraints

- Native installer currently targets Unix shells; PowerShell parity can be a
  later release.
- Current command installer may edit `~/.zprofile`; this is acceptable for
  local source-checkout use but should not be the only public-facing install
  story.
- The repository currently has no LICENSE file.
- Runtime-generated `bilibili-video-reading-tmp/` and `.venv/` content exist
  locally but are ignored by git.
