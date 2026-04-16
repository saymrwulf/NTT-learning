#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON="$VENV_DIR/bin/python"
JUPYTER="$VENV_DIR/bin/jupyter"
START_NOTEBOOK="notebooks/START_HERE.ipynb"

LOG_DIR="$PROJECT_ROOT/.logs"
RUN_DIR="$PROJECT_ROOT/.run"
PID_FILE="$LOG_DIR/jupyter.pid"
LEGACY_PID_FILE="$RUN_DIR/jupyter.pid"
LOG_FILE="$LOG_DIR/jupyterlab.log"

JUPYTER_CONFIG_DIR="$PROJECT_ROOT/.jupyter_config"
JUPYTER_DATA_DIR="$PROJECT_ROOT/.jupyter_data"
JUPYTER_RUNTIME_DIR="$PROJECT_ROOT/.jupyter_runtime"
IPYTHONDIR="$PROJECT_ROOT/.ipython"
MPLCONFIGDIR="$PROJECT_ROOT/.cache/matplotlib"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/app.sh bootstrap
  bash scripts/app.sh start [--foreground] [--no-open] [--port PORT]
  bash scripts/app.sh stop
  bash scripts/app.sh restart [start args...]
  bash scripts/app.sh status
  bash scripts/app.sh logs [-f]

Optional compatibility commands:
  bash scripts/app.sh validate
  bash scripts/app.sh reset-state
EOF
}

ensure_dirs() {
  mkdir -p \
    "$LOG_DIR" \
    "$RUN_DIR" \
    "$JUPYTER_CONFIG_DIR" \
    "$JUPYTER_DATA_DIR" \
    "$JUPYTER_RUNTIME_DIR" \
    "$IPYTHONDIR" \
    "$MPLCONFIGDIR"
}

set_jupyter_env() {
  export JUPYTER_CONFIG_DIR
  export JUPYTER_DATA_DIR
  export JUPYTER_RUNTIME_DIR
  export IPYTHONDIR
  export MPLCONFIGDIR
}

