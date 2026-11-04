"""Prueba real de la API local y, opcionalmente, persistencia al reemplazar su pod."""
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import urllib.error
import urllib.parse

ROOT = Path(__file__).resolve().parents[2]
BASE = 'http://localhost:8081'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--persistence', action='store_true', help='Reemplaza solo el pod local de la app')
    args = parser.parse_args()
    pin = (ROOT / '.local/cafeteria-pin.txt').read_text().strip()
    checks = []

    def api(path, method='GET', data=None, admin=False, expected=200):
        headers = {'Content-Type': 'application/json'}
        if admin:
            headers['X-PIN'] = pin
        request = urllib.request.Request(BASE + path, headers=headers, method=method,
                   data=json.dumps(data).encode() if data is not None else None)
        try:
            response = urllib.request.urlopen(request, timeout=10)
        except urllib.error.HTTPError as error:
            response = error
        body = response.read()
        if response.code != expected:
            raise RuntimeError(f'{method} {path}: expected {expected}, actual {response.code}')
        checks.append({'method': method, 'path': path, 'expected': expected, 'actual': response.code})
        if body and response.headers.get('Content-Type','').startswith('application/json'):
            return json.loads(body)
        return None

    api('/')
    api('/cafeteria')
    assert api('/healthz') == {'status': 'ok'}
    api('/api/cafeteria/pedidos', expected=401)
    api('/api/cafeteria/pedidos', admin=True)
    products = api('/api/productos')
    product = products[0]
    config = api('/api/recreos')['minutos_corte']
    now = datetime.now(timezone(timedelta(hours=-3)))
    if now.hour >= 23 or now.hour == 0:
        raise RuntimeError('Repetir fuera de la hora cercana a medianoche para validar recreos del mismo dia')
    future = api('/api/cafeteria/recreos', 'POST', {'nombre': 'Demo DevSecOps', 'hora': (now + timedelta(minutes=45)).strftime('%H:%M')}, True, 201)
    past = api('/api/cafeteria/recreos', 'POST', {'nombre': 'Corte DevSecOps', 'hora': (now - timedelta(minutes=45)).strftime('%H:%M')}, True, 201)
    student = 'Demo DevSecOps ' + now.strftime('%Y%m%d-%H%M%S')
    order = {'alumno': student, 'recreo_id': future['id'], 'items': [{'producto_id': product['id'], 'cantidad': 2}]}
    try:
        api('/api/cafeteria/config', 'PUT', {'minutos_corte': 0}, True)
        api(f"/api/cafeteria/productos/{product['id']}/agotado", 'PUT', {'agotado': False}, True)
        created = api('/api/pedidos', 'POST', order, expected=201)
        assert created['total'] == product['precio'] * 2
        api(f"/api/cafeteria/productos/{product['id']}/agotado", 'PUT', {'agotado': True}, True)
        api('/api/pedidos', 'POST', order, expected=409)
        api(f"/api/cafeteria/productos/{product['id']}/agotado", 'PUT', {'agotado': False}, True)
        api('/api/pedidos', 'POST', {**order, 'recreo_id': past['id']}, expected=409)
        for state in ('listo', 'entregado'):
            api(f"/api/cafeteria/pedidos/{created['id']}/estado", 'POST', {'estado': state}, True)
            orders = api('/api/pedidos?' + urllib.parse.urlencode({'alumno': student}))
            assert orders[0]['estado'] == state
        api('/api/cafeteria/resumen', admin=True)
    finally:
        api('/api/cafeteria/config', 'PUT', {'minutos_corte': config}, True)
        api(f"/api/cafeteria/productos/{product['id']}/agotado", 'PUT', {'agotado': product['agotado']}, True)
        api(f"/api/cafeteria/recreos/{past['id']}", 'DELETE', admin=True, expected=204)
    evidence = {'timestampUTC': datetime.now(timezone.utc).isoformat(), 'baseURL': BASE,
                'orderId': created['id'], 'student': student, 'checks': checks}
    if args.persistence:
        k = ['kubectl', '--kubeconfig', str(ROOT / '.local/kubeconfig.yaml')]
        def command(arguments):
            return subprocess.check_output(k + arguments, text=True).strip()
        if command(['config', 'current-context']) != 'kind-cafeteria-devsecops':
            raise RuntimeError('Contexto inesperado; no se reemplaza ningun pod')
        selector = ['-n', 'cafeteria-devsecops']
        before = json.loads(command(selector + ['get', 'pods', '-l', 'app=cafeteria-agustin', '-o', 'json']))['items'][0]
        command(selector + ['delete', 'pod', before['metadata']['name'], '--wait=true'])
        command(selector + ['rollout', 'status', 'deployment/cafeteria-agustin', '--timeout=120s'])
        for _ in range(30):
            try:
                orders = api('/api/pedidos?' + urllib.parse.urlencode({'alumno': student}))
                break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(1)
        else:
            raise RuntimeError('La app no volvio a responder')
        assert any(p['id'] == created['id'] and p['estado'] == 'entregado' for p in orders)
        after = json.loads(command(selector + ['get', 'pods', '-l', 'app=cafeteria-agustin', '-o', 'json']))['items'][0]
        assert before['metadata']['uid'] != after['metadata']['uid']
        evidence['persistence'] = {'status': 'PASS', 'oldPod': before['metadata']['name'], 'newPod': after['metadata']['name'], 'retainedOrderId': created['id']}
    evidence['status'] = 'PASS'
    (ROOT / 'reports/application-smoke.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(f"PASS: {len(checks)} respuestas verificadas, pedido #{created['id']}, persistencia={args.persistence}")


if __name__ == '__main__':
    main()
