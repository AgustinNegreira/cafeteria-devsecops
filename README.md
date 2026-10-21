# Cafetería · pedidos para el recreo

Los alumnos piden desde el celular antes del recreo; la cafetería ve lo pendiente agrupado por recreo y lo marca como listo o entregado.

## Arquitectura

### La app: un solo contenedor

```text
 Celular del alumno ─┐       ┌─────────── contenedor ───────────┐
                     ├─────> │ FastAPI (uvicorn, puerto 8000)   │
 Pantalla cafetería ─┘       │  /            página alumno      │
                             │  /cafeteria   página cafetería   │
                             │  /api/...     reglas y datos     │
                             │  /healthz     "estoy vivo"       │
                             │        │                         │
                             │     SQLite ──> /data (volumen)   │
                             └──────────────────────────────────┘
```

- **Un solo contenedor**: FastAPI sirve la API y también las dos páginas (HTML + JS sin frameworks ni build).
- **SQLite en un volumen** montado en `/data`. Por eso hay **una sola réplica**; si hicieran falta más, se cambia a Postgres.
- **La regla de los X minutos vive en el backend** (`POST /api/pedidos` devuelve `409` con un mensaje claro). El frontend solo muestra el estado.
- **X se guarda en la base** (tabla `config`) y la cafetería lo cambia desde su pantalla: aplica en el próximo request, **sin redesplegar**.
- **Roles mínimos**: el alumno no tiene login, solo escribe su nombre (queda guardado en el celular); la cafetería entra con un PIN (`CAFETERIA_PIN`, en k8s va en un Secret).
- **Hora de Uruguay**: los pods corren en UTC, así que los recreos se interpretan en `America/Montevideo`.
- **"En vivo" por polling**: la pantalla de la cafetería se refresca cada 5 s y la del alumno cada 10 s. No usa websockets.

### El despliegue (en construcción)

```text
 git push ──> Jenkins: tests ──> docker build ──> push al registry ──> kubectl apply
                         │                                                  │
                  si fallan, no se                                          ▼
                  despliega nada                        cluster UCU, namespace alumno-team10

 Celular ──> Ingress (APISIX) ──> Service ──> Deployment (1 pod) ──> PVC en /data (SQLite)
                                                 ▲          ▲
                                        Secret (PIN)    ConfigMap (zona horaria, X inicial)
```

| Pieza | Por qué está |
|---|---|
| Deployment | Mantiene el pod siempre corriendo: si se cae o se cuelga, Kubernetes lo recrea |
| Probes en `/healthz` | Kubernetes detecta un proceso colgado y no le manda tráfico hasta que esté listo |
| PVC | Los pedidos sobreviven cuando el pod se reinicia o se actualiza |
| Secret | El PIN no queda en el código ni en la imagen |
| ConfigMap | Configuración que no es secreta, separada de la imagen |
| Service + Ingress | Una URL fija para que los alumnos entren desde el celular |
| Jenkins | Cada cambio pasa por los tests antes de llegar al cluster, sin pasos manuales |

**Publicada en:** https://cafeteria-agustin-team4.reto-ucu.net (el certificado del cluster está vencido, así que el navegador avisa; hay que tocar "Avanzar"). Por `http://` no funciona: el puerto 80 de esa IP lo atiende otro servidor.

Todo lo nuestro en el namespace se llama `cafeteria-agustin` y lleva la etiqueta `owner: agustin`, porque el namespace se comparte con otros compañeros:

```powershell
kubectl get all,pvc,cm,secret,apisixroute -l owner=agustin
```

Despliegue a mano (Jenkins va a automatizar exactamente esto):

```bash
docker build -t agustinnegreira/cafeteria:0.1 .
docker push agustinnegreira/cafeteria:0.1
# una sola vez: el PIN no va en git
kubectl create secret generic cafeteria-agustin --from-literal=CAFETERIA_PIN=<pin>
for f in k8s/*.yaml; do sed 's|image: IMAGEN|image: agustinnegreira/cafeteria:0.1|' "$f"; echo ---; done | kubectl apply -f -
kubectl rollout status deployment/cafeteria-agustin
```

Lo que **no** se usa, a propósito: varias réplicas, autoescalado y una base aparte. La carga de una cafetería escolar no lo justifica, y SQLite no admite varios pods escribiendo a la vez.

## Cómo cubre la consigna

| Pide | Dónde |
|---|---|
| Catálogo inventado con precio | `app/db.py` (semilla) |
| Recreos con hora de inicio | tabla `recreos`; la cafetería los agrega o borra |
| Pedido con varios productos | página alumno → `POST /api/pedidos` |
| Ver estado del pedido | "Mis pedidos" (pendiente / listo / entregado) |
| Pantalla cafetería, agrupada por recreo, con el próximo arriba | `/cafeteria` → `GET /api/cafeteria/pedidos` |
| Corte X minutos antes, impuesto por el backend | `crear_pedido` en `app/main.py` + tests |
| X configurable sin redesplegar | Configuración en `/cafeteria` → `PUT /api/cafeteria/config` |
| Extra: resumen de ventas del día | `GET /api/cafeteria/resumen` |
| Extra: productos agotados | switch "agotado" → no se muestran como pedibles y el backend los rechaza |

## Correr local

```powershell
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest -v
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

- Alumno: http://localhost:8000
- Cafetería: http://localhost:8000/cafeteria (PIN por defecto `1234`)
- Docs de la API: http://localhost:8000/docs

## Correr en Docker

```powershell
docker build -t cafeteria .
docker run --rm -p 8000:8000 -v cafeteria-data:/data cafeteria
```

El volumen `cafeteria-data` hace que los pedidos sobrevivan si se borra el contenedor.

## Variables de entorno

| Variable | Default | Para qué |
|---|---|---|
| `DB_PATH` | `./data/cafeteria.db` (en la imagen: `/data/cafeteria.db`) | archivo SQLite |
| `CAFETERIA_PIN` | `1234` | PIN de la pantalla de la cafetería |
| `MINUTOS_CORTE` | `15` | valor **inicial** de X. Después manda lo que se guarde desde la pantalla |
| `ZONA_HORARIA` | `America/Montevideo` | zona horaria de los recreos |

## Probar la regla contra el backend, sin pasar por el frontend

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/pedidos -ContentType application/json `
  -Body '{"alumno":"Ana","recreo_id":1,"items":[{"producto_id":1,"cantidad":1}]}'
# Pasado el corte: 409 "Ya no se aceptan pedidos para el Recreo 1 de las 10:00: se podía pedir hasta las 09:45."
```
