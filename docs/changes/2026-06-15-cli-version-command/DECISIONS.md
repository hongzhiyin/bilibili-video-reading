# DECISIONS - CLI Version Command

> This packet records the small CLI-surface choice for exposing version output.

## Maintenance Rules

1. `D-XXX` 在本工作包内单调递增，不复用。
2. 每条记录 2-3 个真实选项；不要编造凑数选项。
3. 写清选择、理由、风险和对应文件。
4. 决策被推翻时，新增一条 D-XXX 引用旧决策，旧决策保留原文。

---

## D-001 - Step 2 - Use Top-Level Version Flag

**Date**: 2026-06-15

**Context**:
Users need a terminal command to confirm the active `bvr` version after native
install or update. The CLI already has an update subcommand with its own
`--version <version>` argument.

**Options**:
- A. Add top-level `bvr --version` - standard CLI convention, exits before
  subcommand parsing, and leaves `bvr update --version <version>` unchanged.
- B. Add `bvr version` subcommand - also explicit, but adds a new subcommand for
  a simple read-only metadata check.

**Chosen**: A

**Rationale**:
- It matches common terminal expectations for installed CLI tools.
- Argparse handles output and exit code without a custom command function.
- It reuses the existing package `__version__` that release packaging already
  checks against `pyproject.toml`.

**Risks**:
- Users who prefer subcommand-style metadata need to use `bvr --version`.

**Related code / docs**:
- SPEC §5
- ROADMAP Step 2
- `src/bilibili_video_reading/cli.py`
