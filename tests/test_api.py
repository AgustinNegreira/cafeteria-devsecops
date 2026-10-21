"""Tests de la API. Lo central: la regla de los X minutos la hace cumplir el backend."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import db, main

PIN = {"X-PIN": main.CAFETERIA_PIN}


def a_las(hora: int, minuto: int):
    """Reloj fijo para no depender de la hora en que corre el pipeline."""
    return lambda: datetime(2026, 10, 20, hora, minuto, tzinfo=main.TZ)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(main, "ahora", a_las(9, 0))
    with TestClient(main.app) as c:
        yield c


def recreo(client, hora):
    return next(r for r in client.get("/api/recreos").json()["recreos"] if r["hora"] == hora)


def producto(client, nombre):
    return next(p for p in client.get("/api/productos").json() if p["nombre"] == nombre)


def pedir(client, hora="10:00", nombre="Café", cantidad=1):
    return client.post("/api/pedidos", json={
        "alumno": "Ana 3ºB",
        "recreo_id": recreo(client, hora)["id"],
        "items": [{"producto_id": producto(client, nombre)["id"], "cantidad": cantidad}],
    })


def test_pedido_a_tiempo_se_acepta(client):
    r = pedir(client, cantidad=2)

    assert r.status_code == 201
    assert r.json()["total"] == 2 * producto(client, "Café")["precio"]


def test_pedido_pasado_el_corte_se_rechaza_con_mensaje_claro(client, monkeypatch):
    # Corte por defecto: 15 min. Para el recreo de las 10:00 se cierra a las 09:45.
    monkeypatch.setattr(main, "ahora", a_las(9, 50))

    r = pedir(client)

    assert r.status_code == 409
    assert "09:45" in r.json()["detail"]


def test_cambiar_el_corte_aplica_sin_reiniciar(client, monkeypatch):
    monkeypatch.setattr(main, "ahora", a_las(9, 50))
    assert pedir(client).status_code == 409

    client.put("/api/cafeteria/config", json={"minutos_corte": 5}, headers=PIN)

    assert pedir(client).status_code == 201


def test_producto_agotado_no_se_puede_pedir(client):
    cafe = producto(client, "Café")
    client.put(f"/api/cafeteria/productos/{cafe['id']}/agotado", json={"agotado": True}, headers=PIN)

    r = pedir(client)

    assert r.status_code == 409
    assert "agotado" in r.json()["detail"]


def test_la_cafeteria_necesita_pin(client):
    assert client.get("/api/cafeteria/pedidos").status_code == 401
    assert client.get("/api/cafeteria/pedidos", headers={"X-PIN": "mal"}).status_code == 401


def test_la_cafeteria_ve_los_pedidos_agrupados_y_el_proximo_recreo(client):
    pedir(client, "10:00")
    pedir(client, "12:00")

    datos = client.get("/api/cafeteria/pedidos", headers=PIN).json()

    assert datos["proximo_recreo_id"] == recreo(client, "10:00")["id"]
    por_hora = {r["hora"]: len(r["pedidos"]) for r in datos["recreos"]}
    assert por_hora["10:00"] == 1 and por_hora["12:00"] == 1


def test_el_alumno_ve_el_estado_que_marca_la_cafeteria(client):
    pedido_id = pedir(client).json()["id"]

    client.post(f"/api/cafeteria/pedidos/{pedido_id}/estado", json={"estado": "listo"}, headers=PIN)

    mios = client.get("/api/pedidos", params={"alumno": "Ana 3ºB"}).json()
    assert mios[0]["estado"] == "listo"


def test_resumen_de_ventas_del_dia(client):
    pedir(client, nombre="Café", cantidad=3)
    pedir(client, nombre="Medialuna", cantidad=2)

    r = client.get("/api/cafeteria/resumen", headers=PIN).json()

    assert r["pedidos"] == 2
    assert r["total"] == 3 * producto(client, "Café")["precio"] + 2 * producto(client, "Medialuna")["precio"]
    assert {p["nombre"] for p in r["por_producto"]} == {"Café", "Medialuna"}


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}
