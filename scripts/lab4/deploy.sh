#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tag=${1:?Indicar la etiqueta versionada que se publicó en el registry}
chart -n "$namespace" upgrade --install "$release" ./helm-chart \
    --values ./helm-chart/values-dev.yaml --set-string "image.repository=$image_repo" \
    --set-string "image.tag=$tag" --wait --timeout 4m
kube -n "$namespace" rollout status "deployment/$release" --timeout=90s
