#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BVR_BIN="$PROJECT_DIR/.venv/bin/bvr"
COMMAND_NAME=${BVR_COMMAND_NAME:-bvr}
PROFILE_FILE=${BVR_PROFILE_FILE:-"$HOME/.zprofile"}

if [ ! -x "$BVR_BIN" ]; then
  echo "Missing executable wrapper: $BVR_BIN" >&2
  echo "Run ./scripts/install_cli.sh first." >&2
  exit 1
fi

path_has_dir() {
  case ":${PATH:-}:" in
    *":$1:"*) return 0 ;;
    *) return 1 ;;
  esac
}

choose_bin_dir() {
  if [ -n "${BVR_BIN_DIR:-}" ]; then
    printf '%s\n' "$BVR_BIN_DIR"
    return
  fi

  for dir in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin" "$HOME/bin"; do
    if path_has_dir "$dir"; then
      if [ -d "$dir" ] && [ -w "$dir" ]; then
        printf '%s\n' "$dir"
        return
      fi
      if [ ! -e "$dir" ]; then
        mkdir -p "$dir"
        printf '%s\n' "$dir"
        return
      fi
    fi
  done

  mkdir -p "$HOME/.local/bin"
  printf '%s\n' "$HOME/.local/bin"
}

escape_double_quoted() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\$/\\$/g; s/`/\\`/g'
}

ensure_profile_line() {
  line=$1
  [ -f "$PROFILE_FILE" ] || touch "$PROFILE_FILE"
  if grep -qxF "$line" "$PROFILE_FILE"; then
    return
  fi
  printf '\n%s\n' "$line" >> "$PROFILE_FILE"
}

BIN_DIR=$(choose_bin_dir)
mkdir -p "$BIN_DIR"

if [ ! -w "$BIN_DIR" ]; then
  echo "Cannot write command entry to $BIN_DIR." >&2
  echo "Set BVR_BIN_DIR to a writable directory in PATH, then rerun this script." >&2
  exit 1
fi

LINK="$BIN_DIR/$COMMAND_NAME"
if [ -e "$LINK" ] && [ ! -L "$LINK" ]; then
  echo "Refusing to replace non-symlink command entry: $LINK" >&2
  exit 1
fi

ln -sfn "$BVR_BIN" "$LINK"
echo "Installed command entry: $LINK -> $BVR_BIN"

if [ "${BVR_SKIP_PROFILE:-0}" = "1" ]; then
  exit 0
fi

if ! path_has_dir "$BIN_DIR"; then
  case "$BIN_DIR" in
    "$HOME/.local/bin")
      ensure_profile_line 'export PATH="$HOME/.local/bin:$PATH"'
      ;;
    "$HOME/bin")
      ensure_profile_line 'export PATH="$HOME/bin:$PATH"'
      ;;
    *)
      escaped_bin_dir=$(escape_double_quoted "$BIN_DIR")
      ensure_profile_line "export PATH=\"$escaped_bin_dir:\$PATH\""
      ;;
  esac
  echo "Added $BIN_DIR to $PROFILE_FILE"
fi

if grep -q '^export BVR_PROJECT_DIR=' "$PROFILE_FILE"; then
  echo "BVR_PROJECT_DIR already configured in $PROFILE_FILE"
else
  escaped_project_dir=$(escape_double_quoted "$PROJECT_DIR")
  printf '\n# Bilibili video reading CLI\nexport BVR_PROJECT_DIR="%s"\n' "$escaped_project_dir" >> "$PROFILE_FILE"
  echo "Added BVR_PROJECT_DIR to $PROFILE_FILE"
fi
