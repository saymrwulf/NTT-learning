#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

if ! [[ -f "$PID_FILE" ]]; then
  echo "No JupyterLab pid file found."
  exit 0
fi

if is_running; then
  kill -TERM "$(<"$PID_FILE")"
  rm -f "$PID_FILE"
  echo "JupyterLab stopped."
  exit 0
fi

rm -f "$PID_FILE"
echo "Stale pid file removed."

