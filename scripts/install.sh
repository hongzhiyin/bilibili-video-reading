#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

echo "==> Install local CLI wrapper"
"$PROJECT_DIR/scripts/install_cli.sh"

echo
echo "==> Sync Codex skill"
"$PROJECT_DIR/scripts/sync_skill.sh"

echo
echo "==> Check installation"
"$PROJECT_DIR/scripts/check_install.sh"
