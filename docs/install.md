# Install and Migration

This project supports native release installs for ordinary use and source
checkout installs for development.

## What Is Installed

- Python CLI package: `bilibili-video-reading`
- Console command: `bvr`
- Codex skill source: `skill/`
- Installed Codex skill target: `${CODEX_HOME:-~/.codex}/skills/bilibili-video-reading`
- Native release root: `${BVR_INSTALL_ROOT:-~/.local/share/bvr}`
- Native launcher: `${BVR_BIN_DIR:-~/.local/bin}/bvr`

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

## Native Install

Recommended install from the latest GitHub Release:

```bash
curl -fsSL https://github.com/hongzhiyin/bilibili-video-reading/releases/latest/download/install_remote.sh | sh
```

The installer downloads `manifest.json`, verifies the release tarball sha256,
extracts it under:

```text
~/.local/share/bvr/releases/<version>/
~/.local/share/bvr/current
```

It then writes:

```text
~/.local/bin/bvr
```

The launcher runs the release through:

```bash
BVR_PROJECT_DIR="$HOME/.local/share/bvr/current" \
PYTHONPATH="$HOME/.local/share/bvr/current/src" \
python3 -m bilibili_video_reading.cli
```

The installer does not edit shell startup files. If `~/.local/bin` is not on
PATH, run `~/.local/bin/bvr` directly or add the directory yourself.

To update a native install:

```bash
bvr update
```

If `bvr` is not on PATH:

```bash
~/.local/bin/bvr update
```

To uninstall after previewing the plan:

```bash
bvr uninstall --dry-run
bvr uninstall --yes
```

The uninstall command removes the native install root, generated launchers, and
skill targets marked with `.bvr-skill-source`. Unmarked skill directories are
skipped.

Private GitHub Releases require explicit authentication. Use `GITHUB_TOKEN` only
for the installer process, or download the assets locally and install from:

```bash
BVR_RELEASE_BASE_URL="file:///path/to/release-assets" ./scripts/install_remote.sh
```

## Source Checkout Install

For development from the repo root:

```bash
make install
```

If `make` is unavailable, run:

```bash
sh scripts/install.sh
```

This runs the local CLI install, installs a `bvr` command entry in a writable
PATH directory, writes a `BVR_PROJECT_DIR` shell fallback when needed, syncs the
Codex skill, and checks the resulting setup.

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

## Package a Release

From the repo root:

```bash
./scripts/package_release.sh
```

This writes release assets under `dist/releases/`:

```text
bvr-<version>.tar.gz
bvr-<version>.tar.gz.sha256
manifest.json
install_remote.sh
```

Smoke-test the packaged assets locally with:

```bash
BVR_RELEASE_BASE_URL="file://$PWD/dist/releases" ./scripts/install_remote.sh
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

The installed skill delegates deterministic work to `bvr`. Sync also generates
an installed skill-local wrapper:

```text
${CODEX_HOME:-~/.codex}/skills/bilibili-video-reading/bin/bvr
```

Supported sync targets:

```bash
./scripts/sync_skill.sh --targets codex,cursor,agents,claude --force
```

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

Native install is preferred for portability because the skill can call `bvr`
without relying on a mutable source checkout.
