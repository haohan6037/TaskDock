from __future__ import annotations

import html
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


def worker_health(url: str) -> str:
    try:
        response = requests.get(url, timeout=5)
        return response.text
    except Exception as exc:
        return str(exc)


def proposals_list() -> str:
    if not PROPOSALS_DIR.exists():
        return "memory/proposals/ does not exist"
    files = sorted(path.name for path in PROPOSALS_DIR.glob("*.md"))
    return "\n".join(files) if files else "No proposal files found."


def section(title: str, body: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2><pre>{html.escape(body)}</pre></section>"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
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
        "pre{white-space:pre-wrap;background:#111;color:#f4f4f4;padding:12px;border-radius:6px;overflow:auto}",
        ".notice{color:#555}",
        "</style>",
        "</head>",
        "<body><main>",
        "<h1>TaskDock Control Panel MVP</h1>",
        '<p class="notice">Local only: run with 127.0.0.1:8890. This MVP has no commit, push, or proposal creation actions.</p>',
        section("Git status", run_fixed(["git", "status"])),
        section("Docker compose ps", run_fixed(["docker", "compose", "ps"])),
        section("base-worker health", worker_health("http://127.0.0.1:8811/health")),
        section("doc-worker health", worker_health("http://127.0.0.1:8812/health")),
        section("Proposal files", proposals_list()),
        "</main></body></html>",
    ]
    return "\n".join(parts)
