# Proposal 012: Add Worker Lifecycle Manager

Status: proposed

Proposed at: 2026-06-04

Requires approval before implementation: yes

## Goal

Add a minimal Worker Lifecycle Manager to TaskDock Control Panel.

The first version should let the Control Panel display registered Docker workers and run a small set of whitelisted lifecycle operations for each registered worker.

## Motivation

TaskDock now has multiple Docker workers:

- `base-worker`
- `doc-worker`
- `demo-worker`

The Control Panel should stop being only a status viewer. It needs a safe operator surface for basic worker management without exposing arbitrary shell command execution.

This proposal adds lifecycle controls while keeping worker implementation, Docker Compose configuration, and worker registry content unchanged.

## Scope

Read worker metadata dynamically from `registry/workers.json`.

Display each registered worker with:

- worker name
- type
- docker_service
- endpoint
- model
- skills
- health status

Provide these whitelisted actions:

- Start
- Stop
- Restart
- Health Check
- View Logs

## Command Plan

All commands must be executed with argument lists and `shell=False`.

Allowed commands:

- Start: `docker compose up -d {service}`
- Stop: `docker compose stop {service}`
- Restart: `docker compose restart {service}`
- Logs: `docker compose logs --tail 100 {service}`

`Health Check` should use the worker endpoint from `registry/workers.json` and call the derived `/health` URL.

## Safety Rules

- Only allow `docker_service` values that exist in `registry/workers.json`.
- Do not accept arbitrary command text from the page.
- Do not run `docker run`.
- Do not delete workers.
- Do not modify worker code.
- Do not modify `docker-compose.yml`.
- Do not modify `registry/workers.json`.
- Do not modify `workers/base-worker/`.
- Do not modify `workers/doc-worker/`.
- Do not modify `workers/demo-worker/`.
- Do not git push.

## Proposed New Files

- `control_panel/services/worker_lifecycle_service.py`
- `control_panel/rendering_workers.py`

## Proposed Modified Files

- `control_panel/routes/workers.py`
- `control_panel/rendering.py`

## UI Plan

The `/workers` page should render a table of registered workers.

Each row should include:

- metadata from `registry/workers.json`
- current health status
- lifecycle action buttons

When an action is run, the page should show a concise result and keep detailed output inside a `<details>` block.

## Validation Plan

1. Compile changed Python files.
2. Run `docker compose config`.
3. Validate `registry/workers.json` as JSON.
4. Check base-worker health.
5. Check doc-worker health.
6. Check demo-worker health.
7. Confirm `docker-compose.yml` is unchanged.
8. Confirm `registry/workers.json` is unchanged.
9. Confirm `workers/base-worker/`, `workers/doc-worker/`, and `workers/demo-worker/` are unchanged.

## Approval

This proposal is approved by the user in the current request if it is complete and within scope.

Implementation may proceed after confirming there is no missing detail or placeholder text.
