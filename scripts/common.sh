#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$REPO_ROOT/.venv/bin/python"
PID_FILE="$REPO_ROOT/.run/jupyter.pid"
LOG_FILE="$REPO_ROOT/.run/jupyter.log"

ensure_runtime_dirs() {
  mkdir -p \
    "$REPO_ROOT/.run" \
    "$REPO_ROOT/.cache/matplotlib" \
    "$REPO_ROOT/.ipython" \
    "$REPO_ROOT/.jupyter_config" \
    "$REPO_ROOT/.jupyter_data" \
    "$REPO_ROOT/.jupyter_runtime"
}

require_venv() {
  if [[ ! -x "$VENV_PY" ]]; then
    echo "Missing .venv. Run scripts/bootstrap.sh first."
    exit 1
  fi
}

jupyter_installed() {
  "$VENV_PY" -c "import jupyterlab" >/dev/null 2>&1
}

is_running() {
  if [[ ! -f "$PID_FILE" ]]; then
    return 1
  fi

  local pid
  pid="$(<"$PID_FILE")"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

