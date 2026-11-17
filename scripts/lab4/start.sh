#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

bash scripts/lab4/start-platform.sh
bash scripts/lab4/start-security.sh
bash scripts/lab4/start-monitoring.sh
bash scripts/lab4/start-jenkins.sh

if [[ $# -gt 0 ]]; then
    bash scripts/lab4/deploy.sh "$1"
fi
