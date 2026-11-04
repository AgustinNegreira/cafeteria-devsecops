> **Actualización 04/11/2026:** el entregable 3 usa el laboratorio local, con Jenkins autenticado, kind, Kyverno y Falco. Ver [informe](ENTREGABLE_3.md) y [guía vigente](GUIA_ENTREGABLE_3.md). El contenido inferior conserva el historial anterior; las menciones a pendientes, falta de remoto o despliegue automático UCU son históricas.

# Cafetería: guía para probar y defender el proyecto

Preparada el 27/10/2026 a partir del código y del despliegue real. Todos los comandos de esta guía son para **cmd de Windows**.

## 1. Dónde está cada cosa

| Qué querés abrir | Dirección |
|---|---|
| Código y repositorio Git local | C:\Users\AgustinNegreira\UCU\2do Semestre 2026\DevOps\cafeteria |
| Imágenes publicadas | https://hub.docker.com/r/agustinnegreira/cafeteria/tags |
| App para alumnos, en Kubernetes | https://cafeteria-agustin-team4.reto-ucu.net/ |
| Pantalla de la cafetería | https://cafeteria-agustin-team4.reto-ucu.net/cafeteria |
| API interactiva, Swagger | https://cafeteria-agustin-team4.reto-ucu.net/docs |
| Salud de la app | https://cafeteria-agustin-team4.reto-ucu.net/healthz |
| Jenkins y sus builds | http://localhost:8080/job/cafeteria/ |
| Arquitectura completa | [ARQUITECTURA.md](ARQUITECTURA.md) |

**Todavía no hay un remoto en GitHub.** El código está en Git, en tu disco. Jenkins clona ese repositorio local. Docker Hub aloja las imágenes ejecutables.

Estado comprobado al escribir la guía: builds #1 y #2 SUCCESS, 9 tests en cada uno, imagen desplegada agustinnegreira/cafeteria:2, pod 1/1 y PVC Bound. El segundo build fue iniciado por un cambio de SCM.

## 2. Para qué se usó el token

Jenkins necesita autenticarse en Docker Hub para hacer **docker push** y publicar una imagen nueva. La credencial dockerhub combina tu usuario con el token Read & Write. El pipeline lo entrega a docker login por la entrada estándar, hace push y cierra la sesión al completar esa etapa.

Tu sesión de Docker Desktop no se hereda automáticamente al cliente Docker que corre dentro de Jenkins. Por eso Jenkins usa su propia credencial, aunque se comunique con el motor Docker de la laptop.

El token está en jenkins/secrets/dockerhub-token.txt. Docker Compose lo monta como archivo en /run/secrets/dockerhub-token, y JCasC carga la credencial. Git y el contexto de build lo excluyen. Su valor no está en este documento ni en la imagen de la app.

Hay **tres accesos distintos**:

| Acceso | Para qué sirve |
|---|---|
| Token Docker Hub | Jenkins publica imágenes en tu cuenta |
| Kubeconfig UCU | Jenkins y kubectl se autentican ante la API de Kubernetes |
| PIN de cafetería | El encargado usa las operaciones de la app para gestionar pedidos |

Como la imagen de la app es pública, Kubernetes puede descargarla sin usar el token de publicación.

## 3. Preparación antes de la clase: 5 minutos

Abrí cmd y prepará las variables:

~~~bat
cd /d "C:\Users\AgustinNegreira\UCU\2do Semestre 2026\DevOps\cafeteria"
set "KUBECONFIG=%USERPROFILE%\.kube\ucu.yaml"
set "CAFE_NS=alumno-team10"
set "CAFE_URL=https://cafeteria-agustin-team4.reto-ucu.net"
~~~

Comprobá las herramientas:

~~~bat
git status
git log -3 --oneline
git remote -v
docker version
kubectl version --client
~~~

git remote -v no muestra nada porque todavía no configuramos GitHub. Si kubectl no se reconoce en esta terminal, agregá la instalación comprobada al PATH de esa ventana:

~~~bat
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Kubernetes.kubectl_Microsoft.Winget.Source_8wekyb3d8bbwe;%PATH%"
kubectl version --client
~~~

Si Docker está apagado, iniciá Docker Desktop y esperá a que el motor esté listo:

~~~bat
docker desktop start
docker info
docker compose -f jenkins/docker-compose.yml up -d
docker compose -f jenkins/docker-compose.yml ps
~~~

Jenkins debería aparecer Up, publicado en 127.0.0.1:8080. Si cambiás su Dockerfile o los plugins, usá up -d --build.

