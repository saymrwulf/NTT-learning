#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$REPO_ROOT/.venv/bin/python"
PID_FILE="$REPO_ROOT/.logs/jupyter.pid"
LEGACY_PID_FILE="$REPO_ROOT/.run/jupyter.pid"
LOG_FILE="$REPO_ROOT/.logs/jupyterlab.log"

ensure_runtime_dirs() {
  mkdir -p \
    "$REPO_ROOT/.logs" \
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
  local pid
  if [[ -f "$PID_FILE" ]]; then
    pid="$(<"$PID_FILE")"
  elif [[ -f "$LEGACY_PID_FILE" ]]; then
    pid="$(<"$LEGACY_PID_FILE")"
  else
    return 1
  fi
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

runtime_json_for_pid() {
  local pid="${1:-}"
  local runtime_json="$REPO_ROOT/.jupyter_runtime/jpserver-$pid.json"

  [[ -n "$pid" ]] || return 1
  [[ -f "$runtime_json" ]] || return 1
  printf '%s\n' "$runtime_json"
}

access_url_for_pid() {
  local pid="${1:-}"
  local runtime_json

  runtime_json="$(runtime_json_for_pid "$pid")" || return 1

  "$VENV_PY" -c '
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

url = payload["url"].rstrip("/")
token = payload.get("token")
print(f"{url}/lab?token={token}" if token else f"{url}/lab")
' "$runtime_json"
}
