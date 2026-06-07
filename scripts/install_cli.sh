#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VENV_DIR=${BVR_VENV_DIR:-"$PROJECT_DIR/.venv"}

python3 -m venv "$VENV_DIR"
cat > "$VENV_DIR/bin/bvr" <<EOF
#!/usr/bin/env sh
PYTHONPATH="$PROJECT_DIR/src\${PYTHONPATH:+:\$PYTHONPATH}" exec "$VENV_DIR/bin/python" -m bilibili_video_reading.cli "\$@"
EOF
chmod +x "$VENV_DIR/bin/bvr"

echo "Installed source-checkout CLI wrapper into $VENV_DIR/bin/bvr"
echo "Try: $VENV_DIR/bin/bvr tools doctor"
echo "To install bvr as a PATH command:"
echo "  $PROJECT_DIR/scripts/install_command.sh"
echo "To make the installed skill use the source checkout fallback:"
echo "  export BVR_PROJECT_DIR=\"$PROJECT_DIR\""
echo "To make bvr directly available in this shell:"
echo "  export PATH=\"$VENV_DIR/bin:\$PATH\""
