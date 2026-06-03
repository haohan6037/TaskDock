from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from control_panel.rendering import page, section
from control_panel.services.filesystem_service import load_worker_registry
from control_panel.services.worker_service import check_all_health, compose_ps

router = APIRouter()


@router.get("/workers", response_class=HTMLResponse)
def workers_page() -> str:
    content = [
        section("Registered workers", json.dumps(load_worker_registry(), ensure_ascii=False, indent=2)),
        section("Docker compose ps", compose_ps().stdout or "No docker compose ps output."),
    ]
    for worker, health in check_all_health().items():
        content.append(section(f"{worker} health", health.output))
    return page(content)
