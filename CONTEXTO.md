# Contexto para seguir este trabajo (handoff a otra IA)

Última actualización: 2026-10-27. El detalle original corresponde al 21/10; el punto de control siguiente tiene prioridad para retomar.

## Punto de control del 27/10/2026

Plan activo: `PLAN.md`. Se retomo la puesta en marcha de Jenkins.

- Docker Desktop iniciado; motor 29.9.1 disponible.
- La imagen de Jenkins se construyo y se probo su arranque, acceso al socket de Docker, lectura de `main` via `file:///proyecto`, Python 3.13.5 y kubectl 1.29.5.
- Se encontraron archivos vacios en el snapshot local de la imagen oficial de Jenkins. Reconstruir sin cache y reiniciar Docker no bastaron. Se eliminaron solo las imagenes locales de Jenkins y se volvio a descargar la base; eso recupero los archivos y el arranque. No se borraron los datos de la app ni su imagen.
- Los 9 tests pasaron en Windows y tambien dentro de Linux con la imagen real de Jenkins (clon temporal del repo). Hay un aviso de deprecacion de Starlette/AnyIO, sin fallos.
- El cluster se consulto: Deployment propio 1/1 con `agustinnegreira/cafeteria:0.1`, PVC Bound, URL publica `/healthz` devuelve `status: ok`.
- `Jenkinsfile` ahora fija `NAMESPACE=alumno-team10` en los comandos kubectl. El mensaje general de fallo ya no afirma que siempre se recupero la version anterior.
- `jenkins/.dockerignore` excluye `secrets/`. README explica los comandos cmd y que Jenkins toma commits locales, sin GitHub ni git push.
- **Falta el token de Docker Hub**: `jenkins/secrets/dockerhub-token.txt` todavia no existe. La carpeta `secrets` ya esta creada. Se le dieron al usuario los pasos para generar un token Read & Write; no leerlo ni imprimirlo.
- **Jenkins aun no se levanto, no se ejecuto ningun pipeline y no se publico una version nueva.** No marcar CI/CD como terminado.

Siguiente accion cuando el usuario guarde el archivo: `docker compose -f jenkins/docker-compose.yml up -d --build`, verificar carga de JCasC/job/credenciales sin mostrar valores y ejecutar el primer build. Luego comprobar despliegue y probar el polling con un commit visible minimo.
## Quién y qué

- Agustín, curso de **DevOps de la UCU** (2do semestre 2026). Escribe en español rioplatense.
- Tarea: **Proyecto 1 "pedidos de la cafetería"**: construir la app y desplegarla en el **cluster Kubernetes de la UCU** con **CI/CD en Jenkins**.
- Hay **4 compañeros haciendo el mismo flujo completo por separado**, en el **mismo namespace**. Después comparan entre todos.

### Cómo quiere trabajar Agustín

- Quiere **entender el porqué**. Kubernetes y Jenkins tienen que tener sentido para esta app: nada metido "porque sí". Explicar corto y aplicado a la cafetería.
- Quiere que **la IA implemente** y él **revisa** los manifiestos. No quiere escribir YAML a mano.
- **Menor trabajo posible**, pero cumpliendo toda la consigna, extras incluidos.
- No va a preguntarle nada al profe. El kubeconfig menciona un `alumno.md` que no tenemos: lo que haga falta se averigua mirando el cluster.
- Su terminal suele ser **cmd**, no PowerShell. Darle comandos en sintaxis de cmd (`set VAR=...`, no `$env:VAR`).

## Consigna (la foto del enunciado)

> Los alumnos entran desde el celular antes del recreo, eligen qué quieren y la cafetería lo tiene pronto a la hora del recreo.

- **Roles**: alumno (hace y consulta sus pedidos); cafetería (ve los pedidos agrupados por recreo y los marca como listos o entregados).
- **MVP**: catálogo de productos inventado con precio; recreos configurados con hora de inicio; pedido con varios productos; ver el estado del pedido; pantalla de la cafetería con todo lo pendiente del próximo recreo.
- **Condiciones**: un pedido se acepta solo hasta X minutos antes del recreo. **X es configurable sin volver a desplegar.** Pasado ese límite, la app no deja pedir y lo dice claro. **La regla la hace cumplir el backend**, no el frontend.
- **Extras**: resumen de ventas del día, productos agotados.

La foto no habla de Docker, Kubernetes ni Jenkins. Eso lo pidió Agustín. Es el objetivo del curso y por eso le dieron el kubeconfig.

## Estado

