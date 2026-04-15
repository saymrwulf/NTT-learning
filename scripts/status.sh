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
  pid="$(<"$PID_FILE")"
  echo "server=running"
  echo "pid=$pid"
  if access_url="$(access_url_for_pid "$pid" 2>/dev/null)"; then
    echo "access_url=$access_url"
  fi
else
  echo "server=stopped"
fi

echo "notebooks_dir=$REPO_ROOT/notebooks"
