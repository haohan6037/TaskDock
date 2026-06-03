from __future__ import annotations

import html
from pathlib import Path

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")


def section(title: str, body: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2><pre>{html.escape(body)}</pre></section>"


def validation_section(results: list[dict] | None = None) -> str:
    if not results:
        return (
            "<section><h2>Validation</h2>"
            '<form method="post" action="/validate/run">'
            '<button type="submit">Run Validation</button>'
            "</form></section>"
        )

    rows = []
    for item in results:
        name = item["name"] if isinstance(item, dict) else item.name
        passed = item["passed"] if isinstance(item, dict) else item.passed
        output = item["output"] if isinstance(item, dict) else item.output
        status = "pass" if passed else "fail"
        rows.append(
            "<tr>"
            f"<td>{html.escape(name)}</td>"
            f"<td><strong class=\"{status}\">{status}</strong></td>"
            f"<td><details><summary>details</summary><pre>{html.escape(output)}</pre></details></td>"
            "</tr>"
        )
    return (
        "<section><h2>Validation</h2>"
        '<form method="post" action="/validate/run">'
        '<button type="submit">Run Validation</button>'
        "</form>"
        "<table><thead><tr><th>check</th><th>result</th><th>details</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "</section>"
    )


def create_worker_form(created_path: Path | None = None) -> str:
    message = ""
    if created_path:
        message = f"<p class=\"pass\">Created proposal: {html.escape(str(created_path.relative_to(PROJECT_ROOT)))}</p>"
    return (
        "<section><h2>Create Worker Proposal</h2>"
        "<p class=\"notice\">Creates a proposal markdown file only. It does not create worker code, edit Docker Compose, edit registry, commit, or push.</p>"
        f"{message}"
        '<form method="post" action="/proposals/create-worker">'
        '<label>worker_name <input name="worker_name" placeholder="data-worker" required></label>'
        '<label>worker_type <input name="worker_type" placeholder="data" required></label>'
        '<label>port <input name="port" placeholder="8813" required></label>'
        '<label>purpose <input name="purpose" placeholder="CSV / Excel / Python analysis" required></label>'
        '<label>skills <input name="skills" placeholder="csv, excel, python analysis" required></label>'
        '<label>risk_level <input name="risk_level" value="low"></label>'
        '<button type="submit">Create Worker Proposal</button>'
        "</form></section>"
    )


def page(content: list[str]) -> str:
    parts = [
        "<!doctype html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>TaskDock Control Panel MVP</title>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:24px;background:#f7f7f8;color:#202124}",
        "main{max-width:1100px;margin:0 auto}",
        "nav a{margin-right:12px}",
        "section{background:white;border:1px solid #ddd;border-radius:8px;padding:16px;margin:16px 0}",
        "form{display:grid;gap:10px;max-width:640px}label{display:grid;gap:4px;font-weight:600}input{padding:8px;border:1px solid #bbb;border-radius:6px}",
        "button{padding:8px 12px;border:1px solid #777;border-radius:6px;background:#fff;cursor:pointer}",
        "table{width:100%;border-collapse:collapse;margin-top:12px}td,th{border-top:1px solid #ddd;padding:8px;text-align:left}",
        "pre{white-space:pre-wrap;background:#111;color:#f4f4f4;padding:12px;border-radius:6px;overflow:auto}",
        ".notice{color:#555}",
        ".pass{color:#087a2e}.fail{color:#b00020}",
        "</style>",
        "</head>",
        "<body><main>",
        "<h1>TaskDock Control Panel MVP</h1>",
        '<p class="notice">Local only: run with 127.0.0.1:8890. This MVP has no commit, push, or proposal creation actions.</p>',
        '<nav><a href="/">Dashboard</a><a href="/workers">Workers</a><a href="/worker-specs">Worker Specs</a><a href="/proposals">Proposals</a><a href="/validate">Validation</a></nav>',
        *content,
        "</main></body></html>",
    ]
    return "\n".join(parts)
