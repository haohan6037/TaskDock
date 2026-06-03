from __future__ import annotations

from control_panel.command_whitelist import CommandResult, run_allowed


def get_status() -> CommandResult:
    return run_allowed("git_status")


def get_diff_stat() -> CommandResult:
    return run_allowed("git_diff_stat")


def stage_all() -> CommandResult:
    return run_allowed("git_add_all")


def commit(message: str) -> CommandResult:
    return run_allowed("git_commit", [message])


def push() -> CommandResult:
    return run_allowed("git_push")
