# ROADMAP - CLI Sync Skill Command

> This file tracks the scoped `bvr sync-skill` addition.

## 0. Current Status

**Phase**: Implementation
**Current Step**: Step 3 - verify and release
**Architecture Omission Reason**: Omitted; this change adds a thin CLI wrapper
around the existing `scripts/sync_skill.sh` lifecycle and does not alter module
boundaries, target path layout, marker semantics, or install data flow.

## 1. Gates

### Pre-Implementation Gate

- [x] User goal confirmed in one sentence
- [x] Scope and non-goals written into SPEC
- [x] Existing implementation, call points, tests, and config researched
- [x] Key constraints / invariants written into SPEC
- [x] Required DECISIONS entry recorded
- [x] Implementation steps and verification written clearly
- [x] User explicitly approved adding the command

### Completion Gate

- [ ] All implementation tasks complete or have explicit skip reasons
- [ ] Acceptance criteria verified one by one
- [ ] Docs match final implementation
- [ ] Remaining risks and follow-up work recorded

## 2. Research Log

| ID | Topic | Finding | Evidence / File | Conclusion |
|---|---|---|---|---|
| R-1 | Existing sync script | `scripts/sync_skill.sh` already supports `--targets`, `--force`, and `--dry-run`. | `scripts/sync_skill.sh` | CLI should delegate to this script. |
| R-2 | Native update behavior | `bvr update` already defaults to `--sync-skill`; installer default `SYNC_SKILL=1` runs the sync script after install. | `src/bilibili_video_reading/cli.py`, `src/bilibili_video_reading/release.py`, `scripts/install_remote.sh` | New command is for explicit refresh, not replacing update behavior. |
| R-3 | `skill-cli-kit` contract | `skill-cli-kit` documents `skillcli sync-skill` for itself and `scripts/sync_skill.sh` for generated projects; it does not require generated business CLIs to expose `<cli> sync-skill`. | `/Users/chihoyo/Project/skill-cli-kit/skill/SKILL.md`, `/Users/chihoyo/Project/skill-cli-kit/docs/SPEC.md`, `/Users/chihoyo/Project/skill-cli-kit/skill/references/patterns.md` | Add `bvr sync-skill` locally; consider upstream pattern update separately. |

## 3. Step Status Overview

| Step | Content | Status |
|---|---|---|
| 0 | Establish packet | Done |
| 1 | Research sync/update behavior | Done |
| 2 | Implement command and docs | Done |
| 3 | Verify and release | In progress |

---

## Step 0 - Establish Packet

**Goal**: Create scoped docs and decide whether ARCHITECTURE is needed.

**Tasks**:
- [x] Initialize packet docs
- [x] Record ARCHITECTURE omission reason

**Acceptance**:
1. Packet exists and is scoped to the command addition.

---

## Step 1 - Research Sync/Update Behavior

**Goal**: Confirm where sync currently lives before adding a CLI command.

**Tasks**:
- [x] Inspect `bvr update`
- [x] Inspect native installer sync default
- [x] Inspect `scripts/sync_skill.sh`
- [x] Inspect `skill-cli-kit` contract

**Acceptance**:
1. Research identifies whether the command is already required upstream.

---

## Step 2 - Implement Command and Docs

**Goal**: Add a direct CLI entrypoint while reusing existing script behavior.

**Tasks**:
- [x] Add `cmd_sync_skill`
- [x] Add `bvr sync-skill` parser
- [x] Add unit test for pass-through invocation
- [x] Update README, install docs, root SPEC, boundary docs, and skill guidance
- [x] Bump patch version for release distribution

**Acceptance**:
1. Command delegates to `scripts/sync_skill.sh`.
2. Documentation explains both CLI and script entrypoints.

---

## Step 3 - Verify and Release

**Goal**: Verify the command locally, publish it, and update the native install.

**Tasks**:
- [ ] Run unit tests
- [ ] Run `bvr sync-skill --help`
- [ ] Run dry-run sync smoke
- [ ] Run `skillcli audit`
- [ ] Run `docdev audit`
- [x] Smoke test packaged native install from local release assets
- [ ] Package and publish patch release
- [ ] Update local native install

**Acceptance**:
1. All verification rows pass.

## 4. Verification Log

| Acceptance item | Verification method | Result | Notes |
|---|---|---|---|
| AC-1 | `PYTHONPATH=src python3 -m bilibili_video_reading.cli sync-skill --help` | Pass | Command and options shown |
| AC-2 | `PYTHONPATH=src python3 -m bilibili_video_reading.cli sync-skill --targets codex --dry-run` | Pass | Printed Codex target path |
| AC-3 | `PYTHONPATH=src python3 -m unittest discover -s tests` | Pass | 12 tests passed |
| AC-4 | `skillcli audit /Users/chihoyo/Project/bilibili-video-reading --write-report` | Pending | Warns until native install is updated and skill targets resynced |
| AC-5 | `docdev audit /Users/chihoyo/Project/bilibili-video-reading --write-report` | Pass | No findings |
| AC-6 | `env BVR_INSTALL_ROOT=/private/tmp/bvr-sync-skill-smoke-20260615/root ... ./scripts/install_remote.sh --release-base-url file:///Users/chihoyo/Project/bilibili-video-reading/dist/releases --sync-skill` | Pass | Installed packaged `v0.1.2`; temp `bvr sync-skill --dry-run` worked |

## 5. Risks and Follow-Up

| ID | Risk / Follow-up | Impact | Handling |
|---|---|---|---|
| F-1 | `skill-cli-kit` does not yet require generated project CLIs to expose `<cli> sync-skill` | Future projects may repeat the same discoverability gap | Track as a separate skill-cli-kit improvement |
