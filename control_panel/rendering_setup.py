from __future__ import annotations

import html

from control_panel.services.setup_service import SetupCheck


def setup_page(checks: list[SetupCheck]) -> list[str]:
    rows = []
    for check in checks:
        status = "pass" if check.passed else "fail"
        rows.append(
            "<tr>"
            f"<td>{html.escape(check.name)}</td>"
            f"<td><strong class=\"{status}\">{status}</strong></td>"
            f"<td>{html.escape(check.summary)}</td>"
            f"<td><details><summary>details</summary><pre>{html.escape(check.details)}</pre></details></td>"
            "</tr>"
        )

    return [
        (
            "<section><h2>Setup Status</h2>"
            "<p class=\"notice\">Read-only environment checks for TaskDock bootstrap readiness. "
            "This page does not start Docker workers, commit, push, or run arbitrary shell commands.</p>"
            "<table><thead><tr><th>check</th><th>status</th><th>summary</th><th>details</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</section>"
        )
    ]
