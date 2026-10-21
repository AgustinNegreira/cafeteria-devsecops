"""SQLite: conexion, esquema y datos iniciales (catalogo y recreos inventados)."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# En el contenedor el Dockerfile lo apunta a /data (el volumen).
# Local, por defecto queda en cafeteria/data/ sin importar desde donde se corra.
DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).resolve().parent.parent / "data" / "cafeteria.db"))

ESQUEMA = """
CREATE TABLE IF NOT EXISTS productos (
    id      INTEGER PRIMARY KEY,
    nombre  TEXT    NOT NULL,
    precio  INTEGER NOT NULL,
    agotado INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS recreos (
    id     INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    hora   TEXT NOT NULL              -- 'HH:MM', hora de inicio
);
CREATE TABLE IF NOT EXISTS pedidos (
    id        INTEGER PRIMARY KEY,
    alumno    TEXT    NOT NULL,
    recreo_id INTEGER NOT NULL REFERENCES recreos(id),
    fecha     TEXT    NOT NULL,       -- 'YYYY-MM-DD'
    estado    TEXT    NOT NULL DEFAULT 'pendiente',
    total     INTEGER NOT NULL,
    creado    TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS pedido_items (
    pedido_id   INTEGER NOT NULL REFERENCES pedidos(id),
    producto_id INTEGER NOT NULL,
    nombre      TEXT    NOT NULL,     -- copia: si cambia el catalogo, el pedido no cambia
    precio      INTEGER NOT NULL,
    cantidad    INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
"""

PRODUCTOS = [
    ("Café", 90),
    ("Café con leche", 110),
    ("Medialuna", 45),
    ("Tostado jamón y queso", 180),
    ("Empanada de carne", 120),
    ("Sándwich olímpico", 220),
    ("Alfajor", 60),
    ("Fruta", 40),
    ("Agua 500 ml", 70),
    ("Refresco", 95),
]

RECREOS = [
    ("Recreo 1", "10:00"),
    ("Recreo 2", "12:00"),
    ("Recreo 3", "16:00"),
    ("Recreo nocturno", "20:30"),
]


@contextmanager
def conexion():
    """Una conexion por uso: commit si todo sale bien, rollback si hay excepcion."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        with con:
            yield con
    finally:
        con.close()


def init() -> None:
    """Crea las tablas y carga los datos iniciales la primera vez."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with conexion() as con:
        con.executescript(ESQUEMA)
        if not con.execute("SELECT 1 FROM productos").fetchone():
            con.executemany("INSERT INTO productos (nombre, precio) VALUES (?, ?)", PRODUCTOS)
            con.executemany("INSERT INTO recreos (nombre, hora) VALUES (?, ?)", RECREOS)
        # MINUTOS_CORTE solo es el valor inicial: despues manda lo que diga la base,
        # que la cafeteria cambia desde su pantalla sin redesplegar.
        con.execute(
            "INSERT OR IGNORE INTO config VALUES ('minutos_corte', ?)",
            (os.getenv("MINUTOS_CORTE", "15"),),
        )
