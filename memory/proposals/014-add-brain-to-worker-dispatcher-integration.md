# Proposal 014: Add Brain-to-Worker Dispatcher Integration

Status: proposed

Proposed at: 2026-06-04

Requires approval before implementation: yes

## Goal

Add a unified Brain-to-Worker dispatcher integration to TaskDock.

The first version should let the Brain select a registered worker from `registry/workers.json`, check worker health, send the task to `/run-task`, and save task history under `memory/tasks/`.

## Motivation

TaskDock now has registered Docker workers and a Control Panel, but worker dispatch is still mostly a thin script with hard-coded routing.

The Brain needs a clearer dispatch layer so worker selection, config loading, task history, and Control Panel testing all use the same path.

## Scope

The first version should:

- read `registry/workers.json`
- read `config/brain.json`
- read `config/permissions.json`
- infer or accept a task type
- choose a worker using task type, worker type, skills, and fallback metadata
- verify selected worker health before sending the task
- send the task with HTTP `POST /run-task`
- save task input, selected worker, result, and error to `memory/tasks/`
- expose a simple Control Panel dispatch test page

## Worker Selection Rules

Selection should use this order:

1. Match by exact registered worker `type`.
2. Match by registered worker `skills`.
3. Match by known task text markers:
   - generic/scaffold tasks to `base-worker`
   - document/markdown/proposal tasks to `doc-worker`
   - demo/template tasks to `demo-worker`
4. Use a worker with `fallback: true`.
5. If no fallback exists, return a clear selection error.

## Health Rules

Before dispatch, the selected worker must pass health check.

Health check should call the worker endpoint with `/run-task` replaced by `/health`.

If health fails, dispatcher should return a clear failed result and save task history. The first version should not automatically start workers.

## Proposed New Files

- `brain/config_loader.py`
- `brain/worker_selector.py`
- `brain/task_history.py`
- `brain/task_dispatcher.py`
- `control_panel/routes/task_dispatch.py`
- `control_panel/rendering_task_dispatch.py`

## Proposed Modified Files

- `brain/dispatcher.py`
- `brain/worker_registry.py`
- `control_panel/app.py`
- `control_panel/rendering.py`

## Control Panel Plan

Add a simple Task Dispatch page.

The page should:

- accept task input
- accept optional task type
- call the unified dispatcher
- show selected worker
- show status
- show result or error
- show history path

The page must not execute arbitrary shell commands.

## Safety Rules

- Do not modify `workers/base-worker/`.
- Do not modify `workers/doc-worker/`.
- Do not modify `workers/demo-worker/`.
- Do not modify `docker-compose.yml`.
- Do not modify `registry/workers.json`.
- Do not automatically start workers.
- Do not call real LLMs.
- Do not git push.

## Config Use

`config/brain.json` should provide:

- default language
- task timeout seconds
- working directory

`config/permissions.json` should be loaded into the task history record so each dispatch result records the active permission contract. This proposal does not enforce every permission rule yet.

## Validation Plan

1. Compile changed Python files.
2. Validate `config/brain.json`.
3. Validate `config/permissions.json`.
4. Validate `registry/workers.json`.
5. Run `docker compose config`.
6. Check base-worker health.
7. Check doc-worker health.
8. Check demo-worker health.
9. Dispatch a generic task and verify it routes to `base-worker`.
10. Dispatch a document/markdown/proposal task and verify it routes to `doc-worker`.
11. Dispatch a demo/template task and verify it routes to `demo-worker`.
12. Dispatch an unknown task type and verify fallback or clear error.
13. Confirm task history files are saved.
14. Confirm worker code, Docker Compose, and worker registry remain unchanged.

## Approval

This proposal is approved by the user in the current request if it is complete and within scope.

Implementation may proceed after confirming there is no missing detail or placeholder text.
