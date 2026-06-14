# SPEC - CLI Version Command

> This packet defines the user-visible version command for `bvr`.

## 0. Status

| Field | Content |
|---|---|
| Status | Implemented |
| Request source | User asked to add a terminal command for checking the version |
| Packet directory | `docs/changes/2026-06-15-cli-version-command/` |
| Last updated | 2026-06-15 |

## 1. One-Sentence Goal

Users can run a single terminal command to see the installed `bvr` CLI version.

## 2. Background and Problem

- Current behavior: `pyproject.toml` and `src/bilibili_video_reading/__init__.py`
  define the package version, but the argparse entrypoint had no top-level
  version flag.
- Problem: after native install or update, users cannot quickly confirm which
  CLI release is active.
- Expected benefit: `bvr --version` reports the active package version without
  network access or side effects.

## 3. Scope

### 3.1 In Scope

- Add a top-level `bvr --version` command.
- Document the command in user-facing CLI/install docs.
- Add an automated test for version output.

### 3.2 Out of Scope

- No change to package version semantics beyond the patch release required to
  make the command available through the native installer.
- No change to `bvr update --version <version>`.

## 4. User Scenarios

| Scenario ID | Trigger | Expected result |
|---|---|---|
| S1 | User runs `bvr --version` | The command prints `bvr <version>` and exits 0. |
| S2 | User runs `bvr update --version <version>` | Existing update version selection still works. |

## 5. Requirements

| ID | Requirement | Acceptance | Status |
|---|---|---|---|
| R1 | Expose top-level version output | `PYTHONPATH=src python3 -m bilibili_video_reading.cli --version` prints the package version | Done |
| R2 | Keep update version argument compatible | `bvr update --version <version>` remains a subcommand argument | Done |

## 6. Constraints and Invariants

1. **#1**: Version output must not require network, external tools, browser
   state, or file writes.
2. **#2**: The version string remains sourced from the package version constant
   checked by release packaging.

## 7. Compatibility and Defaults

| Scenario | Default behavior |
|---|---|
| Existing subcommands | Unchanged. |
| Native launcher | Prints the version from the installed release tree. |
| Source checkout | Prints the version from the checkout on `PYTHONPATH`. |

## 8. Acceptance Criteria

1. `bvr --version` or module-form equivalent prints the active package version.
2. Unit tests cover the top-level version flag.
3. `docdev audit` reports no findings.

## 9. Open Questions

| ID | Question | Current judgment | Blocks implementation |
|---|---|---|---|
| Q1 | Should this packet publish a new release? | Yes; otherwise the native `bvr` already on PATH will not expose the command | No |
