#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
umask 077

kube apply -f security/jenkins-lab4-rbac.yaml
internal=$(kind get kubeconfig --name "$cluster" --internal | tr -d '\r')
server=$(sed -n 's/^    server: //p' <<<"$internal")
ca=$(sed -n 's/^    certificate-authority-data: //p' <<<"$internal")
[[ -n "$server" && -n "$ca" ]]
token=$(kube -n "$namespace" create token jenkins-deployer --duration=24h | tr -d '\r')
[[ -n "$token" ]]
cat > "$state_dir/kubeconfig.internal.yaml" <<EOF
apiVersion: v1
kind: Config
current-context: $cluster
clusters:
  - name: $cluster
    cluster:
      server: $server
      certificate-authority-data: $ca
contexts:
  - name: $cluster
    context:
      cluster: $cluster
      user: jenkins-deployer
      namespace: $namespace
users:
  - name: jenkins-deployer
    user:
      token: $token
EOF

if [[ ! -s "$state_dir/jenkins-admin-password.txt" ]]; then
    openssl rand -hex 16 > "$state_dir/jenkins-admin-password.txt"
fi
if [[ ! -s "$state_dir/snyk-token.txt" ]]; then
    printf '%s\n' "${SNYK_TOKEN:-SIN_CONFIGURAR}" > "$state_dir/snyk-token.txt"
fi
if ! docker image inspect cafeteria-jenkins-devsecops:2.580.1 >/dev/null 2>&1; then
    docker build -f jenkins/Dockerfile.devsecops -t cafeteria-jenkins-devsecops:2.580.1 jenkins
fi
export REPO_BRANCH=${REPO_BRANCH:-$(git branch --show-current)}
docker compose -f jenkins/docker-compose.lab4.yml up -d --build --force-recreate
printf 'Jenkins del Lab 4: http://localhost:8083/ (usuario agustin)\n'
