# ARCHITECTURE - CLI Install and Public Readiness

> This packet affects install/sync/update structure and public repository
> surface, so an architecture note is required.

## 0. Status

| Field | Content |
|---|---|
| Status | Implementation |
| Creation reason | CLI discovery, native install, sync output, update automation, and publication metadata are structural concerns |
| Last updated | 2026-06-15 |

## 1. Existing Structure Snapshot

| Module / File | Current responsibility | Relation to this packet |
|---|---|---|
| `pyproject.toml` | Declares package `bilibili-video-reading` and console script `bvr` | Keep |
| `src/bilibili_video_reading/cli.py` | Argparse entrypoint for deterministic helper commands | Added `update` and `uninstall` |
| `src/bilibili_video_reading/release.py` | Native update/uninstall helpers | Added |
| `src/bilibili_video_reading/tools.py` | Doctor/check output for CLI, skill, external tools, model state | Extended installed `bin/bvr` checks |
| `skill/SKILL.md` | Agent workflow and CLI resolution instructions | Added metadata and skill-local wrapper resolution |
| `scripts/install_cli.sh` | Creates `.venv/bin/bvr` wrapper for source checkout | Keep |
| `scripts/install_command.sh` | Symlinks `bvr` into a writable PATH dir and may write shell profile fallback | Keep for source checkout development |
| `scripts/sync_skill.sh` | Copies `skill/` into agent skill homes and generates `bin/bvr` | Updated |
| `scripts/check_install.sh` | Runs `bvr tools doctor` through source checkout | Keep |
| `scripts/update_cli.sh` | Source-checkout install/test/check/sync lifecycle | Added |
| `scripts/package_release.sh` | Native release tarball, sha256, manifest, and installer packager | Added |
| `scripts/install_remote.sh` | Remote native installer for GitHub Release or `file://` assets | Added |
| `AGENTS.md` | First-read rules for future agents | Added |
| `LICENSE` | Missing | Still required before public visibility is useful |

## 2. Current Calls / Data Flow

Native install:

```text
install_remote.sh
  -> download manifest.json
  -> download bvr-<version>.tar.gz
  -> verify sha256
  -> extract to ~/.local/share/bvr/releases/<version>
  -> update ~/.local/share/bvr/current
  -> write ~/.local/bin/bvr launcher
  -> run bvr tools doctor
  -> scripts/sync_skill.sh --targets codex,cursor,agents,claude --force
```

Source checkout maintenance:

```text
scripts/update_cli.sh
  -> scripts/install_cli.sh
  -> PYTHONPATH=src python3 -m unittest discover -s tests
  -> scripts/check_install.sh
  -> scripts/sync_skill.sh
  -> scripts/check_install.sh
```

Skill CLI resolution:

```text
skill/SKILL.md
  -> try bvr on PATH
  -> else try skill-local bin/bvr
  -> else use BVR_PROJECT_DIR + PYTHONPATH module form
```

## 3. Target Structure

```text
GitHub Release assets
  -> install_remote.sh downloads manifest + artifact
  -> sha256 verification
  -> ~/.local/share/bvr/releases/<version>
  -> ~/.local/share/bvr/current
  -> ~/.local/bin/bvr launcher
  -> installed skill bin/bvr wrapper
  -> bvr update / bvr uninstall
```

The installed skill-local wrapper is generated during sync with the current
release or source checkout path embedded at sync time.

## 4. Module and Interface Contracts

| Module / File | New / Changed | Responsibility | Should not depend on |
|---|---|---|---|
| `scripts/sync_skill.sh` | Changed | Copy skill and generate executable `bin/bvr` wrapper | Network, package indexes, cookies |
| `scripts/update_cli.sh` | New | One-command source checkout update/verify/sync lifecycle | Git pull unless explicitly requested |
| `scripts/package_release.sh` | New | Build native release assets | GitHub mutation |
| `scripts/install_remote.sh` | New | Install release assets under `~/.local/share/bvr` and write launcher | Shell profile edits |
| `src/bilibili_video_reading/release.py` | New | Implement `bvr update` and safe uninstall planning | Browser state |
| `skill/SKILL.md` | Changed | Declare CLI metadata and resolution order | Hard-coded private paths |
| `AGENTS.md` | New | First-read rules for future agents | Secrets or generated artifacts |

## 5. Data, Config, Resource Changes

| Type | Path / Field | Change | Compatibility |
|---|---|---|---|
| Native install root | `${BVR_INSTALL_ROOT:-~/.local/share/bvr}` | New versioned release layout | Does not affect source checkout install |
| Native launcher | `${BVR_BIN_DIR:-~/.local/bin}/bvr` | New generated launcher | Does not edit shell profiles |
| Generated installed wrapper | `${CODEX_HOME:-~/.codex}/skills/bilibili-video-reading/bin/bvr` | New generated file during sync | Adds a fallback, does not remove PATH `bvr` |
| Skill metadata | `skill/SKILL.md` frontmatter | Add required bin and help command | Agent hosts can surface dependency |
| Update script | `scripts/update_cli.sh` | Add project-local lifecycle command | Mirrors skill-cli-kit pattern |
| Release assets | `dist/releases/` | Add package output directory | Ignored by git unless explicitly added |

## 6. Tests and Observation Points

- `./scripts/package_release.sh`
- `BVR_RELEASE_BASE_URL=file://... ./scripts/install_remote.sh` with temp roots
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `bvr tools doctor`
- `skillcli audit /Users/chihoyo/Project/bilibili-video-reading --json`
- `docdev audit /Users/chihoyo/Project/bilibili-video-reading --write-report`
