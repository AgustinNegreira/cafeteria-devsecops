#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

chart -n monitoring upgrade --install lab4-monitoring \
    oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack \
    --version 93.1.1 --create-namespace --values monitoring/values.yaml --wait --timeout 8m
kube apply -f monitoring/cafeteria-servicemonitor.yaml
kube -n monitoring create configmap cafeteria-dashboard \
    --from-file=dashboard.json=grafana/dashboard.json --dry-run=client -o yaml |
    kube label --local -f - grafana_dashboard=1 -o yaml |
    kube apply -f -
