import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="OpenClawBrain Doc Worker")


class TaskRequest(BaseModel):
    task_id: str
    task_type: str
    input: str
    constraints: Dict[str, Any] = {}
    memory_context: str = ""


def split_points(text: str) -> List[str]:
    lines = [line.strip(" -\t") for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        return lines
    sentences = [item.strip() for item in re.split(r"[。.!?]\s*", text) if item.strip()]
    return sentences[:8] or [text.strip()] if text.strip() else []


def markdown_outline(req: TaskRequest) -> str:
    points = split_points(req.input)
    bullets = "\n".join(f"- {point}" for point in points[:6]) or "- No input provided."
    return (
        "# Document Draft\n\n"
        "## Summary\n\n"
        f"{req.input.strip()[:500] or 'No input provided.'}\n\n"
        "## Key Points\n\n"
        f"{bullets}\n\n"
        "## Suggested Structure\n\n"
        "1. Context\n"
        "2. Main Content\n"
        "3. Decisions or Output\n"
        "4. Next Steps\n"
    )


def proposal_format(req: TaskRequest) -> str:
    return (
        "# Proposal Draft\n\n"
        "Status: proposed\n\n"
        "Requires approval before implementation: yes\n\n"
        "## Goal\n\n"
        f"{req.input.strip() or 'TBD'}\n\n"
        "## Motivation\n\n"
        "TBD\n\n"
        "## Proposed New Files\n\n"
        "- TBD\n\n"
        "## Proposed Modified Files\n\n"
        "- TBD\n\n"
        "## Why This Shape\n\n"
        "TBD\n\n"
        "## Risk Level\n\n"
        "TBD\n\n"
        "## Validation Plan\n\n"
        "TBD\n\n"
        "## Approval\n\n"
        "This proposal is not approved yet.\n"
    )


def choose_document_output(req: TaskRequest) -> str:
    combined = f"{req.task_type} {req.input}".lower()
    if "proposal" in combined or "提案" in combined:
        return proposal_format(req)
    return markdown_outline(req)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "worker": os.getenv("WORKER_NAME", "doc-worker"),
        "model": os.getenv("WORKER_MODEL", "none"),
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/run-task")
def run_task(req: TaskRequest):
    memory_preview = req.memory_context[:800] if req.memory_context else ""
    markdown = choose_document_output(req)

    return {
        "task_id": req.task_id,
        "status": "success",
        "worker": os.getenv("WORKER_NAME", "doc-worker"),
        "model": os.getenv("WORKER_MODEL", "none"),
        "received_task_type": req.task_type,
        "memory_loaded": bool(req.memory_context),
        "memory_preview": memory_preview,
        "memory_boundary": "doc-worker only uses memory_context from the request and does not read long-term memory.",
        "output_format": "markdown",
        "markdown": markdown,
        "cost_estimate": {
            "model": "none",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost": 0,
        },
    }
