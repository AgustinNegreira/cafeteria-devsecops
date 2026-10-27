# Plan para completar CI/CD de la cafeteria

Actualizado: 2026-10-27. Punto de partida: CONTEXTO.md.

## Objetivo
Cada commit en main pasa por tests, construye y publica una imagen en Docker Hub y despliega cafeteria-agustin en el namespace alumno-team10 de la UCU.

## Pasos
- [x] Leer contexto, README, Jenkinsfile y configuracion de Jenkins.
- [x] Iniciar Docker Desktop y comprobar el motor.
- [ ] Usuario: crear token Read & Write en Docker Hub y guardarlo en jenkins/secrets/dockerhub-token.txt.
- [x] Construir Jenkins y comprobar Docker, Git, Python y kubectl desde su contenedor.
- [ ] Levantar Jenkins local en http://localhost:8080.
- [ ] Confirmar carga de configuracion, credenciales y job cafeteria.
- [ ] Ejecutar el pipeline y corregir errores encontrados.
- [ ] Confirmar version desplegada y /healthz publico.
- [ ] Probar commit -> polling -> nuevo despliegue con un cambio visible minimo.
- [ ] Actualizar README y CONTEXTO.md con resultados y comandos para cmd.

## Condiciones
- No leer ni imprimir el token de Docker Hub ni el PIN.
- Cambiar solo recursos propios (cafeteria-agustin, owner=agustin).
- Conservar SQLite y su PVC existente.
- Jenkins usa el repositorio local; no requiere remoto en GitHub.
- Verificar primero lo local antes de publicar o desplegar.

## Comprobaciones iniciales
- Docker Engine 29.9.1 disponible; no habia contenedores corriendo.
- Repositorio en main, sin remoto; CONTEXTO.md estaba sin versionar.
- Kubeconfig presente; archivo del token ausente al inicio.

- Tests locales: 9 passed (1 aviso de deprecacion de una dependencia).
- Cluster: Deployment 1/1, imagen :0.1, PVC Bound; /healthz publico respondio status ok.
- Snapshot local de Jenkins reparado reemplazando solo sus imagenes locales y descargando otra vez la base. El contenedor arranca correctamente.
- Pipeline: namespace explicito y mensaje de fallo corregido; secretos excluidos del build.

- Tests en la imagen Linux de Jenkins: 9 passed con Python 3.13.5.
- Pendiente al cerrar este punto de control: el usuario aun no guardo el archivo del token. Jenkins y el primer pipeline esperan ese archivo.
