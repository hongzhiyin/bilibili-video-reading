#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

log() {
  printf '[bvr update] %s\n' "$*"
}

run_step() {
  step=$1
  total=$2
  name=$3
  shift 3
  log "step $step/$total start: $name"
  if "$@"; then
    log "step $step/$total done: $name"
  else
    code=$?
    log "step $step/$total failed with exit code $code: $name"
    exit "$code"
  fi
}

log "start: project=$PROJECT_DIR args=$*"
run_step 1 4 "install local CLI wrapper" "$PROJECT_DIR/scripts/install_cli.sh"

if [ -d "$PROJECT_DIR/tests" ]; then
  run_step 2 4 "run unit tests" env \
    "PYTHONPATH=$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m unittest discover -s "$PROJECT_DIR/tests"
else
  log "step 2/4 skipped: tests directory missing"
fi

run_step 3 4 "sync skill targets" "$PROJECT_DIR/scripts/sync_skill.sh" "$@"
run_step 4 4 "check after sync" "$PROJECT_DIR/scripts/check_install.sh"
log "done"
