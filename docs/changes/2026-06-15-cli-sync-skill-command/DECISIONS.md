# DECISIONS - CLI Sync Skill Command

> This packet records the small CLI-surface choice for explicit skill sync.

## Maintenance Rules

1. `D-XXX` numbers are monotonic within this packet.
2. Keep decisions tied to SPEC requirements and ROADMAP evidence.
3. Do not use this file for task status.

---

## D-001 - Step 2 - Wrap Existing Sync Script

**Date**: 2026-06-15

**Context**:
`bvr update` already refreshes installed skill targets by default, but users
also need an explicit terminal command for syncing skill edits without doing a
release update. The repo already has `scripts/sync_skill.sh`.

**Options**:
- A. Add `bvr sync-skill` as a thin wrapper around `scripts/sync_skill.sh` -
  improves discoverability while keeping one sync implementation.
- B. Reimplement skill sync in Python - easier to test in isolation, but risks
  drift from the script used by installers.
- C. Keep only the repo script - works, but users must remember where the sync
  behavior lives.

**Chosen**: A

**Rationale**:
- It exposes the maintenance action at the same level as `bvr update`.
- It preserves `scripts/sync_skill.sh` as the single implementation of target
  copying and wrapper generation.
- It matches the spirit of `skillcli sync-skill` without requiring a cross-repo
  `skill-cli-kit` change first.

**Risks**:
- `skill-cli-kit` does not currently enforce this pattern for generated project
  CLIs, so future projects may still need the same improvement.

**Related code / docs**:
- SPEC §5
- ROADMAP Step 2
- `src/bilibili_video_reading/release.py`
- `scripts/sync_skill.sh`
