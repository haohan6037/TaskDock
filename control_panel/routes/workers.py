from __future__ import annotations

from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from control_panel.rendering import page, section
from control_panel.rendering_workers import action_result_section, workers_table
from control_panel.services.worker_service import check_all_health, compose_ps
from control_panel.services.worker_lifecycle_service import registered_workers, run_lifecycle_action

router = APIRouter()


@router.get("/workers", response_class=HTMLResponse)
def workers_page() -> str:
    content = [
        workers_table(registered_workers(), check_all_health()),
        section("Docker compose ps", compose_ps().stdout or "No docker compose ps output."),
    ]
    return page(content)


@router.post("/workers/action", response_class=HTMLResponse)
async def worker_action(request: Request) -> str:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    worker_name = parsed.get("worker_name", [""])[0]
    action = parsed.get("action", [""])[0]
    try:
        result = run_lifecycle_action(worker_name, action)
    except Exception as exc:
        from control_panel.services.worker_lifecycle_service import LifecycleResult

        result = LifecycleResult(
            worker=worker_name,
            action=action,
            passed=False,
            summary=f"{action or 'action'} failed",
            output=str(exc),
        )
    content = [
        action_result_section(result),
        workers_table(registered_workers(), check_all_health()),
        section("Docker compose ps", compose_ps().stdout or "No docker compose ps output."),
    ]
    return page(content)
