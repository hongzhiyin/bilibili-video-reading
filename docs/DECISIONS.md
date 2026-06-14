# DECISIONS - Bilibili Video Reading

> Source of truth for rationale. Current status lives in ROADMAP.md.

## Maintenance Rules

1. D-XXX numbers are monotonic: do not reuse and do not skip.
2. Reversing a decision means adding a new D-XXX and marking the old entry as
   superseded; do not rewrite old conclusions.
3. Each non-trivial decision should include options, chosen path, rationale,
   risks, and links.

---

## D-001 - Phase 0 - Split Agent Judgment From Deterministic CLI Work

**Date**: 2026-06-15

**Context**:
The project packages a reusable Bilibili video-reading workflow for agents.
Some tasks are deterministic and repeatable, while others require judgment
about source trust, fallback choice, and safety.

**Options**:
- A. Put the full workflow in `skill/SKILL.md` only - easy to install but
  brittle, hard to test, and prone to repeated shell snippets.
- B. Put all behaviour in the CLI - testable, but would force policy and
  user-facing interpretation into deterministic code.
- C. Keep a skill + CLI split - deterministic operations in `bvr`, judgment and
  safety decisions in the skill.

**Chosen**: C

**Rationale**:
- The CLI can produce stable JSON, files, and manifests that tests can cover.
- The skill can adapt to user intent, Chrome fallback, ASR reliability, and
  visual/OCR caveats without turning those choices into rigid CLI policy.
- The split matches the portability model expected by skill-backed CLI
  projects.

**Risks**:
- Install and sync flows must make the CLI discoverable for agents; otherwise
  the split becomes confusing on a new machine.
- Public docs must explain which layer owns deterministic work versus judgment.

**Related code / docs**:
- SPEC §2
- ARCHITECTURE §1
- `skill/SKILL.md`
- `src/bilibili_video_reading/cli.py`

---

## D-002 - Phase 2 - Prefer Native Release Install for Ordinary Users

**Date**: 2026-06-15

**Context**:
The source checkout install works locally, but ordinary users and future agents
should be able to install and update the project without cloning the repository,
mutating system Python, or remembering private source paths.

**Options**:
- A. Keep source-checkout install as the only supported path - simple, but weak
  for new machines and public releases.
- B. Publish through a package index first - familiar to Python users, but adds
  registry/account/release complexity before the skill workflow needs it.
- C. Use native GitHub Release assets with `install_remote.sh`, checksum
  manifest, versioned install root, launcher, `bvr update`, and `bvr uninstall`.

**Chosen**: C

**Rationale**:
- It matches the already working pattern in the sibling tool projects.
- It keeps the install self-contained under `~/.local/share/bvr` and
  `~/.local/bin/bvr`.
- It gives agents a stable command while preserving source checkout development
  workflows.

**Risks**:
- Initial native installer is Unix-shell focused; Windows PowerShell parity is
  deferred.
- A GitHub Release still needs to be packaged and published before the public
  curl command works.

**Related code / docs**:
- SPEC §3.3
- ARCHITECTURE §5
- ROADMAP Step 2
- `scripts/package_release.sh`
- `scripts/install_remote.sh`
- `src/bilibili_video_reading/release.py`

---

## D-003 - Phase 2 - Publish Repository After Native Release Verification

**Date**: 2026-06-15

**Context**:
The native release was packaged, pushed as `v0.1.0`, installed locally, and
verified from GitHub Release assets. The user then explicitly confirmed changing
the repository visibility to public.

**Options**:
- A. Keep the repository private until a LICENSE is chosen - safest for reuse
  clarity, but blocks the public `curl` install path.
- B. Make the repository public now and track LICENSE as a follow-up - enables
  anonymous install while keeping the remaining policy gap visible.
- C. Move distribution to a package index first - unnecessary for this release.

**Chosen**: B

**Rationale**:
- Public GitHub Release assets let new machines install without `GITHUB_TOKEN`.
- The native installer already verifies the release tarball checksum.
- The missing LICENSE affects reuse clarity, not whether the public installer can
  download and run.

**Risks**:
- `licenseInfo` is still null, so external reuse rights are unclear until a
  LICENSE is added.
- Public visibility exposes the existing committed history.

**Related code / docs**:
- ROADMAP Step 2
- `docs/install.md`
- `scripts/install_remote.sh`
