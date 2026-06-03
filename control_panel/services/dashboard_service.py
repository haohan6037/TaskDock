from __future__ import annotations

from control_panel.command_whitelist import run_allowed
from control_panel.services.filesystem_service import proposal_names_text
from control_panel.services.worker_service import check_all_health, compose_ps


def dashboard_data() -> dict:
    return {
        "git_status": run_allowed("git_status").stdout or "No git status output.",
        "compose_ps": compose_ps().stdout or "No docker compose ps output.",
        "worker_health": check_all_health(),
        "proposal_files": proposal_names_text(),
    }
