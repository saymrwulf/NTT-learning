#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

ensure_runtime_dirs

echo "repo_root=$REPO_ROOT"

if [[ -x "$VENV_PY" ]]; then
  echo "venv=present"
else
  echo "venv=missing"
fi

if [[ -x "$VENV_PY" ]] && jupyter_installed; then
  echo "jupyterlab=installed"
else
  echo "jupyterlab=missing"
fi

if is_running; then
  echo "server=running"
  echo "pid=$(<"$PID_FILE")"
else
  echo "server=stopped"
fi

echo "notebooks_dir=$REPO_ROOT/notebooks"

