# Genera PNG y SVG de la arquitectura documentada, sin servicios externos.
Add-Type -AssemblyName System.Drawing
$taskWidth = 2240
$taskHeight = 1740
$taskBitmap = [System.Drawing.Bitmap]::new($taskWidth, $taskHeight)
$taskGraphics = [System.Drawing.Graphics]::FromImage($taskBitmap)
$taskGraphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$taskGraphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$taskGraphics.Clear([System.Drawing.ColorTranslator]::FromHtml('#ffffff'))
$taskSvg = [System.Text.StringBuilder]::new()
[void]$taskSvg.AppendLine('<svg xmlns="http://www.w3.org/2000/svg" width="2240" height="1740" viewBox="0 0 2240 1740"><rect width="2240" height="1740" fill="white"/><defs>')
foreach ($taskColor in @('#2563eb','#087f8c','#7c3aed','#64748b')) {
    $taskMarker = $taskColor.TrimStart('#')
    [void]$taskSvg.AppendLine("<marker id='a$taskMarker' markerWidth='10' markerHeight='10' refX='8' refY='5' orient='auto' markerUnits='userSpaceOnUse'><path d='M0,0 L10,5 L0,10 Z' fill='$taskColor'/></marker>")
}
[void]$taskSvg.AppendLine('</defs>')

function Draw-Rect([float]$x,[float]$y,[float]$w,[float]$h,[string]$fill,[string]$stroke,[float]$line=2) {
    $p = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $r = 20
    $p.AddArc($x,$y,$r,$r,180,90)
    $p.AddArc(($x+$w-$r),$y,$r,$r,270,90)
    $p.AddArc(($x+$w-$r),($y+$h-$r),$r,$r,0,90)
    $p.AddArc($x,($y+$h-$r),$r,$r,90,90)
    $p.CloseFigure()
    $b = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml($fill))
    $pen = [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml($stroke),$line)
    $taskGraphics.FillPath($b,$p)
    $taskGraphics.DrawPath($pen,$p)
    [void]$taskSvg.AppendLine("<rect x='$x' y='$y' width='$w' height='$h' rx='10' fill='$fill' stroke='$stroke' stroke-width='$line'/>")
    $b.Dispose(); $pen.Dispose(); $p.Dispose()
}
function Draw-Text([float]$x,[float]$y,[float]$size,[string]$value,[string]$color='#163047',[bool]$bold=$false) {
    $style = [System.Drawing.FontStyle]::Regular
    $weight = 400
    if ($bold) { $style = [System.Drawing.FontStyle]::Bold; $weight = 700 }
    $font = [System.Drawing.Font]::new('Segoe UI',$size,$style,[System.Drawing.GraphicsUnit]::Pixel)
    $brush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml($color))
    $taskGraphics.DrawString($value,$font,$brush,$x,$y)
    $safe = [System.Security.SecurityElement]::Escape($value)
    $svgY = $y + $size
    [void]$taskSvg.AppendLine("<text x='$x' y='$svgY' font-family='Segoe UI,Arial,sans-serif' font-size='$size' font-weight='$weight' fill='$color'>$safe</text>")
    $font.Dispose(); $brush.Dispose()
}
function Draw-Box([float]$x,[float]$y,[float]$w,[float]$h,[string]$title,[string[]]$lines,[string]$stroke='#9bb0c3',[string]$fill='#ffffff',[float]$titleSize=25,[float]$bodySize=21) {
    Draw-Rect $x $y $w $h $fill $stroke 2
    Draw-Text ($x+20) ($y+15) $titleSize $title '#163047' $true
    $textY = $y+55
    foreach ($lineText in $lines) { Draw-Text ($x+20) $textY $bodySize $lineText '#425c72'; $textY += 29 }
}
function Draw-Arrow([string]$coordinates,[string]$color,[bool]$dash=$false) {
    $points = [System.Drawing.PointF[]]@($coordinates.Split(';') | ForEach-Object { $pair = $_.Split(','); [System.Drawing.PointF]::new([single]$pair[0],[single]$pair[1]) })
    $pen = [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml($color),3)
    $cap = [System.Drawing.Drawing2D.AdjustableArrowCap]::new(5,7,$true)
    $pen.CustomEndCap = $cap
    $dashSvg = ''
    if ($dash) { $pen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash; $dashSvg = " stroke-dasharray='9,6'" }
    $taskGraphics.DrawLines($pen,$points)
    $svgPoints = $coordinates.Replace(';',' ')
    $marker = $color.TrimStart('#')
    [void]$taskSvg.AppendLine("<polyline points='$svgPoints' fill='none' stroke='$color' stroke-width='3'$dashSvg marker-end='url(#a$marker)'/>")
    $pen.Dispose(); $cap.Dispose()
}

Draw-Text 55 28 43 'Arquitectura · Cafetería' '#10283e' $true
Draw-Text 58 90 23 'Código local, entrega automática y aplicación publicada' '#425c72'
Draw-Text 60 145 21 'Azul: código e imágenes' '#2563eb'
Draw-Text 340 145 21 'Verde: HTTP y datos' '#087f8c'
Draw-Text 605 145 21 'Violeta: control y configuración' '#7c3aed'

Draw-Rect 40 220 650 1430 '#f2f7fd' '#86a4c2' 2
Draw-Text 70 250 25 'LAPTOP · Windows + Docker Desktop' '#163047' $true
Draw-Text 70 288 21 'Motor Linux sobre WSL2' '#425c72'
Draw-Rect 1180 220 1020 1430 '#f1faf8' '#72a99e' 2
Draw-Text 1215 250 28 'UCU · CLUSTER KUBERNETES' '#163047' $true
Draw-Text 1215 292 21 'Recursos de la app: namespace alumno-team10' '#425c72'

