# Cafetería - Entregable 3 DevSecOps

Aplicación de pedidos para recreos: FastAPI + SQLite y páginas HTML/JavaScript. El alumno pide antes del corte; cafetería administra con PIN, marca estados, agotados y consulta ventas.

**Repositorio:** https://github.com/AgustinNegreira/cafeteria-devsecops

## Entrega y demostración

- [Informe del entregable 3](ENTREGABLE_3.md): requisitos, resultados, correcciones y límites.
- [Guía de prueba de punta a punta](GUIA_ENTREGABLE_3.md): preparar, mostrar, repetir controles y diagnosticar.
- [Arquitectura local](LAB_LOCAL.md) y [diagrama](docs/arquitectura-devsecops.svg).
- [Informes reales](reports/), incluida la [disposición de cada HIGH original](reports/remediaciones.md).
- PDF de entrega en `output/pdf/` y ZIP de fuentes/evidencias preparado al cerrar la entrega.

## Abrir lo que ya está corriendo

- Alumno: http://localhost:8081/
- Cafetería: http://localhost:8081/cafeteria
- API/Swagger: http://localhost:8081/docs
- Jenkins: http://localhost:8080/job/cafeteria-devsecops/ (usuario `agustin`).

PIN local: archivo privado `.local/cafeteria-pin.txt`. Clave de Jenkins: `.local/jenkins-admin-password.txt`. No están en Git ni en el ZIP; cada instalación nueva genera los suyos.

## Preparar otra instalación en Windows

Requiere Git, Python 3.12 o compatible en PATH, Docker Desktop con motor Linux/WSL2 iniciado y acceso a Internet para descargar herramientas/imágenes. Este laboratorio fue probado con kernel WSL2 6.18 y soporte BTF/eBPF; Falco necesita esas capacidades del kernel.

Desde cmd:

```bat
git clone https://github.com/AgustinNegreira/cafeteria-devsecops.git
cd cafeteria-devsecops
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local/Start-Lab.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local/Start-Jenkins.ps1
```

El primer script instala herramientas privadas con checksum, crea kind, Kyverno y Falco, genera el PIN local, construye/analiza la app y la despliega. El segundo levanta Jenkins autenticado y renueva su token Kubernetes de 24 horas. Un repositorio privado requiere acceso GitHub para clonarlo.

## Controles implementados

| Capa | Herramienta / control | Resultado observado |
|---|---|---|
| Funcional | pytest | 11 tests pasan |
| Dependencias npm | npm audit real | ENOLOCK: no hay proyecto npm; justificación conservada |
| Dependencias Python | pip-audit del lock productivo | 0 vulnerabilidades conocidas |
| Código/configuración | Semgrep | 0 hallazgos y 0 errores de herramienta |
| Imagen de la app | Trivy | 0 vulnerabilidades conocidas, 0 HIGH/CRITICAL |
| Manifiestos de la app | KubeLinter | 0 errores |
| Admisión | Kyverno Enforce | 4 casos inseguros rechazados; 1 válido aceptado |
| Ejecución | Falco modern eBPF | Alerta real de terminal en el pod; UID 10001 |
| App y datos | HTTP + reemplazo de pod | 25 respuestas verificadas; pedido retenido en PVC |
| CI/CD | Jenkins local | Pipeline completo SUCCESS; reportes archivados |

Los resultados son una fotografía de las bases/reglas usadas en la fecha de ejecución. No constituyen una certificación de ausencia de fallas. `reports/security-summary.json` identifica commit, imagen y hashes del código analizado.

## Diseño

Docker Desktop ejecuta dos contenedores principales: Jenkins y el nodo kind. El nodo contiene Kubernetes/containerd, la app, Kyverno y Falco. Jenkins construye y escanea con el motor Docker; `kind load` copia la imagen al containerd del nodo. Kubernetes aplica las políticas antes de admitir pods. La app corre como UID/GID 10001, con raíz de solo lectura, recursos y capacidades retiradas. SQLite escribe únicamente en el PVC `/data`; `/tmp` usa emptyDir.

La ruta del navegador es `localhost:8081 -> puerto 30080 del nodo -> Service -> pod:8000`. No se necesita Docker Hub ni APISIX en este entregable. Una réplica y estrategia Recreate: hay un breve corte al actualizar. El PVC sobrevive al reemplazo del pod; no se garantiza conservarlo al borrar el cluster.

## Estructura

```text
app/                       FastAPI, SQLite y frontend
tests/                     reglas de negocio y configuración del PIN
k8s/base/ + k8s/local/      Kustomize de la aplicación
local/                     kind y valores Helm/versiones
security/kyverno/          tres políticas Enforce
security/tests/            casos positivos y negativos
security/jenkins-rbac.yaml permisos de despliegue limitados
scripts/                   preparación, escaneos y demostración
jenkins/                   controller autenticado y configuración como código
reports/                   resultados reales y línea base
.local/                    herramientas y credenciales privadas, ignoradas
```

La app valida pedidos, corte y agotados en backend, usa consultas parametrizadas para entradas, exige un PIN configurado de al menos ocho caracteres y compara el PIN con `compare_digest`. El alumno no tiene identidad autenticada: el nombre es solo identificador de demostración.

## Material de entregables anteriores

[Guía original](GUIA_DEMO.md), [arquitectura UCU](ARQUITECTURA.md) y [README original](docs/README_ENTREGABLES_1_2.md) conservan el trabajo de octubre. Son históricos: sus comandos, URLs y Jenkins no representan el laboratorio de este entregable. El controller legado `jenkins-cafeteria` quedó detenido y su volumen se conservó.
