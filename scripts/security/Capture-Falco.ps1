. "$PSScriptRoot/../local/Common.ps1"
Assert-Local
$start = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$pod = & kubectl --kubeconfig $Kubeconfig -n cafeteria-devsecops get pods -l app=cafeteria-agustin -o 'jsonpath={.items[0].metadata.name}'
if ($LASTEXITCODE -ne 0 -or -not $pod) { throw 'No hay pod de la app' }
Write-Output 'En la shell ejecutar id y luego exit. Falco debe detectar la terminal.'
& kubectl --kubeconfig $Kubeconfig -n cafeteria-devsecops exec -it $pod -- sh
if ($LASTEXITCODE -ne 0) { throw 'No se pudo ejecutar la shell con TTY' }
Start-Sleep -Seconds 3
$logs = & kubectl --kubeconfig $Kubeconfig -n falco logs -l app.kubernetes.io/name=falco -c falco "--since-time=$start" --tail=1000
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron leer logs Falco' }
$events = @($logs | Where-Object { $_.StartsWith('{') } | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $_.rule -eq 'Terminal shell in container' -and $_.output_fields.'k8s.pod.name' -eq $pod })
if ($events.Count -eq 0) { throw 'No aparecio una alerta correlacionada; revisar sensor y metadatos' }
$events | ForEach-Object { $_ | ConvertTo-Json -Depth 10 -Compress } | Set-Content (Join-Path $Repo 'reports/falco-event.log') -Encoding utf8
Write-Output "PASS: $($events.Count) alerta(s) reales del pod $pod guardadas en reports/falco-event.log."
