"""Bloquea el despliegue ante un crítico o un escaneo incompleto."""

import json
import sys
from pathlib import Path


def main(status, report):
    if status not in {0, 1}:
        raise SystemExit(f"Snyk no completó el escaneo (código {status}).")
    try:
        result = json.loads(report.read_text(encoding="utf-8"))
        findings = result["vulnerabilities"]
        severities = [finding["severity"] for finding in findings]
        if result.get("error") or not isinstance(findings, list) or bool(findings) != (status == 1):
            raise ValueError("Salida incoherente con el estado del escaneo")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"El resultado de Snyk no pudo verificarse: {error}") from error

    critical = severities.count("critical")
    if critical:
        raise SystemExit(f"Snyk detectó {critical} vulnerabilidades críticas. Se bloquea el despliegue.")
    print(f"Snyk completó el escaneo con {len(findings)} hallazgos y cero críticos.")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
