from __future__ import annotations

import html
import json
from pathlib import Path

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")


def worker_spec_form(created_path: Path | None = None) -> str:
    message = ""
    if created_path:
        message = f"<p class=\"pass\">Created worker spec: {html.escape(str(created_path.relative_to(PROJECT_ROOT)))}</p>"
    return (
        "<section><h2>Create Worker Spec</h2>"
        "<p class=\"notice\">Creates a draft JSON spec only. It does not create workers, edit Docker Compose, edit registry/workers.json, commit, or push.</p>"
        f"{message}"
        '<form method="post" action="/worker-specs">'
        '<label>worker_name <input name="worker_name" placeholder="data-worker" required></label>'
        '<label>worker_type <input name="worker_type" placeholder="data" required></label>'
        '<label>runtime <input name="runtime" placeholder="python" required></label>'
        '<label>preferred_model <input name="preferred_model" value="none"></label>'
        '<label>port <input name="port" placeholder="8813" required></label>'
        '<label>skills <input name="skills" placeholder="csv, excel, python-analysis" required></label>'
        '<label>purpose <input name="purpose" placeholder="CSV / Excel / Python analysis" required></label>'
        '<label>risk_level <input name="risk_level" value="low"></label>'
        '<label>permissions <input name="permissions" placeholder="read-workspace-files"></label>'
        '<button type="submit">Create Worker Spec</button>'
        "</form></section>"
    )


def worker_specs_section(specs: list[dict], generated_path: Path | None = None, generated_worker: object | None = None, error: str = "") -> str:
    message = ""
    if generated_path:
        message = f"<p class=\"pass\">Generated proposal: {html.escape(str(generated_path.relative_to(PROJECT_ROOT)))}</p>"
    if generated_worker:
        created = "".join(
            f"<li>{html.escape(str(path.relative_to(PROJECT_ROOT)))}</li>" for path in generated_worker.created_files
        )
        modified = "".join(
            f"<li>{html.escape(str(path.relative_to(PROJECT_ROOT)))}</li>" for path in generated_worker.modified_files
        )
        message += (
            f"<p class=\"pass\">Generated worker: {html.escape(generated_worker.worker_name)}</p>"
            f"<details open><summary>generated files</summary><ul>{created}</ul><p>modified files:</p><ul>{modified}</ul></details>"
        )
    if error:
        message += f"<p class=\"fail\">Worker generation failed: {html.escape(error)}</p>"
    if not specs:
        return f"<section><h2>Worker Specs</h2>{message}<p>No worker specs found.</p></section>"

    rows = []
    for item in specs:
        data = item.get("data", {})
        if item.get("error"):
            rows.append(
                "<tr>"
                f"<td>{html.escape(item['file'])}</td>"
                "<td colspan=\"6\"><strong class=\"fail\">invalid json</strong></td>"
                f"<td><pre>{html.escape(item['error'])}</pre></td>"
                "</tr>"
            )
            continue
        rows.append(
            "<tr>"
            f"<td>{html.escape(data.get('worker_name', item['file']))}</td>"
            f"<td>{html.escape(data.get('worker_type', ''))}</td>"
            f"<td>{html.escape(data.get('runtime', ''))}</td>"
            f"<td>{html.escape(data.get('preferred_model', ''))}</td>"
            f"<td>{html.escape(str(data.get('port', '')))}</td>"
            f"<td>{html.escape(data.get('risk_level', ''))}</td>"
            f"<td><strong>{html.escape(data.get('status', 'draft'))}</strong></td>"
            f"<td>{generate_proposal_action(data)}{generate_worker_action(data)}<details><summary>json</summary><pre>{html.escape(json.dumps(data, ensure_ascii=False, indent=2))}</pre></details></td>"
            "</tr>"
        )

    return (
        "<section><h2>Worker Specs</h2>"
        f"{message}"
        "<table><thead><tr><th>name</th><th>type</th><th>runtime</th><th>model</th><th>port</th><th>risk</th><th>status</th><th>details</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "</section>"
    )


def generate_proposal_action(data: dict) -> str:
    if data.get("status") != "draft":
        return ""
    worker_name = html.escape(data.get("worker_name", ""))
    return (
        '<form method="post" action="/worker-specs/generate-proposal" style="margin-bottom:8px">'
        f'<input type="hidden" name="worker_name" value="{worker_name}">'
        '<button type="submit">Generate Proposal</button>'
        "</form>"
    )


def generate_worker_action(data: dict) -> str:
    if data.get("status") != "draft":
        return ""
    worker_name = html.escape(data.get("worker_name", ""))
    return (
        '<form method="post" action="/worker-specs/generate-worker" style="margin-bottom:8px">'
        f'<input type="hidden" name="worker_name" value="{worker_name}">'
        '<button type="submit">Generate Worker</button>'
        '<p class="notice">Creates worker files and updates Docker Compose plus registry metadata.</p>'
        "</form>"
    )
