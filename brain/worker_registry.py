from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILE = PROJECT_ROOT / "registry" / "workers.json"

def load_workers() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def first_registered_worker(workers: dict, candidates: list[str]) -> dict | None:
    for worker_name in candidates:
        if worker_name in workers:
            return workers[worker_name]
    return None


def fallback_worker(workers: dict) -> dict:
    for worker in workers.values():
        if worker.get("fallback") is True:
            return worker
    if "base-worker" in workers:
        return workers["base-worker"]
    raise ValueError("No fallback worker is registered.")


def choose_worker(task_text: str) -> dict:
    """
    Registry-backed routing.

    If a specific worker type is registered, route to it. If that target is
    not registered yet, use the registered fallback worker.
    """
    workers = load_workers()
    lowered = task_text.lower()

    routing_rules = [
        (
            [
                "validation",
                "qa",
                "check",
                "gate",
                "test-gate",
                "验证",
                "校验",
                "检查",
            ],
            ["validation-worker"],
        ),
        (
            [
                "demo",
                "template",
                "example",
                "generated-worker",
                "模板",
                "示例",
            ],
            ["demo-worker"],
        ),
        (
            [
                "doc",
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
            ],
            ["doc-worker"],
        ),
    ]

    for markers, candidates in routing_rules:
        if any(marker in lowered for marker in markers):
            worker = first_registered_worker(workers, candidates)
            if worker:
                return worker
            return fallback_worker(workers)

    return fallback_worker(workers)
