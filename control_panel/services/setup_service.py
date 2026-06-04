from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from control_panel.command_whitelist import PROJECT_ROOT


@dataclass(frozen=True)
class SetupCheck:
    name: str
    passed: bool
    summary: str
    details: str


def run_fixed_command(name: str, command: list[str]) -> SetupCheck:
    executable = command[0]
    if shutil.which(executable) is None:
        return SetupCheck(name, False, f"{executable} not found", "Command is unavailable on PATH.")
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        return SetupCheck(name, False, f"{name} check failed", str(exc))

    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part).strip()
    return SetupCheck(
        name=name,
        passed=completed.returncode == 0,
        summary=output.splitlines()[0] if output else "No output.",
        details=output or "No output.",
    )


def check_file(path: Path, label: str) -> SetupCheck:
    exists = path.exists()
    return SetupCheck(
        name=label,
        passed=exists,
        summary="found" if exists else "missing",
        details=str(path),
    )


def check_registry() -> SetupCheck:
    path = PROJECT_ROOT / "registry" / "workers.json"
    if not path.exists():
        return SetupCheck("registry/workers.json", False, "missing", str(path))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("registry root must be a JSON object")
        return SetupCheck(
            "registry/workers.json",
            True,
            f"{len(data)} workers registered",
            json.dumps(sorted(data.keys()), indent=2),
        )
    except Exception as exc:
        return SetupCheck("registry/workers.json", False, "invalid JSON", str(exc))


def check_worker_dirs() -> SetupCheck:
    registry_path = PROJECT_ROOT / "registry" / "workers.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return SetupCheck("worker directories", False, "registry unavailable", str(exc))

    missing = []
    present = []
    for worker_name in sorted(registry):
        worker_dir = PROJECT_ROOT / "workers" / worker_name
        if worker_dir.is_dir():
            present.append(worker_name)
        else:
            missing.append(worker_name)

    details = f"present: {', '.join(present) or 'none'}\nmissing: {', '.join(missing) or 'none'}"
    return SetupCheck(
        "worker directories",
        not missing,
        "all registered worker directories exist" if not missing else f"missing {len(missing)} worker directories",
        details,
    )


def setup_checks() -> list[SetupCheck]:
    venv_path = PROJECT_ROOT / ".venv"
    return [
        SetupCheck(
            "Python",
            True,
            sys.version.splitlines()[0],
            sys.executable,
        ),
        run_fixed_command("Docker", ["docker", "--version"]),
        run_fixed_command("docker compose", ["docker", "compose", "version"]),
        SetupCheck(
            ".venv",
            venv_path.is_dir(),
            "found" if venv_path.is_dir() else "missing",
            str(venv_path),
        ),
        check_file(PROJECT_ROOT / "config" / "brain.json", "config/brain.json"),
        check_file(PROJECT_ROOT / "config" / "permissions.json", "config/permissions.json"),
        check_registry(),
        check_file(PROJECT_ROOT / "docker-compose.yml", "docker-compose.yml"),
        check_worker_dirs(),
    ]
