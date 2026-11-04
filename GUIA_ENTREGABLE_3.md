# Guía para probar y defender el entregable 3

Repositorio: https://github.com/AgustinNegreira/cafeteria-devsecops

## 1. Preparar la demo en esta laptop

Abrir Docker Desktop y esperar que el motor Linux esté listo. Abrir cmd en la carpeta del proyecto; la carpeta actual es:

```bat
cd /d "C:\Users\AgustinNegreira\UCU\2do Semestre 2026\DevOps\cafeteria"
```

Si la app y Jenkins ya están encendidos, se puede ir al paso 2. Para levantar o reparar el laboratorio, con Internet:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local/Start-Lab.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local/Start-Jenkins.ps1
```

El primer inicio descarga herramientas e imágenes y puede demorar varios minutos. No cambiar el contexto global ni usar credenciales de la UCU: todos los scripts señalan el kubeconfig local y comprueban `kind-cafeteria-devsecops`.

En una instalación nueva, primero clonar el repositorio y entrar en esa carpeta. Requisitos: Windows, Git, Python 3.12 o compatible accesible como `python`, Docker Desktop/WSL2 y un kernel con soporte para modern eBPF/BTF. Este laboratorio se probó en WSL2 6.18; no se promete compatibilidad con cualquier kernel anterior.

`Start-Lab.ps1` conserva el PIN existente; `Start-Jenkins.ps1` conserva su contraseña y renueva la credencial de despliegue por 24 h. Detiene el Jenkins legado si está funcionando, preservando su volumen e historial.

## 2. Mostrar la aplicación (3 minutos)

1. Abrir http://localhost:8081/ y http://localhost:8081/cafeteria en dos pestañas.
2. Obtener el PIN local, solo para uso en la laptop:

```bat
type .local\cafeteria-pin.txt
```

3. Entrar a cafetería. Crear un recreo para dentro de 45 minutos y dejar el corte en 5 minutos. Si los recreos predeterminados ya pasaron, no permitirán nuevos pedidos: es la regla de negocio funcionando.
4. Desde alumno, escribir un nombre de prueba, elegir ese recreo y varios productos. Crear el pedido.
5. Desde cafetería, ver el pedido, marcarlo listo y entregado. Volver a alumno para mostrar la actualización del estado.
6. Marcar un producto agotado y mostrar que no puede pedirse; restaurarlo al terminar.
7. Configurar un corte que deje cerrado el recreo y mostrar el mensaje de rechazo. Restaurar el corte deseado.
8. Abrir el resumen diario para ver cantidad de pedidos, ventas y productos.

La regla se aplica en FastAPI, aunque un cliente llame directamente a la API. El frontend solo presenta el resultado. Swagger está en http://localhost:8081/docs; los endpoints de cafetería usan la cabecera `X-PIN`.

## 3. Mostrar Kubernetes y el endurecimiento (2 minutos)

Desde cmd:

```bat
kubectl --kubeconfig .local\kubeconfig.yaml get pods -A
kubectl --kubeconfig .local\kubeconfig.yaml -n cafeteria-devsecops get deploy,svc,pvc
kubectl --kubeconfig .local\kubeconfig.yaml -n cafeteria-devsecops exec deployment/cafeteria-agustin -- id
kubectl --kubeconfig .local\kubeconfig.yaml get clusterpolicies
```

Esperado: app Ready 1/1, PVC Bound, Service NodePort 30080, UID/GID 10001 y tres políticas Ready. Ver en `k8s/base/deployment.yaml`: recursos, `runAsNonRoot`, raíz de solo lectura, sin escalado de privilegios, capacidades retiradas y seccomp. `/data` es el único almacenamiento persistente y `/tmp` un espacio temporal.

Explicación: el nodo kind es un contenedor Docker; dentro ejecuta Kubernetes y containerd. Jenkins es otro contenedor, conectado a la red `kind`. Windows entra por 8081; Jenkins verifica la app mediante el nombre interno del nodo y el puerto 30080. Mostrar `docs/arquitectura-devsecops.svg`.

## 4. Demostrar Kyverno (2 minutos)

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/security/Test-Kyverno.ps1
```

Esperado: `PASS`. El script intenta aplicar de verdad cuatro pods, aislando la condición inválida de cada uno:

| Manifiesto | Motivo del rechazo |
|---|---|
| bad-latest.yaml | usa tag latest |
| bad-untagged.yaml | omite el tag y equivale a latest implícito |
| bad-resources.yaml | faltan requests/limits |
| bad-root.yaml | intenta UID 0 / runAsNonRoot false |
| good.yaml | se acepta, llega a Ready y muestra UID 10001 |

Los errores `denied` son el resultado esperado. El script comprueba que nombran la política correcta y que no son un error de conexión. El control positivo se borra al terminar. Evidencia: `reports/kyverno-validation.txt` y JSON.

Las políticas se aplican a todos los pods del namespace de la app; los namespaces del sistema, Kyverno y Falco son infraestructura separada. Falco necesita privilegios para observar el kernel. No se configura una excepción que permita root a la app.

## 5. Demostrar Falco (2 minutos)