| Paso | Estado |
|---|---|
| App con todo lo de la consigna, extras incluidos | ✅ 9 tests pasan, probada en el navegador |
| Imagen Docker, probada en local con volumen | ✅ |
| Imagen publicada en Docker Hub (repo público, aprobado por Agustín) | ✅ `agustinnegreira/cafeteria:0.1` |
| Desplegada a mano en el cluster, con URL pública | ✅ https://cafeteria-agustin-team4.reto-ucu.net |
| Repo git + primer commit | ✅ rama `main`, commit `5d99e6b`, sin remoto |
| Jenkins (CI/CD) | ⏳ **Archivos escritos pero NUNCA ejecutados** (ver abajo) |

## La app (`cafeteria/`)

- **FastAPI + SQLite en un solo contenedor.** La API sirve también las dos páginas: HTML + JS plano, sin build.
  - `app/main.py`: endpoints y reglas.
  - `app/db.py`: esquema y semilla (10 productos y 4 recreos: 10:00, 12:00, 16:00 y 20:30).
  - `app/static/`: `index.html` (alumno), `cafeteria.html`, `style.css`.
  - `tests/test_api.py`: pytest con el reloj fijado mediante un monkeypatch de `main.ahora`.
- **Rutas**:
  - `/`: página del alumno. No tiene login: el nombre se guarda en `localStorage`.
  - `/cafeteria`: pantalla de la cafetería. Usa un PIN que viaja en el header `X-PIN`.
  - `/api/...`: la API.
  - `/healthz`: para las probes de Kubernetes.
  - `/docs`: Swagger.
- **Regla de corte**: `POST /api/pedidos` devuelve **409** con un mensaje claro si ya pasó el límite.
- **X** vive en la tabla `config` de la base y se edita desde la pantalla de la cafetería (`PUT /api/cafeteria/config`). No está en un ConfigMap a propósito: cambiar un ConfigMap obliga a reiniciar el pod, y eso choca con "sin volver a desplegar".
- **Variables de entorno**:
  - `DB_PATH`: en la imagen vale `/data/cafeteria.db`.
  - `CAFETERIA_PIN`: por defecto `1234`. En el cluster sale de un Secret.
  - `MINUTOS_CORTE`: solo el valor inicial de X; por defecto 15.
  - `ZONA_HORARIA`: `America/Montevideo`. Los pods corren en UTC.
- **Tiempo real por polling**: la cafetería se refresca cada 5 s y el alumno cada 10 s.
- **Correr en local**:

  ```
  .venv/Scripts/uvicorn app.main:app --port 8000
  ```

  Hay una configuración `cafeteria` en `DevOps/.claude/launch.json` para el navegador de Claude Desktop. La base local está en `cafeteria/data/` (ignorada por git).

## El cluster de la UCU (averiguado mirándolo)

- **Kubeconfig**: `C:\Users\AgustinNegreira\.kube\ucu.yaml`, copiado de `Downloads\team4.kubeconfig`.
  - Ojo: el archivo se llama "team4" pero adentro es **team10** (ServiceAccount `team10`, namespace `alumno-team10`). Existe también un namespace `alumno-team4` aparte. Los compañeros también despliegan en `alumno-team10`.
- **kubectl** está instalado con winget. En terminales abiertas antes de instalarlo no está en el PATH. Ruta completa:
  `C:\Users\AgustinNegreira\AppData\Local\Microsoft\WinGet\Packages\Kubernetes.kubectl_Microsoft.Winget.Source_8wekyb3d8bbwe\kubectl.exe`
- **Versión**: el server es v1.29.5.
- **Permisos**: solo dentro del namespace (Deployments, Services, PVC, Secrets, ConfigMaps, Ingress, `apisixroutes`). Puede leer nodos, namespaces y storageclasses. No puede listar ingressclasses.
- **Cuota del namespace, compartida por los 5**: 15 pods, 2 CPU / 3 GiB de requests, 4 CPU / 6 GiB de limits, **3 PVC**, 5 GiB de storage, 0 LoadBalancers.
  - **Los PVC están 3/3 usados**: uno de `cantina` (compañero), uno del Postgres de `pedidos-cafeteria` (compañero) y uno nuestro.
- **LimitRange por defecto**: requests de 100m / 128Mi y limits de 500m / 512Mi.
- **Storage**: la StorageClass por defecto es `local-path`.
- **Exposición a internet**:
  - DNS comodín `*.reto-ucu.net` → 167.62.144.208.
  - **Solo funciona por HTTPS.** Por http (puerto 80) contesta un Apache ajeno, con la página "Coro Estudiantil UCU".
  - Adelante hay un nginx y después **APISIX**, que es el ingress controller. Se usa el CRD **`ApisixRoute`** (apiVersion `apisix.apache.org/v2`), que es lo que usan los compañeros y funciona.
  - El certificado comodín de Let's Encrypt **está vencido desde el 2026-09-27**: el navegador avisa, y con curl hay que usar `-k`.
