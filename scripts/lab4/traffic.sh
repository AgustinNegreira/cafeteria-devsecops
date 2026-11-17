#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

python_cmd=python
if [[ -x .venv/Scripts/python.exe ]]; then
    python_cmd=.venv/Scripts/python.exe
elif [[ "$OSTYPE" != msys* ]] && command -v python3 >/dev/null 2>&1; then
    python_cmd=python3
fi
"$python_cmd" scripts/lab4/traffic.py "$@"
