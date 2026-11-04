# Plan Entregable 3 - cierre de implementación

Actualizado: 04/11/2026. Alcance autorizado: laboratorio local completo, evidencias, repositorio y material de entrega.

- [x] Conservar el proyecto y crear una rama del entregable.
- [x] Verificar kernel/BTF y crear kind sobre Docker Desktop/WSL2.
- [x] Fijar versiones de herramientas y charts, con checksums en instaladores.
- [x] Instalar Falco modern eBPF y demostrar un evento real.
- [x] Conservar línea base de npm/pip, Semgrep, Trivy y KubeLinter.
- [x] Actualizar dependencias Python, fijar lock productivo y retirar instaladores de la imagen.
- [x] Endurecer app/imagen/manifiestos y probar 11 tests.
- [x] Configurar las tres políticas Kyverno Enforce y probar cuatro rechazos y un pod válido.
- [x] Conservar los cuatro archivos de evidencia pedidos y análisis complementarios.
- [x] Validar el uso no-root, requests/limits, raíz de solo lectura y escritura SQLite en PVC.
- [x] Verificar pedidos/corte/agotados/estados y persistencia al reemplazar el pod.
- [x] Implementar Jenkins autenticado, RBAC del namespace y pipeline completo SUCCESS.
- [x] Crear y subir repositorio privado GitHub mediante autorización explícita del usuario.
- [x] Redactar guía, arquitectura local e informe de seguridad.

El PDF, ZIP y la verificación final de publicación se generan al cerrar la entrega. No se considera falla de seguridad ni un análisis npm limpio la salida ENOLOCK: la justificación está en el informe y se complementa con pip-audit. Los documentos de octubre conservan el historial del CI/CD UCU; el controller legado quedó detenido.

Evidencias principales: `reports/security-summary.json`, `jenkins-build.json`, `kyverno-validation.txt`, `falco-event.log` y `application-smoke.json`. Reproducir con `GUIA_ENTREGABLE_3.md`.
