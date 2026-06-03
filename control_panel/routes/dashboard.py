from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from control_panel.rendering import create_worker_form, page, section, validation_section
from control_panel.rendering_worker_specs import worker_specs_section
from control_panel.services.dashboard_service import dashboard_data
from control_panel.services.worker_spec_service import list_worker_specs

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index() -> str:
    data = dashboard_data()
    content = [
        validation_section(),
        create_worker_form(),
        section("Git status", data["git_status"]),
        section("Docker compose ps", data["compose_ps"]),
    ]
    for worker, health in data["worker_health"].items():
        content.append(section(f"{worker} health", health.output))
    content.append(worker_specs_section(list_worker_specs()))
    content.append(section("Proposal files", data["proposal_files"]))
    return page(content)
