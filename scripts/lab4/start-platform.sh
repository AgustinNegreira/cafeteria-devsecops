#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

umask 077
mkdir -p "$state_dir"

if ! kind get clusters | grep -Fxq "$cluster"; then
    kind create cluster --name "$cluster" --config local/kind-lab4.yaml \
        --kubeconfig "$kubeconfig" --wait 180s
else
    kind export kubeconfig --name "$cluster" --kubeconfig "$kubeconfig"
fi

if docker container inspect "$registry_container" >/dev/null 2>&1; then
    docker start "$registry_container" >/dev/null
else
    docker run -d --name "$registry_container" --network kind \
        -p 127.0.0.1:5001:5000 registry:3.0.0 >/dev/null
fi

# El motor Docker usa el puerto local, containerd llega al registry por la red de kind.
registry_dir=/etc/containerd/certs.d/localhost:5001
while IFS= read -r node; do
    node=${node%$'\r'}
    MSYS2_ARG_CONV_EXCL='*' docker exec "$node" mkdir -p "$registry_dir"
    printf 'server = "http://%s:5000"\n[host."http://%s:5000"]\n  capabilities = ["pull", "resolve"]\n' \
        "$registry_container" "$registry_container" |
        MSYS2_ARG_CONV_EXCL='*' docker exec -i "$node" cp /dev/stdin "$registry_dir/hosts.toml"
done < <(kind get nodes --name "$cluster")

if ! kube get namespace "$namespace" >/dev/null 2>&1; then
    kube create namespace "$namespace"
fi
if [[ ! -s "$state_dir/pin.env" ]]; then
    printf 'CAFETERIA_PIN=%s\n' "$(openssl rand -hex 16)" > "$state_dir/pin.env"
fi
if ! kube -n "$namespace" get secret cafeteria-pin >/dev/null 2>&1; then
    kube -n "$namespace" create secret generic cafeteria-pin --from-env-file "$state_dir/pin.env"
fi
