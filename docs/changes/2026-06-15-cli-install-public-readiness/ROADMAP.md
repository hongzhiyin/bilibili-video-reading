# ROADMAP - CLI Install and Public Readiness

> This file tracks the current packet: research, gates, tasks, and verification.

## 0. Current Status

**Phase**: Implementation
**Current Step**: Step 5 - verified; public visibility pending license/confirmation
**Architecture Omission Reason**: Not omitted; install/sync/update structure is
part of the requirement.

## 1. Gates

### Pre-Implementation Gate

- [x] User goal confirmed in one sentence
- [x] Scope and non-goals written into SPEC
- [x] Existing implementation, call points, tests, and config researched
- [x] Key constraints / invariants written into SPEC
- [x] Required DECISIONS entry recorded
- [x] Implementation steps and verification written clearly
- [x] User has approved implementation plan

### Completion Gate

- [x] All implementation tasks complete or have explicit skip reasons
- [x] Acceptance criteria verified one by one
- [x] Docs match final implementation
- [x] Remaining risks and follow-up work recorded

## 2. Research Log

| ID | Topic | Finding | Evidence / File | Conclusion |
|---|---|---|---|---|
| R-1 | CLI package entrypoint | `pyproject.toml` declares package name `bilibili-video-reading`, Python `>=3.10`, and console script `bvr = bilibili_video_reading.cli:main`. | `pyproject.toml` | CLI itself does not need to be recreated. |
| R-2 | Source checkout install | `scripts/install_cli.sh` creates `.venv/bin/bvr`; `scripts/install_command.sh` symlinks into PATH and can write `BVR_PROJECT_DIR` to `~/.zprofile`. | `scripts/install_cli.sh`, `scripts/install_command.sh` | Keep for development, but ordinary users should get native release install. |
| R-3 | Skill sync | `scripts/sync_skill.sh` previously copied only Codex skill source and did not generate `bin/bvr`. | `scripts/sync_skill.sh`, `skillcli audit` | Sync now generates skill-local wrapper and supports target selection. |
| R-4 | Skill metadata | Skill frontmatter lacked `metadata.requires.bins` and `metadata.cliHelp`. | `skill/SKILL.md`, `skillcli audit` | Metadata and resolution order are updated. |
| R-5 | Update lifecycle | `scripts/update_cli.sh` was missing; native `bvr update` was missing. | `skillcli status --json`, `skillcli audit` | Both source checkout and native update paths are added. |
| R-6 | Installed state | Codex installed skill exists and matches source files, but installed target initially had no `bin/bvr`. | `bvr tools doctor`, `skillcli audit` | Needs resync after implementation. |
| R-7 | Tests | Plain `python3 -m unittest discover -s tests` fails because `src/` is not on `PYTHONPATH`; source-layout invocation passes. | command output | Update script uses `PYTHONPATH=src`. |
| R-8 | Public visibility | GitHub repo is currently private; `gh repo view` returned `visibility: PRIVATE`, `licenseInfo: null`. | `gh repo view hongzhiyin/bilibili-video-reading --json visibility,isPrivate,url,description,licenseInfo` | Do not switch to public until final confirmation. |
| R-9 | No-secrets scan | Token/cookie scan found safety-rule text, redaction code/tests, and one local path reference; no real cookie/token material was found in tracked source. | `rg -n -S "(SESSDATA|...|/Users/chihoyo)"` | Local path reference was generalized. |
| R-10 | Native pattern | Sibling projects use `package_release.sh`, `install_remote.sh`, manifest sha256, versioned install root, launcher, and update command. | `docs-driven-dev`, `skill-cli-kit` scripts | Current implementation follows that shape. |

## 3. Step Status Overview

| Step | Content | Status |
|---|---|---|
| 0 | Establish packet | Done |
| 1 | Clarify scope | Done |
| 2 | Research existing implementation | Done |
| 3 | Form and confirm plan | Done |
| 4 | Implement native install/update changes | Done |
| 5 | Verify and close | Done |

---

## Step 0 - Establish Packet

**Goal**: Create SPEC / ROADMAP / DECISIONS / ARCHITECTURE for this review.

**Tasks**:
- [x] Initialize packet docs
- [x] Keep ARCHITECTURE because structure is affected

**Acceptance**:
1. Packet directory exists and records the design gate.

---

## Step 1 - Clarify Scope

**Goal**: Turn the broad request into acceptance criteria.

**Tasks**:
- [x] Define CLI/install/public readiness scope
- [x] Define explicit non-goals
- [x] List open questions

**Acceptance**:
1. SPEC states that GitHub visibility changes wait for user approval.

---

## Step 2 - Research Existing Implementation

**Goal**: Gather enough evidence to decide whether CLI/install changes are
needed.

**Tasks**:
- [x] Inspect scripts, skill metadata, packaging, and docs
- [x] Run `skillcli status` and `skillcli audit`
- [x] Run tests and doctor checks
- [x] Check GitHub visibility and public-readiness basics

**Acceptance**:
1. Research log includes file evidence and command evidence.

---

## Step 3 - Recommended Plan

**Goal**: Pause with a concrete implementation slice.

**Recommendation**:
Yes, change install/sync/update, and make the ordinary-user path native release
install rather than source-checkout-first. The current CLI package is fine.

**Implementation tasks after approval**:
- [x] Add `scripts/package_release.sh` and `scripts/install_remote.sh` for
  native GitHub Release assets.
