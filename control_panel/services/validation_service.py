from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

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


def command_step(name: str, checks: str, operation: str, result: CommandResult) -> ValidationStep:
    output = result.stdout
    if result.stderr:
        output = f"{output}\n{result.stderr}".strip()
    return ValidationStep(name=name, checks=checks, operation=operation, passed=result.passed, output=output)


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
    steps = [
        command_step(
            "Python compile",
            "doc-worker app and worker registry compile.",
            "python3 -m py_compile workers/doc-worker/app.py brain/worker_registry.py",
            run_allowed("compile_doc_worker"),
        ),
        command_step(
            "Worker registry JSON",
            "registry/workers.json is valid JSON.",
            "python3 -m json.tool registry/workers.json",
            run_allowed("json_workers"),
        ),
        command_step(
            "Docker Compose config",
            "Docker Compose configuration is valid.",
            "docker compose config",
            run_allowed("docker_compose_config"),
        ),
        command_step(
            "Docker Compose status",
            "Worker status can be listed.",
            "docker compose ps",
            compose_ps(),
        ),
        *health_steps(),
        route_check_step(),
    ]
    LATEST_VALIDATION = steps
    return steps


def latest_validation() -> Optional[List[ValidationStep]]:
    return LATEST_VALIDATION


def validation_passed() -> bool:
    return bool(LATEST_VALIDATION) and all(step.passed for step in LATEST_VALIDATION)
