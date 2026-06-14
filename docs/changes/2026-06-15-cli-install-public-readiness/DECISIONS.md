# DECISIONS - CLI Install and Public Readiness

> This file records real trade-offs for this packet only.

## Maintenance Rules

1. `D-XXX` numbers are monotonic within this packet.
2. Keep decisions tied to SPEC requirements and ROADMAP evidence.
3. Do not use this file for task status.

---

## D-001 - Step 3 - Improve Source-Checkout Install Instead of Recreating the CLI

**Date**: 2026-06-15

**Context**:
The project already has a working Python console script, local wrapper, tests,
and doctor command. The audit gaps are around portability, metadata, sync, and
update lifecycle rather than CLI command design.

**Options**:
- A. Recreate the CLI project from scratch with `skillcli init` - would align
  generated structure but risks overwriting domain-specific code and current
  user changes.
- B. Keep the CLI and patch the missing portable install/sync/update surfaces -
  smaller, preserves working behaviours, and directly addresses audit warnings.
- C. Skip install changes and only make the repo public - fastest, but leaves
  future agents dependent on PATH/profile/local memory.

**Chosen**: B

**Rationale**:
- `pyproject.toml` already exposes `bvr` correctly and tests pass under the
  source-layout invocation.
- `skillcli audit` reports 0 errors; its 7 warnings map to narrow install,
  metadata, sync, handoff, and installed-wrapper fixes.
- The current dirty worktree makes a from-scratch scaffold risky and unnecessary.

**Risks**:
- Generated installed wrapper will likely embed the current source checkout
  path, so moving the checkout requires resync.
- Public polish still needs a license and README updates before changing
  GitHub visibility.

**Related code / docs**:
- SPEC §5
- ROADMAP Step 3
- ARCHITECTURE §3
- `pyproject.toml`
- `scripts/sync_skill.sh`
- `skill/SKILL.md`

---

## D-002 - Step 4 - Native Release Install Matches Sibling Tools

**Date**: 2026-06-15

**Context**:
The user explicitly asked for an install style like the other two projects.
Those projects use GitHub Release assets, manifest checksum verification,
versioned native install roots, and launcher-based updates.

**Options**:
- A. Only add source-checkout `update_cli.sh` and skill-local wrappers - smaller
  but still requires cloning for ordinary use.
- B. Add native release packaging and remote installer now - larger slice, but
  matches the desired install/update model.
- C. Publish to a package index first - not needed for agent-local workflows.

**Chosen**: B

**Rationale**:
- It gives a public-friendly `curl ... install_remote.sh | sh` path.
- It preserves source checkout development while making ordinary installs
  independent of private local paths.
- It creates the release assets needed before making the repository public.

**Risks**:
- First implementation is Unix-shell only.
- The public curl command requires a GitHub Release to be published after this
  code lands.

**Related code / docs**:
- SPEC §3
- ROADMAP Step 4
- ARCHITECTURE §3
- `scripts/package_release.sh`
- `scripts/install_remote.sh`
- `src/bilibili_video_reading/release.py`

---

## D-003 - Step 6 - Make Repository Public After Native Install Verification

**Date**: 2026-06-15

**Context**:
The release assets were published and the local machine was switched to the
native installer. The user asked why public visibility was still needed for
unauthenticated remote install, then explicitly said to make the repository
public.

**Options**:
- A. Keep the repo private and require `GITHUB_TOKEN` for remote install.
- B. Change GitHub visibility to public now and leave LICENSE as a follow-up.
- C. Delay public visibility until LICENSE is chosen.

**Chosen**: B

**Rationale**:
- It makes `https://github.com/hongzhiyin/bilibili-video-reading/releases/latest/download/install_remote.sh`
  work for anonymous `curl`.
- It matches the native install contract documented for ordinary users.
- The user explicitly confirmed the visibility change.

**Risks**:
- The repository still has no LICENSE.
- The existing committed history is now public.

**Related code / docs**:
- SPEC §9
- ROADMAP Verification Log Step 6
- `docs/install.md`
- `scripts/install_remote.sh`
