from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from control_panel.rendering import page, validation_section
from control_panel.services.validation_service import run_validation

router = APIRouter()


@router.get("/validate", response_class=HTMLResponse)
def validate_page() -> str:
    return page([validation_section()])


@router.post("/validate/run", response_class=HTMLResponse)
def validate_run() -> str:
    return page([validation_section(run_validation())])
