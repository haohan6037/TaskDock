from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import requests

from control_panel.command_whitelist import CommandResult, run_allowed


LOCAL_HEALTH_ENDPOINTS = {
    "base-worker": "http://127.0.0.1:8811/health",
    "doc-worker": "http://127.0.0.1:8812/health",
}


@dataclass
class HealthResult:
    worker: str
    url: str
    passed: bool
    output: str


def compose_ps() -> CommandResult:
    return run_allowed("docker_compose_ps")


def compose_up() -> CommandResult:
    return run_allowed("docker_compose_up")


def check_worker_health(worker: str) -> HealthResult:
    url = LOCAL_HEALTH_ENDPOINTS[worker]
    try:
        response = requests.get(url, timeout=5)
        return HealthResult(worker=worker, url=url, passed=response.ok, output=response.text)
    except Exception as exc:
        return HealthResult(worker=worker, url=url, passed=False, output=str(exc))


def check_all_health() -> Dict[str, HealthResult]:
    return {worker: check_worker_health(worker) for worker in LOCAL_HEALTH_ENDPOINTS}
