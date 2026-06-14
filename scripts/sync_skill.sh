#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TARGETS="codex"
FORCE=0
DRY_RUN=0
SKILL_NAME="bilibili-video-reading"
MARKER=".bvr-skill-source"

usage() {
  cat <<'EOF'
Usage: scripts/sync_skill.sh [--targets codex,cursor,agents,claude,all] [--force] [--dry-run]
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --targets)
      TARGETS=${2:?missing value for --targets}
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'sync_skill: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

target_path() {
  target=$1
  upper=$(printf '%s' "$target" | tr 'abcdefghijklmnopqrstuvwxyz' 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
  direct_var="BVR_${upper}_SKILL_DIR"
  direct=$(eval "printf '%s' \"\${$direct_var:-}\"")
  if [ -n "$direct" ]; then
    printf '%s\n' "$direct"
    return
  fi

  case "$target" in
    codex)
      home=${BVR_CODEX_HOME:-${CODEX_HOME:-"$HOME/.codex"}}
      ;;
    cursor)
      home=${BVR_CURSOR_HOME:-"$HOME/.cursor"}
      ;;
    agents)
      home=${BVR_AGENTS_HOME:-"$HOME/.agents"}
      ;;
    claude)
      home=${BVR_CLAUDE_HOME:-"$HOME/.claude"}
      ;;
    *)
      printf 'sync_skill: unknown target: %s\n' "$target" >&2
      exit 2
      ;;
  esac
  printf '%s/skills/%s\n' "$home" "$SKILL_NAME"
}

expand_targets() {
  printf '%s\n' "$TARGETS" | tr ',' '\n' | while IFS= read -r target; do
    case "$target" in
      "" ) ;;
      all|default)
        printf 'codex\ncursor\nagents\nclaude\n'
        ;;
      codex|cursor|agents|claude)
        printf '%s\n' "$target"
        ;;
      *)
        printf 'sync_skill: unknown target: %s\n' "$target" >&2
        exit 2
        ;;
    esac
  done
}

write_wrapper() {
  target_dir=$1
  # Generate the installed skill-local bin/bvr wrapper.
  bin_dir="$target_dir/bin"
  mkdir -p "$bin_dir"
  cat > "$bin_dir/bvr" <<EOF
#!/bin/sh
BVR_PROJECT_DIR="$PROJECT_DIR" PYTHONPATH="$PROJECT_DIR/src\${PYTHONPATH:+:\$PYTHONPATH}" exec python3 -m bilibili_video_reading.cli "\$@"
EOF
  chmod +x "$bin_dir/bvr"
}

sync_one() {
  target=$1
  target_dir=$(target_path "$target")
  printf '%s: %s\n' "$target" "$target_dir"
  if [ "$DRY_RUN" -eq 1 ]; then
    return
  fi

  if [ -e "$target_dir" ] || [ -L "$target_dir" ]; then
    if [ -L "$target_dir" ] || [ -f "$target_dir" ]; then
      if [ "$FORCE" -eq 1 ]; then
        rm -f "$target_dir"
      else
        printf 'sync_skill: target exists and is not a directory: %s\n' "$target_dir" >&2
        exit 1
      fi
    else
      rm -rf "$target_dir/SKILL.md" "$target_dir/agents" "$target_dir/references" "$target_dir/scripts"
    fi
  fi

  mkdir -p "$target_dir"
  cp -R "$PROJECT_DIR/skill/." "$target_dir/"
  rm -rf "$target_dir/scripts"
  write_wrapper "$target_dir"
  printf '%s\n' "$PROJECT_DIR/skill" > "$target_dir/$MARKER"
}

printf 'sync target paths:\n'
expanded=$(expand_targets | awk '!seen[$0]++')
printf '%s\n' "$expanded" | while IFS= read -r target; do
  [ -n "$target" ] || continue
  sync_one "$target"
done

if [ "$DRY_RUN" -eq 0 ]; then
  echo "Try: bvr tools doctor"
fi
