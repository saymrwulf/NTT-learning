#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

require_venv
ensure_runtime_dirs

if ! jupyter_installed; then
  echo "jupyterlab is not installed in .venv. Run scripts/bootstrap.sh first."
  exit 1
fi

if is_running; then
  pid="$(<"$PID_FILE")"
  echo "JupyterLab is already running with pid $pid."
  if access_url="$(access_url_for_pid "$pid" 2>/dev/null)"; then
    echo "$access_url"
  fi
  exit 0
fi

PORT="${PORT:-8888}"

nohup env \
  JUPYTER_CONFIG_DIR="$REPO_ROOT/.jupyter_config" \
  JUPYTER_DATA_DIR="$REPO_ROOT/.jupyter_data" \
  JUPYTER_RUNTIME_DIR="$REPO_ROOT/.jupyter_runtime" \
  IPYTHONDIR="$REPO_ROOT/.ipython" \
  MPLCONFIGDIR="$REPO_ROOT/.cache/matplotlib" \
  "$VENV_PY" -m jupyter lab \
  --no-browser \
  --ip=127.0.0.1 \
  --port="$PORT" \
  --ServerApp.root_dir="$REPO_ROOT" \
  >"$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
pid="$(<"$PID_FILE")"

for _ in $(seq 1 20); do
  if ! is_running; then
    echo "JupyterLab failed to start. Check $LOG_FILE."
    exit 1
  fi

  if access_url="$(access_url_for_pid "$pid" 2>/dev/null)"; then
    echo "JupyterLab started at $access_url"
    exit 0
  fi

  sleep 0.5
done

echo "JupyterLab started with pid $pid, but the runtime URL was not detected yet. Check $LOG_FILE."
