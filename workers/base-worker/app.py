import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="OpenClawBrain Base Worker")

class TaskRequest(BaseModel):
    task_id: str
    task_type: str
    input: str
    constraints: Dict[str, Any] = {}
    memory_context: str = ""

@app.get("/health")
def health():
    return {
        "status": "ok",
        "worker": os.getenv("WORKER_NAME", "base-worker"),
        "time": datetime.now(timezone.utc).isoformat()
    }

@app.post("/run-task")
def run_task(req: TaskRequest):
    memory_preview = req.memory_context[:800] if req.memory_context else ""

    return {
        "task_id": req.task_id,
        "status": "success",
        "worker": os.getenv("WORKER_NAME", "base-worker"),
        "received_task_type": req.task_type,
        "summary": f"Task received: {req.input[:200]}",
        "memory_loaded": bool(req.memory_context),
        "memory_preview": memory_preview,
        "recommendation": "This is the base test worker. In the next stage, route coding tasks to code-worker, document tasks to doc-worker, and data tasks to data-worker.",
        "cost_estimate": {
            "model": "none",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost": 0
        }
    }