pid_alive() {
  local pid="${1:-}"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

clear_pid_files() {
  rm -f "$PID_FILE" "$LEGACY_PID_FILE"
}

write_pid_files() {
  local pid="$1"
  ensure_dirs
  printf '%s\n' "$pid" > "$PID_FILE"
  printf '%s\n' "$pid" > "$LEGACY_PID_FILE"
}

get_running_pid() {
  local candidate pid
  for candidate in "$PID_FILE" "$LEGACY_PID_FILE"; do
    [[ -f "$candidate" ]] || continue
    pid="$(<"$candidate")"
    if pid_alive "$pid"; then
      printf '%s\n' "$pid"
      return 0
    fi
    if runtime_json_alive_for_pid "$pid"; then
      printf '%s\n' "$pid"
      return 0
    fi
    rm -f "$candidate"
  done
  return 1
}

jupyter_installed() {
  [[ -x "$PYTHON" ]] || return 1
  "$PYTHON" -c "import jupyterlab, ipykernel" >/dev/null 2>&1
}

cleanup_stale_runtime() {
  [[ -x "$PYTHON" ]] || return 0
  ensure_dirs
  "$PYTHON" - "$JUPYTER_RUNTIME_DIR" <<'PY'
import json
import os
import sys
from pathlib import Path

runtime_dir = Path(sys.argv[1])
for path in runtime_dir.glob("jpserver-*.json"):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pid = int(payload.get("pid", -1))
        os.kill(pid, 0)
    except (FileNotFoundError, ProcessLookupError, ValueError, json.JSONDecodeError, TypeError):
        path.unlink(missing_ok=True)
        path.with_name(f"{path.stem}-open.html").unlink(missing_ok=True)
    except PermissionError:
        pass
PY
}

latest_active_runtime_json() {
  [[ -x "$PYTHON" ]] || return 1
  "$PYTHON" - "$JUPYTER_RUNTIME_DIR" <<'PY'
import json
import os
import sys
from pathlib import Path

runtime_dir = Path(sys.argv[1])
paths = sorted(
    runtime_dir.glob("jpserver-*.json"),
    key=lambda candidate: candidate.stat().st_mtime,
    reverse=True,
)

for path in paths:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pid = int(payload.get("pid", -1))
        os.kill(pid, 0)
    except (ProcessLookupError, ValueError, json.JSONDecodeError, TypeError, FileNotFoundError):
        continue
    except PermissionError:
        pass
    print(path)
    sys.exit(0)

sys.exit(1)
PY
}

runtime_json_for_pid() {
  local pid="${1:-}"
  local candidate
  [[ -n "$pid" ]] || return 1

  candidate="$JUPYTER_RUNTIME_DIR/jpserver-$pid.json"
  if [[ -f "$candidate" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi

  latest_active_runtime_json
}

runtime_json_alive_for_pid() {
  local pid="${1:-}"
  local runtime_json api_url

  [[ -n "$pid" ]] || return 1
  runtime_json="$JUPYTER_RUNTIME_DIR/jpserver-$pid.json"
  [[ -f "$runtime_json" ]] || return 1

  if ! command -v curl >/dev/null 2>&1; then
    return 0
  fi

  api_url="$(runtime_json_to_api_url "$runtime_json")" || return 1
  curl --silent --show-error --max-time 2 "$api_url" >/dev/null 2>&1
}

runtime_json_to_access_url() {
  local runtime_json="$1"
  "$PYTHON" -c '
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

url = payload["url"].rstrip("/")
token = payload.get("token", "")
target = f"{url}/lab/tree/notebooks/START_HERE.ipynb"
print(f"{target}?token={token}" if token else target)
' "$runtime_json"
}

runtime_json_to_api_url() {
  local runtime_json="$1"
  "$PYTHON" -c '
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

url = payload["url"].rstrip("/")
token = payload.get("token", "")
target = f"{url}/api"
print(f"{target}?token={token}" if token else target)
' "$runtime_json"
}

runtime_json_to_port() {
  local runtime_json="$1"
  "$PYTHON" -c '
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

print(payload.get("port", ""))
' "$runtime_json"
}

server_access_url() {
  local runtime_json
  if [[ $# -gt 0 ]]; then
    runtime_json="$(runtime_json_for_pid "$1")" || return 1
  else
    runtime_json="$(latest_active_runtime_json)" || return 1
  fi
  runtime_json_to_access_url "$runtime_json"
}

server_port() {
  local runtime_json
  if [[ $# -gt 0 ]]; then
    runtime_json="$(runtime_json_for_pid "$1")" || return 1
  else
    runtime_json="$(latest_active_runtime_json)" || return 1
  fi
  runtime_json_to_port "$runtime_json"
}

server_ready() {
  local pid="$1"
  local runtime_json api_url

  runtime_json="$(runtime_json_for_pid "$pid")" || return 1
  if ! command -v curl >/dev/null 2>&1; then
    return 0
  fi

  api_url="$(runtime_json_to_api_url "$runtime_json")" || return 1
  curl --silent --show-error --max-time 2 "$api_url" >/dev/null 2>&1
}

find_project_jupyter_pids() {
  local process_table
  process_table="$(ps -axo pid=,command= 2>/dev/null || true)"
  [[ -n "$process_table" ]] || return 0

  printf '%s\n' "$process_table" | awk -v root="$PROJECT_ROOT" 'index($0, "jupyter") && (index($0, "--ServerApp.root_dir=" root) || index($0, "--ServerApp.root_dir " root) || index($0, "--notebook-dir=" root "/notebooks") || index($0, "--notebook-dir " root "/notebooks")) { print $1 }'
}

orphan_pids() {
  local tracked_pid="${1:-}"
  find_project_jupyter_pids | awk -v tracked="$tracked_pid" '$1 != tracked'
}

find_free_port() {
  local requested_port="${1:-}"
  local port

  if [[ -n "$requested_port" ]]; then
    if lsof -i :"$requested_port" >/dev/null 2>&1; then
      echo "Requested port $requested_port is already in use." >&2
      return 1
    fi
    printf '%s\n' "$requested_port"
    return 0
  fi

  port=8888
  while lsof -i :"$port" >/dev/null 2>&1; do
    port=$((port + 1))
    if (( port > 8899 )); then
      echo "No free port in range 8888-8899." >&2
      return 1
    fi
  done

  printf '%s\n' "$port"
}

open_url() {
  local url="$1"

  if command -v open >/dev/null 2>&1; then
    open "$url" >/dev/null 2>&1 || true
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 || true
  fi
}

require_bootstrap() {
  if [[ ! -x "$PYTHON" ]]; then
    echo "Missing .venv. Run: bash scripts/app.sh bootstrap" >&2
    exit 1
  fi
  if ! jupyter_installed; then
    echo "JupyterLab/ipykernel are not available. Run: bash scripts/app.sh bootstrap" >&2
    exit 1
  fi
}

cmd_bootstrap() {
  local py_cmd="${PYTHON_BIN:-}"
  if [[ -z "$py_cmd" ]]; then
    for candidate in python3.12 python3.11 python3; do
      if command -v "$candidate" >/dev/null 2>&1; then
        py_cmd="$candidate"
        break
      fi
    done
  fi

  if [[ -z "$py_cmd" ]]; then
    echo "Python 3.11+ not found." >&2
    exit 1
  fi

  if [[ ! -x "$PYTHON" ]]; then
    "$py_cmd" -m venv "$VENV_DIR"
  fi

  ensure_dirs
  set_jupyter_env

  "$PYTHON" -m pip install --disable-pip-version-check --no-build-isolation -e ".[dev]"

  "$PYTHON" -m ipykernel install \
    --sys-prefix \
    --name "ntt-learning" \
    --display-name "NTT Learning" \
    --env IPYTHONDIR "$IPYTHONDIR" \
    --env MPLCONFIGDIR "$MPLCONFIGDIR"

  echo "Bootstrap complete."
}

cmd_start() {
  local open_browser=true
  local foreground=false
  local requested_port=""
  local port pid url runtime_url

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --no-open)
        open_browser=false
        shift
        ;;
      --foreground)
        foreground=true
        shift
        ;;
      --port)
        [[ $# -ge 2 ]] || { echo "--port requires a value." >&2; exit 1; }
        requested_port="$2"
        shift 2
        ;;
      *)
        echo "Unknown start option: $1" >&2
        exit 1
        ;;
    esac
  done

  require_bootstrap
  ensure_dirs
  set_jupyter_env
  cleanup_stale_runtime

  if pid="$(get_running_pid 2>/dev/null)"; then
    echo "JupyterLab is already running with pid $pid."
    if url="$(server_access_url "$pid" 2>/dev/null)"; then
      echo "$url"
      if $open_browser; then
        open_url "$url"
      fi
    fi
    exit 0
  fi

  port="$(find_free_port "$requested_port")"

  if $foreground; then
    echo "Starting JupyterLab in foreground on port $port."
    echo "Jupyter will print the tokenized URL in this terminal."
    exec env \
      JUPYTER_CONFIG_DIR="$JUPYTER_CONFIG_DIR" \
      JUPYTER_DATA_DIR="$JUPYTER_DATA_DIR" \
      JUPYTER_RUNTIME_DIR="$JUPYTER_RUNTIME_DIR" \
      IPYTHONDIR="$IPYTHONDIR" \
      MPLCONFIGDIR="$MPLCONFIGDIR" \
      "$JUPYTER" lab \
        --no-browser \
        --ip=127.0.0.1 \
        --port="$port" \
        --ServerApp.root_dir="$PROJECT_ROOT"
  fi

  : > "$LOG_FILE"
  nohup env \
    JUPYTER_CONFIG_DIR="$JUPYTER_CONFIG_DIR" \
    JUPYTER_DATA_DIR="$JUPYTER_DATA_DIR" \
    JUPYTER_RUNTIME_DIR="$JUPYTER_RUNTIME_DIR" \
    IPYTHONDIR="$IPYTHONDIR" \
    MPLCONFIGDIR="$MPLCONFIGDIR" \
    "$JUPYTER" lab \
      --no-browser \
      --ip=127.0.0.1 \
      --port="$port" \
      --ServerApp.root_dir="$PROJECT_ROOT" \
      >"$LOG_FILE" 2>&1 &

  pid=$!
  write_pid_files "$pid"

  url=""
  for _ in $(seq 1 40); do
    if ! pid_alive "$pid"; then
      echo "JupyterLab exited during startup. Recent log output:" >&2
      tail -n 20 "$LOG_FILE" >&2 || true
      clear_pid_files
      exit 1
    fi

    cleanup_stale_runtime
    if server_ready "$pid"; then
      url="$(server_access_url "$pid" 2>/dev/null || true)"
      break
    fi
    sleep 0.5
  done

  if [[ -z "$url" ]]; then
    if runtime_url="$(server_access_url "$pid" 2>/dev/null)"; then
      url="$runtime_url"
    else
      echo "JupyterLab started with pid $pid, but the runtime URL was not detected. Check $LOG_FILE." >&2
      exit 1
    fi
  fi

  echo "JupyterLab started."
  echo "pid=$pid"
  echo "port=$(server_port "$pid" 2>/dev/null || printf '%s' "$port")"
  echo "access_url=$url"
  echo "log_file=$LOG_FILE"

  if $open_browser; then
    open_url "$url"
  fi
}

cmd_stop() {
  local pid orphans

  cleanup_stale_runtime

  if pid="$(get_running_pid 2>/dev/null)"; then
    kill -TERM "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      if ! pid_alive "$pid"; then
        break
      fi
      sleep 0.5
    done
    if pid_alive "$pid"; then
      kill -KILL "$pid" 2>/dev/null || true
    fi
    clear_pid_files
    cleanup_stale_runtime
    echo "JupyterLab stopped."
    return 0
  fi

  clear_pid_files
  orphans="$(orphan_pids | tr '\n' ' ' | xargs || true)"
  if [[ -n "$orphans" ]]; then
    echo "No managed PID file, but orphan Jupyter processes were detected: $orphans"
  else
    echo "JupyterLab is not running."
  fi
}

cmd_restart() {
  cmd_stop
  sleep 1
  cmd_start "$@"
}

cmd_status() {
  local running_pid="" access_url="" port="" orphans=""

  ensure_dirs
  cleanup_stale_runtime

  echo "repo_root=$PROJECT_ROOT"

  if [[ -x "$PYTHON" ]]; then
    echo "venv=present"
  else
    echo "venv=missing"
  fi

  if jupyter_installed; then
    echo "jupyterlab=installed"
  else
    echo "jupyterlab=missing"
  fi

  if running_pid="$(get_running_pid 2>/dev/null)"; then
    echo "server=running"
    echo "pid=$running_pid"
    if port="$(server_port "$running_pid" 2>/dev/null)"; then
      echo "port=$port"
    fi
    if access_url="$(server_access_url "$running_pid" 2>/dev/null)"; then
      echo "access_url=$access_url"
    fi
  else
    echo "server=stopped"
  fi

  orphans="$(orphan_pids "${running_pid:-}" | tr '\n' ' ' | xargs || true)"
  if [[ -n "$orphans" ]]; then
    echo "orphan_pids=$orphans"
  else
    echo "orphan_pids=none"
  fi

  echo "pid_file=$PID_FILE"
  echo "log_file=$LOG_FILE"
  echo "notebooks_dir=$PROJECT_ROOT/notebooks"
}

cmd_logs() {
  local follow=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -f|--follow)
        follow=true
        shift
        ;;
      *)
        echo "Unknown logs option: $1" >&2
        exit 1
        ;;
    esac
  done

  ensure_dirs
  if [[ ! -f "$LOG_FILE" ]]; then
    echo "No Jupyter log file found."
    return 0
  fi

  if $follow; then
    exec tail -n 100 -f "$LOG_FILE"
  fi

  tail -n 100 "$LOG_FILE"
}

cmd_validate() {
  require_bootstrap
  cd "$PROJECT_ROOT"
  "$PYTHON" -m unittest discover -s tests -t .
}

cmd_reset_state() {
  cmd_stop >/dev/null 2>&1 || true
  ensure_dirs
  clear_pid_files
  rm -f "$LOG_FILE"
  rm -f "$JUPYTER_RUNTIME_DIR"/jpserver-*.json "$JUPYTER_RUNTIME_DIR"/jpserver-*-open.html
  rm -rf "$JUPYTER_DATA_DIR/lab/workspaces"/*
  rm -rf "$MPLCONFIGDIR"/*
  find "$PROJECT_ROOT/notebooks" -type d -name .ipynb_checkpoints -prune -exec rm -rf {} +
  echo "Repo-local runtime state reset."
}

main() {
  local command="${1:-}"
  if [[ -z "$command" ]]; then
    usage
    exit 1
  fi
  shift || true

  case "$command" in
    bootstrap) cmd_bootstrap "$@" ;;
    start) cmd_start "$@" ;;
    stop) cmd_stop "$@" ;;
    restart) cmd_restart "$@" ;;
    status) cmd_status "$@" ;;
    logs) cmd_logs "$@" ;;
    validate) cmd_validate "$@" ;;
    reset-state) cmd_reset_state "$@" ;;
    -h|--help|help) usage ;;
    *)
      echo "Unknown command: $command" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
