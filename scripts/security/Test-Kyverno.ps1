param([string]$Kubeconfig = "")
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false
$repo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
if (-not $Kubeconfig) { $Kubeconfig = Join-Path $repo ".local/kubeconfig.yaml" }
$context = & kubectl --kubeconfig $Kubeconfig config current-context
if ($LASTEXITCODE -ne 0 -or $context.Trim() -ne "kind-cafeteria-devsecops") { throw "Se requiere el contexto local kind-cafeteria-devsecops" }
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("Kyverno admission tests - " + (Get-Date).ToUniversalTime().ToString("o"))
$lines.Add("Context: " + $context.Trim())
$cases = @(
  @{File="bad-latest.yaml";Policy="cafeteria-no-latest"},
  @{File="bad-untagged.yaml";Policy="cafeteria-no-latest"},
  @{File="bad-resources.yaml";Policy="cafeteria-require-resources"},
  @{File="bad-root.yaml";Policy="cafeteria-non-root"}
)
$results = @()
foreach ($case in $cases) {
    $path = Join-Path $repo ("security/tests/" + $case.File)
    # Windows PowerShell 5 convierte stderr nativo en ErrorRecord; el rechazo es esperado.
    $ErrorActionPreference = 'Continue'
    $output = & kubectl --kubeconfig $Kubeconfig apply -f $path 2>&1 | ForEach-Object { $_.ToString() } | Out-String
    $code = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    $passed = $code -ne 0 -and $output.Contains($case.Policy) -and $output.Contains("denied")
    $lines.Add("CASE: " + $case.File + " expected=DENY actual_exit=" + $code + " passed=" + $passed)
    $lines.Add($output.Trim())
    $results += @{case=$case.File;expected="DENY";exitCode=$code;passed=$passed;policy=$case.Policy}
}
$positive = & kubectl --kubeconfig $Kubeconfig apply -f (Join-Path $repo "security/tests/good.yaml") 2>&1 | Out-String
$positiveCode = $LASTEXITCODE
$lines.Add("CASE: good.yaml expected=ALLOW actual_exit=" + $positiveCode)
$lines.Add($positive.Trim())
if ($positiveCode -eq 0) {
    & kubectl --kubeconfig $Kubeconfig -n cafeteria-devsecops wait --for=condition=Ready pod/accept-compliant --timeout=90s | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "El control positivo no llego a Ready" }
    $uid = & kubectl --kubeconfig $Kubeconfig -n cafeteria-devsecops exec accept-compliant -- id -u
    $lines.Add("Positive control UID: " + $uid.Trim())
    $positivePassed = $uid.Trim() -eq "10001"
    & kubectl --kubeconfig $Kubeconfig -n cafeteria-devsecops delete pod accept-compliant --wait=false | Out-Null
} else { $positivePassed = $false }
$results += @{case="good.yaml";expected="ALLOW";exitCode=$positiveCode;passed=$positivePassed}
[System.IO.File]::WriteAllLines((Join-Path $repo "reports/kyverno-validation.txt"),$lines,[System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $repo "reports/kyverno-validation.json"),($results | ConvertTo-Json -Depth 5),[System.Text.UTF8Encoding]::new($false))
$lines | Write-Output
if (@($results | Where-Object {-not $_.passed}).Count -gt 0) { throw "Fallo una validacion Kyverno; ver reportes" }
Write-Output "PASS: cuatro negativos rechazados por su politica y control positivo UID 10001."
