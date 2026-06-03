from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")
PROPOSALS_DIR = PROJECT_ROOT / "memory" / "proposals"
REGISTRY_FILE = PROJECT_ROOT / "registry" / "workers.json"


def project_path(*parts: str) -> Path:
    path = (PROJECT_ROOT.joinpath(*parts)).resolve()
    path.relative_to(PROJECT_ROOT)
    return path


def proposal_files() -> list[Path]:
    if not PROPOSALS_DIR.exists():
        return []
    return sorted(PROPOSALS_DIR.glob("*.md"))


def proposal_names_text() -> str:
    files = [path.name for path in proposal_files()]
    return "\n".join(files) if files else "No proposal files found."


def load_worker_registry() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
