from __future__ import annotations

import html
import json
import subprocess
from pathlib import Path

import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")
PROPOSALS_DIR = PROJECT_ROOT / "memory" / "proposals"

app = FastAPI(title="TaskDock Control Panel MVP")


def run_fixed(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = completed.stdout
    if completed.stderr:
        output = f"{output}\n{completed.stderr}".strip()
    return output or f"exit code: {completed.returncode}"


def run_fixed_result(command: list[str]) -> dict:
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = completed.stdout
        if completed.stderr:
            output = f"{output}\n{completed.stderr}".strip()
        return {"passed": completed.returncode == 0, "output": output or f"exit code: {completed.returncode}"}
    except Exception as exc:
        return {"passed": False, "output": str(exc)}


def worker_health(url: str) -> str:
    try:
        response = requests.get(url, timeout=5)
        return response.text
    except Exception as exc:
        return str(exc)


def worker_health_result(url: str) -> dict:
    try:
        response = requests.get(url, timeout=5)
        return {"passed": response.ok, "output": response.text}
    except Exception as exc:
        return {"passed": False, "output": str(exc)}


def extract_json_object(output: str) -> dict:
    start = output.find("{")
    end = output.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in dispatcher output.")
    return json.loads(output[start : end + 1])


def dispatcher_result(task: str, expected_worker: str) -> dict:
    result = run_fixed_result([".venv/bin/python", "brain/dispatcher.py", task])
    passed = False
    try:
        payload = extract_json_object(result["output"])
        passed = (
            result["passed"]
            and payload.get("status") == "success"
            and payload.get("result", {}).get("worker") == expected_worker
        )
    except Exception:
        passed = False
    return {"passed": passed, "output": result["output"]}


def run_validation() -> list[dict]:
    checks = [
        {
            "name": "base-worker health",
            **worker_health_result("http://127.0.0.1:8811/health"),
        },
        {
            "name": "doc-worker health",
            **worker_health_result("http://127.0.0.1:8812/health"),
        },
        {
            "name": "base dispatcher",
            **dispatcher_result("Run a generic scaffold test.", "base-worker"),
        },
        {
            "name": "doc-worker routing",
            **dispatcher_result("Format this proposal as Markdown sections.", "doc-worker"),
        },
    ]
    overall = all(check["passed"] for check in checks)
    checks.append({"name": "overall", "passed": overall, "output": "All checks passed." if overall else "One or more checks failed."})
    return checks


def proposals_list() -> str:
    if not PROPOSALS_DIR.exists():
        return "memory/proposals/ does not exist"
    files = sorted(path.name for path in PROPOSALS_DIR.glob("*.md"))
    return "\n".join(files) if files else "No proposal files found."


def section(title: str, body: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2><pre>{html.escape(body)}</pre></section>"


def validation_section(results: list[dict] | None = None) -> str:
    if not results:
        return (
            "<section><h2>Validation</h2>"
            '<form method="post" action="/validate/run">'
            "<button type=\"submit\">Run Validation</button>"
            "</form></section>"
        )

    rows = []
    for item in results:
        status = "pass" if item["passed"] else "fail"
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['name'])}</td>"
            f"<td><strong class=\"{status}\">{status}</strong></td>"
            f"<td><details><summary>details</summary><pre>{html.escape(item['output'])}</pre></details></td>"
            "</tr>"
        )
    return (
        "<section><h2>Validation</h2>"
        '<form method="post" action="/validate/run">'
        "<button type=\"submit\">Run Validation</button>"
        "</form>"
        "<table><thead><tr><th>check</th><th>result</th><th>details</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "</section>"
    )


def render_page(validation_results: list[dict] | None = None) -> str:
    parts = [
        "<!doctype html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>TaskDock Control Panel MVP</title>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:24px;background:#f7f7f8;color:#202124}",
        "main{max-width:1100px;margin:0 auto}",
        "section{background:white;border:1px solid #ddd;border-radius:8px;padding:16px;margin:16px 0}",
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
        validation_section(validation_results),
        section("Git status", run_fixed(["git", "status"])),
        section("Docker compose ps", run_fixed(["docker", "compose", "ps"])),
        section("base-worker health", worker_health("http://127.0.0.1:8811/health")),
        section("doc-worker health", worker_health("http://127.0.0.1:8812/health")),
        section("Proposal files", proposals_list()),
        "</main></body></html>",
    ]
    return "\n".join(parts)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return render_page()


@app.post("/validate/run", response_class=HTMLResponse)
def validate_run() -> str:
    return render_page(run_validation())
