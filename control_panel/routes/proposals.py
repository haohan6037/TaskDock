from __future__ import annotations

from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from control_panel.rendering import create_worker_form, page, section
from control_panel.services.filesystem_service import proposal_names_text
from control_panel.services.proposal_service import create_worker_proposal

router = APIRouter()


@router.get("/proposals", response_class=HTMLResponse)
def proposals_page() -> str:
    return page([create_worker_form(), section("Proposal files", proposal_names_text())])


@router.post("/proposals/create-worker", response_class=HTMLResponse)
async def create_worker_proposal_action(request: Request) -> str:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    data = {key: values[0] if values else "" for key, values in parsed.items()}
    created_path = create_worker_proposal(data)
    return page([create_worker_form(created_path), section("Proposal files", proposal_names_text())])