Esperar a que termine cualquier build de Jenkins para que no reemplace el pod durante esta prueba.

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/security/Capture-Falco.ps1
```

Se abre una shell dentro del pod. Escribir:

```sh
id
exit
```

Esperado: UID 10001, y después `PASS` indicando que la alerta se guardó. Abrir:

```bat
type reports\falco-event.log
```

Se debe ver `Terminal shell in container`, prioridad Notice, `source: syscall`, nombre del pod, namespace, TTY y `user.uid: 10001`. La regla alerta por una terminal dentro del contenedor aunque el usuario no sea root. Falco detecta y registra; no bloquea la shell. Kyverno actúa antes de crear el pod, en una capa distinta.

Si se suspende/reanuda WSL y las horas de eventos se desplazan, reiniciar el sensor y repetir la captura:

```bat
kubectl --kubeconfig .local\kubeconfig.yaml -n falco rollout restart daemonset/falco
kubectl --kubeconfig .local\kubeconfig.yaml -n falco rollout status daemonset/falco --timeout=120s
```

## 6. Mostrar los análisis y explicar npm (2 minutos)

Abrir `reports/npm-audit.txt`, `semgrep.txt`, `trivyreport.txt` y `kubelinter.txt`. Los JSON complementarios guardan los datos completos, y `security-summary.json` el commit, imagen y hashes de fuente.

- **npm audit sí se ejecutó**. Devuelve ENOLOCK porque la aplicación usa Python y JS sin dependencias npm. El informe conserva el error y lo justifica como no aplicable; no se presenta como cero vulnerabilidades npm. Se agregó pip-audit para analizar las dependencias Python reales.
- Semgrep revisa Python/JS, Dockerfile y manifiestos base con `p/default`, `p/security-audit` y `p/dockerfile`; resultado: 0 hallazgos.
- Trivy analiza paquetes de la imagen productiva de la app; resultado final: 0 vulnerabilidades conocidas y 0 HIGH/CRITICAL. No se escaneó toda la laptop ni la imagen de Jenkins con este resultado.
- KubeLinter revisa la configuración renderizada de la app; resultado: 0 errores. Los YAML negativos de pruebas no forman parte del despliegue productivo analizado.
- La línea base tenía 48 filas HIGH en Trivy y 14 vulnerabilidades de Starlette en pip-audit. `reports/remediaciones.md` documenta los 12 CVE HIGH distintos y su tratamiento.

Para repetir todos los análisis fuera de Jenkins, preparar la etiqueta local:

```bat
docker build -t cafeteria:devsecops-local .
python scripts/security/scan.py --image cafeteria:devsecops-local
```

Necesita `.local/bin/kube-linter.exe` y kubectl, instalados por `Install-Tools.ps1`. El script retorna error si falla una herramienta o un control aplicable; solo acepta el caso npm N/A cuando faltan archivos npm y el error corresponde a esa ausencia.

## 7. Mostrar CI/CD (3 minutos)

Abrir http://localhost:8080/ e iniciar sesión con usuario `agustin`. Obtener su clave local:

```bat
type .local\jenkins-admin-password.txt
```

Entrar al job `cafeteria-devsecops`, abrir un build SUCCESS y mostrar:

1. Tests: 11 pasan y generan JUnit.
2. Código y manifiestos: npm, pip-audit, Semgrep y KubeLinter.
3. Build: imagen con tag del número de build y etiquetas OCI de commit/versión.
4. Trivy: si hay HIGH/CRITICAL, el job falla y no continúa al despliegue.
5. Deploy local: carga de la imagen mediante kind y aplicación bajo Kyverno.
6. Verificación HTTP del `/healthz`.
7. Artifactos archivados: todos los reportes del build.

Pulsar **Build Now / Construir ahora** para repetirlo. Las reglas/registros y bases de vulnerabilidades se descargan desde Internet: un resultado futuro puede cambiar si aparece un CVE. El job también consulta la rama local cada minuto. Para probar un cambio, hacer commit en la rama que estaba seleccionada al iniciar Jenkins; no basta editar un archivo sin commit.

El job lee `file:///proyecto`, una copia local del repo montada de solo lectura. `git push` respalda/entrega el código en GitHub; el polling de este laboratorio no depende de GitHub ni usa un webhook.

Si pasaron más de 24 h o el deploy falla con Unauthorized, volver a ejecutar `Start-Jenkins.ps1`. Renueva el token del ServiceAccount sin cambiar la contraseña. Kubernetes permite desplegar dentro del namespace y leer solo el Secret nombrado de la app; no concede administración global. El acceso al socket Docker sigue siendo un privilegio alto sobre el motor local y se usa únicamente en este laboratorio de confianza.

## 8. Prueba funcional automática y persistencia

```bat
python scripts/local/smoke.py --persistence
```

Valida las páginas, health, autorización del PIN, creación de pedido, cálculo de importe, agotado, corte, cambios de estado y resumen. Luego reemplaza solo el pod local de la app y comprueba que el pedido sigue en SQLite. Esperado: `PASS: 25 respuestas verificadas` y persistencia True. La prueba deja un pedido identificado como Demo DevSecOps para inspeccionarlo y restaura el corte/agotado anteriores. Ejecutarla fuera de la hora cercana a medianoche y con Jenkins sin desplegar.

Para correr los tests aislados en Windows:

```bat
python -m venv .local\test-env
.local\test-env\Scripts\pip install -r requirements-dev.txt
.local\test-env\Scripts\python -m pytest -q
```

## 9. Entregar y apagar

Entregar el PDF de `output/pdf/`, el enlace al repo y, si se admite adjunto, el ZIP de fuentes/evidencias. El ZIP no contiene herramientas descargadas, tokens, PIN, kubeconfigs ni bases de datos privadas. Si el repo queda privado, el docente debe tener acceso o se debe autorizar su publicación antes de compartirlo.

Para detener Jenkins y conservar historial:

```bat
docker compose -f jenkins/docker-compose.devsecops.yml stop
```

Para pausar el nodo y conservar sus datos locales:

```bat
docker stop cafeteria-devsecops-control-plane
```

Para volver: iniciar Docker Desktop, `docker start cafeteria-devsecops-control-plane` y ejecutar `Start-Jenkins.ps1`. No borrar el cluster durante una demostración de persistencia: su eliminación puede borrar la base de datos del laboratorio.
