# SPEC - Bilibili Video Reading

> Source of truth for expected behaviour. Implementation shape lives in
> ARCHITECTURE.md; progress lives in ROADMAP.md; rationale lives in DECISIONS.md.

## 1. One-Sentence Goal

Provide a local, cookie-safe skill + CLI workflow that turns Bilibili video
links into AI-readable transcript, ASR, visual, diagnostic, and manifest
artifacts for agents.

## 2. Decision Table

| ID | Decision | Choice | Notes |
|---|---|---|---|
| A | Runtime / platform | Python 3.10+ source-layout CLI with no required third-party Python dependencies | External tools are optional capabilities. |
| B | Skill / CLI split | CLI performs deterministic work; skill owns judgment and fallback selection | See D-001. |
| C | Browser safety | Never read browser cookies, profile files, local storage, saved passwords, or session stores | Visible Chrome UI fallback is allowed when the user is logged in. |
| D | Artifact storage | Write run artifacts under user-selected output directories and record redacted `manifest.json` evidence | Default temp path is project-local or caller-local, not committed. |
| E | Distribution | Native GitHub Release installer for ordinary use; source checkout install for development | Public-ready distribution includes release packaging, checksum manifest, launcher, update/uninstall, and skill sync. |
| F | Public repository readiness | Repository can become public only after license, install contract, no-secrets check, and local-path cleanup are satisfied | Visibility change is a release action, not a code default. |

## 3. Derived Rules

### 3.1 Safety

- The project must not require users or agents to copy cookies, headers, browser
  profiles, or credential material.
- Short-lived subtitle URLs may be used as local run inputs, but persisted
  manifests and normal output must redact authorization-like query parameters.
- Whisper model binaries and generated media artifacts are external assets and
  must remain untracked.

### 3.2 Commands

| Command | Purpose | Side effects |
|---|---|---|
| `bvr --version` | Print the installed CLI version | No file writes |
| `bvr sync-skill` | Refresh installed skill targets and generated skill-local `bin/bvr` wrappers | Writes configured skill target dirs |
| `bvr parse <source>` | Parse a Bilibili URL or BVID without network access | No file writes |
| `bvr diagnose <source>` | Produce an issue-ready subtitle/media fallback diagnostic report | Writes output directory artifacts and optional manifest |
| `bvr subtitles export <source>` | Resolve and export subtitle JSON, SRT, transcript, and manifest evidence | Writes output directory artifacts |
| `bvr subtitles convert <json>` | Convert a manually copied subtitle Response body | Writes SRT/transcript/manifest artifacts |
| `bvr media download <source>` | Download public audio/video through external media tools | Writes media artifacts |
| `bvr media sample <source>` | Sample frames and create visual contact sheets | Writes frame/contact-sheet artifacts |
| `bvr asr whisper-cpp <audio>` | Run local whisper.cpp ASR with an external model | Writes ASR transcript/SRT artifacts |
| `bvr tools doctor` | Report local CLI, skill, external tool, and model readiness | No required project mutation |

### 3.3 Installation

- A released version must provide a remote native installer that downloads a
  manifest and tarball, verifies sha256, installs under `~/.local/share/bvr`,
  and writes `~/.local/bin/bvr`.
- A fresh source checkout must still provide a reproducible local development
  install path that does not require PyPI or system Python mutation.
- A synced installed skill should be able to find the deterministic CLI from an
  arbitrary working directory through `bvr`, a skill-local `bin/bvr`, or an
  explicit source checkout fallback.
- Skill sync should be available both through the project script
  (`./scripts/sync_skill.sh`) and through the installed CLI (`bvr sync-skill`).
- Update flow should be one command for native installs (`bvr update`) and one
  command for source checkouts (`./scripts/update_cli.sh`).

## 4. Default Handling

| Scenario | Default behaviour |
|---|---|
| Public subtitle retrieval works | Use generated transcript as primary evidence. |
| Public subtitle retrieval fails due login/blocking | Use logged-in Chrome UI fallback without reading cookies or storage. |
| No reliable subtitles exist | Move to ASR or visual/OCR fallback and state the limitation. |
| External media/ASR tools are missing | Report capability gaps via `bvr tools doctor`; do not auto-install tools. |
| Asked to publish repository | Verify license, no-secrets scan, generated artifact hygiene, native install docs, and GitHub visibility before changing visibility. |

## 5. Module Contracts

### 5.1 CLI

```text
bvr command args -> redacted JSON result + optional manifest/artifacts
```

Constraints:
- Inputs are Bilibili URLs/BVIDs, local media paths, or local subtitle JSON
  files.
- Outputs must be agent-readable JSON and files under caller-selected output
  directories.
- Errors should be classified enough for the skill to choose the next fallback.

### 5.2 Skill

```text
user task + CLI evidence -> answer, fallback selection, or next safe action
```

Constraints:
- The skill interprets artifacts and decides whether subtitles, ASR, or visual
  evidence is trustworthy.
- The skill must preserve the cookie/profile safety boundary.
- The skill should prefer deterministic CLI output over ad hoc browser or shell
  scraping.

## 6. Non-Goals

- No committed browser credentials, cookies, profile copies, or copied cURL
  requests.
- No committed Whisper model binaries or generated media/transcript artifacts.
- No package-index-only install path for the local CLI.
- No automatic installation of external tools such as `yt-dlp`, `ffmpeg`, or
  whisper.cpp.

## 7. Invariants

1. **#1**: Browser credentials and session material are never read, exported,
   copied, printed, or required by project workflows.
2. **#2**: Deterministic operations stay in the CLI; the skill owns policy,
   fallback choice, interpretation, and user-facing caveats.
3. **#3**: Run artifacts, media files, model binaries, and generated reports
   stay out of source-of-truth docs and normal commits.
4. **#4**: Public-ready install/update flows must be reproducible through native
   release assets without private local paths or agent memory.
5. **#5**: Repository visibility must not be changed to public until license,
   no-secrets scan, install instructions, and generated-artifact hygiene have
   been checked.
