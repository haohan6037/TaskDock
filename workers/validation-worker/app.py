from __future__ import annotations

import glob
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI
from pydantic import BaseModel

WORKER_NAME = os.getenv("WORKER_NAME", "validation-worker")
WORKER_MODEL = "none"
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "/project"))
WORKER_HOST = os.getenv("WORKER_HOST", "host.docker.internal")
TASK_TIMEOUT_SECONDS = int(os.getenv("TASK_TIMEOUT_SECONDS", "120"))

app = FastAPI(title="TaskDock Validation Worker")


class TaskRequest(BaseModel):
    task_id: str
    task_type: str
    input: str
    constraints: dict[str, Any] = {}
    memory_context: str = ""


def run_command(name: str, command: list[str], timeout: int = TASK_TIMEOUT_SECONDS) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = "\n".join(part for part in [completed.stdout, completed.stderr] if part).strip()
        return {
            "name": name,
            "status": "pass" if completed.returncode == 0 else "fail",
            "summary": output[:300] if output else "command completed",
            "details": output,
        }
    except Exception as exc:
        return {"name": name, "status": "fail", "summary": str(exc), "details": str(exc)}


def docker_compose_config_check() -> dict[str, Any]:
    result = run_command("docker compose config", ["docker", "compose", "config"])
    if result["status"] == "pass":
        return result
    fallback = run_command("docker compose config", ["docker-compose", "config"])
    if fallback["status"] == "pass":
        fallback["summary"] = "docker-compose config passed"
    else:
        fallback["details"] = f"docker compose output:\n{result['details']}\n\ndocker-compose output:\n{fallback['details']}"
    return fallback


def health_check(worker: str, port: int) -> dict[str, Any]:
    url = f"http://{WORKER_HOST}:{port}/health"
    try:
        response = requests.get(url, timeout=5)
        passed = response.ok and response.json().get("status") == "ok"
        return {
            "name": f"{worker} health",
            "status": "pass" if passed else "fail",
            "summary": f"{worker} returned {response.status_code}",
            "details": response.text,
        }
    except Exception as exc:
        return {"name": f"{worker} health", "status": "fail", "summary": str(exc), "details": str(exc)}


def registry_json_check() -> dict[str, Any]:
    try:
        data = json.loads((PROJECT_ROOT / "registry" / "workers.json").read_text(encoding="utf-8"))
        return {
            "name": "registry/workers.json JSON valid",
            "status": "pass",
            "summary": f"{len(data)} workers registered",
            "details": json.dumps(data, ensure_ascii=False, indent=2),
        }
    except Exception as exc:
        return {"name": "registry/workers.json JSON valid", "status": "fail", "summary": str(exc), "details": str(exc)}


def choose_worker_from_registry(task_text: str, task_type: str = "") -> dict[str, Any]:
    workers = json.loads((PROJECT_ROOT / "registry" / "workers.json").read_text(encoding="utf-8"))
    lowered = f"{task_type} {task_text}".lower()

    demo_markers = ["demo", "template", "模板", "示例"]
    doc_markers = ["doc", "document", "markdown", "proposal", "summary", "format", "文档", "提案", "总结"]

    if any(marker in lowered for marker in demo_markers) and "demo-worker" in workers:
        return workers["demo-worker"]
    if any(marker in lowered for marker in doc_markers) and "doc-worker" in workers:
        return workers["doc-worker"]
    if task_type:
        for worker in workers.values():
            if worker.get("type") == task_type:
                return worker
            if task_type in worker.get("skills", []):
                return worker
    for worker in workers.values():
        if worker.get("fallback"):
            return worker
    raise ValueError("No matching worker and no fallback worker registered.")


def routing_check(name: str, task_text: str, task_type: str, expected_service: str) -> dict[str, Any]:
    try:
        worker = choose_worker_from_registry(task_text, task_type)
        actual = worker.get("docker_service")
        passed = actual == expected_service
        return {
            "name": name,
            "status": "pass" if passed else "fail",
            "summary": f"expected {expected_service}, got {actual}",
            "details": json.dumps(worker, ensure_ascii=False, indent=2),
        }
    except Exception as exc:
        return {"name": name, "status": "fail", "summary": str(exc), "details": str(exc)}


def git_summary() -> dict[str, Any]:
    result = run_command("git status summary", ["git", "status", "--short"])
    lines = [line for line in result.get("details", "").splitlines() if line.strip()]
    return {
        "status": result["status"],
        "short": lines,
        "has_changes": bool(lines),
    }


def generated_file_check() -> dict[str, Any]:
    task_files = sorted(glob.glob(str(PROJECT_ROOT / "memory" / "tasks" / "*.json")))
    return {
        "name": "memory/tasks generated files",
        "status": "pass",
        "summary": f"{len(task_files)} generated task history files found; do not commit them.",
        "details": "\n".join(str(Path(path).relative_to(PROJECT_ROOT)) for path in task_files[-20:]),
    }


def forbidden_path_check() -> dict[str, Any]:
    tracked = run_command("tracked files", ["git", "ls-files", ".venv", "logs", "workspaces"])
    staged = run_command("staged files", ["git", "diff", "--cached", "--name-only"])
    tracked_lines = [line for line in tracked.get("details", "").splitlines() if line.strip()]
    staged_forbidden = [
        line
        for line in staged.get("details", "").splitlines()
        if line.startswith((".venv/", "logs/", "workspaces/"))
    ]
    passed = not tracked_lines and not staged_forbidden
    return {
        "name": "forbidden paths not submitted",
        "status": "pass" if passed else "fail",
        "summary": "no forbidden generated paths tracked or staged" if passed else "forbidden paths detected",
        "details": json.dumps({"tracked": tracked_lines, "staged": staged_forbidden}, ensure_ascii=False, indent=2),
    }


def run_validation_report() -> dict[str, Any]:
    checks = [
        run_command("Python compile checks", ["python3", "-m", "py_compile", "workers/doc-worker/app.py", "brain/worker_registry.py", "workers/validation-worker/app.py"]),
        docker_compose_config_check(),
        registry_json_check(),
        health_check("base-worker", 8811),
        health_check("doc-worker", 8812),
        health_check("demo-worker", 8817),
        routing_check("dispatcher generic task routes to base-worker", "Run a generic scaffold validation task.", "generic", "base-worker"),
        routing_check("dispatcher document task routes to doc-worker", "Format this proposal as Markdown sections.", "document", "doc-worker"),
        routing_check("dispatcher demo/template task routes to demo-worker", "Run demo template validation.", "demo", "demo-worker"),
        generated_file_check(),
        forbidden_path_check(),
    ]
    git = git_summary()
    overall = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    return {
        "worker": WORKER_NAME,
        "model": WORKER_MODEL,
        "overall": overall,
        "checks": checks,
        "git_summary": git,
        "commit_advice": {
            "ready": overall == "pass",
            "include": [],
            "exclude": ["memory/tasks/*.json", ".venv/", "logs/", "workspaces/"],
        },
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "worker": WORKER_NAME, "model": WORKER_MODEL}


@app.post("/run-task")
def run_task(req: TaskRequest) -> dict[str, Any]:
    report = run_validation_report()
    return {
        "task_id": req.task_id,
        "status": "success" if report["overall"] == "pass" else "failed",
        **report,
    }