Comprobá lo desplegado:

~~~bat
kubectl -n %CAFE_NS% get deployment,pods,service,pvc,apisixroute -l owner=agustin
curl.exe -fsSk "%CAFE_URL%/healthz"
~~~

Esperado: Deployment 1/1, pod Running 1/1, PVC Bound y respuesta {"status":"ok"}. El parámetro -k se usa por el certificado vencido observado en la infraestructura del curso; la conexión sigue siendo HTTPS, pero curl omite validar el certificado.

Abrí cuatro pestañas: alumno, cafetería, Swagger y Jenkins. Usá el PIN real del cluster, guardado en .pin-cluster.txt. El 1234 documentado para desarrollo local no garantiza acceso al cluster.

Para ver a dos alumnos distintos, usá perfiles o ventanas privadas diferentes. El nombre se guarda en localStorage; varias pestañas del mismo origen comparten ese almacenamiento.

## 4. Recorrido funcional: hacer y preparar un pedido

### Prepará un recreo que sirva para la demostración

Los recreos se evalúan con la fecha y hora actuales de Uruguay. Elegí uno futuro que siga abierto. También podés crear desde la pantalla cafetería un recreo llamado Demo Docente, aproximadamente 30 minutos más tarde, dentro del día actual.

Anotá el valor original de Cortar pedidos. Para este ejemplo usá 15 minutos. Un recreo dentro de 30 minutos todavía permite pedir durante unos 15 minutos. Cerca de medianoche elegí una hora futura del mismo día; los tests automatizados permiten demostrar la regla sin depender del reloj real.

### Hacé el pedido

1. En la pantalla del alumno, ingresá un nombre identificable, por ejemplo Demo Docente 27-10.
2. Elegí el recreo preparado.
3. Pedí 2 cafés y 1 medialuna, o productos disponibles equivalentes.
4. Revisá el total y pulsá Hacer pedido.
5. Anotá el número del pedido.

**Esperado:** aparece pendiente en Mis pedidos. Con los precios de la semilla, 2 cafés de $90 y una medialuna de $45 suman $225. Si cambió el catálogo, usá los precios que muestra la app.

**Qué explicar:** el navegador manda alumno, recreo y cantidades. El backend consulta los precios en SQLite, calcula el total y guarda el pedido y sus líneas dentro de una transacción.

### Preparalo y entregalo

1. En la pantalla cafetería, buscá el mismo número y nombre.
2. Mostrá el grupo del recreo y el resumen Para preparar.
3. Pulsá Listo.
4. Volvé al alumno y esperá hasta 10 segundos.
5. Marcá Entregado desde cafetería.
6. Activá Mostrar entregados para volver a ver la tarjeta.

**Esperado:** el estado cambia de pendiente a listo y luego a entregado. La pantalla de cafetería refresca pedidos y resumen cada 5 segundos; el alumno refresca cada 10. Es polling HTTP.

Mis pedidos devuelve los últimos 20 pedidos de ese nombre, incluso de días anteriores. La pantalla de cafetería y el resumen se concentran en el día actual.

## 5. Probar el corte configurable y demostrar que lo controla el backend

Usá el recreo de Demo Docente, aproximadamente 30 minutos más tarde:

1. Con X=15, comprobá que se puede pedir.
2. En cafetería, cambiá Cortar pedidos a 45 y guardá.
3. Volvé al alumno; recargá o esperá su refresco.
4. El recreo debe aparecer cerrado: el corte quedó 15 minutos antes de la hora actual.
5. Abrí Swagger, desplegá POST /api/pedidos y pulsá Try it out.
6. Mandá un pedido para ese mismo recreo, usando IDs reales.

Consultá los IDs en GET /api/recreos y GET /api/productos. Este cuerpo es un ejemplo: reemplazá 999 por el ID del recreo de demostración y verificá que el producto 1 exista y esté disponible.

~~~json
{
  "alumno": "Demo Backend",
  "recreo_id": 999,
  "items": [
    {"producto_id": 1, "cantidad": 1}
  ]
}
~~~

**Esperado:** HTTP 409 y un mensaje que indica hasta qué hora se aceptaban pedidos. Mandarlo por Swagger saltea la interfaz y demuestra que el backend hace cumplir la regla.

Ahora volvé a X=15 y guardá. Sin reconstruir la imagen ni reiniciar el pod, repetí el pedido mientras siga dentro del horario permitido: debe devolver 201.

Para demostrar que no hubo despliegue, compará antes y después:

~~~bat
kubectl -n %CAFE_NS% get pods -l app=cafeteria-agustin
kubectl -n %CAFE_NS% get deployment cafeteria-agustin -o jsonpath="{.spec.template.spec.containers[0].image}"
~~~

El nombre del pod y la imagen deberían seguir iguales. X vive en la tabla config; la app lo lee al procesar las solicitudes. MINUTOS_CORTE solo inicializa ese valor cuando todavía no existe.

Restaurá el valor original de X al terminar.

## 6. Probar los extras y el PIN

| Prueba | Acción | Resultado esperado |
|---|---|---|
| Agotados en la interfaz | Marcar Café como agotado en cafetería y refrescar alumno | Aparece agotado y no permite agregarlo |
| Agotados en backend | Intentar POST /api/pedidos con ese producto y un recreo abierto | 409 indicando producto agotado |
| Recuperar disponibilidad | Desmarcar agotado | El producto vuelve a poder pedirse |
| Resumen diario | Comparar el resumen antes y después de un pedido | Aumentan cantidad de pedidos, cantidades por producto y total |
| Recreos configurables | Crear un recreo sin pedidos y borrarlo | Aparece y luego desaparece |
| Recreo con pedidos | Intentar borrar el usado en la demo | 409; no se permite borrar un recreo referenciado |
| PIN | Abrir GET /api/cafeteria/pedidos en Swagger sin x-pin o con uno incorrecto | 401 |
| PIN correcto | Completar el parámetro de cabecera x-pin en la operación protegida | Acceso permitido |

El resumen suma pedidos de hoy de todos los estados; no hay pagos ni caja cobrada. No esperes que el total general sea solo el de tu pedido: pueden existir otros pedidos del día.

El alumno se identifica por nombre, sin autenticación. El PIN es una protección básica para la gestión; no hay cuentas de usuario ni aislamiento seguro entre alumnos.

## 7. Mostrar la API y los tests

Swagger muestra los contratos de la API. Podés enseñar:

- GET /api/productos y GET /api/recreos: datos públicos.
- POST /api/pedidos: creación y validaciones.
- GET /api/pedidos?alumno=...: consulta por nombre.
- Operaciones /api/cafeteria/...: requieren cabecera X-PIN.
- GET /healthz: abre una conexión a SQLite y ejecuta SELECT 1.

Los 9 tests existentes cubren:

| Caso | Qué comprueba |
|---|---|
| Pedido a tiempo | Aceptación y cálculo del total |
| Pedido fuera de hora | Rechazo 409 con hora de corte clara |
| Cambio de X | Aplica sin reinicio |
| Producto agotado | El backend lo rechaza |
| PIN | Acceso protegido |
| Agrupación | Pedidos separados por recreo y próximo recreo identificado |
| Estado | El alumno ve el cambio hecho por cafetería |
| Resumen | Totales y cantidades por producto |
| Salud | Respuesta de /healthz |

Para ejecutarlos localmente con el entorno ya instalado:

~~~bat
.venv\Scripts\python.exe -m pytest -v
~~~

Los tests usan bases temporales y un reloj fijado; no necesitan que en ese momento sea antes del recreo y no modifican la base del cluster. En Jenkins, abrí un build y su reporte Test Result / Resultados de pruebas.

## 8. Mostrar Docker y Kubernetes

En la laptop:

~~~bat
docker ps
docker images agustinnegreira/cafeteria
docker inspect jenkins-cafeteria --format "{{json .Mounts}}"
~~~

Qué explicar: docker ps muestra Jenkins local. El contenedor de producción de la app está en un nodo de la UCU, por eso no aparece entre los contenedores locales. Las imágenes construidas sí quedan en el motor de Docker Desktop.

En el cluster:

~~~bat
kubectl -n %CAFE_NS% get deployment,pods,service,pvc,configmap,secret,apisixroute -l owner=agustin
kubectl -n %CAFE_NS% describe deployment cafeteria-agustin
kubectl -n %CAFE_NS% logs deployment/cafeteria-agustin --tail=30
kubectl -n %CAFE_NS% get apisixroute cafeteria-agustin -o yaml
~~~

El listado de Secrets muestra nombres y cantidad de claves; no es necesario mostrar su contenido. La etiqueta owner=agustin limita estos listados a nuestros recursos en el namespace compartido.

Mostrá los archivos de k8s y relacioná cada uno con el recurso real. La explicación de cada componente, puertos, volúmenes y credenciales está en ARQUITECTURA.md.

## 9. Probar persistencia y recuperación de un pod