- **No hay registry en el cluster.** `registry.reto-ucu.net` es solo el comodín que cae en el Apache. Por eso usamos Docker Hub.
- **Recursos de compañeros: NO TOCAR.**
  - `cantina`: corre sobre `python:3.12-slim` con el código montado desde ConfigMaps. No construye una imagen propia, y es un buen contraste para la charla.
  - `pedidos-cafeteria-api`, `pedidos-cafeteria-web` (2 réplicas) y un Postgres en StatefulSet.

### Lo nuestro en el cluster

- Todo se llama **`cafeteria-agustin`** y lleva la etiqueta **`owner: agustin`**.

  ```
  kubectl get all,pvc,cm,secret,apisixroute -l owner=agustin
  ```

- **Manifiestos** en `k8s/`:
  - `deployment.yaml`: 1 réplica, estrategia `Recreate` porque SQLite está sobre un PVC RWO, probes en `/healthz`, recursos 50m/96Mi → 300m/256Mi. La imagen dice `image: IMAGEN`, un placeholder que se reemplaza con `sed`.
  - `service.yaml`: ClusterIP 80 → 8000.
  - `configmap.yaml`: `ZONA_HORARIA` y `MINUTOS_CORTE`.
  - `pvc.yaml`: 256Mi, `local-path`.
  - `apisixroute.yaml`: host `cafeteria-agustin-team4.reto-ucu.net`. El nombre sigue la convención `cantina-team4` de un compañero.
- **Secret `cafeteria-agustin`**, clave `CAFETERIA_PIN`.
  - Se creó con `kubectl create secret` y **no está en git**.
  - El PIN real está en `cafeteria/.pin-cluster.txt` (ignorado por git). **No lo imprimas en el chat.**
- **Despliegue manual de referencia**: está en el README, sección "El despliegue".

## Entorno local

- **Sistema**: Windows 11 Enterprise (laptop corporativa). Hay Git Bash y PowerShell 5.1. Python 3.12 en `cafeteria/.venv`.
- **Docker Desktop 4.96 sobre WSL2.** Se instaló en esta sesión y se reinició la máquina.
  - **Tiene que estar abierto**: al cerrar la sesión estaba **apagado**, y por eso falló el build de Jenkins con `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`.
- **Docker Hub**: usuario **`agustinnegreira`**. Inició sesión en Docker Desktop con GitHub. El push manual funcionó con esa sesión.
- **Git**: el repo es solo `cafeteria/`. La identidad está configurada a nivel repo, igual que en sus otros repos del curso: `Agustin Negreira <anegreira2004@gmail.com>`. `core.autocrlf=false`.
  - Los commits hechos por la IA llevan la línea `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Ignorado por git**: `.pin-cluster.txt`, `jenkins/secrets/`, `data/` y `.venv/`.
- Hay otras carpetas del curso en `DevOps/` (`notes-api`, `carpincho-express`, `jenkins`). **No tienen relación con este proyecto.** Agustín se molestó cuando la IA las tomó como referencia sin avisar.

## Jenkins: lo que falta (siguiente paso)

### Diseño (decidido y explicado a Agustín)

- **Jenkins corre en Docker en la laptop**, haciendo de "servidor de CI". No va en el cluster: la cuota se comparte entre 5 y ya no quedan PVC, y construir imágenes dentro de un pod pide privilegios que el namespace no da.
- **Limitaciones aceptadas**: solo funciona con la laptop prendida, y como GitHub no puede avisarle, hace polling.
- **Pipeline** (`Jenkinsfile`): Tests (pytest + reporte JUnit) → Build (`agustinnegreira/cafeteria:$BUILD_NUMBER`) → Push (credencial `dockerhub`) → Deploy (credencial `kubeconfig-ucu`, `kubectl apply`, `rollout status`, `rollout undo` si falla) → Verificación (`curl -fsSk` a la URL pública + `/healthz`).
- **Archivos en `jenkins/`**:
  - `Dockerfile`: `jenkins/jenkins:lts` + docker-cli + python3/venv + kubectl v1.29.5. Le agrega a jenkins el grupo root para el socket y declara `safe.directory /proyecto`. `JAVA_OPTS` lleva `runSetupWizard=false` y `ALLOW_LOCAL_CHECKOUT=true`.
  - `plugins.txt`: workflow-aggregator, pipeline-stage-view, git, credentials-binding, junit, configuration-as-code, job-dsl.
  - `casc.yaml` (JCasC):
    - Jenkins **sin login**, a propósito: escucha solo en 127.0.0.1.
    - Credenciales desde archivos de Docker secrets: `kubeconfig-ucu` (tipo file, `${readFileBase64:/run/secrets/kubeconfig}`) y `dockerhub` (usernamePassword, `${readFile:/run/secrets/dockerhub-token}`).
    - Job `cafeteria` definido con Job DSL: SCM `file:///proyecto`, rama `*/main`, `pollSCM('* * * * *')`.
  - `docker-compose.yml`:
    - Puerto `127.0.0.1:8080`.
    - Volúmenes: `jenkins_home`, `/var/run/docker.sock` (Docker outside of Docker) y el repo en `/proyecto:ro`.
    - Secrets: `kubeconfig` desde `${USERPROFILE}/.kube/ucu.yaml` y `dockerhub-token` desde `./secrets/dockerhub-token.txt`.

