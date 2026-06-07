# Install and Migration

This project is portable as a source checkout plus an installed Codex skill.

## What Is Installed

- Python CLI package: `bilibili-video-reading`
- Console command: `bvr`
- Codex skill source: `skill/`
- Installed Codex skill target: `${CODEX_HOME:-~/.codex}/skills/bilibili-video-reading`

The CLI itself has no third-party Python package dependencies. It uses standard-library Python and calls external tools when needed.

## External Tools

Recommended tools:

- `yt-dlp`: download public Bilibili audio/video fallback artifacts
- `ffmpeg`: audio conversion, frame sampling, and contact sheets
- `ffprobe`: video metadata and duration probing
- `whisper-cli`: local ASR through whisper.cpp
- GGML Whisper model: external asset, not committed to this repo

On macOS with Homebrew:

```bash
brew install yt-dlp ffmpeg whisper-cpp
```

The project does not auto-install these tools. Run installs only when you explicitly choose to.

## Install CLI

Recommended one-command setup from the repo root:

```bash
make install
```

If `make` is unavailable, run:

```bash
sh scripts/install.sh
```

This runs the local CLI install, installs a `bvr` command entry in a writable PATH directory, writes a `BVR_PROJECT_DIR` shell fallback when needed, syncs the Codex skill, and checks the resulting setup.

From a fresh clone:

```bash
git clone https://github.com/hongzhiyin/bilibili-video-reading.git "$HOME/Project/bilibili-video-reading"
cd "$HOME/Project/bilibili-video-reading"
make install
```

Recommended local editable install from the repo root:

```bash
./scripts/install_cli.sh
```

This creates `.venv/` inside the project and writes a `.venv/bin/bvr` wrapper that runs the checkout's `src/` tree. It does not modify system Python and does not need PyPI.

Use the local command directly:

```bash
./.venv/bin/bvr --help
./.venv/bin/bvr tools doctor
```

To install `bvr` as a command in a writable PATH directory:

```bash
./scripts/install_command.sh
```

This prefers an existing writable command directory such as `/opt/homebrew/bin` or `/usr/local/bin`, and falls back to `~/.local/bin`. If it uses a directory not already in PATH, it adds that directory to `~/.zprofile`.

To let the installed skill use a source checkout fallback when `bvr` is not on PATH, the installer writes:

```bash
export BVR_PROJECT_DIR="/path/to/bilibili-video-reading"
```

For a packaged editable install, use your own environment manager such as `pipx`, or explicitly install into a virtual environment with packaging tools available:

```bash
python3 -m pip install -e .
```

## Install or Sync Skill

From the repo root:

```bash
./scripts/sync_skill.sh
```

This copies `skill/` into:

```text
${CODEX_HOME:-~/.codex}/skills/bilibili-video-reading
```

The installed skill delegates deterministic work to `bvr`. It should not contain or depend on legacy installed scripts.

## Model Assets

Do not commit Whisper model binaries. Use one of:

- `--model <path>` for a single ASR run
- `WHISPER_CPP_MODEL=/path/to/ggml-small.bin`
- `BVR_WHISPER_MODEL=/path/to/ggml-small.bin`
- `BVR_ASSET_DIR=/path/to/assets`
- `${CODEX_HOME:-~/.codex}/skills/bilibili-video-reading/assets/models/whisper/...`

## Source Checkout Fallback

If `bvr` is not installed, set:

```bash
export BVR_PROJECT_DIR=/path/to/bilibili-video-reading
```

Then run the module form:

```bash
PYTHONPATH="$BVR_PROJECT_DIR/src" python3 -m bilibili_video_reading.cli tools doctor
```

Installing the CLI is preferred for portability because the skill can then simply call `bvr`.