Esta prueba provoca una interrupción breve de nuestra app porque existe una sola réplica. Hacela después de anotar un pedido y su estado.

1. Mostrá el pedido en el alumno y su número.
2. Anotá el pod y el volumen:

~~~bat
kubectl -n %CAFE_NS% get pods -l app=cafeteria-agustin
kubectl -n %CAFE_NS% get pvc cafeteria-agustin-data
~~~

3. Eliminá únicamente el pod de nuestra app:

~~~bat
kubectl -n %CAFE_NS% delete pod -l app=cafeteria-agustin
kubectl -n %CAFE_NS% get pods -l app=cafeteria-agustin -w
~~~

4. Cuando el nuevo pod esté Running y 1/1, cortá la observación con Ctrl+C.
5. Recargá el alumno y comprobá que el pedido sigue.
6. Volvé a listar el PVC: debe seguir Bound y conservar el mismo volumen.

**Qué explicar:** el Deployment, mediante su ReplicaSet, reemplaza el pod. El disco se pide con un PVC y se monta en /data; la base no depende del sistema de archivos descartable del contenedor. No borres el PVC para esta demostración.

Esto demuestra persistencia ante reemplazo del pod. No demuestra alta disponibilidad ni recuperación ante pérdida del nodo o del disco.

## 10. Probar el ciclo completo de CI/CD

Antes de empezar, comprobá que Jenkins esté libre y anotá la imagen actual:

~~~bat
git status --short
kubectl -n %CAFE_NS% get deployment cafeteria-agustin -o jsonpath="{.spec.template.spec.containers[0].image}"
~~~

1. Abrí app/static/index.html en tu editor.
2. Cambiá solo el texto de la etiqueta title, por ejemplo agregando Demo docente.
3. Guardá el archivo.
4. Mostrá el diff y creá un commit solo de ese archivo:

~~~bat
git diff -- app/static/index.html
git add app/static/index.html
git commit -m "Demo docente: actualizar titulo"
~~~

5. Abrí Jenkins y esperá el siguiente chequeo de SCM, aproximadamente un minuto más el tiempo del pipeline.
6. Mostrá que el nuevo build dice Started by an SCM change.
7. Seguí sus etapas:

| Etapa | Qué hace | Evidencia |
|---|---|---|
| Checkout | Clona main desde file:///proyecto | Commit en el log |
| Tests | Ejecuta pytest y publica JUnit | 9 tests |
| Build | Construye agustinnegreira/cafeteria:N | Log de docker build |
| Push | Se autentica con token y publica la imagen | Tag N en Docker Hub |
| Deploy | Aplica manifiestos y espera rollout | Pod nuevo con imagen :N |
| Verificacion | Consulta /healthz por la URL pública | status ok |

8. Esperá SUCCESS.
9. Volvé a consultar la imagen con kubectl.
10. Recargá la página pública y comprobá el título de la pestaña.
11. Mostrá que los pedidos anteriores siguen presentes.

No hace falta git push: el SCM del job es el repositorio local montado de solo lectura en /proyecto. Jenkins trabaja en su propio checkout. Guardar un archivo sin hacer commit no alcanza.

El número de imagen es el número del build; puede haber saltos si algún build falló antes de publicar.

## 11. Demostración opcional: un test fallido frena la entrega

El objetivo es demostrar un filtro de CI. Elegí un momento sin otros cambios o commits simultáneos.

1. Anotá la imagen actual del cluster.
2. En tests/test_api.py, dentro de test_pedido_a_tiempo_se_acepta, cambiá solo la aserción de status 201 a 418.
3. Creá un commit únicamente de ese archivo:

~~~bat
git diff -- tests/test_api.py
git add tests/test_api.py
git commit -m "Demo temporal: forzar fallo de un test"
~~~

4. Esperá el build automático.
5. Mostrá Tests en rojo. Build, Push y Deploy deben quedar sin ejecutar.
6. Consultá otra vez la imagen del cluster: debe seguir siendo la anterior.

Restaurá el test. Si el último commit todavía es exactamente el de esta demostración, podés revertirlo así:

~~~bat
git log -1 --oneline
git revert --no-edit HEAD
~~~

Esperá el nuevo build exitoso. No dejes el test roto. Si hubo otros commits, revertí por su hash el de la demostración.

Esta prueba es distinta del rollback de Kubernetes: aquí el fallo ocurre antes de desplegar y el cluster no se toca.

## 12. Ejecutar una copia de la app solo en la laptop

