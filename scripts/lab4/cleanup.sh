#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

docker compose -f jenkins/docker-compose.lab4.yml down --volumes
kind delete cluster --name "$cluster" --kubeconfig "$kubeconfig"
if docker container inspect "$registry_container" >/dev/null 2>&1; then
    docker rm --force --volumes "$registry_container"
fi
