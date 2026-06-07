#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

BVR_PROJECT_DIR="$PROJECT_DIR" PYTHONPATH="$PROJECT_DIR/src" python3 -m bilibili_video_reading.cli tools doctor
