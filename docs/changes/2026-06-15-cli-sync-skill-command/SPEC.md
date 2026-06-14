# SPEC - CLI Sync Skill Command

> This packet defines the user-visible `bvr sync-skill` command.

## 0. Status

| Field | Content |
|---|---|
| Status | Implemented |
| Request source | User approved adding a `bvr` sync command and asked whether the pattern is covered by `skill-cli-kit` |
| Packet directory | `docs/changes/2026-06-15-cli-sync-skill-command/` |
| Last updated | 2026-06-15 |

## 1. One-Sentence Goal

Users can refresh installed `bilibili-video-reading` skill targets from the
terminal through `bvr sync-skill`, without remembering the repo-local script
path.

## 2. Background and Problem

- Current behavior: `bvr update` syncs skill targets by default, and
  `scripts/sync_skill.sh` can be run from the repo or release tree.
- Problem: there is no explicit `bvr sync-skill` command, so users may not know
  how to refresh skill copies after local skill edits or when checking drift.
- Expected benefit: the installed CLI exposes the maintenance action directly,
  matching the discoverability of `skillcli sync-skill`.

## 3. Scope

### 3.1 In Scope

- Add `bvr sync-skill`.
- Pass through `--targets`, `--force`, and `--dry-run` to `scripts/sync_skill.sh`.
- Document the command in README, install docs, SPEC, skill instructions, and
  boundary docs.
- Bump and publish a patch release so the native CLI on PATH has the command.

### 3.2 Out of Scope

- No reimplementation of sync logic in Python.
- No change to installed skill target paths or marker semantics.
- No cross-repo edit to `skill-cli-kit` in this packet.

## 4. User Scenarios

| Scenario ID | Trigger | Expected result |
|---|---|---|
| S1 | User runs `bvr sync-skill --targets codex,cursor,agents,claude --force` | Installed skill targets refresh from the current release/source skill directory. |
| S2 | User runs `bvr sync-skill --dry-run` | Target paths are printed without writing files. |
| S3 | User runs `bvr update` | Existing default update sync behavior remains unchanged. |

## 5. Requirements

| ID | Requirement | Acceptance | Status |
|---|---|---|---|
| R1 | Expose explicit CLI sync command | `bvr sync-skill --help` shows the command and options | Done |
| R2 | Reuse existing script behavior | Unit test verifies the CLI invokes `scripts/sync_skill.sh` with pass-through args | Done |
| R3 | Keep release update sync default | `bvr update --help` still documents `--sync-skill` as default | Done |

## 6. Constraints and Invariants

1. **#1**: `bvr sync-skill` must not copy browser data, credentials, generated
   media, model binaries, or run artifacts.
2. **#2**: The sync command delegates to `scripts/sync_skill.sh`; Python code
   must not fork a second sync implementation.
3. **#3**: The command should work from both native releases and source
   checkouts by resolving the current project/release root.

## 7. Compatibility and Defaults

| Scenario | Default behavior |
|---|---|
| No target provided | Sync Codex target, matching `scripts/sync_skill.sh` default. |
| Existing `bvr update` | Still syncs skill targets unless `--no-sync-skill` is passed. |
| Source checkout development | `./scripts/sync_skill.sh` and `./scripts/update_cli.sh` remain valid. |

## 8. Acceptance Criteria

1. `bvr sync-skill --help` works.
2. `bvr sync-skill --targets codex --dry-run` exits 0 and prints target paths.
3. Unit tests pass.
4. `skillcli audit` and `docdev audit` have no findings.

## 9. Open Questions

| ID | Question | Current judgment | Blocks implementation |
|---|---|---|---|
| Q1 | Is this pattern already required by `skill-cli-kit` generated projects? | No; `skill-cli-kit` documents `skillcli sync-skill` and generated `scripts/sync_skill.sh`, but not mandatory `<cli> sync-skill` for each generated project. | No |
