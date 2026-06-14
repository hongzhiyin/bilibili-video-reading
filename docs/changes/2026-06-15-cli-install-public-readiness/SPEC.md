# SPEC - CLI Install and Public Readiness

> This packet defines what must be true before changing CLI/install behaviour or
> making the GitHub repository public.

## 0. Status

| Field | Content |
|---|---|
| Status | Implemented; repository made public after explicit confirmation |
| Request source | User asked whether the current project should adjust CLI creation/install flow and whether the repo can be public |
| Packet directory | `docs/changes/2026-06-15-cli-install-public-readiness/` |
| Last updated | 2026-06-15 |

## 1. One-Sentence Goal

Implement native-release style install/update/sync so `bilibili-video-reading`
matches the sibling tool projects and is ready for public release packaging.

## 2. Background and Problem

- Current behaviour: the repo has a working `bvr` source-checkout CLI and Codex
  skill sync path, but lacked GitHub Release packaging, remote native install,
  native update/uninstall, and installed skill-local `bin/bvr`.
- Problem: a public repo or fresh agent session should not need hidden local
  memory to discover the deterministic helper CLI.
- Expected benefit: users can clone, install, update, sync, and inspect the
  project with clear commands and fewer local-machine assumptions.

## 3. Scope

### 3.1 In Scope

- Audit the current CLI/skill structure against the skill-backed CLI pattern.
- Decide whether to add `scripts/update_cli.sh`.
- Decide whether `scripts/sync_skill.sh` should generate an installed
  skill-local `bin/bvr` wrapper.
- Decide whether `skill/SKILL.md` should declare `metadata.requires.bins` and
  `metadata.cliHelp`.
- Add native release packaging and remote install/update/uninstall paths.
- Check public-readiness basics: GitHub visibility, LICENSE, secrets/local-path
  scan, ignored generated artifacts, and docs clarity.

### 3.2 Out of Scope

- No implementation before user approval.
- No GitHub visibility change before explicit final confirmation.
- No automatic installation of `yt-dlp`, `ffmpeg`, whisper.cpp, or model
  binaries.
- No PyPI/npm publication in this packet.

## 4. User Scenarios

| Scenario ID | Trigger | Expected result |
|---|---|---|
| S1 | Future agent enters another project and needs Bilibili video reading | The skill can resolve `bvr` via PATH, installed skill-local wrapper, or explicit source checkout fallback. |
| S2 | Maintainer pulls or edits this checkout | One project-local update command can install, test, check, sync, and verify. |
| S3 | User changes GitHub repo from private to public | The repo has no obvious secret leaks, has public-friendly install docs, and records LICENSE as a follow-up. |

## 5. Requirements

| ID | Requirement | Acceptance | Status |
|---|---|---|---|
| R1 | Record evidence-backed CLI/install gaps before implementation | `skillcli audit` findings and file paths are in ROADMAP | Done |
| R2 | Keep production code unchanged until the design gate is approved | Implementation starts only after approval | Done |
| R3 | Define public-readiness blockers and non-blockers | ROADMAP risk table lists visibility, license, secret scan, and generated artifacts | Done |
| R4 | Provide and implement a native-release slice | ROADMAP Step 4 lists concrete files and checks | Done |

## 6. Constraints and Invariants

1. **#1**: Do not weaken the cookie/profile safety boundary from root SPEC #1.
2. **#2**: The CLI remains deterministic; it must not make agent policy
   decisions.
3. **#3**: Public repository work must not publish generated media, local
   virtualenv content, model binaries, or credentials.
4. **#4**: GitHub visibility may change only after explicit user confirmation.

## 7. Compatibility and Defaults

| Scenario | Default behaviour |
|---|---|
| Existing `bvr` command on PATH | Preserve it as the first resolution path. |
| Existing source-checkout fallback | Preserve `BVR_PROJECT_DIR` module-form fallback. |
| Existing installed Codex skill | Sync should replace source-controlled skill files and may add generated `bin/bvr`. |
| Missing external media/ASR tools | Report via doctor; do not auto-install. |

## 8. Acceptance Criteria

1. The recommendation clearly says whether CLI/install changes are needed.
2. Public-readiness decision separates "safe to make public now" from "better to
   fix first".
3. Verification commands and current results are recorded.

## 9. Open Questions

| ID | Question | Current judgment | Blocks implementation |
|---|---|---|---|
| Q1 | Which LICENSE should this public repo use? | User still needs to choose; repo is public without a license for now | No; follow-up |
| Q2 | Should public distribution remain source-checkout-first or add native GitHub Release installer later? | Native release is now the implementation target | No |
| Q3 | Should we make the repo public immediately after cleanup? | Done after explicit user confirmation | No |
