#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

if is_running; then
  "$SCRIPT_DIR/stop.sh"
fi

ensure_runtime_dirs

rm -f "$PID_FILE" "$LOG_FILE"
rm -rf "$REPO_ROOT/.jupyter_runtime"/*
rm -rf "$REPO_ROOT/.jupyter_data/lab/workspaces"/*
rm -rf "$REPO_ROOT/.cache/matplotlib"/*
find "$REPO_ROOT/notebooks" -type d -name .ipynb_checkpoints -prune -exec rm -rf {} +

echo "Repo-local runtime state reset."

