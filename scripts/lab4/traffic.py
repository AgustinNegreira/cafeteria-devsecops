"""Genera tráfico HTTP y pedidos de ejemplo para el dashboard de Cafetería."""

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4


def request(base_url, path, payload=None, expected=200):
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(base_url + path, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as response:
            status, body = response.status, json.load(response)
    except HTTPError as error:
        status, body = error.code, json.load(error)
    if status != expected:
        raise SystemExit(f"{path}: HTTP {status}, se esperaba {expected}. {body}")
    return body


def verify_persistence(base_url, state):
    order = json.loads(state.read_text(encoding="utf-8"))
    query = urlencode({"alumno": order["alumno"]})
    orders = request(base_url, f"/api/pedidos?{query}")
    if not any(item["id"] == order["id"] for item in orders):
        raise SystemExit(f"El pedido {order['id']} no está disponible.")
    print(f"Pedido {order['id']} de {order['alumno']} disponible después del reemplazo del pod.")


def generate_traffic(base_url, count, delay, state):
    request(base_url, "/healthz")
    breaks = request(base_url, "/api/recreos")["recreos"]
    available = max((item for item in breaks if item["abierto"]),
                    key=lambda item: item["cierra"], default=None)
    closed = next((item for item in breaks if not item["abierto"]), None)
    products = request(base_url, "/api/productos")
    product = next((item for item in products if not item["agotado"]), None)
    if available is None or product is None:
        raise SystemExit("Preparar un recreo abierto y un producto disponible antes de generar pedidos.")
    name = f"Demo Lab 4 {uuid4().hex[:8]}"
    order = {"alumno": name, "recreo_id": available["id"],
             "items": [{"producto_id": product["id"], "cantidad": 1}]}
    created = request(base_url, "/api/pedidos", order, expected=201)
    state.write_text(json.dumps({"alumno": name, "id": created["id"]}), encoding="utf-8")
    print(f"HTTP 201. Pedido {created['id']} creado para {name}.", flush=True)
    if closed is not None:
        rejected = request(base_url, "/api/pedidos", {**order, "recreo_id": closed["id"]}, expected=409)
        print(f"HTTP 409. {rejected['detail']}", flush=True)
    for index in range(count):
        if index % 5 == 0:
            created = request(base_url, "/api/pedidos", order, expected=201)
        else:
            request(base_url, "/api/productos")
        time.sleep(delay)
    state.write_text(json.dumps({"alumno": name, "id": created["id"]}), encoding="utf-8")
    print(f"{count} solicitudes adicionales completadas.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8082")
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--delay", type=float, default=1)
    parser.add_argument("--verify-persistence", action="store_true")
    args = parser.parse_args()
    if args.count < 0 or args.delay < 0:
        parser.error("La cantidad y el intervalo deben ser mayores o iguales a cero.")
    state = Path(".local/lab4/last-order.json")
    if args.verify_persistence:
        verify_persistence(args.url, state)
    else:
        generate_traffic(args.url, args.count, args.delay, state)


if __name__ == "__main__":
    main()
