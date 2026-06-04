# Proposal 013: Add Brain Settings Manager

Status: proposed

Proposed at: 2026-06-04

Requires approval before implementation: yes

## Goal

Add a Brain Settings Manager to TaskDock.

The first version should introduce project-owned configuration files for OpenClaw Brain behavior rules and expose them through a Control Panel page.

This version only manages configuration. It must not change the main Brain runtime mechanism.

## Motivation

TaskDock currently relies on repeated prompt instructions for important operating rules such as validation, commits, push behavior, protected paths, and allowed operations.

Those rules should become visible, reviewable, and editable through project files so the Control Panel can show the current operating contract without depending on every conversation to restate it.

The first version should keep the configuration passive. It records intended behavior and allows safe editing, but does not yet enforce the settings in the dispatcher, worker runtime, or Control Panel automation.

## Proposed New Files

### `config/brain.json`

Stores high-level Brain behavior settings.

Initial fields:

- `brain_name`
- `runtime`
- `working_directory`
- `default_language`
- `auto_validation_enabled`
- `auto_commit_enabled`
- `auto_push_enabled`
- `require_validation_before_commit`
- `task_timeout_seconds`

Initial defaults should reflect the current TaskDock operating mode:

- default language is Chinese
- auto validation is enabled
- auto commit is enabled after validation passes
- auto push is disabled
- validation is required before commit
- working directory is `/Users/happyfamily/OpenClawBrain`

### `config/permissions.json`

Stores editable permission and safety boundaries.

Initial fields:

- `allowed_write_paths`
- `protected_paths`
- `allowed_operations`
- `forbidden_operations`
- `require_approval_for`

Initial defaults should reflect current project rules:

- allow writes inside controlled project areas
- protect worker implementations unless explicitly approved
- protect `docker-compose.yml` and `registry/workers.json` unless a task explicitly allows changes
- forbid arbitrary shell command execution
- forbid automatic push
- forbid force push
- forbid destructive git reset
- forbid submitting logs, workspaces, `.venv`, and temporary generated files

## Proposed Modified Files

### `control_panel/app.py`

Include the Brain Settings route.

`app.py` must remain only the FastAPI entrypoint and route mounting file.

### `control_panel/routes/brain_settings.py`

Add a Control Panel route for Brain Settings.

Required routes:

- `GET /brain-settings`
- `POST /brain-settings/brain`
- `POST /brain-settings/permissions`

The page must not execute shell commands.

### `control_panel/services/brain_settings_service.py`

Provide file-backed settings operations.

Responsibilities:

- ensure `config/brain.json` exists with defaults
- ensure `config/permissions.json` exists with defaults
- load both files as JSON
- validate JSON before saving
- allow saving only known safe fields
- preserve protected fields that should not be edited through the page

### `control_panel/rendering_brain_settings.py`

Render the Brain Settings page.

Required display:

- current `brain.json`
- current `permissions.json`
- editable form for safe `brain.json` fields
- editable form for safe `permissions.json` fields
- concise save result
- detailed JSON shown in collapsible details

### `control_panel/rendering.py`

Add a navigation link to the Brain Settings page.

## Safe Editable Fields

The first version should allow editing only fields that do not change execution power by themselves.

Editable `brain.json` fields:

- `brain_name`
- `default_language`
- `task_timeout_seconds`

Editable `permissions.json` fields:

- `allowed_write_paths`
- `protected_paths`
- `allowed_operations`
- `forbidden_operations`
- `require_approval_for`

Boolean automation fields should be displayed but not editable in this first version:

- `auto_validation_enabled`
- `auto_commit_enabled`
- `auto_push_enabled`
- `require_validation_before_commit`

`auto_push_enabled` must remain `false`.

## Safety Rules

- Do not change the dispatcher behavior in this proposal.
- Do not change worker behavior.
- Do not modify worker code.
- Do not modify `docker-compose.yml`.
- Do not modify `registry/workers.json`.
- Do not execute arbitrary shell commands from the page.
- Do not add push capability.
- Do not enable automatic push.
- Validate JSON before saving.
- Keep settings project-rooted under `config/`.

## Validation Plan

1. Compile changed Python files.
2. Validate `config/brain.json` with `python3 -m json.tool`.
3. Validate `config/permissions.json` with `python3 -m json.tool`.
4. Confirm `docker-compose.yml` is unchanged.
5. Confirm `registry/workers.json` is unchanged.
6. Confirm worker code is unchanged.
7. Confirm the Control Panel route can render the Brain Settings page.

## Out of Scope

- Enforcing settings in dispatcher runtime.
- Enforcing settings in worker runtime.
- Adding authentication.
- Adding arbitrary command execution.
- Adding push controls.
- Changing Docker services.
- Changing registered worker metadata.

## Approval

This proposal is not approved yet.

No implementation should happen until the user explicitly approves Proposal 013.
