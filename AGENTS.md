# Agent Handoff

Read these first:

1. `docs/SPEC.md`
2. `docs/ARCHITECTURE.md`
3. `docs/ROADMAP.md`
4. `docs/DECISIONS.md`
5. The active packet under `docs/changes/`

Use the deterministic helper CLI for repeatable work:

```bash
bvr --help
bvr tools doctor
```

For source checkout maintenance:

```bash
./scripts/update_cli.sh --force
```

For native release packaging and smoke tests:

```bash
./scripts/package_release.sh
BVR_RELEASE_BASE_URL="file://$PWD/dist/releases" ./scripts/install_remote.sh
```

Do not read browser cookies, profile files, local storage, saved passwords, or
session stores. Do not commit generated media, transcripts, Whisper model
binaries, `.venv/`, or `bilibili-video-reading-tmp/`.
