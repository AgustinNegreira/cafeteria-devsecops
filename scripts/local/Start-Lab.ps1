param([switch]$SkipScans)
. "$PSScriptRoot/Common.ps1"
& "$PSScriptRoot/Install-Tools.ps1"
Push-Location $Repo
try {
    & docker info --format '{{.OSType}}' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Abrir Docker Desktop y esperar el motor Linux antes de continuar' }
    $clusters = & kind get clusters
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron consultar los clusters' }
    if ($clusters -notcontains 'cafeteria-devsecops') { Run kind create cluster --config local/kind-config.yaml --kubeconfig $Kubeconfig --wait 180s }
    else { Run kind export kubeconfig --name cafeteria-devsecops --kubeconfig $Kubeconfig }
    Assert-Local
    Run helm repo add kyverno https://kyverno.github.io/kyverno/
    Run helm repo add falcosecurity https://falcosecurity.github.io/charts
    Run helm repo update
    Run helm upgrade --install kyverno kyverno/kyverno --version 3.9.2 --namespace kyverno --create-namespace --kubeconfig $Kubeconfig -f local/kyverno-values.yaml --wait --timeout 10m
    Run helm upgrade --install falco falcosecurity/falco --version 9.2.2 --namespace falco --create-namespace --kubeconfig $Kubeconfig -f local/falco-values.yaml --wait --timeout 10m
    Run kubectl --kubeconfig $Kubeconfig apply -f k8s/local/namespace.yaml
    $pinPath = Join-Path $Private 'cafeteria-pin.txt'
    if (-not (Test-Path $pinPath)) { [IO.File]::WriteAllText($pinPath,(New-LocalPassword)) }
    $secret = & kubectl --kubeconfig $Kubeconfig -n cafeteria-devsecops create secret generic cafeteria-agustin "--from-file=CAFETERIA_PIN=$pinPath" --dry-run=client -o yaml | Out-String
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar el secreto' }
    $secret | & kubectl --kubeconfig $Kubeconfig apply -f - | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo aplicar el secreto' }
    Run kubectl --kubeconfig $Kubeconfig apply -f security/kyverno/
    Run docker build -t cafeteria:devsecops-local .
    if (-not $SkipScans) { Run python scripts/security/scan.py --image cafeteria:devsecops-local }
    Run python scripts/local/deploy.py --image cafeteria:devsecops-local --kubeconfig $Kubeconfig
    Write-Output 'App: http://localhost:8081 - PIN privado en .local/cafeteria-pin.txt'
} finally { Pop-Location }
