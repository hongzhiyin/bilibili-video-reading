# ROADMAP - CLI Version Command

> This file tracks the scoped version-command change.

## 0. Current Status

**Phase**: Implementation
**Current Step**: Step 3 - release and local install verification
**Architecture Omission Reason**: Omitted; this change only exposes an existing
package version through the CLI parser and uses the existing release/install
lifecycle without changing its structure.

## 1. Gates

### Pre-Implementation Gate

- [x] User goal confirmed in one sentence
- [x] Scope and non-goals written into SPEC
- [x] Existing implementation, call points, tests, and config researched
- [x] Key constraints / invariants written into SPEC
- [x] Required DECISIONS entry recorded
- [x] Implementation steps and verification written clearly
- [x] User request treated as implementation approval for this narrow fix

### Completion Gate

- [ ] All implementation tasks complete or have explicit skip reasons
- [ ] Acceptance criteria verified one by one
- [ ] Docs match final implementation
- [ ] Remaining risks and follow-up work recorded

## 2. Research Log

| ID | Topic | Finding | Evidence / File | Conclusion |
|---|---|---|---|---|
| R-1 | Version source | Version is already defined in both package metadata and `__init__.py`; release packaging checks these stay aligned. | `pyproject.toml`, `src/bilibili_video_reading/__init__.py`, `scripts/package_release.sh` | Reuse `__version__`; do not introduce a new source. |
| R-2 | CLI parser | `build_parser()` creates top-level argparse parser and subcommands; no top-level `--version` exists. | `src/bilibili_video_reading/cli.py` | Add argparse `action="version"` before subparsers. |
| R-3 | Existing update flag | `bvr update --version` already selects a release version. | `src/bilibili_video_reading/cli.py` | Keep it scoped to the update subcommand. |
| R-4 | Installed terminal command | Current PATH `bvr` comes from the previously published native release and does not include this source change. | `bvr --version` | Publish a patch release and update local native install. |

## 3. Step Status Overview

| Step | 内容 | 状态 |
|---|---|---|
| 0 | Establish packet | Done |
| 1 | Define scope and research | Done |
| 2 | Implement code, tests, and docs | Done |
| 3 | Verify and close | In progress |

---

## Step 0 - Establish Packet

**Goal**: Create scoped SPEC / ROADMAP / DECISIONS and decide whether
ARCHITECTURE is needed.

**Tasks**:
- [x] Initialize packet docs
- [x] Record ARCHITECTURE omission reason

**Acceptance**:
1. Packet directory exists and documents are scoped to the change.

---

## Step 1 - Define Scope and Research

**Goal**: Turn the request into a narrow, verifiable CLI behavior.

**Tasks**:
- [x] Fill SPEC goal
- [x] Fill scope and non-goals
- [x] Research version source and parser

**Acceptance**:
1. Scope is limited to `bvr --version`, docs, and test coverage.

---

## Step 2 - Implement Code, Tests, and Docs

**Goal**: Add the version command without changing install or update lifecycle.

**Tasks**:
- [x] Add top-level argparse `--version`
- [x] Add unit test for output
- [x] Update README/install/SPEC command documentation
- [x] Bump patch version for native release distribution

**Acceptance**:
1. `bvr --version` prints the package version.
2. Existing subcommands continue to parse.

---

## Step 3 - Verify and Close

**Goal**: Run checks and record final state.

**Tasks**:
- [x] Run unit tests
- [x] Run module-form version command
- [x] Run `docdev audit`
- [x] Smoke test packaged native install from local release assets
- [ ] Package and publish patch release
- [ ] Update local native install

**Acceptance**:
1. All verification rows pass.

## 4. Verification Log

| Acceptance item | Verification method | Result | Notes |
|---|---|---|---|
| AC-1 | `PYTHONPATH=src python3 -m bilibili_video_reading.cli --version` | Pass | Printed `bvr 0.1.1` |
| AC-2 | `PYTHONPATH=src python3 -m unittest discover -s tests` | Pass | 11 tests passed |
| AC-3 | `PYTHONPATH=src python3 -m bilibili_video_reading.cli update --help` | Pass | Existing `update --version VERSION` remains scoped to update |
| AC-4 | `docdev audit /Users/chihoyo/Project/bilibili-video-reading --write-report` | Pass | No findings |
| AC-5 | `bvr --version` after native update | Pending |  |
| AC-6 | `env BVR_INSTALL_ROOT=/private/tmp/bvr-version-smoke-20260615/root ... ./scripts/install_remote.sh --release-base-url file:///Users/chihoyo/Project/bilibili-video-reading/dist/releases --sync-skill` | Pass | Installed packaged `v0.1.1`; temp launcher printed `bvr 0.1.1` |

## 5. Risks and Follow-Up

| ID | Risk / Follow-up | Impact | Handling |
|---|---|---|---|
| F-1 | Existing release `v0.1.0` does not include this command | Public latest release must move forward before terminal `bvr --version` works after native install | Publish patch release `v0.1.1` |
