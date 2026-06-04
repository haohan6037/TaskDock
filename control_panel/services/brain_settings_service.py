from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")
CONFIG_DIR = PROJECT_ROOT / "config"
BRAIN_CONFIG_PATH = CONFIG_DIR / "brain.json"
PERMISSIONS_CONFIG_PATH = CONFIG_DIR / "permissions.json"

BRAIN_DEFAULTS = {
    "brain_name": "OpenClaw Brain",
    "runtime": "openclaw-host",
    "working_directory": str(PROJECT_ROOT),
    "default_language": "zh-CN",
    "auto_validation_enabled": True,
    "auto_commit_enabled": True,
    "auto_push_enabled": False,
    "require_validation_before_commit": True,
    "task_timeout_seconds": 120,
}

PERMISSIONS_DEFAULTS = {
    "allowed_write_paths": [
        "brain/",
        "config/",
        "control_panel/",
        "memory/prompts/",
        "memory/proposals/",
        "registry/worker_specs/",
        "worker_templates/",
        "workers/",
    ],
    "protected_paths": [
        "docker-compose.yml",
        "registry/workers.json",
        "workers/base-worker/",
        "workers/doc-worker/",
        "workers/demo-worker/",
    ],
    "allowed_operations": [
        "read_files",
        "write_approved_project_files",
        "run_validation",
        "git_commit_after_validation",
        "docker_compose_config",
        "docker_compose_worker_lifecycle",
    ],
    "forbidden_operations": [
        "arbitrary_shell_command_execution",
        "automatic_git_push",
        "git_push_force",
        "git_reset_hard",
        "docker_run",
        "delete_existing_worker",
        "commit_memory_tasks",
        "commit_logs",
        "commit_workspaces",
        "commit_venv",
        "commit_temporary_test_files",
    ],
    "require_approval_for": [
        "git_push",
        "docker-compose.yml changes",
        "registry/workers.json changes",
        "base-worker changes",
        "doc-worker changes",
        "demo-worker changes",
        "worker deletion",
        "new runtime enforcement",
    ],
}

EDITABLE_BRAIN_FIELDS = {"brain_name", "default_language", "task_timeout_seconds"}
EDITABLE_PERMISSIONS_FIELDS = {
    "allowed_write_paths",
    "protected_paths",
    "allowed_operations",
    "forbidden_operations",
    "require_approval_for",
}


@dataclass(frozen=True)
class SaveResult:
    passed: bool
    message: str


def ensure_settings_files() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not BRAIN_CONFIG_PATH.exists():
        write_json(BRAIN_CONFIG_PATH, BRAIN_DEFAULTS)
    if not PERMISSIONS_CONFIG_PATH.exists():
        write_json(PERMISSIONS_CONFIG_PATH, PERMISSIONS_DEFAULTS)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_brain_settings() -> dict[str, Any]:
    ensure_settings_files()
    data = BRAIN_DEFAULTS | load_json(BRAIN_CONFIG_PATH)
    data["auto_push_enabled"] = False
    return data


def load_permissions_settings() -> dict[str, Any]:
    ensure_settings_files()
    return PERMISSIONS_DEFAULTS | load_json(PERMISSIONS_CONFIG_PATH)


def parse_json_object(raw_json: str) -> dict[str, Any]:
    data = json.loads(raw_json)
    if not isinstance(data, dict):
        raise ValueError("Settings JSON must be an object.")
    return data


def require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings.")
    return value


def save_brain_settings(raw_json: str) -> SaveResult:
    try:
        incoming = parse_json_object(raw_json)
        current = load_brain_settings()
        for field in EDITABLE_BRAIN_FIELDS:
            if field in incoming:
                current[field] = incoming[field]
        if not isinstance(current["brain_name"], str) or not current["brain_name"].strip():
            raise ValueError("brain_name must be a non-empty string.")
        if not isinstance(current["default_language"], str) or not current["default_language"].strip():
            raise ValueError("default_language must be a non-empty string.")
        current["task_timeout_seconds"] = int(current["task_timeout_seconds"])
        if current["task_timeout_seconds"] <= 0:
            raise ValueError("task_timeout_seconds must be positive.")
        current["auto_push_enabled"] = False
        write_json(BRAIN_CONFIG_PATH, current)
        return SaveResult(True, "Saved brain settings.")
    except Exception as exc:
        return SaveResult(False, f"Failed to save brain settings: {exc}")


def save_permissions_settings(raw_json: str) -> SaveResult:
    try:
        incoming = parse_json_object(raw_json)
        current = load_permissions_settings()
        for field in EDITABLE_PERMISSIONS_FIELDS:
            if field in incoming:
                current[field] = require_string_list(incoming[field], field)
        if "automatic_git_push" not in current["forbidden_operations"]:
            current["forbidden_operations"].append("automatic_git_push")
        if "git_push_force" not in current["forbidden_operations"]:
            current["forbidden_operations"].append("git_push_force")
        write_json(PERMISSIONS_CONFIG_PATH, current)
        return SaveResult(True, "Saved permissions settings.")
    except Exception as exc:
        return SaveResult(False, f"Failed to save permissions settings: {exc}")
