from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import parse_qs

import requests
from fastapi import FastAPI, Request
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


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "worker"


def next_proposal_id() -> str:
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    ids = []
    for path in PROPOSALS_DIR.glob("[0-9][0-9][0-9]-*.md"):
        try:
            ids.append(int(path.name.split("-", 1)[0]))
        except ValueError:
            continue
    return str(max(ids, default=0) + 1).zfill(3)


def create_worker_proposal(data: dict[str, str]) -> Path:
    worker_name = slugify(data.get("worker_name", ""))
    worker_type = data.get("worker_type", "").strip() or worker_name.replace("-worker", "")
    port = data.get("port", "").strip()
    purpose = data.get("purpose", "").strip()
    skills = [skill.strip() for skill in data.get("skills", "").split(",") if skill.strip()]
    risk_level = data.get("risk_level", "").strip() or "low"
    proposal_id = next_proposal_id()
    path = PROPOSALS_DIR / f"{proposal_id}-add-{worker_name}.md"
    skills_text = "\n".join(f"- {skill}" for skill in skills) or "- No skills provided."

    content = f"""# Proposal {proposal_id}: Add {worker_name}

Status: proposed

Requires approval before implementation: yes

## Goal

Add a future `{worker_name}` Docker worker proposal for `{worker_type}` tasks.

## Motivation

Purpose: {purpose or "No purpose provided."}

## Proposed New Files

- `workers/{worker_name}/Dockerfile`: Docker image definition for the proposed worker.
- `workers/{worker_name}/app.py`: FastAPI worker with `/health` and `/run-task`.
- `workers/{worker_name}/requirements.txt`: Worker dependencies.
- `memory/prompts/{worker_name}.md`: Worker role, constraints, and future model notes.

## Proposed Modified Files

- `docker-compose.yml`: Add the proposed worker service on port `{port or "unassigned"}` after approval.
- `registry/workers.json`: Register `{worker_name}` with `model: none` for the first version after approval.
- `brain/worker_registry.py`: Add minimal routing for `{worker_type}` tasks after approval.
- `README.md`: Document startup and testing instructions after approval.

## Worker Draft

- worker_name: `{worker_name}`
- worker_type: `{worker_type}`
- port: `{port or "unassigned"}`
- model: `none`
- risk_level: `{risk_level}`

## Skills

{skills_text}

## Why This Shape

This proposal only describes a future worker. It does not create `workers/{worker_name}`, does not modify Docker Compose, and does not modify the worker registry. The worker should remain disposable and stateless, while the Brain remains responsible for memory loading, routing, approval, and task history.

## Risk Level

{risk_level}

The main risks are incorrect routing, port collision, and accidentally giving the worker access to long-term memory. The first implementation should use `model: none` and should only use `memory_context` passed by the Brain.

## Validation Plan

After approval and implementation:

1. Compile the worker Python file.
2. Validate `registry/workers.json`.
3. Validate Docker Compose config.
4. Build and start the worker.
5. Check `/health` on `127.0.0.1:{port or "PORT"}`.
6. Call `/run-task` with explicit `memory_context`.
7. Confirm the worker does not read `memory/`.
8. Confirm existing base-worker and doc-worker behavior is unchanged.

## Approval

This proposal is not approved yet.

No code should be modified, no `workers/{worker_name}` directory should be created, and no Docker Compose or registry changes should be made until the human explicitly approves this proposal.
"""
    path.write_text(content, encoding="utf-8")
    return path


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


def render_page(validation_results: list[dict] | None = None, created_path: Path | None = None) -> str:
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
        validation_section(validation_results),
        create_worker_form(created_path),
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


@app.post("/proposals/create-worker", response_class=HTMLResponse)
async def create_worker_proposal_action(request: Request) -> str:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    data = {key: values[0] if values else "" for key, values in parsed.items()}
    created_path = create_worker_proposal(data)
    return render_page(created_path=created_path)
