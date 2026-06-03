from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")


@dataclass
class CommandResult:
    name: str
    command: List[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


ALLOWED_COMMANDS = {
    "git_status": ["git", "status"],
    "git_diff_stat": ["git", "diff", "--stat"],
    "git_add_all": ["git", "add", "--all"],
    "git_commit": ["git", "commit", "-m"],
    "git_push": ["git", "push"],
    "docker_compose_ps": ["docker", "compose", "ps"],
    "docker_compose_up": ["docker", "compose", "up", "--build", "-d"],
    "docker_compose_config": ["docker", "compose", "config"],
    "compile_doc_worker": ["python3", "-m", "py_compile", "workers/doc-worker/app.py", "brain/worker_registry.py"],
    "json_workers": ["python3", "-m", "json.tool", "registry/workers.json"],
    "run_dispatcher": [".venv/bin/python", "brain/dispatcher.py"],
}


def run_allowed(name: str, extra_args: Optional[List[str]] = None) -> CommandResult:
    if name not in ALLOWED_COMMANDS:
        raise ValueError(f"Command is not whitelisted: {name}")

    command = list(ALLOWED_COMMANDS[name])
    if name == "git_commit":
        if not extra_args or len(extra_args) != 1 or not extra_args[0].strip():
            raise ValueError("git_commit requires one non-empty commit message.")
        command.append(extra_args[0].strip())
    elif name == "run_dispatcher":
        if not extra_args or len(extra_args) != 1 or not extra_args[0].strip():
            raise ValueError("run_dispatcher requires one non-empty task.")
        command.append(extra_args[0].strip())
    elif extra_args:
        raise ValueError(f"Command {name} does not accept extra arguments.")

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return CommandResult(
        name=name,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
