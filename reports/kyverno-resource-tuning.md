# Ajuste de recursos de Kyverno — 17/11/2026

Se detuvieron los contenedores del laboratorio anterior `jenkins-devsecops` y `cafeteria-devsecops-control-plane`, conservando sus datos. Consumían aproximadamente 0,75 GiB y 1,45 GiB de RAM respectivamente. Jenkins y el registry del Lab 4 ya estaban detenidos; para el repaso se dejó activo solamente el nodo `cafeteria-lab4-control-plane`.

Después de detener el entorno anterior, se detectó consumo sostenido cercano al 300 % de CPU del nodo del Lab 4. Los auxiliares reports/background de Kyverno acumulaban 26/25 reinicios; los logs mostraban pérdida de liderazgo, timeouts y fallas de sincronización de caché. El proceso reports-controller encabezaba el consumo de CPU. Ambos conservaban el límite predeterminado de memoria de 128 MiB.

Se aumentó a 512 MiB el límite de memoria de esos dos controladores y a 128 MiB su request de memoria, manteniendo el request de CPU de 100m. El cambio está en `local/kyverno-values.yaml`, que también utiliza el script de arranque. Se aplicó mediante Helm sobre la misma versión del chart (3.9.2, Kyverno 1.19.2), generando la revisión 2 de la release kyverno. No se desactivaron controladores ni políticas.

En las mediciones posteriores, los cuatro Deployments quedaron 1/1 listos, los dos pods reemplazados estaban sin reinicios y el consumo total del nodo fue 29,81 % y luego 20,23 % de CPU, con aproximadamente 3,5 GiB de RAM. Docker cuenta 100 % como un núcleo lógico. Son mediciones puntuales posteriores al ajuste, no una prueba de estabilidad prolongada ni un perfil que demuestre por sí solo el mecanismo interno del problema.

Verificación de admisión con dry-run del servidor, sin crear pods:

- Manifiesto válido: aceptado.
- Imagen latest: rechazado por cafeteria-no-latest.
- Sin límite de CPU: rechazado por cafeteria-require-resources.
- UID 0: rechazado por cafeteria-non-root.
- allowPrivilegeEscalation=true: rechazado por cafeteria-no-privilege-escalation.

Cafetería respondió HTTP 200 con status ok. No se ejecutó un build nuevo de Jenkins; las evidencias históricas del pipeline se conservaron.
