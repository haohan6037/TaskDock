from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import json
import uuid

import requests

from control_panel.command_whitelist import CommandResult, run_allowed
from control_panel.services.worker_service import check_all_health, compose_ps

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")
BRAIN_DIR = PROJECT_ROOT / "brain"
if str(BRAIN_DIR) not in sys.path:
    sys.path.insert(0, str(BRAIN_DIR))

from worker_registry import choose_worker  # noqa: E402


@dataclass
class ValidationStep:
    name: str
    checks: str
    operation: str
    passed: bool
    output: str


LATEST_VALIDATION: Optional[List[ValidationStep]] = None
VALIDATION_WORKER_URL = "http://127.0.0.1:8818/run-task"


def command_step(name: str, checks: str, operation: str, result: CommandResult) -> ValidationStep:
    output = result.stdout
    if result.stderr:
        output = f"{output}\n{result.stderr}".strip()
    return ValidationStep(name=name, checks=checks, operation=operation, passed=result.passed, output=output)


def run_dispatcher(task: str) -> CommandResult:
    return run_allowed("run_dispatcher", [task])


def extract_json_object(output: str) -> dict:
    start = output.find("{")
    end = output.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in dispatcher output.")
    return json.loads(output[start : end + 1])


def dispatcher_step(name: str, task: str, expected_worker: str) -> ValidationStep:
    result = run_dispatcher(task)
    output = result.stdout
    if result.stderr:
        output = f"{output}\n{result.stderr}".strip()
    passed = False
    try:
        payload = extract_json_object(output)
        passed = result.passed and payload.get("status") == "success" and payload.get("result", {}).get("worker") == expected_worker
    except Exception:
        passed = False
    return ValidationStep(
        name=name,
        checks=f"Dispatcher returns top-level success and result.worker is {expected_worker}.",
        operation=f".venv/bin/python brain/dispatcher.py {task}",
        passed=passed,
        output=output,
    )


def route_check_step() -> ValidationStep:
    doc_worker = choose_worker("Format this proposal as Markdown sections.").get("docker_service")
    fallback_worker = choose_worker("Run a generic scaffold test.").get("docker_service")
    passed = doc_worker == "doc-worker" and fallback_worker == "base-worker"
    output = f"document task -> {doc_worker}\ngeneric task -> {fallback_worker}"
    return ValidationStep(
        name="Routing",
        checks="Document tasks route to doc-worker and generic tasks fall back to base-worker.",
        operation="internal Python route check",
        passed=passed,
        output=output,
    )


def health_steps() -> List[ValidationStep]:
    steps = []
    for worker, result in check_all_health().items():
        steps.append(
            ValidationStep(
                name=f"{worker} health",
                checks=f"{worker} responds on its local health endpoint.",
                operation=f"structured HTTP GET {result.url}",
                passed=result.passed,
                output=result.output,
            )
        )
    return steps


def run_validation() -> List[ValidationStep]:
    global LATEST_VALIDATION
    steps = run_validation_worker()
    LATEST_VALIDATION = steps
    return steps


def run_validation_worker() -> List[ValidationStep]:
    payload = {
        "task_id": "control_panel_validation_" + uuid.uuid4().hex[:8],
        "task_type": "validation",
        "input": "Run TaskDock fixed validation flow.",
        "constraints": {"output_format": "json"},
        "memory_context": "",
    }
    try:
        response = requests.post(VALIDATION_WORKER_URL, json=payload, timeout=180)
        response.raise_for_status()
        report = response.json()
    except Exception as exc:
        return [
            ValidationStep(
                name="validation-worker",
                checks="validation-worker responds to POST /run-task.",
                operation=f"POST {VALIDATION_WORKER_URL}",
                passed=False,
                output=str(exc),
            )
        ]

    steps = []
    for check in report.get("checks", []):
        status = check.get("status") == "pass"
        output = json.dumps(check, ensure_ascii=False, indent=2)
        steps.append(
            ValidationStep(
                name=check.get("name", "unnamed check"),
                checks=check.get("summary", ""),
                operation="validation-worker fixed check",
                passed=status,
                output=output,
            )
        )
    steps.append(
        ValidationStep(
            name="validation-worker overall",
            checks="validation-worker report overall status is pass.",
            operation=f"POST {VALIDATION_WORKER_URL}",
            passed=report.get("overall") == "pass",
            output=json.dumps(report, ensure_ascii=False, indent=2),
        )
    )
    return steps


def latest_validation() -> Optional[List[ValidationStep]]:
    return LATEST_VALIDATION


def validation_passed() -> bool:
    return bool(LATEST_VALIDATION) and all(step.passed for step in LATEST_VALIDATION)
