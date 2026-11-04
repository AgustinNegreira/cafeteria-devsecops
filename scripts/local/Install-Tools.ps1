. "$PSScriptRoot/Common.ps1"
$bin = Join-Path $Private 'bin'
New-Item -ItemType Directory -Force $bin | Out-Null
function Download-Checked($Url,$Target,$Hash) {
    if (Test-Path $Target) {
        if ((Get-FileHash $Target -Algorithm SHA256).Hash.ToLower() -eq $Hash) { return }
    }
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Target
    if ((Get-FileHash $Target -Algorithm SHA256).Hash.ToLower() -ne $Hash) { throw "SHA256 incorrecto: $Target" }
}
Download-Checked 'https://kind.sigs.k8s.io/dl/v0.33.0/kind-windows-amd64' "$bin/kind.exe" '4b22adaa135368c5a465d56bbd8e520cbea87272a06ca00b6078e7b81515c9fc'
Download-Checked 'https://get.helm.sh/helm-v4.3.1-windows-amd64.zip' "$Private/helm.zip" 'fcfd7b796dcf0f225abc40b5636a3b01f55f3de2fb1dfb18475df94e62c14112'
Expand-Archive -Path "$Private/helm.zip" -DestinationPath "$Private/helm" -Force
Copy-Item "$Private/helm/windows-amd64/helm.exe" "$bin/helm.exe" -Force
Download-Checked 'https://github.com/stackrox/kube-linter/releases/download/v0.8.3/kube-linter-windows.tar.gz' "$Private/kube-linter.tar.gz" '27132f8505d156e3877c6235970f567f47bedf11102f79fd6780d4ab536f6525'
Run tar -xzf "$Private/kube-linter.tar.gz" -C $bin
# kubectl: checksum oficial publicado para el mismo artefacto/version.
$kubectlHash = (Invoke-WebRequest -UseBasicParsing 'https://dl.k8s.io/release/v1.35.8/bin/windows/amd64/kubectl.exe.sha256').Content.Trim()
Download-Checked 'https://dl.k8s.io/release/v1.35.8/bin/windows/amd64/kubectl.exe' "$bin/kubectl.exe" $kubectlHash
Write-Output 'Herramientas verificadas en .local/bin (sin modificar el PATH global).'

