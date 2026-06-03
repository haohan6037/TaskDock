from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from control_panel.services.worker_template_service import render_template, validate_template_files

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")
WORKER_SPECS_DIR = PROJECT_ROOT / "registry" / "worker_specs"
WORKERS_DIR = PROJECT_ROOT / "workers"
PROMPTS_DIR = PROJECT_ROOT / "memory" / "prompts"
COMPOSE_PATH = PROJECT_ROOT / "docker-compose.yml"
REGISTRY_PATH = PROJECT_ROOT / "registry" / "workers.json"

REQUIRED_SPEC_FIELDS = [
    "worker_name",
    "worker_type",
    "runtime",
    "preferred_model",
    "port",
    "skills",
    "purpose",
    "risk_level",
    "permissions",
    "status",
    "created_at",
]


@dataclass(frozen=True)
class GeneratedWorker:
    worker_name: str
    created_files: list[Path]
    modified_files: list[Path]


def load_worker_spec(worker_name: str) -> dict:
    path = WORKER_SPECS_DIR / f"{worker_name}.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    missing = [field for field in REQUIRED_SPEC_FIELDS if field not in spec]
    if missing:
        raise ValueError(f"Worker spec is missing fields: {', '.join(missing)}")
    if spec["status"] != "draft":
        raise ValueError("Only draft worker specs can generate workers.")
    if spec["preferred_model"] != "none":
        raise ValueError("The first template generator only supports model:none workers.")
    return spec


def list_items(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- none"


def template_values(spec: dict) -> dict[str, str]:
    skills = [str(item) for item in spec.get("skills", [])]
    permissions = [str(item) for item in spec.get("permissions", [])]
    return {
        "WORKER_NAME": spec["worker_name"],
        "WORKER_TYPE": spec["worker_type"],
        "WORKER_MODEL": "none",
        "WORKER_SKILLS": ",".join(skills),
        "PORT": str(spec["port"]),
        "RUNTIME": spec["runtime"],
        "PURPOSE": spec["purpose"],
        "SKILLS_LIST": list_items(skills),
        "PERMISSIONS_LIST": list_items(permissions),
        "RISK_LEVEL": spec["risk_level"],
    }


def add_compose_service(spec: dict) -> None:
    service_name = spec["worker_name"]
    content = COMPOSE_PATH.read_text(encoding="utf-8")
    if f"  {service_name}:" in content:
        raise FileExistsError(f"docker-compose.yml already contains service {service_name}")

    skills = ",".join(str(item) for item in spec.get("skills", []))
    block = f"""
  {service_name}:
    build:
      context: ./workers/{service_name}
    container_name: openclawbrain-{service_name}
    ports:
      - "{spec['port']}:{spec['port']}"
    volumes:
      - ./workspaces:/workspaces
    environment:
      - WORKER_NAME={service_name}
      - WORKER_TYPE={spec['worker_type']}
      - WORKER_MODEL=none
      - WORKER_SKILLS={skills}
"""
    COMPOSE_PATH.write_text(content.rstrip() + "\n" + block, encoding="utf-8")


def add_registry_worker(spec: dict) -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    worker_name = spec["worker_name"]
    if worker_name in registry:
        raise FileExistsError(f"registry/workers.json already contains {worker_name}")

    registry[worker_name] = {
        "type": spec["worker_type"],
        "endpoint": f"http://localhost:{spec['port']}/run-task",
        "docker_service": worker_name,
        "model": "none",
        "skills": spec.get("skills", []),
        "cost_level": "free",
        "risk_level": spec["risk_level"],
    }
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_worker(worker_name: str) -> GeneratedWorker:
    validate_template_files()
    spec = load_worker_spec(worker_name)
    name = spec["worker_name"]
    worker_dir = WORKERS_DIR / name
    prompt_path = PROMPTS_DIR / f"{name}.md"

    if worker_dir.exists():
        raise FileExistsError(f"Worker directory already exists: {worker_dir}")
    if prompt_path.exists():
        raise FileExistsError(f"Prompt file already exists: {prompt_path}")

    values = template_values(spec)
    worker_dir.mkdir(parents=True, exist_ok=False)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    files = {
        worker_dir / "Dockerfile": render_template("Dockerfile.template", values),
        worker_dir / "app.py": render_template("app.py.template", values),
        worker_dir / "requirements.txt": render_template("requirements.txt", values),
        prompt_path: render_template("prompt.md.template", values),
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")

    add_compose_service(spec)
    add_registry_worker(spec)

    return GeneratedWorker(
        worker_name=name,
        created_files=list(files.keys()),
        modified_files=[COMPOSE_PATH, REGISTRY_PATH],
    )
