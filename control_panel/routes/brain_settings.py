from __future__ import annotations

from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from control_panel.rendering import page
from control_panel.rendering_brain_settings import brain_settings_page
from control_panel.services.brain_settings_service import (
    load_brain_settings,
    load_permissions_settings,
    save_brain_settings,
    save_permissions_settings,
)

router = APIRouter()


@router.get("/brain-settings", response_class=HTMLResponse)
def brain_settings() -> str:
    return page(brain_settings_page(load_brain_settings(), load_permissions_settings()))


@router.post("/brain-settings/brain", response_class=HTMLResponse)
async def save_brain_settings_action(request: Request) -> str:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    result = save_brain_settings(parsed.get("settings_json", ["{}"])[0])
    return page(brain_settings_page(load_brain_settings(), load_permissions_settings(), result))


@router.post("/brain-settings/permissions", response_class=HTMLResponse)
async def save_permissions_settings_action(request: Request) -> str:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    result = save_permissions_settings(parsed.get("settings_json", ["{}"])[0])
    return page(brain_settings_page(load_brain_settings(), load_permissions_settings(), result))
