import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILE = PROJECT_ROOT / "registry" / "workers.json"

def load_workers() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))

def choose_worker(task_text: str) -> dict:
    """
    Stage 2 routing:
    Use doc-worker for obvious document tasks when registered.
    Keep base-worker as fallback.
    """
    workers = load_workers()
    lowered = task_text.lower()
    doc_markers = [
        "markdown",
        "document",
        "documentation",
        "summary",
        "summarize",
        "proposal",
        "format",
        "outline",
        "文档",
        "总结",
        "摘要",
        "提案",
        "格式",
        "大纲",
    ]
    if "doc-worker" in workers and any(marker in lowered for marker in doc_markers):
        return workers["doc-worker"]
    return workers["base-worker"]
