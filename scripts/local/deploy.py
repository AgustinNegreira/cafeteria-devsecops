"""Carga una imagen analizada y despliega con credencial limitada al namespace local."""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def command(args, capture=False):
    p = subprocess.run([str(x) for x in args], cwd=ROOT, text=True, encoding="utf-8",
                       errors="replace", capture_output=capture)
    if p.returncode:
        raise RuntimeError("Command failed: " + " ".join(map(str, args[:4])))
    return p.stdout if capture else None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--kubeconfig", default=str(ROOT / ".local/kubeconfig.yaml"))
    args = parser.parse_args()
    if not re.fullmatch(r"cafeteria:devsecops-[A-Za-z0-9_.-]+", args.image):
        raise RuntimeError("Se requiere un tag local explicito")
    kubectl = ["kubectl", "--kubeconfig", args.kubeconfig]
    if command(kubectl + ["config", "current-context"], True).strip() != "kind-cafeteria-devsecops":
        raise RuntimeError("Se requiere el contexto local esperado")
    kind = str(ROOT / ".local/bin/kind.exe") if (ROOT / ".local/bin/kind.exe").exists() else "kind"
    command([kind, "load", "docker-image", args.image, "--name", "cafeteria-devsecops"])
    text = command(["kubectl", "kustomize", "k8s/local"], True)
    if text.count("image: cafeteria:devsecops-1") != 1:
        raise RuntimeError("Imagen base de Kustomize inesperada")
    text = text.replace("image: cafeteria:devsecops-1", "image: " + args.image)
    # Namespace y RBAC se preparan desde el host; Jenkins solo gestiona recursos namespaced.
    documents = [doc for doc in text.split("---") if not re.search(r"(?m)^kind: Namespace\s*$", doc)]
    text = "---".join(documents)
    target = ROOT / "reports/rendered-manifests.yaml"
    target.parent.mkdir(exist_ok=True)
    target.write_text(text, encoding="utf-8")
    command(kubectl + ["-n", "cafeteria-devsecops", "get", "secret", "cafeteria-agustin", "-o", "name"])
    command(kubectl + ["apply", "-f", target])
    try:
        command(kubectl + ["-n", "cafeteria-devsecops", "rollout", "status",
                          "deployment/cafeteria-agustin", "--timeout=180s"])
    except RuntimeError:
        command(kubectl + ["-n", "cafeteria-devsecops", "rollout", "undo", "deployment/cafeteria-agustin"])
        raise

if __name__ == "__main__":
    main()
