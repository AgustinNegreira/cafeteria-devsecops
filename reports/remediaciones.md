# Tratamiento de HIGH/CRITICAL de la imagen original

Línea base `agustinnegreira/cafeteria:2`: 48 filas HIGH, 12 CVE distintos, 0 CRITICAL. Todas las filas originales se conservan en `trivy-baseline.json` y `.txt`.

| CVE original | Paquetes afectados en la línea base | Tratamiento |
|---|---|---|
| CVE-2025-62727 | starlette | Starlette actualizada de 0.41.3 a 1.10.0; FastAPI actualizada y lock fijado. |
| CVE-2025-69720 | libncursesw6, libtinfo6, ncurses-base, ncurses-bin | Se reemplazó la base Debian por Alpine 3.23, se actualizaron paquetes y se retiraron herramientas de instalación innecesarias. El componente/versionado anterior no se distribuye en la imagen final. |
| CVE-2026-119373 | libsqlite3-0 | Se reemplazó la base Debian por Alpine 3.23, se actualizaron paquetes y se retiraron herramientas de instalación innecesarias. El componente/versionado anterior no se distribuye en la imagen final. |
| CVE-2026-16742 | libsystemd0, libudev1 | Se reemplazó la base Debian por Alpine 3.23, se actualizaron paquetes y se retiraron herramientas de instalación innecesarias. El componente/versionado anterior no se distribuye en la imagen final. |
| CVE-2026-48818 | starlette | Starlette actualizada de 0.41.3 a 1.10.0; FastAPI actualizada y lock fijado. |
| CVE-2026-54283 | starlette | Starlette actualizada de 0.41.3 a 1.10.0; FastAPI actualizada y lock fijado. |
| CVE-2026-54369 | libacl1 | Se reemplazó la base Debian por Alpine 3.23, se actualizaron paquetes y se retiraron herramientas de instalación innecesarias. El componente/versionado anterior no se distribuye en la imagen final. |
| CVE-2026-76642 | bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util-linux | Se reemplazó la base Debian por Alpine 3.23, se actualizaron paquetes y se retiraron herramientas de instalación innecesarias. El componente/versionado anterior no se distribuye en la imagen final. |
| CVE-2026-78408 | bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util-linux | Se reemplazó la base Debian por Alpine 3.23, se actualizaron paquetes y se retiraron herramientas de instalación innecesarias. El componente/versionado anterior no se distribuye en la imagen final. |
| CVE-2026-78409 | bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util-linux | Se reemplazó la base Debian por Alpine 3.23, se actualizaron paquetes y se retiraron herramientas de instalación innecesarias. El componente/versionado anterior no se distribuye en la imagen final. |
| CVE-2026-78410 | bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util-linux | Se reemplazó la base Debian por Alpine 3.23, se actualizaron paquetes y se retiraron herramientas de instalación innecesarias. El componente/versionado anterior no se distribuye en la imagen final. |
| CVE-2026-9538 | perl-base | Se reemplazó la base Debian por Alpine 3.23, se actualizaron paquetes y se retiraron herramientas de instalación innecesarias. El componente/versionado anterior no se distribuye en la imagen final. |

Resultado final: 0 vulnerabilidades conocidas en `trivyreport.json`, incluido 0 HIGH/CRITICAL. No se usaron exclusiones de CVE. El alcance es la imagen de la aplicación; no implica un escaneo de Jenkins, Docker Desktop o de todo el cluster. Los conteos corresponden a la base de vulnerabilidades usada en la fecha del análisis.