Draw-Arrow '365,490;365,575' '#2563eb'
Draw-Arrow '365,815;365,935' '#7c3aed'
Draw-Arrow '645,1010;720,1010;720,635;750,635' '#2563eb'
Draw-Arrow '1120,635;1160,635;1160,795;1290,795' '#2563eb'
Draw-Arrow '1900,200;1900,340' '#087f8c'
Draw-Arrow '1690,450;1690,505' '#087f8c'
Draw-Arrow '1690,605;1690,685' '#087f8c'
Draw-Arrow '1880,900;1880,970' '#087f8c'
Draw-Arrow '1390,980;1390,940;1460,940;1460,910' '#7c3aed' $true
Draw-Arrow '85,1250;65,1250;65,700;75,700' '#7c3aed' $true
Draw-Arrow '85,1470;55,1470;55,750;75,750' '#64748b' $true
Draw-Arrow '645,680;735,680;735,1337;1230,1337' '#7c3aed' $true
Draw-Arrow '1630,1337;1730,1337' '#7c3aed' $true
Draw-Arrow '2140,1337;2170,1337;2170,815;2070,815' '#7c3aed' $true

Draw-Box 85 350 560 140 'Git local · carpeta cafeteria' @('main · sin remoto GitHub','Montaje de solo lectura: /proyecto') '#86a4c2'
Draw-Box 85 585 560 230 'Contenedor Jenkins' @('http://localhost:8080','Checkout → tests (pytest + JUnit)','Build → Push → Deploy → /healthz','Polling de main: cada minuto') '#7396b8'
Draw-Box 85 945 560 130 'Motor Docker de la laptop' @('/var/run/docker.sock','Construye las imágenes de la app') '#86a4c2' '#ffffff' 24 21
Draw-Box 85 1190 560 120 'Archivos locales → Docker secrets' @('Token Docker Hub · kubeconfig UCU','/run/secrets → credenciales de Jenkins') '#86a4c2' '#ffffff' 23 20
Draw-Box 85 1410 560 120 'Volumen jenkins_home' @('/var/jenkins_home','Configuración e historial de builds') '#86a4c2'
Draw-Box 760 520 360 230 'Docker Hub' @('agustinnegreira/','cafeteria:N','Imágenes públicas','N = número de build') '#d3a746' '#fff9e9' 27 22

Draw-Box 1260 100 900 100 'Celular alumno / navegador cafetería' @('Páginas, API y Swagger por HTTPS') '#9db0bf' '#ffffff' 25 20
Draw-Box 1240 350 900 100 'Entrada HTTPS UCU + APISIX' @('ApisixRoute: cafeteria-agustin-team4.reto-ucu.net') '#72a99e' '#ffffff' 25 21
Draw-Box 1380 515 620 90 'Service · cafeteria-agustin' @('ClusterIP :80 → pod :8000') '#72a99e' '#ffffff' 25 21
Draw-Box 1300 695 760 205 'Pod · 1 contenedor de la app' @('FastAPI + Uvicorn · Python 3.12','HTML/JS alumno + cafetería · API','SQLite: /data/cafeteria.db') '#348c7b' '#ffffff' 28 23
Draw-Box 1240 980 300 145 'ConfigMap + Secret' @('Zona horaria / X inicial','PIN por variable','de entorno') '#8ab5aa' '#ffffff' 21 19
Draw-Box 1620 980 520 145 'PVC · cafeteria-agustin-data' @('256 Mi · RWO · local-path','PV / directorio del nodo','Montado en /data') '#8ab5aa' '#ffffff' 24 21
Draw-Box 1240 1270 390 135 'API de Kubernetes' @('Autenticación: kubeconfig','Control plane compartido') '#9c89c8' '#ffffff' 24 19
Draw-Box 1740 1270 400 135 'Deployment → ReplicaSet' @('1 réplica · Recreate','Pod con probes en /healthz') '#9c89c8' '#ffffff' 22 19

Draw-Text 385 528 20 'clona main' '#2563eb'
Draw-Text 380 868 20 'docker CLI por socket' '#7c3aed'
Draw-Text 772 825 21 'push' '#2563eb' $true
Draw-Text 1175 755 19 'pull :N' '#2563eb'
Draw-Text 1920 317 19 'HTTPS :443' '#087f8c'
Draw-Text 1720 474 19 'ruta por host' '#087f8c'
Draw-Text 1710 643 20 ':8000' '#087f8c'
Draw-Text 1900 930 19 'lee / escribe' '#087f8c'
Draw-Text 790 1248 22 'kubectl apply' '#7c3aed' $true
Draw-Text 790 1280 20 'usa kubeconfig' '#7c3aed'
Draw-Text 1645 1305 17 'actualiza' '#7c3aed'
Draw-Text 1240 1485 22 'La app continúa si se apaga la laptop.' '#205e52' $true
Draw-Text 1240 1523 21 'El disco sobrevive al pod; no reemplaza un backup.' '#425c72'
Draw-Text 80 1580 20 'Jenkins requiere laptop y Docker encendidos.' '#425c72'
Draw-Text 60 1680 19 '27/10/2026 · Versión comprobada :2 · Builds #1 y #2 SUCCESS · Detalles en ARQUITECTURA.md y GUIA_DEMO.md' '#5c7081'

[void]$taskSvg.AppendLine('</svg>')
$taskBitmap.Save((Join-Path $PSScriptRoot 'arquitectura.png'),[System.Drawing.Imaging.ImageFormat]::Png)
[System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'arquitectura.svg'),$taskSvg.ToString(),[System.Text.UTF8Encoding]::new($false))
$taskGraphics.Dispose()
$taskBitmap.Dispose()
Write-Output 'Diagrama PNG y SVG generado.'
