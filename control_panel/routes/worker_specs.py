from __future__ import annotations

from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from control_panel.rendering import page
from control_panel.rendering_worker_specs import worker_spec_form, worker_specs_section
from control_panel.services.worker_spec_service import create_worker_spec, list_worker_specs
from control_panel.services.worker_proposal_service import generate_worker_proposal

router = APIRouter()


@router.get("/worker-specs", response_class=HTMLResponse)
def worker_specs_page() -> str:
    return page([worker_spec_form(), worker_specs_section(list_worker_specs())])


@router.post("/worker-specs", response_class=HTMLResponse)
async def create_worker_spec_action(request: Request) -> str:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    data = {key: values[0] if values else "" for key, values in parsed.items()}
    created_path = create_worker_spec(data)
    return page([worker_spec_form(created_path), worker_specs_section(list_worker_specs())])


@router.post("/worker-specs/generate-proposal", response_class=HTMLResponse)
async def generate_worker_proposal_action(request: Request) -> str:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    worker_name = parsed.get("worker_name", [""])[0]
    generated_path = generate_worker_proposal(worker_name)
    return page([worker_spec_form(), worker_specs_section(list_worker_specs(), generated_path=generated_path)])
