from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from control_panel.rendering import page
from control_panel.rendering_setup import setup_page
from control_panel.services.setup_service import setup_checks

router = APIRouter()


@router.get("/setup", response_class=HTMLResponse)
def setup_status() -> str:
    return page(setup_page(setup_checks()))
