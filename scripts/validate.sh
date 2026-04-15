#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

require_venv

cd "$REPO_ROOT"
"$VENV_PY" -m unittest discover -s tests -t .

