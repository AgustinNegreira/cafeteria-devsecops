"""Pedidos de la cafeteria: API + las dos paginas, en un solo proceso."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import db

# Los pods corren en UTC: los recreos se interpretan en hora de Uruguay.
TZ = ZoneInfo(os.getenv("ZONA_HORARIA", "America/Montevideo"))
CAFETERIA_PIN = os.getenv("CAFETERIA_PIN", "1234")
STATIC = Path(__file__).parent / "static"


def ahora() -> datetime:
    """Hora local. Los tests la reemplazan para fijar el reloj."""
    return datetime.now(TZ)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    yield


app = FastAPI(title="Cafetería", lifespan=lifespan)


# --- helpers ----------------------------------------------------------------


def minutos_corte(con) -> int:
    return int(con.execute("SELECT valor FROM config WHERE clave = 'minutos_corte'").fetchone()[0])


def recreos_de_hoy(con) -> list[dict]:
    """Recreos de hoy con la hora de cierre de pedidos y si siguen abiertos."""
    now = ahora()
    corte = minutos_corte(con)
    recreos = []
    for r in con.execute("SELECT * FROM recreos ORDER BY hora"):
        inicio = datetime.combine(now.date(), time.fromisoformat(r["hora"]), TZ)
        cierre = inicio - timedelta(minutes=corte)
        recreos.append({**dict(r), "cierra": f"{cierre:%H:%M}", "abierto": now <= cierre})
    return recreos


def pedidos_con_items(con, filtro: str, params: tuple, orden: str = "r.hora, p.id") -> list[dict]:
    pedidos = [
        dict(p)
        for p in con.execute(
            "SELECT p.*, r.nombre AS recreo, r.hora FROM pedidos p "
            f"JOIN recreos r ON r.id = p.recreo_id WHERE {filtro} ORDER BY {orden}",
            params,
        )
    ]
    for p in pedidos:
        p["items"] = [
            dict(i)
            for i in con.execute(
                "SELECT nombre, precio, cantidad FROM pedido_items WHERE pedido_id = ?", (p["id"],)
            )
        ]
    return pedidos


# --- alumno -----------------------------------------------------------------


class Item(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0, le=20)


class NuevoPedido(BaseModel):
    alumno: str = Field(max_length=60)
    recreo_id: int
    items: list[Item] = Field(min_length=1)


@app.get("/api/recreos")
def listar_recreos():
    with db.conexion() as con:
        return {"minutos_corte": minutos_corte(con), "recreos": recreos_de_hoy(con)}


@app.get("/api/productos")
def listar_productos():
    with db.conexion() as con:
        return [
            {**dict(p), "agotado": bool(p["agotado"])}
            for p in con.execute("SELECT * FROM productos ORDER BY nombre")
        ]


@app.post("/api/pedidos", status_code=201)
def crear_pedido(pedido: NuevoPedido):
    alumno = pedido.alumno.strip()
    if not alumno:
        raise HTTPException(400, "Falta el nombre del alumno")

    with db.conexion() as con:
        recreo = next((r for r in recreos_de_hoy(con) if r["id"] == pedido.recreo_id), None)
        if recreo is None:
            raise HTTPException(404, "Ese recreo no existe")

        # La regla de negocio vive aca. El frontend solo la muestra.
        if not recreo["abierto"]:
            raise HTTPException(
                409,
                f"Ya no se aceptan pedidos para el {recreo['nombre']} de las {recreo['hora']}: "
                f"se podía pedir hasta las {recreo['cierra']}.",
            )

        total, filas = 0, []
        for item in pedido.items:
            prod = con.execute("SELECT * FROM productos WHERE id = ?", (item.producto_id,)).fetchone()
            if prod is None:
                raise HTTPException(404, f"No existe el producto {item.producto_id}")
            if prod["agotado"]:
                raise HTTPException(409, f"{prod['nombre']} está agotado")
            total += prod["precio"] * item.cantidad
            filas.append((prod["id"], prod["nombre"], prod["precio"], item.cantidad))

        now = ahora()
        cur = con.execute(
            "INSERT INTO pedidos (alumno, recreo_id, fecha, total, creado) VALUES (?, ?, ?, ?, ?)",
            (alumno, pedido.recreo_id, now.date().isoformat(), total, now.isoformat(timespec="seconds")),
        )
        con.executemany(
            "INSERT INTO pedido_items VALUES (?, ?, ?, ?, ?)", [(cur.lastrowid, *f) for f in filas]
        )
        return {"id": cur.lastrowid, "total": total, "estado": "pendiente"}


@app.get("/api/pedidos")
def mis_pedidos(alumno: str):
    with db.conexion() as con:
        return pedidos_con_items(con, "p.alumno = ?", (alumno.strip(),), "p.id DESC LIMIT 20")


# --- cafeteria (protegido con PIN) -------------------------------------------


def solo_cafeteria(x_pin: str = Header(default="")):
    if x_pin != CAFETERIA_PIN:
        raise HTTPException(401, "PIN de cafetería incorrecto")


cafe = APIRouter(prefix="/api/cafeteria", dependencies=[Depends(solo_cafeteria)])


class CambioEstado(BaseModel):
    estado: Literal["pendiente", "listo", "entregado"]


class Config(BaseModel):
    minutos_corte: int = Field(ge=0, le=240)


class Agotado(BaseModel):
    agotado: bool


class NuevoRecreo(BaseModel):
    nombre: str = Field(min_length=1, max_length=40)
    hora: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


@cafe.get("/pedidos")
def pedidos_de_hoy():
    """Pedidos de hoy agrupados por recreo, marcando cual es el proximo."""
    hora_actual = f"{ahora():%H:%M}"
    with db.conexion() as con:
        recreos = recreos_de_hoy(con)
        pedidos = pedidos_con_items(con, "p.fecha = ?", (ahora().date().isoformat(),))
    for r in recreos:
        r["pedidos"] = [p for p in pedidos if p["recreo_id"] == r["id"]]
    proximo = next((r["id"] for r in recreos if r["hora"] >= hora_actual), None)
    return {"proximo_recreo_id": proximo, "recreos": recreos}


@cafe.post("/pedidos/{pedido_id}/estado")
def cambiar_estado(pedido_id: int, cambio: CambioEstado):
    with db.conexion() as con:
        cur = con.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (cambio.estado, pedido_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "No existe ese pedido")
    return {"id": pedido_id, "estado": cambio.estado}


@cafe.put("/config")
def cambiar_config(config: Config):
    with db.conexion() as con:
        con.execute(
            "UPDATE config SET valor = ? WHERE clave = 'minutos_corte'", (str(config.minutos_corte),)
        )
    return config


@cafe.put("/productos/{producto_id}/agotado")
def marcar_agotado(producto_id: int, cambio: Agotado):
    with db.conexion() as con:
        cur = con.execute("UPDATE productos SET agotado = ? WHERE id = ?", (int(cambio.agotado), producto_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "No existe ese producto")
    return {"id": producto_id, "agotado": cambio.agotado}


@cafe.post("/recreos", status_code=201)
def crear_recreo(recreo: NuevoRecreo):
    with db.conexion() as con:
        cur = con.execute("INSERT INTO recreos (nombre, hora) VALUES (?, ?)", (recreo.nombre, recreo.hora))
    return {"id": cur.lastrowid, **recreo.model_dump()}


@cafe.delete("/recreos/{recreo_id}", status_code=204)
def borrar_recreo(recreo_id: int):
    with db.conexion() as con:
        if con.execute("SELECT 1 FROM pedidos WHERE recreo_id = ?", (recreo_id,)).fetchone():
            raise HTTPException(409, "Ese recreo ya tiene pedidos, no se puede borrar")
        con.execute("DELETE FROM recreos WHERE id = ?", (recreo_id,))


@cafe.get("/resumen")
def resumen_del_dia():
    hoy = ahora().date().isoformat()
    with db.conexion() as con:
        totales = con.execute(
            "SELECT COUNT(*) AS pedidos, COALESCE(SUM(total), 0) AS total FROM pedidos WHERE fecha = ?",
            (hoy,),
        ).fetchone()
        por_estado = {
            r["estado"]: r["n"]
            for r in con.execute(
                "SELECT estado, COUNT(*) AS n FROM pedidos WHERE fecha = ? GROUP BY estado", (hoy,)
            )
        }
        por_producto = [
            dict(r)
            for r in con.execute(
                "SELECT i.nombre, SUM(i.cantidad) AS cantidad, SUM(i.cantidad * i.precio) AS total "
                "FROM pedido_items i JOIN pedidos p ON p.id = i.pedido_id "
                "WHERE p.fecha = ? GROUP BY i.nombre ORDER BY total DESC",
                (hoy,),
            )
        ]
    return {"fecha": hoy, **dict(totales), "por_estado": por_estado, "por_producto": por_producto}


app.include_router(cafe)


# --- infraestructura y paginas ----------------------------------------------


@app.get("/healthz")
def healthz():
    """Para las probes de Kubernetes: responde solo si la base esta accesible."""
    with db.conexion() as con:
        con.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def pagina_alumno():
    return FileResponse(STATIC / "index.html")


@app.get("/cafeteria", include_in_schema=False)
def pagina_cafeteria():
    return FileResponse(STATIC / "cafeteria.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
