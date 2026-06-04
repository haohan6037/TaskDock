# Proposal 016: Add Bootstrap and Setup Wizard

Status: proposed

Proposed at: 2026-06-04

Requires approval before implementation: yes

## Goal

Add a first-version bootstrap and setup flow so TaskDock can be initialized quickly on a new computer with fewer manual steps.

The first version should prepare local Python dependencies, check required project files, and show setup readiness in the Control Panel. It must not start workers automatically and must not change existing worker code.

## Motivation

TaskDock now has several moving parts:

- Brain Python dependencies
- Control Panel Python dependencies
- Docker Compose
- registry files
- config files
- Docker workers

New machines should have one clear bootstrap command that checks prerequisites, prepares `.venv`, installs local requirements, and prints the next commands to run. The Control Panel should also expose a read-only setup status page so the current environment state is visible without asking the user to run shell commands manually.

## Proposed New Files

- `scripts/bootstrap.sh`
- `control_panel/services/setup_service.py`
- `control_panel/rendering_setup.py`
- `control_panel/routes/setup.py`

## Proposed Modified Files

- `control_panel/app.py`
- `control_panel/rendering.py`
- `README.md`

## Bootstrap Script Plan

Add `scripts/bootstrap.sh` with this behavior:

1. Resolve the project root from the script location.
2. Check that Python is available.
3. Check that Docker is available.
4. Check that `docker compose` is available.
5. Create `.venv` if it does not exist.
6. Install `brain/requirements.txt`.
7. Install `control_panel/requirements.txt`.
8. Check that `config/brain.json` exists.
9. Check that `config/permissions.json` exists.
10. Check that `registry/workers.json` exists.
11. Check that `docker-compose.yml` exists.
12. Print next-step commands for starting the Control Panel and Docker workers.

The script must not:

- automatically start Docker workers
- automatically git commit
- automatically git push
- modify existing worker code

## Control Panel Setup Page Plan

Add a `/setup` page to the Control Panel.

The page should show:

- Python status
- Docker status
- `docker compose` status
- `.venv` status
- config status
- registry status
- worker directory status

The page should be read-only and must not execute arbitrary shell commands. It should run only fixed allowlisted checks implemented in Python with `subprocess.run(..., shell=False)`.

## Safety Rules

- Do not modify `workers/base-worker/`.
- Do not modify `workers/doc-worker/`.
- Do not modify `workers/demo-worker/`.
- Do not modify `workers/validation-worker/`.
- Do not automatically start Docker workers.
- Do not git push.
- Do not commit generated files from `memory/tasks/`.
- Do not commit `.venv`, `logs`, `workspaces`, or temporary files.
- Keep `docker-compose.yml` unchanged.
- Keep `registry/workers.json` unchanged.

## Validation Plan

1. Compile changed Python files.
2. Run `bash -n scripts/bootstrap.sh`.
3. Run `scripts/bootstrap.sh`.
4. Run `docker compose config`.
5. Validate `registry/workers.json` as JSON.
6. Check `base-worker` health.
7. Check `doc-worker` health.
8. Check `demo-worker` health.
9. Check `validation-worker` health.
10. Import the Control Panel app and setup route modules.
11. Confirm `docker-compose.yml` is not modified.
12. Confirm `registry/workers.json` is not modified.
13. Confirm no forbidden generated files are staged.

## Approval

This proposal is approved by the user in the current request if it is complete and within scope.

Implementation may proceed after confirming there is no missing detail or placeholder text.
