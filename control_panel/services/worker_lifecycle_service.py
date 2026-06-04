from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Literal

from control_panel.command_whitelist import PROJECT_ROOT
from control_panel.services.filesystem_service import load_worker_registry
from control_panel.services.worker_service import HealthResult, check_worker_health

LifecycleAction = Literal["start", "stop", "restart", "health", "logs"]


@dataclass(frozen=True)
class LifecycleResult:
    worker: str
    action: str
    passed: bool
    summary: str
    output: str


def registered_workers() -> dict:
    return load_worker_registry()


def allowed_services() -> dict[str, str]:
    services = {}
    for worker_name, metadata in registered_workers().items():
        service = metadata.get("docker_service", "")
        if service:
            services[worker_name] = service
    return services


def resolve_service(worker_name: str) -> str:
    services = allowed_services()
    if worker_name not in services:
        raise ValueError(f"Worker is not registered: {worker_name}")
    return services[worker_name]


def run_compose_action(worker_name: str, action: LifecycleAction) -> LifecycleResult:
    service = resolve_service(worker_name)
    commands = {
        "start": ["docker", "compose", "up", "-d", service],
        "stop": ["docker", "compose", "stop", service],
        "restart": ["docker", "compose", "restart", service],
        "logs": ["docker", "compose", "logs", "--tail", "100", service],
    }
    if action not in commands:
        raise ValueError(f"Unsupported compose action: {action}")

    completed = subprocess.run(
        commands[action],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part).strip()
    return LifecycleResult(
        worker=worker_name,
        action=action,
        passed=completed.returncode == 0,
        summary=f"{action} {'passed' if completed.returncode == 0 else 'failed'} for {service}",
        output=output or "No output.",
    )


def run_health_action(worker_name: str) -> LifecycleResult:
    result: HealthResult = check_worker_health(worker_name)
    return LifecycleResult(
        worker=worker_name,
        action="health",
        passed=result.passed,
        summary=f"health {'passed' if result.passed else 'failed'} for {worker_name}",
        output=result.output,
    )


def run_lifecycle_action(worker_name: str, action: str) -> LifecycleResult:
    if action == "health":
        resolve_service(worker_name)
        return run_health_action(worker_name)
    if action in {"start", "stop", "restart", "logs"}:
        return run_compose_action(worker_name, action)  # type: ignore[arg-type]
    raise ValueError(f"Unsupported lifecycle action: {action}")
