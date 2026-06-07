#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CODEX_HOME_DIR=${CODEX_HOME:-"$HOME/.codex"}
TARGET_DIR="$CODEX_HOME_DIR/skills/bilibili-video-reading"

mkdir -p "$TARGET_DIR"
cp -R "$PROJECT_DIR/skill/." "$TARGET_DIR/"

# The installed skill is a decision layer. Deterministic code lives in this repo's CLI.
rm -rf "$TARGET_DIR/scripts"

echo "Synced skill to $TARGET_DIR"
echo "Try: bvr tools doctor"
