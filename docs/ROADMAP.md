# ROADMAP - Bilibili Video Reading

> Source of truth for progress. Rationale lives in DECISIONS.md.

## Current Progress

**Phase**: Phase 2 - native install implementation
**Current Step**: Step 4 done; `bvr sync-skill` available in native install

### Step Status

| Step | Scope | Status |
|---|---|---|
| 0 | Adopt docs-driven root docs | Done |
| 1 | Decide public-ready CLI/install changes | Done |
| 2 | Implement native install/update/public changes | Done |
| 3 | Add terminal version command | Done |
| 4 | Add explicit skill sync command | Done |

---

## Step 0 - Adopt Docs-Driven Root Docs

**Goal**: Make project intent, decisions, modules, and progress legible before
changing install or publication behaviour.

**Tasks**:
- [x] Create root `SPEC.md`, `ARCHITECTURE.md`, `ROADMAP.md`, and `DECISIONS.md`
- [x] Preserve existing dirty README/skill/code changes
- [x] Create generated report directory under `docs/_generated/docdev/`

**Acceptance**:
1. A new reader can explain the project goal, current state, and next step from
   the four docs alone.

---

## Step 1 - CLI/Install/Public-Readiness Gate

**Goal**: Decide which installation and publication changes are required before
making the repository public.

**Tasks**:
- [x] Create change packet `docs/changes/2026-06-15-cli-install-public-readiness/`
- [x] Run `skillcli audit` and record CLI/install findings
- [x] Run local tests and `bvr tools doctor`
- [x] Get user approval for implementation changes

**Acceptance**:
1. The change packet identifies current CLI/install gaps with file evidence.
2. Public visibility risks are listed before any GitHub visibility change.
3. Implementation starts only after the user approves the proposed scope.

---

## Step 2 - Implement Native Install/Update/Public Changes

**Goal**: Make the project installable, updateable, syncable, and publishable
through native release assets without relying on hidden local state.

**Tasks**:
- [x] Add native release packager and remote installer
- [x] Add `bvr update` and `bvr uninstall`
- [x] Add project-local CLI update automation
- [x] Generate installed skill-local `bin/bvr` during sync
- [x] Add skill metadata for required CLI bin and help command
- [x] Add agent handoff documentation
- [x] Change GitHub visibility to public after user confirmation
- [ ] Add LICENSE after user chooses one
- [x] Run verification suite

**Acceptance**:
1. `skillcli audit <project> --json` has no portability/update/sync metadata
   warnings for the approved scope.
2. `PYTHONPATH=src python3 -m unittest discover -s tests` passes.
3. `bvr tools doctor` reports a usable local install.
4. `docdev audit <project> --write-report` has no unaddressed docs warnings,
   or each remaining warning has a written skip reason.
5. Packaged release assets install from a local `file://` base into a temp
   native root.
6. Latest GitHub Release assets install anonymously from the public repository.

---

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Public repo has no LICENSE | External users cannot clearly reuse the project | Choose and add LICENSE in a follow-up |
| Native installer is Unix-shell only | Windows users need manual/source checkout path for now | Track PowerShell parity as a future release |
| Dirty working tree contains user changes | Accidental overwrite or mixed ownership | Keep implementation scoped and review diffs before edits |
| GitHub visibility change is irreversible in effect | Private history becomes public | Completed only after explicit user confirmation |

---

## Step 3 - Add Terminal Version Command

**Goal**: Let users confirm the active `bvr` CLI version from the terminal.

**Tasks**:
- [x] Add top-level `bvr --version`
- [x] Document the command in user-facing docs
- [x] Bump patch version for native release distribution
- [x] Publish patch release and update local native install
- [x] Run verification suite

**Acceptance**:
1. `bvr --version` or module-form equivalent prints the active package version.
2. Unit tests pass.
3. `docdev audit` has no findings.
4. Local native `bvr` on PATH reports `0.1.1`.

---

## Step 4 - Add Explicit Skill Sync Command

**Goal**: Let users refresh installed skill targets through the `bvr` CLI.

**Tasks**:
- [x] Add `bvr sync-skill`
- [x] Reuse `scripts/sync_skill.sh`
- [x] Document the command in user-facing docs and skill instructions
- [x] Publish patch release and update local native install
- [x] Run verification suite

**Acceptance**:
1. `bvr sync-skill --help` exposes the command.
2. `bvr sync-skill --targets codex --dry-run` exits successfully.
3. Unit tests, `skillcli audit`, and `docdev audit` pass.
4. Local native `bvr` on PATH reports `0.1.2`.