- [x] Add `bvr update` and `bvr uninstall`.
- [x] Add `scripts/update_cli.sh` to run install, source-layout tests,
  `scripts/check_install.sh`, `scripts/sync_skill.sh`, and final check.
- [x] Update `scripts/sync_skill.sh` to generate executable installed
  `${CODEX_HOME:-~/.codex}/skills/bilibili-video-reading/bin/bvr`.
- [x] Update `skill/SKILL.md` frontmatter with required CLI metadata and update
  CLI resolution order to `bvr` on PATH, skill-local `bin/bvr`, then
  `BVR_PROJECT_DIR`.
- [x] Extend `bvr tools doctor` to report installed `bin/bvr` state.
- [x] Add `AGENTS.md` with first-read rules for future agents.
- [ ] Add a LICENSE after user chooses the license.
- [x] Update README Documentation Map and public install notes.
- [x] Clean or generalize the user-local path reference in
  `docs/skill-cli-boundary.md`.

**Acceptance**:
1. User confirms the implementation scope. License choice remains before public
   visibility change.

---

## Step 4 - Implement Native Release Install

**Goal**: Add native packaging, install, update, sync, and uninstall surfaces.

**Tasks**:
- [x] Add native release scripts
- [x] Add source checkout update script
- [x] Add CLI update/uninstall commands
- [x] Update skill metadata and resolution docs
- [x] Update README/install docs and AGENTS handoff
- [x] Run verification and update results

**Acceptance**:
1. Packaged assets install from a local `file://` release base into a temp
   native root.
2. Unit tests, `bvr tools doctor`, `skillcli audit`, and `docdev audit` pass or
   have scoped residual warnings.

## 4. Verification Log

| Acceptance item | Verification method | Result | Notes |
|---|---|---|---|
| R1 | `skillcli audit /Users/chihoyo/Project/bilibili-video-reading --write-report` | Pass | No findings; report written to `docs/_generated/skillcli/audit.json` |
| R2 | `git status --short` | In progress | Existing dirty files predated this packet; implementation now touches approved files |
| R3 | `gh repo view hongzhiyin/bilibili-video-reading --json visibility,isPrivate,url,description,licenseInfo` | Done | Repository is private; no licenseInfo |
| R3 | `rg` no-secrets scan | Done | No real credential material found; docs/tests contain expected safety/redaction text |
| R4 | `PYTHONPATH=src python3 -m unittest discover -s tests` | Pass | 10 tests passed |
| R4 | `bvr tools doctor` | Pass | Local install status `ok`; installed Codex `bin/bvr` exists |
| R4 | `docdev audit /Users/chihoyo/Project/bilibili-video-reading --write-report` | Pass | No findings; report written to `docs/_generated/docdev/audit.json` |
| Step 4 | `./scripts/package_release.sh` | Pass | Wrote `dist/releases/bvr-0.1.0.tar.gz`, sha256, manifest, and installer |
| Step 4 | `env BVR_INSTALL_ROOT=/private/tmp/bvr-native-smoke4/root ... ./scripts/install_remote.sh --release-base-url file:///Users/chihoyo/Project/bilibili-video-reading/dist/releases --sync-skill` | Pass | Installed release, synced temp codex/cursor/agents/claude homes, `tools doctor` status ok |
| Step 4 | `PYTHONPATH=src python3 -m bilibili_video_reading.cli update --release-base-url file:///Users/chihoyo/Project/bilibili-video-reading/dist/releases --install-root /private/tmp/bvr-native-smoke5/root --bin-dir /private/tmp/bvr-native-smoke5/bin --no-sync-skill` | Pass | Verified `bvr update` entrypoint invokes native installer |
| Step 4 | `./scripts/update_cli.sh --targets codex --force` | Pass | Refreshed local source wrapper and real Codex installed skill; installed `bin/bvr` exists |
| Step 5 | `./scripts/install_remote.sh --release-base-url file:///Users/chihoyo/Project/bilibili-video-reading/dist/releases --sync-skill` | Pass | Real local native install now lives at `~/.local/share/bvr/releases/0.1.0`; launcher is `~/.local/bin/bvr` |
| Step 5 | `which -a bvr` | Pass | Only `/Users/chihoyo/.local/bin/bvr` remains on PATH |
| Step 5 | `ls -l /opt/homebrew/bin/bvr .venv/bin/bvr` | Pass | Old global source-checkout symlink and local `.venv/bin/bvr` wrapper are absent |
| Step 5 | `rg -n "BVR_PROJECT_DIR|Bilibili video reading CLI|bilibili-video-reading/.venv/bin/bvr" ~/.zprofile ~/.zshrc` | Pass | No old shell-profile fallback remains |

## 5. Risks and Follow-Up

| ID | Risk / Follow-up | Impact | Handling |
|---|---|---|---|
| F-1 | Making repo public before adding LICENSE | Reuse rights are unclear | Ask user for license or explicit publish-without-license approval |
| F-2 | Editing dirty README/skill/code owned by existing work | Could mix unrelated changes | Kept edits scoped to approved install/public readiness work |
| F-3 | Installed wrapper embeds current release or source path | Moving checkout or release root requires resync | Accept; native update/sync refreshes wrapper |
| F-4 | Native installer is Unix-shell only | Windows users need manual/source checkout path for now | Track as future PowerShell parity |
| F-5 | Current GitHub visibility change would publish existing committed history | Private history becomes public | Require explicit confirmation before `gh repo edit --visibility public` |
