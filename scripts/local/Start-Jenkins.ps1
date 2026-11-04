. "$PSScriptRoot/Common.ps1"
Assert-Local
Push-Location $Repo
try {
    Run kubectl --kubeconfig $Kubeconfig apply -f security/jenkins-rbac.yaml
    $internal = & kind get kubeconfig --name cafeteria-devsecops --internal | Out-String
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo obtener endpoint interno' }
    $temp = Join-Path $Private 'kubeconfig.admin.tmp'
    try {
        [IO.File]::WriteAllText($temp,$internal)
        $config = (& kubectl --kubeconfig $temp config view --raw -o json | Out-String) | ConvertFrom-Json
        if ($LASTEXITCODE -ne 0) { throw 'Kubeconfig interno invalido' }
    } finally { if (Test-Path $temp) { Remove-Item -LiteralPath $temp -Force } }
    $token = & kubectl --kubeconfig $Kubeconfig -n cafeteria-devsecops create token jenkins-deployer --duration=24h
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar token limitado' }
    $limited = @{
        apiVersion='v1';kind='Config';'current-context'='kind-cafeteria-devsecops'
        clusters=@(@{name='kind-cafeteria-devsecops';cluster=$config.clusters[0].cluster})
        contexts=@(@{name='kind-cafeteria-devsecops';context=@{cluster='kind-cafeteria-devsecops';user='jenkins-deployer';namespace='cafeteria-devsecops'}})
        users=@(@{name='jenkins-deployer';user=@{token=$token.Trim()}})
    }
    [IO.File]::WriteAllText((Join-Path $Private 'kubeconfig.internal.yaml'),($limited | ConvertTo-Json -Depth 10))
    $passwordPath = Join-Path $Private 'jenkins-admin-password.txt'
    if (-not (Test-Path $passwordPath)) { [IO.File]::WriteAllText($passwordPath,(New-LocalPassword)) }
    $branch = & git branch --show-current
    if ($LASTEXITCODE -ne 0 -or -not $branch) { throw 'Se requiere una rama Git con el Jenkinsfile nuevo commiteado' }
    $committed = & git show HEAD:Jenkinsfile | Out-String
    if (-not $committed.Contains('scripts/local/deploy.py')) { throw 'Primero confirmar el pipeline DevSecOps en Git' }
    $env:REPO_BRANCH = $branch.Trim()
    $legacy = & docker ps --filter 'name=^/jenkins-cafeteria$' --format '{{.Names}}'
    if ($legacy) { Run docker stop jenkins-cafeteria }
    Run docker compose -f jenkins/docker-compose.devsecops.yml up -d --build --force-recreate
    Write-Output 'Jenkins: http://localhost:8080 - usuario agustin'
    Write-Output 'Clave privada: .local/jenkins-admin-password.txt. Token Kubernetes valido 24 h; ejecutar este script para renovarlo.'
} finally { Pop-Location }
