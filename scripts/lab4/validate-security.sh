#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

kyverno_case() {
    sed "s/cafeteria-devsecops/$namespace/g" "$1" | kube create --dry-run=server -f -
}

verify_rejection() {
    local expected=$1 output
    if output=$(kube create --dry-run=server -f - 2>&1); then
        printf 'Se esperaba el rechazo de %s. %s\n' "$expected" "$output" >&2
        return 1
    fi
    printf '%s\n' "$output"
    grep -Fq "$expected" <<<"$output"
}

{
    date -u '+%FT%TZ'
    kyverno_case security/tests/good.yaml
    for check in latest resources root; do
        case "$check" in
            latest) policy=cafeteria-no-latest ;;
            resources) policy=cafeteria-require-resources ;;
            root) policy=cafeteria-non-root ;;
        esac
        sed "s/cafeteria-devsecops/$namespace/g" "security/tests/bad-$check.yaml" |
            verify_rejection "$policy"
    done
    sed -e "s/cafeteria-devsecops/$namespace/g" -e 's/accept-compliant/reject-escalation/' \
        -e 's/allowPrivilegeEscalation: false/allowPrivilegeEscalation: true/' security/tests/good.yaml |
        verify_rejection cafeteria-no-privilege-escalation
} | tee "$state_dir/kyverno-validation.log"
cp "$state_dir/kyverno-validation.log" reports/kyverno-validation.log

pod=lab4-falco-demo
kube -n "$namespace" delete pod "$pod" --ignore-not-found --timeout=60s
kube apply -f security/tests/falco-lab4.yaml
kube -n "$namespace" wait --for=condition=Ready "pod/$pod" --timeout=120s
since=$(date -u '+%FT%TZ')
MSYS2_ARG_CONV_EXCL='*' kube -n "$namespace" exec "$pod" -- touch /tmp/lab4-falco-event
for attempt in {1..15}; do
    if event=$(kube -n falco logs daemonset/falco -c falco --since-time "$since" |
        grep -F 'Lab4 Demo File Opened For Write' | grep -F "pod=$pod"); then
        {
            printf 'Acción ejecutada con touch en %s/%s.\n' "$namespace" "$pod"
            printf '%s\n' "$event"
        } | tee reports/falco-event.log
        kube -n "$namespace" delete pod "$pod" --timeout=60s
        exit 0
    fi
    sleep 2
done
printf 'Falco no registró el evento esperado para %s.\n' "$pod" >&2
exit 1
