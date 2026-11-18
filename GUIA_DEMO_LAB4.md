# Guía práctica de demostración — Laboratorio 4

Agustín y Valentín. Usar este recorrido para ensayar y para presentar desde la laptop. Duración aproximada: 15–20 minutos, más lo que tarde el pipeline. Los comandos son para **Git Bash**, abierto en la raíz del repositorio `cafeteria`, rama `laboratorio-4`.

Ensayo verificado: [build 6 y resultados actuales](reports/lab4-demo-2026-11-17.md). Los accesos y claves están juntos en `.local/lab4/accesos-demo.txt`, archivo local ignorado por Git.

## 0. Dejar listo antes de presentar

Docker Desktop debe estar iniciado. En esta laptop ya existe el cluster y conserva sus datos. Para reabrir este entorno:

```bash
docker start cafeteria-lab4-control-plane
bash scripts/lab4/start-platform.sh
bash scripts/lab4/start-jenkins.sh
export PATH="$PWD/.local/bin:$PATH"
export KUBECONFIG="$PWD/.local/lab4/kubeconfig.yaml"
kubectl config current-context
```

Esperado: `kind-cafeteria-lab4`. El arranque de Jenkins renueva su acceso a Kubernetes, que dura 24 horas. Para crear todo desde un entorno nuevo existe `bash scripts/lab4/start.sh`, que también instala las herramientas y el operador de Prometheus; no hace falta reinstalarlos para cada ensayo.

En otras dos terminales Git Bash, desde el mismo repositorio, dejar abiertos estos accesos si no están funcionando ya:

```bash
.local/bin/kubectl.exe --kubeconfig .local/lab4/kubeconfig.yaml -n monitoring port-forward svc/lab4-grafana 3001:80
```

```bash
.local/bin/kubectl.exe --kubeconfig .local/lab4/kubeconfig.yaml -n monitoring port-forward svc/lab4-monitoring-prometheus 9091:9090
```

| Pantalla | Dirección | Acceso |
| --- | --- | --- |
| Alumnos | http://localhost:8082 | Crear un pedido de demostración |
| Personal de Cafetería | http://localhost:8082/cafeteria | PIN de `.local/lab4/pin.env` |
| Jenkins | http://localhost:8083/job/cafeteria-lab4/ | Usuario `agustin`; clave en `.local/lab4/jenkins-admin-password.txt` |
| Dashboard Grafana | http://localhost:3001/d/cafeteria-lab4 | Usuario `admin`; obtener clave con el comando siguiente |
| Prometheus Targets | http://localhost:9091/targets | Verificar target de Cafetería |

Obtener la clave de Grafana antes de compartir la pantalla:

```bash
kubectl -n monitoring get secret lab4-grafana -o jsonpath='{.data.admin-password}' | base64 -d
```

Preparar un recreo de demo abierto y comprobar que haya productos disponibles:

```bash
python scripts/lab4/prepare-demo.py
```

Si un terminal nuevo no encuentra `kubectl`, repetir los dos `export` del inicio. Si un túnel indica puerto ocupado pero su página funciona, el acceso ya está levantado.

## 1. Mostrar el objetivo y la arquitectura — 1 minuto

Abrir `LABORATORIO_4.md` y su diagrama. Decir: **Partimos de Cafetería e integramos construcción, pruebas, seguridad, despliegue y monitoreo. Seguimos un commit de Git hasta la imagen y el pod que atiende pedidos.**

```bash
git status --short --branch
git log -3 --oneline
docker ps --format 'table {{.Names}}\t{{.Status}}'
kubectl get nodes
kubectl get namespaces
kubectl get pods -A
```

Esperado: los tres contenedores exteriores del Lab 4 (Jenkins, registry y nodo kind), un nodo y varios namespaces. Los pods de app, monitoreo y seguridad están dentro del nodo. kind ejecuta Kubernetes real localmente; los nodos son contenedores Docker.

## 2. Ejecutar el pipeline — 4–8 minutos según red y caché

En Jenkins, job `cafeteria-lab4`, pulsar **Build Now / Construir ahora** una sola vez. Abrir el build y **Console Output**. Seguir:

1. Checkout: anotar commit y número de build.
2. Semgrep: dos reglas Python (`eval` y `shell=True`).
3. Snyk: dependencias Python y vulnerabilidades conocidas; bloquea críticos y errores de escaneo.
4. Build y tests: pruebas de la app, incluidas las métricas nuevas de estados de pedidos.
5. Imagen y Trivy: construir la imagen y revisar sus paquetes y bibliotecas.
6. Publicar: enviar la imagen etiquetada al registry local.
7. Desplegar con Helm: actualizar la release y comprobar rollout y `/healthz`.

Esperado: `SUCCESS`. Abrir **Artifacts** y mostrar los reportes de Semgrep, Snyk, Trivy y pytest. Ante un fallo, leer la primera etapa roja; las posteriores se omiten y `post/always` conserva los reportes. No presentar un build fallido como exitoso: corregir el problema o mostrar una ejecución exitosa anterior, indicando su fecha.

Después del build:

```bash
helm list -n cafeteria-lab4
helm history cafeteria -n cafeteria-lab4
kubectl -n cafeteria-lab4 get deployment cafeteria -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
kubectl -n cafeteria-lab4 get pods,svc,pvc
curl -fsS http://localhost:8082/healthz
```

Relacionar el commit con `build-N-COMMIT` de la imagen y la nueva revisión de Helm. **Chart** = plantillas y valores; **release** = instalación concreta; **Kubernetes** mantiene los pods. La primera instalación usa `helm install cafeteria ./helm-chart`; en este entorno instalado usamos `upgrade --install`.

## 3. Mostrar Docker y Dive — 2 minutos

