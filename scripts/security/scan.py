"""Controles reproducibles: Docker transporta entradas/salidas por API, sin bind de paths de Jenkins."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
SEMGREP = "semgrep/semgrep:1.183.0"
TRIVY = "aquasec/trivy:0.76.1"
NODE = "node:24-alpine@sha256:8a32c8cf649a49915a66e81e7a609223c708d0adabf288ee3f4077d765542f85"
PYTHON = "python:3.12-alpine3.23@sha256:a4ad86fc2eaa4f9a5c3153776c9fb56e502dbd8e23dfa855d164308f376a6dd2"


def run(args, check=True):
    p = subprocess.run([str(x) for x in args], cwd=ROOT, text=True,
                       encoding="utf-8", errors="replace", capture_output=True)
    if check and p.returncode:
        raise RuntimeError("Command failed: " + " ".join(map(str, args[:3])) + "\n" + p.stdout + p.stderr)
    return p


def save(name, text):
    (REPORTS / name).write_text(text, encoding="utf-8")


def container(image, command, inputs=(), outputs=(), volumes=()):
    """Only explicitly selected source files enter the tool container; credentials are not copied."""
    cid = None
    with tempfile.TemporaryDirectory(prefix="cafeteria-scan-") as tmp:
        source = Path(tmp) / "src"
        (source / "reports").mkdir(parents=True)
        for item in inputs:
            origin = ROOT / item
            dest = source / item
            dest.parent.mkdir(parents=True, exist_ok=True)
            if origin.is_dir():
                shutil.copytree(origin, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            else:
                shutil.copy2(origin, dest)
        args = ["docker", "create", "-w", "/src", "-e", "NO_COLOR=1", "-e", "PYTHONUTF8=1"]
        for volume in volumes:
            args += ["-v", volume]
        try:
            cid = run(args + [image] + list(command)).stdout.strip().splitlines()[-1]
            if not re.fullmatch(r"[a-f0-9]{64}", cid):
                raise RuntimeError("Invalid container identifier")
            run(["docker", "cp", str(source), cid + ":/"])
            p = run(["docker", "start", "--attach", cid], check=False)
            code = int(run(["docker", "inspect", "--format", "{{.State.ExitCode}}", cid]).stdout.strip())
            for output in outputs:
                run(["docker", "cp", cid + ":/src/reports/" + output, str(REPORTS / output)])
            return code, p.stdout + p.stderr
        finally:
            if cid:
                run(["docker", "rm", "-f", cid], check=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--checks", default="npm,pip,semgrep,kubelinter,trivy")
    args = parser.parse_args()
    if not re.fullmatch(r"cafeteria:devsecops-[A-Za-z0-9_.-]+", args.image):
        parser.error("Expected an explicit local cafeteria:devsecops-* tag")
    REPORTS.mkdir(exist_ok=True)
    checks = args.checks.split(",")
    results = {}
    if "npm" in checks:
        npm_inputs = [p for p in ("package.json", "package-lock.json") if (ROOT / p).exists()]
        code, text = container(NODE, ["sh", "-c", "node --version; npm --version; npm audit"], npm_inputs)
        applicable = bool(npm_inputs)
        expected_na = (not applicable and code != 0 and ("ENOLOCK" in text or "ENOENT" in text))
        explanation = "\nAPLICABILIDAD: app Python/FastAPI con JS sin paquetes npm. No hay package.json/package-lock.json. "
        explanation += "Se conserva la ejecucion fallida real; no significa cero vulnerabilidades. Ver pip-audit.txt.\n"
        save("npm-audit.txt", "$ npm audit\n" + text + "\nExit code: " + str(code) +
             (explanation if not applicable else ""))
        results["npm"] = {"exitCode": code, "applicable": applicable,
                          "status": "NOT_APPLICABLE" if expected_na else ("PASS" if code == 0 else "FAIL")}
        print("npm:", results["npm"]["status"], flush=True)
    if "pip" in checks:
        command = ["sh", "-ec", "python -m pip install --quiet --disable-pip-version-check pip-audit==2.10.1; "
                   "pip-audit --no-deps --disable-pip -r requirements.lock --format json --output /src/reports/pip-audit.json"]
        code, text = container(PYTHON, command, ["requirements.lock"], ["pip-audit.json"])
        data = json.loads((REPORTS / "pip-audit.json").read_text())
        count = sum(len(p.get("vulns", [])) for p in data.get("dependencies", []))
        save("pip-audit.txt", "pip-audit 2.10.1 - requirements.lock\n" + text +
             "\nExit code: " + str(code) + "\nKnown vulnerability findings: " + str(count) + "\n")
        results["pip"] = {"exitCode": code, "findings": count, "status": "PASS" if code == 0 and count == 0 else "FAIL"}
        print("pip-audit:", count, "findings", flush=True)
    if "semgrep" in checks:
        command = ["semgrep", "scan", "--error", "--no-git-ignore", "--config", "p/default",
                   "--config", "p/security-audit", "--config", "p/dockerfile", "--metrics", "off",
                   "--disable-version-check", "--json-output", "/src/reports/semgrep.json",
                   "app", "Dockerfile", "k8s/base"]
        code, text = container(SEMGREP, command, ["app", "Dockerfile", "k8s/base"], ["semgrep.json"])
        data = json.loads((REPORTS / "semgrep.json").read_text())
        count = len(data.get("results", []))
        errors = len(data.get("errors", []))
        save("semgrep.txt", "Semgrep 1.183.0 - p/default + p/security-audit + p/dockerfile\n" +
             text + "\nExit code: " + str(code) + "\nFindings: " + str(count) +
             "\nTool errors: " + str(errors) + "\n")
        results["semgrep"] = {"exitCode": code, "findings": count, "errors": errors,
                              "status": "PASS" if code == 0 and count == 0 and errors == 0 else "FAIL"}
        print("Semgrep:", count, "findings", flush=True)
    if "kubelinter" in checks:
        rendered = run(["kubectl", "kustomize", "k8s/local"]).stdout
        if rendered.count("image: cafeteria:devsecops-1") != 1:
            raise RuntimeError("Unexpected image placeholder in Kustomize output")
        rendered = rendered.replace("image: cafeteria:devsecops-1", "image: " + args.image)
        save("rendered-manifests.yaml", rendered)
        binary = ROOT / ".local/bin/kube-linter.exe"
        if not binary.exists():
            binary = shutil.which("kube-linter")
        if not binary:
            raise RuntimeError("kube-linter is required")
        p = run([str(binary), "lint", "reports/rendered-manifests.yaml", "--format", "plain"], check=False)
        save("kubelinter.txt", p.stdout + p.stderr + "\nExit code: " + str(p.returncode) + "\n")
        results["kubelinter"] = {"exitCode": p.returncode, "status": "PASS" if p.returncode == 0 else "FAIL"}
        print("KubeLinter:", results["kubelinter"]["status"], flush=True)
    if "trivy" in checks:
        code, text = container(TRIVY, ["image", "--quiet", "--scanners", "vuln", "--format", "json",
                           "--output", "/src/reports/trivyreport.json", args.image], outputs=["trivyreport.json"],
                           volumes=["/var/run/docker.sock:/var/run/docker.sock",
                                    "cafeteria_trivy_cache:/root/.cache/trivy"])
        if code:
            raise RuntimeError("Trivy execution failed: " + text)
        data = json.loads((REPORTS / "trivyreport.json").read_text())
        vulns = [v for r in data.get("Results", []) for v in (r.get("Vulnerabilities") or [])]
        high = sum(v["Severity"] in ("HIGH", "CRITICAL") for v in vulns)
        code, table = container(TRIVY, ["convert", "--format", "table",
                            "--output", "/src/reports/trivyreport.txt", "/src/reports/trivyreport.json"],
                            ["reports/trivyreport.json"], ["trivyreport.txt"])
        table_path = REPORTS / "trivyreport.txt"
        converted = table_path.read_text(encoding="utf-8")
        save("trivyreport.txt", "Trivy 0.76.1 - image vulnerability scan\n"
             + "Image: " + args.image + "\n"
             + "Artifact: " + data.get("ArtifactName", args.image) + "\n"
             + "Total known vulnerability findings: " + str(len(vulns)) + "\n"
             + "HIGH/CRITICAL: " + str(high) + "\n"
             + "Scan exit code: " + str(code) + "\n"
             + "Full machine-readable scan: reports/trivyreport.json\n\n" + converted)
        results["trivy"] = {"exitCode": code, "findings": len(vulns), "highCritical": high,
                            "status": "PASS" if code == 0 and high == 0 else "FAIL"}
        print("Trivy:", len(vulns), "total,", high, "HIGH/CRITICAL", flush=True)
    previous = {}
    summary_path = REPORTS / "security-summary.json"
    if summary_path.exists():
        previous = json.loads(summary_path.read_text()).get("checks", {})
    previous.update(results)
    image_lookup = run(["docker", "image", "inspect", args.image], check=False)
    image_info = json.loads(image_lookup.stdout)[0] if image_lookup.returncode == 0 else {"Id": None}
    hashes = {}
    for path in sorted(list((ROOT / "app").rglob("*.py")) + list((ROOT / "app/static").glob("*")) +
                       [ROOT / "Dockerfile", ROOT / "requirements.lock"]):
        if path.is_file():
            hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    summary = {"timestampUTC": datetime.now(timezone.utc).isoformat(), "image": args.image,
               "imageID": image_info["Id"], "gitCommit": run(["git", "rev-parse", "HEAD"]).stdout.strip(),
               "sourceSHA256": hashes, "checks": previous}
    save("security-summary.json", json.dumps(summary, indent=2) + "\n")
    if any(item["status"] == "FAIL" for item in results.values()):
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("SECURITY TOOL ERROR:", error, file=sys.stderr)
        sys.exit(2)
