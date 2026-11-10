#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

chart -n kyverno upgrade --install kyverno kyverno --repo https://kyverno.github.io/kyverno/ \
    --version 3.9.2 --create-namespace --values local/kyverno-values.yaml --wait --timeout 6m
for policy in security/kyverno/0[1-3]-*.yaml; do
    sed "s/cafeteria-devsecops/$namespace/g" "$policy" | kube apply -f -
done
kube apply -f security/kyverno/04-no-privilege-escalation.yaml

chart -n falco upgrade --install falco falco --repo https://falcosecurity.github.io/charts \
    --version 9.2.2 --create-namespace --values local/falco-values.yaml \
    --values local/falco-lab4-values.yaml --wait --timeout 6m
