# Análisis de la imagen de Cafetería

Medición del 10 de noviembre de 2026 con Docker Desktop y Dive 0.13.1.

| Imagen local | Tamaño informado por Docker | Capas de filesystem | Usuario |
| --- | ---: | ---: | --- |
| `cafeteria:lab4-dev-1` | 115.436.515 bytes | 9 | `10001:10001` |
| `cafeteria:devsecops-build-9` | 109.574.739 bytes | 9 | `10001:10001` |

Dive dio **96,1485 % de eficiencia** y estimó **5.980.731 bytes** duplicados o desperdiciados en la imagen del Lab 4. Pasaron las dos reglas activas de Dive. La ejecución de `id -u` en el contenedor devolvió `10001`.

La etapa `dependencies` instala los paquetes de Python en `/opt/dependencies`. La etapa final copia ese directorio y la aplicación. El actualizador de pip de la etapa de dependencias queda en esa etapa. El tamaño observado es mayor que el de la imagen previa. Las dos imágenes incluyen versiones distintas de paquetes base y el Lab 4 incorpora instrumentación, por lo que la comparación mide el cambio total entre builds.

Dive muestra duplicación en bibliotecas y datos de zona horaria que se reemplazan al actualizar Alpine. Una mejora para probar es elegir una imagen base con los parches ya incorporados, conservar la verificación de vulnerabilidades y medir de nuevo. También se puede evaluar instalar dependencias con `--no-compile` y comparar tamaño y tiempo de arranque.

```bash
docker build -t cafeteria:lab4-dev-1 .
docker image inspect cafeteria:lab4-dev-1 --format '{{.Size}} {{len .RootFS.Layers}} {{.Config.User}}'
docker run --rm --entrypoint id cafeteria:lab4-dev-1 -u
MSYS2_ARG_CONV_EXCL='*' docker run --rm -e CI=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  ghcr.io/wagoodman/dive:v0.13.1 cafeteria:lab4-dev-1
```
