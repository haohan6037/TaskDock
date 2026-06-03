from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")
WORKER_SPECS_DIR = PROJECT_ROOT / "registry" / "worker_specs"


def ensure_worker_specs_dir() -> Path:
    WORKER_SPECS_DIR.mkdir(parents=True, exist_ok=True)
    return WORKER_SPECS_DIR


def normalize_worker_name(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    if not name:
        raise ValueError("worker_name is required")
    return name


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def list_worker_specs() -> list[dict]:
    specs = []
    specs_dir = ensure_worker_specs_dir()
    for path in sorted(specs_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            specs.append({"path": str(path), "file": path.name, "data": data})
        except json.JSONDecodeError as exc:
            specs.append({"path": str(path), "file": path.name, "error": str(exc), "data": {}})
    return specs


def create_worker_spec(form: dict[str, str]) -> Path:
    specs_dir = ensure_worker_specs_dir()
    worker_name = normalize_worker_name(form.get("worker_name", ""))
    path = specs_dir / f"{worker_name}.json"
    spec = {
        "worker_name": worker_name,
        "worker_type": form.get("worker_type", "").strip(),
        "runtime": form.get("runtime", "").strip(),
        "preferred_model": form.get("preferred_model", "").strip() or "none",
        "port": int(form.get("port", "0").strip()),
        "skills": split_csv(form.get("skills", "")),
        "purpose": form.get("purpose", "").strip(),
        "risk_level": form.get("risk_level", "").strip() or "low",
        "permissions": split_csv(form.get("permissions", "")),
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
