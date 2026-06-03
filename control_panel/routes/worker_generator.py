from __future__ import annotations

from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from control_panel.rendering import page
from control_panel.rendering_worker_specs import worker_spec_form, worker_specs_section
from control_panel.services.worker_generator_service import generate_worker
from control_panel.services.worker_spec_service import list_worker_specs

router = APIRouter()


@router.post("/worker-specs/generate-worker", response_class=HTMLResponse)
async def generate_worker_action(request: Request) -> str:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    worker_name = parsed.get("worker_name", [""])[0]
    try:
        generated = generate_worker(worker_name)
        return page([worker_spec_form(), worker_specs_section(list_worker_specs(), generated_worker=generated)])
    except Exception as exc:
        return page([worker_spec_form(), worker_specs_section(list_worker_specs(), error=str(exc))])