### Pasos pendientes

1. **Abrir Docker Desktop** y esperar a que diga "running".
2. **Agustín crea el token de Docker Hub**: Account settings → Personal access tokens, permiso Read & Write. Lo guarda en `cafeteria/jenkins/secrets/dockerhub-token.txt`.
   - La IA **no** crea tokens, **no** lo lee y **no** lo imprime.
   - Al cerrar la sesión **el archivo todavía no existía**.
3. Desde `cafeteria/`, levantar Jenkins:

   ```
   docker compose -f jenkins/docker-compose.yml up -d --build
   ```

4. **Verificar** en http://localhost:8080 que JCasC cargó las 2 credenciales y el job `cafeteria`. Si falla, revisar `docker logs jenkins-cafeteria`.
5. **Primer build** (manual o esperando el polling). Al terminar, la imagen del Deployment debería pasar de `:0.1` a `:<número de build>`.
6. **Probar el ciclo completo**: cambiar algo visible (por ejemplo un precio en `app/db.py`; ojo, la semilla solo carga con la base vacía, así que mejor un texto del HTML), hacer commit y ver que en menos de un minuto queda publicado.

### Riesgos a revisar (no probados todavía)

- **Sintaxis de JCasC**: el tipo `file` de credencial, el resolver `readFileBase64` y el bloque `pipelineTriggers/pollSCM` de Job DSL.
- **Permisos del socket** de Docker Desktop dentro del contenedor (`usermod -aG root jenkins`).
- **`${USERPROFILE}`** en el path del secret del compose, en Windows.
- **Python de la imagen de Jenkins** (Debian trixie trae Python 3.13) con las versiones fijadas en `requirements.txt` (fastapi 0.115.6, uvicorn 0.34.0, tzdata 2025.2) y en `requirements-dev.txt` (pytest 9.1.1, httpx 0.28.1).
- **Checkout local**: el Git plugin desde `file:///proyecto` con `safe.directory`.
- **Puerto 8080**: el `DevOps/.mcp.json` tiene un MCP de Jenkins apuntando a `localhost:8080/mcp-server/mcp`. Necesitaría el plugin `mcp-server` y auth. No está configurado y no es necesario.

## Demos pensadas para la defensa y la comparación con compañeros

- **Persistencia**: `kubectl delete pod -l app=cafeteria-agustin` → Kubernetes lo recrea y los pedidos siguen ahí gracias al PVC.
- **Tests como filtro**: romper `test_pedido_pasado_el_corte_se_rechaza_con_mensaje_claro` → el pipeline queda en rojo y el cluster sigue con la versión anterior.
- **X sin redespliegue**: cambiar X desde `/cafeteria` → aplica al instante.
- **Despliegue continuo**: commit → nueva versión publicada sin tocar el cluster a mano.

## Decisiones de diseño (para defender)

- **SQLite y 1 réplica.** La carga de una cafetería escolar no justifica más, y SQLite no admite varios pods escribiendo. Costo: unos segundos sin servicio en cada deploy (`Recreate`). Si hiciera falta escalar: Postgres + varias réplicas + `RollingUpdate`.
- **Sin autoescalado, sin Helm y sin una base aparte**, a propósito.
- **Seguridad mínima**: el alumno no tiene login (solo nombre) y la cafetería usa un PIN. Un Secret es base64, no cifrado.
- **X en la base y no en un ConfigMap**, por el requisito de "sin volver a desplegar".
