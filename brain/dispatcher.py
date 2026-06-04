import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from memory_manager import retrieve_memory_context
from proposal_manager import is_proposal_approved, read_proposal
from worker_registry import choose_worker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASK_HISTORY_DIR = PROJECT_ROOT / "memory" / "tasks"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def save_task_history(record: dict) -> Path:
    TASK_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    path = TASK_HISTORY_DIR / f"{record['task_id']}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def health_url_for(worker: dict) -> str:
    endpoint = worker.get("endpoint", "")
    if endpoint.endswith("/run-task"):
        url = endpoint[: -len("/run-task")] + "/health"
    else:
        url = endpoint.rstrip("/") + "/health"
    return url.replace("localhost", "127.0.0.1")

def check_worker_health(worker: dict) -> None:
    worker_name = worker.get("docker_service") or worker.get("name") or "unknown-worker"
    url = health_url_for(worker)
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Selected worker {worker_name} is not healthy at {url}: {exc}") from exc

def looks_like_implementation_task(task_text: str) -> bool:
    markers = [
        "implement",
        "implementation",
        "modify",
        "change code",
        "edit",
        "add file",
        "新增",
        "实现",
        "修改",
        "改代码",
        "添加",
    ]
    lowered = task_text.lower()
    return any(marker in lowered for marker in markers)

def refusal_record(task_text: str, proposal_id: str) -> dict:
    task_id = "task_" + uuid.uuid4().hex[:12]
    now = now_iso()
    record = {
        "task_id": task_id,
        "status": "blocked",
        "input": task_text,
        "worker": None,
        "proposal_id": proposal_id.zfill(3),
        "started_at": now,
        "finished_at": now,
        "result": None,
        "error": f"Proposal {proposal_id.zfill(3)} is not approved for implementation.",
    }
    history_path = save_task_history(record)
    record["history_path"] = str(history_path)
    return record

def dispatch(task_text: str, proposal_id: Optional[str] = None) -> dict:
    if proposal_id and looks_like_implementation_task(task_text) and not is_proposal_approved(proposal_id):
        return refusal_record(task_text, proposal_id)

    task_id = "task_" + uuid.uuid4().hex[:12]
    worker = choose_worker(task_text)
    memory_context = retrieve_memory_context(task_text, proposal_id=proposal_id)

    payload = {
        "task_id": task_id,
        "task_type": "scaffold_test",
        "input": task_text,
        "constraints": {
            "output_format": "markdown",
            "language": "zh-CN"
        },
        "memory_context": memory_context
    }

    started_at = now_iso()

    try:
        check_worker_health(worker)
        response = requests.post(worker["endpoint"], json=payload, timeout=30)
        response.raise_for_status()
        worker_result = response.json()
        status = "success"
        error = None
    except Exception as exc:
        worker_result = None
        status = "failed"
        error = str(exc)

    finished_at = now_iso()

    record = {
        "task_id": task_id,
        "status": status,
        "input": task_text,
        "worker": worker,
        "proposal_id": proposal_id.zfill(3) if proposal_id else None,
        "started_at": started_at,
        "finished_at": finished_at,
        "result": worker_result,
        "error": error
    }

    history_path = save_task_history(record)
    record["history_path"] = str(history_path)
    return record

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dispatch an OpenClaw Brain task to a worker.")
    parser.add_argument("task", nargs="+", help="Task text to dispatch.")
    parser.add_argument("--proposal", help="Proposal id to load as explicit task context.")
    args = parser.parse_args()

    if args.proposal:
        read_proposal(args.proposal)

    task_text = " ".join(args.task)
    result = dispatch(task_text, proposal_id=args.proposal)
    print(json.dumps(result, ensure_ascii=False, indent=2))
