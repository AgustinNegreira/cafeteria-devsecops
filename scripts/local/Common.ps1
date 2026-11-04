$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$Private = Join-Path $Repo '.local'
New-Item -ItemType Directory -Force $Private | Out-Null
$Kubeconfig = Join-Path $Private 'kubeconfig.yaml'
$env:PATH = (Join-Path $Private 'bin') + [IO.Path]::PathSeparator + $env:PATH
function Run {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
    & $Arguments[0] $Arguments[1..($Arguments.Length-1)]
    if ($LASTEXITCODE -ne 0) { throw ('Fallo: ' + $Arguments[0] + ' ' + $Arguments[1]) }
}
function Assert-Local {
    $ctx = & kubectl --kubeconfig $Kubeconfig config current-context
    if ($LASTEXITCODE -ne 0 -or $ctx.Trim() -ne 'kind-cafeteria-devsecops') { throw 'Contexto local incorrecto' }
}
function New-LocalPassword {
    $bytes = New-Object byte[] 24
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')
}
