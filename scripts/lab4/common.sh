#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export PATH="$PWD/.local/bin:$PATH"

cluster=cafeteria-lab4
namespace=cafeteria-lab4
release=cafeteria
state_dir=.local/lab4
kubeconfig="$state_dir/kubeconfig.yaml"
registry_container=cafeteria-lab4-registry
image_repo=localhost:5001/cafeteria

kube() {
    kubectl --kubeconfig "$kubeconfig" --context "kind-$cluster" "$@"
}

chart() {
    helm --kubeconfig "$kubeconfig" --kube-context "kind-$cluster" "$@"
}
