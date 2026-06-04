from __future__ import annotations

import html
import json

from control_panel.services.brain_settings_service import SaveResult


def result_message(result: SaveResult | None) -> str:
    if not result:
        return ""
    status = "pass" if result.passed else "fail"
    return f'<p class="{status}">{html.escape(result.message)}</p>'


def json_form(title: str, action: str, data: dict, result: SaveResult | None = None) -> str:
    rendered = json.dumps(data, ensure_ascii=False, indent=2)
    return (
        f"<section><h2>{html.escape(title)}</h2>"
        f"{result_message(result)}"
        f'<form method="post" action="{html.escape(action)}">'
        f'<textarea name="settings_json" rows="18">{html.escape(rendered)}</textarea>'
        '<button type="submit">Save JSON</button>'
        "</form>"
        "<details><summary>current json</summary>"
        f"<pre>{html.escape(rendered)}</pre>"
        "</details>"
        "</section>"
    )


def brain_settings_page(brain: dict, permissions: dict, result: SaveResult | None = None) -> list[str]:
    notice = (
        "<section><h2>Brain Settings</h2>"
        "<p class=\"notice\">These files are passive configuration for now. This page does not execute shell commands, does not push, and does not change worker runtime behavior.</p>"
        "<p class=\"notice\">Only safe fields are persisted. Automation fields are displayed but protected; auto_push_enabled is always forced to false.</p>"
        "</section>"
    )
    return [
        notice,
        json_form("config/brain.json", "/brain-settings/brain", brain, result),
        json_form("config/permissions.json", "/brain-settings/permissions", permissions, result),
    ]
