import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILE = PROJECT_ROOT / "registry" / "workers.json"

def load_workers() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))

def choose_worker(task_text: str) -> dict:
    """
    Stage 1 routing:
    Always use base-worker.
    Later this should route by task type and skills.
    """
    workers = load_workers()
    return workers["base-worker"]