Abrir `Dockerfile`: etapa de dependencias, etapa final y usuario no root. En la terminal con los `export`:

```bash
IMAGE=$(kubectl -n cafeteria-lab4 get deployment cafeteria -o jsonpath='{.spec.template.spec.containers[0].image}')
docker image inspect "$IMAGE" --format '{{.Size}} bytes | {{len .RootFS.Layers}} capas | usuario {{.Config.User}}'
docker run --rm --entrypoint id "$IMAGE" -u
MSYS2_ARG_CONV_EXCL='*' docker run --rm -e CI=true -v /var/run/docker.sock:/var/run/docker.sock ghcr.io/wagoodman/dive:v0.13.1 "$IMAGE"
```

Esperado: UID `10001`, imagen versionada y análisis de sus capas. Abrir `reports/image-analysis.md` para explicar tamaño, cantidad de capas y duplicación detectada. Ese informe contiene la medición histórica con su imagen y fecha; la salida que acabamos de ejecutar corresponde a la imagen actual.

## 4. Crear tráfico y mirar Grafana — 2 minutos

```bash
python scripts/lab4/prepare-demo.py
bash scripts/lab4/traffic.sh --count 60 --delay 1
```

Esperado: un pedido `201`, un rechazo `409` si hay un recreo cerrado y 60 solicitudes adicionales. El `409` demuestra una regla del negocio, no una falla de infraestructura.

Abrir Prometheus Targets: Cafetería debe estar `UP`. Abrir el dashboard Grafana, rango **últimos 15 minutos**, actualización cada 10 segundos. Dejar pasar varios scrapes; las tasas necesitan más de una muestra.

Mostrar los siete paneles: RPS por código HTTP, latencia, CPU por pod, memoria, pedidos creados, pedidos entregados hoy y distribución de estados. **La app expone `/metrics`; Prometheus consulta y guarda muestras; Grafana consulta Prometheus.** El `ServiceMonitor` configura al operador para recolectar Cafetería cada 10 segundos.

En `/cafeteria`, marcar un pedido **Listo para retirar** y después **Entregado**. Esperar 10–20 segundos y mostrar el cambio de estado en Grafana. Es el aporte de Valentín.

## 5. Demostrar reemplazo del pod y persistencia — 2 minutos

Hacerlo una vez que el pipeline haya terminado. El generador anterior guardó el pedido que se verificará.

```bash
kubectl -n cafeteria-lab4 get pods -l app.kubernetes.io/instance=cafeteria -o wide
kubectl -n cafeteria-lab4 get pvc
kubectl -n cafeteria-lab4 delete pod -l app.kubernetes.io/instance=cafeteria --timeout=120s
kubectl -n cafeteria-lab4 rollout status deployment/cafeteria --timeout=120s
kubectl -n cafeteria-lab4 get pods -l app.kubernetes.io/instance=cafeteria -o wide
bash scripts/lab4/traffic.sh --verify-persistence
curl -fsS http://localhost:8082/healthz
```

Esperado: otro nombre de pod, pedido conservado y servicio accesible por la misma dirección. El PVC queda; el Service dirige tráfico al pod nuevo. Con una sola réplica puede haber una interrupción breve. Si rollout todavía no detecta el pod nuevo, esperar unos segundos y repetir la comprobación HTTP.

Decir: **Deployment → ReplicaSet → pod reemplazado; SQLite en PVC conserva los pedidos.** El contador de pedidos creados se reinicia con el proceso; el Gauge de estados de hoy vuelve a consultar SQLite y recupera sus cantidades.

Para mostrar configuración y probes, abrir `helm-chart/templates/deployment.yaml`, `configmap.yaml` y `helm-chart/values-dev.yaml`: Secret del PIN, ConfigMap, requests/limits y startup/readiness/liveness. Las probes las ejecuta kubelet.

## 6. Mostrar Kyverno y Falco — 2 minutos

```bash
bash scripts/lab4/validate-security.sh
cat reports/kyverno-validation.log
cat reports/falco-event.log
```

Esperado: manifiesto válido aceptado en dry-run; cuatro casos rechazados (latest, sin recursos, root y escalada de privilegios); alerta Falco por abrir `/tmp/lab4-falco-event` para escritura. El script crea un pod temporal, ejecuta `touch` directamente y elimina ese pod. No abre una shell.

Decir: **Kyverno aplica políticas durante admisión; Falco observa eventos durante ejecución. Semgrep, Snyk y Trivy actúan antes del despliegue en nuestro pipeline.**

## 7. Cerrar con evidencias — 1 minuto

Mostrar `LABORATORIO_4.md`, `reports/`, `grafana/dashboard.json`, `Jenkinsfile` y `scripts/lab4/`. Repartir con Valentín la presentación de forma que ambos puedan explicar el recorrido completo y contestar sobre lo que mostró el otro.

Frase de cierre: **Un commit pasa controles, produce una imagen identificable y se despliega con Helm; Kubernetes mantiene la ejecución, Prometheus/Grafana muestran su comportamiento y Kyverno/Falco agregan controles de seguridad.**

## Si queda poco tiempo

Prioridad: pipeline exitoso y artefactos → imagen/pod/release → tráfico y dashboard → persistencia → Kyverno/Falco. Dockerfile y Dive pueden mostrarse usando el informe y su salida guardada si no hay tiempo para repetir el análisis.

## Al terminar

Para pausar conservando el trabajo:

```bash
docker stop jenkins-lab4 cafeteria-lab4-registry cafeteria-lab4-control-plane
```

`scripts/lab4/cleanup.sh` sirve para borrar los recursos del laboratorio, incluidos datos del cluster y volumen de Jenkins. Dejar esa limpieza para después de la evaluación; mostrar el script alcanza para explicar cómo se retira el entorno.
