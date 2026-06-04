from __future__ import annotations

import html

from control_panel.services.worker_lifecycle_service import LifecycleResult
from control_panel.services.worker_service import HealthResult


def worker_action_form(worker_name: str, action: str, label: str) -> str:
    return (
        '<form class="inline" method="post" action="/workers/action">'
        f'<input type="hidden" name="worker_name" value="{html.escape(worker_name)}">'
        f'<input type="hidden" name="action" value="{html.escape(action)}">'
        f'<button type="submit">{html.escape(label)}</button>'
        "</form>"
    )


def action_result_section(result: LifecycleResult | None) -> str:
    if not result:
        return ""
    status = "pass" if result.passed else "fail"
    return (
        "<section><h2>Lifecycle Result</h2>"
        f"<p><strong>{html.escape(result.worker)}</strong> "
        f"<span class=\"{status}\">{html.escape(result.summary)}</span></p>"
        f"<details open><summary>details</summary><pre>{html.escape(result.output)}</pre></details>"
        "</section>"
    )


def workers_table(workers: dict, health: dict[str, HealthResult]) -> str:
    rows = []
    for worker_name, metadata in sorted(workers.items()):
        health_result = health.get(worker_name)
        health_passed = bool(health_result and health_result.passed)
        health_text = "pass" if health_passed else "fail"
        skills = ", ".join(str(item) for item in metadata.get("skills", []))
        actions = "".join(
            [
                worker_action_form(worker_name, "start", "Start"),
                worker_action_form(worker_name, "stop", "Stop"),
                worker_action_form(worker_name, "restart", "Restart"),
                worker_action_form(worker_name, "health", "Health Check"),
                worker_action_form(worker_name, "logs", "View Logs"),
            ]
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(worker_name)}</td>"
            f"<td>{html.escape(str(metadata.get('type', '')))}</td>"
            f"<td>{html.escape(str(metadata.get('docker_service', '')))}</td>"
            f"<td>{html.escape(str(metadata.get('endpoint', '')))}</td>"
            f"<td>{html.escape(str(metadata.get('model', '')))}</td>"
            f"<td>{html.escape(skills)}</td>"
            f"<td><strong class=\"{health_text}\">{health_text}</strong></td>"
            f"<td>{actions}</td>"
            "</tr>"
        )
    return (
        "<section><h2>Registered Workers</h2>"
        "<table><thead><tr>"
        "<th>name</th><th>type</th><th>docker_service</th><th>endpoint</th>"
        "<th>model</th><th>skills</th><th>health</th><th>actions</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "</section>"
    )
