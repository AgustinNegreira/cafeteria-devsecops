"""Prepara datos mínimos de la demo mediante la API, sin imprimir el PIN."""
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
BASE = "http://127.0.0.1:8082"


def api(path, payload=None, pin=None):
    headers = {"Content-Type": "application/json"}
    if pin:
        headers["X-Pin"] = pin
    data = json.dumps(payload).encode() if payload is not None else None
    with urlopen(Request(BASE + path, data=data, headers=headers), timeout=10) as response:
        return json.load(response)


def main():
    api("/healthz")
    breaks = api("/api/recreos")["recreos"]
    pin_file = ROOT / ".local/lab4/pin.env"
    pin = next(line.split("=", 1)[1].strip() for line in pin_file.read_text().splitlines()
               if line.startswith("CAFETERIA_PIN="))
    if not any(item["nombre"] == "Demo DevOps" and item["hora"] == "23:59" for item in breaks):
        api("/api/cafeteria/recreos", {"nombre": "Demo DevOps", "hora": "23:59"}, pin)
    breaks = api("/api/recreos")["recreos"]
    available = max((item for item in breaks if item["abierto"]),
                    key=lambda item: item["cierra"], default=None)
    if available is None:
        raise SystemExit("No hay recreos abiertos. Revisar la hora y el corte desde la pantalla de Cafetería.")
    products = api("/api/productos")
    if not any(not item["agotado"] for item in products):
        raise SystemExit("Marcar un producto como disponible desde la pantalla de Cafetería.")
    print(f"Recreo abierto: {available['nombre']} {available['hora']} (corte {available['cierra']}).")
    print("Hay productos disponibles. Ya se puede crear un pedido o ejecutar traffic.sh.")


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, FileNotFoundError, StopIteration) as error:
        raise SystemExit(f"No se pudo preparar la demo: {error}") from error
