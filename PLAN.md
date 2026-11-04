> **Actualización 04/11/2026:** el entregable 3 usa el laboratorio local, con Jenkins autenticado, kind, Kyverno y Falco. Ver [informe](ENTREGABLE_3.md) y [guía vigente](GUIA_ENTREGABLE_3.md). El contenido inferior conserva el historial anterior; las menciones a pendientes, falta de remoto o despliegue automático UCU son históricas.

# Plan para completar CI/CD de la cafeteria

Actualizado: 2026-10-27. Estado: completado.

## Objetivo
Cada commit en main pasa por tests, construye y publica una imagen en Docker Hub y despliega cafeteria-agustin en el namespace alumno-team10 de la UCU.

## Pasos completados
- [x] Leer CONTEXTO.md, README y configuracion existente.
- [x] Iniciar Docker Desktop y reparar la copia local de la imagen de Jenkins.
- [x] Guardar la credencial proporcionada por el usuario en jenkins/secrets/dockerhub-token.txt, excluida de Git y del build.
- [x] Comprobar Docker, Git, Python y kubectl desde el contenedor de Jenkins.
- [x] Levantar Jenkins en http://localhost:8080.
- [x] Confirmar JCasC, credenciales dockerhub/kubeconfig-ucu y job cafeteria.
- [x] Validar el Jenkinsfile con Jenkins.
- [x] Ejecutar el primer pipeline completo: build #1 SUCCESS.
- [x] Confirmar la imagen publicada, rollout y /healthz publico.
- [x] Probar commit -> polling -> nuevo despliegue: build #2 SUCCESS, Started by an SCM change.
- [x] Comprobar el titulo nuevo en la pagina publica y el PVC original.
- [x] Actualizar README y CONTEXTO.md.

## Evidencia
| Build | Disparo | Commit | Tests | Resultado | Imagen |
|---|---|---|---|---|---|
| 1 | Manual desde API local | a1c5a50 | 9 pasan | SUCCESS (83 s) | agustinnegreira/cafeteria:1 |
| 2 | Polling SCM automatico | 7d3388a | 9 pasan | SUCCESS (106 s) | agustinnegreira/cafeteria:2 |

- Jenkins: http://localhost:8080/job/cafeteria/.
- App: https://cafeteria-agustin-team4.reto-ucu.net.
- Deployment: generation=observedGeneration=3; updated=ready=available=1; imagen :2.
- /healthz publico: status ok.
- Titulo publico: Cafeteria / Pedidos para el recreo (con tildes y separador en HTML).
- PVC: cafeteria-agustin-data, Bound, 256Mi; volumen original pvc-c7330363-5b1b-4523-8509-cfe5fe5cae42.

## Uso y limites
- Cada commit en main se detecta aproximadamente cada minuto; no hace falta git push ni iniciar el build a mano.
- Jenkins corre mientras la laptop y Docker Desktop esten encendidos.
- Docker compose conserva el historial en jenkins_home.
- Solo se modificaron recursos propios con owner=agustin.
- El rollback por fallo de rollout esta configurado; no se provoco un fallo en el cluster para probarlo.
- Quedan avisos no bloqueantes: deprecacion Starlette/AnyIO en tests y builder clasico de Docker en Jenkins.
- La documentacion final esta guardada en el arbol de trabajo. No se hizo otro commit de documentacion que provocara un despliegue adicional.