Esto sirve para practicar sin escribir pedidos de prueba en la base del cluster. Es un contenedor adicional, separado de Jenkins y de la app UCU:

~~~bat
docker run -d --name cafeteria-demo -p 127.0.0.1:8000:8000 -v cafeteria-demo-data:/data -e CAFETERIA_PIN=1234 -e ZONA_HORARIA=America/Montevideo agustinnegreira/cafeteria:2
~~~

Abrí http://localhost:8000 y http://localhost:8000/cafeteria. En esta copia el PIN es 1234 porque lo especificaste al arrancar. Los pedidos van al volumen local cafeteria-demo-data; no son los pedidos de Kubernetes. El puerto 8000 debe estar libre y el nombre cafeteria-demo no debe existir todavía.

Si ya lo creaste antes:

~~~bat
docker start cafeteria-demo
~~~

Para detener y retirar ese contenedor conservando sus datos:

~~~bat
docker stop cafeteria-demo
docker rm cafeteria-demo
~~~

Para correr desde Python, con el entorno ya instalado:

~~~bat
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
~~~

Esta tercera variante usa data/cafeteria.db de la carpeta local. Elegí una sola variante local a la vez si ambas usan el puerto 8000.

## 13. Orden sugerido para la exposición: 15 a 20 minutos

| Tiempo orientativo | Qué mostrar | Qué demostrar |
|---|---|---|
| 0–2 min | Problema y arquitectura | Dónde corre cada componente |
| 2–6 min | Alumno y cafetería | Pedido, agrupación y estados |
| 6–9 min | Cambio de X + Swagger | Regla en backend y configuración sin deploy |
| 9–11 min | Agotados, resumen y tests | Extras y validación automática |
| 11–15 min | Commit y Jenkins | Integración y despliegue automáticos |
| 15–18 min | Pod nuevo y pedido anterior | Persistencia |
| 18–20 min | Decisiones y límites | Qué simplificamos y cómo escalaríamos |

La prueba del test roto se puede reservar para preguntas o hacerla antes de clase. Cada pipeline agrega tiempo; los tiempos de la tabla son aproximados.

Guion corto para decir en voz alta:

> La app permite pedir antes del recreo y preparar por tanda. FastAPI sirve las páginas y aplica las reglas, y SQLite guarda los datos. La app corre en un pod de la UCU con un volumen persistente. En mi laptop, Jenkins detecta commits, corre tests, construye la imagen y la publica en Docker Hub. Después actualiza Kubernetes y verifica la URL pública. El corte se cambia en la base al instante, sin generar una imagen nueva.

## 14. Después de la demo y diagnóstico

Restaurá el corte original y los productos que hayas marcado como agotados. Podés marcar entregados los pedidos de demostración. Un recreo con pedidos no se puede borrar desde la API actual. No hay una función para eliminar pedidos; evitá borrar la base para limpiar la demo.

Si la pantalla tarda en actualizarse, recordá los intervalos de polling o recargá.

~~~bat
docker compose -f jenkins/docker-compose.yml ps
docker logs --tail=80 jenkins-cafeteria
kubectl -n %CAFE_NS% get pods -l app=cafeteria-agustin
kubectl -n %CAFE_NS% describe pod -l app=cafeteria-agustin
kubectl -n %CAFE_NS% logs deployment/cafeteria-agustin --tail=60
~~~

| Síntoma | Revisar |
|---|---|
| localhost:8080 no abre | Docker y contenedor Jenkins |
| Jenkins no detecta cambios | Commit en main y polling; archivos guardados sin commit no alcanzan |
| 401 en operaciones de cafetería | PIN y cabecera X-PIN |
| 409 al pedir | Corte de hora o producto agotado; leer detail |
| Recreo ya cerrado | Hora de Uruguay, X y hora del recreo |
| Pod Pending / ContainerCreating | describe pod: recursos, montaje y descarga |
| Pod ImagePullBackOff | Tag publicado y acceso a Docker Hub |
| Breve error durante deploy | Recreate baja el pod anterior antes de levantar el nuevo |
| Certificado inválido | Certificado de la infraestructura UCU; usar la URL HTTPS del proyecto |
| Se cortó la laptop | La app UCU sigue corriendo; Jenkins deja de entregar versiones nuevas |

Las pruebas de borrado del pod y de test fallido están documentadas para tu demostración; no fueron ejecutadas al redactar esta guía. La verificación real previa fue el ciclo exitoso de los builds #1 y #2.

Documentación fuente del token: https://docs.docker.com/security/access-tokens/personal-access-tokens/
