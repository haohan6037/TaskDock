# Proposal 005: Refactor Control Panel into modular structure

Status: proposed

Proposed at: 2026-06-03

Requires approval before implementation: yes

## Goal

Refactor TaskDock Control Panel so `control_panel/app.py` is only the FastAPI entrypoint, while dashboard, validation, proposals, and workers logic live in separate modules.

The refactor should make the Control Panel easier to extend without editing `app.py` for every small feature.

## Motivation

The current MVP puts page rendering, validation, proposal creation, worker health checks, and filesystem reads into `control_panel/app.py`. That made the first version fast to ship, but it is already showing pressure: every new button or small feature requires changing the entrypoint and restarting the service.

TaskDock needs a modular control surface where new views and small workflow features can be added by changing focused modules instead of repeatedly editing `app.py`.

## Proposed New Files

### `control_panel/routes/dashboard.py`

Dashboard routes and page assembly.

Responsibilities:

- Render the main dashboard.
- Load dashboard data through services.
- Show Git status, worker status, proposal summary, and latest validation state.

### `control_panel/routes/validation.py`

Validation routes.

Responsibilities:

- Render validation page.
- Run fixed validation workflow.
- Display pass/fail results and optional details.
- Avoid arbitrary command execution.

### `control_panel/routes/proposals.py`

Proposal routes.

Responsibilities:

- List proposals from `memory/proposals/`.
- Read proposal files dynamically.
- Create proposal drafts through controlled forms.
- Avoid implementing or approving proposals.

### `control_panel/routes/workers.py`

Worker routes.

Responsibilities:

- Read worker metadata dynamically from `registry/workers.json`.
- Show worker status and health.
- Keep worker behavior unchanged.

### `control_panel/services/dashboard_service.py`

Dashboard data service.

Responsibilities:

- Collect high-level status from Git, workers, proposals, and validation services.
- Return structured data for the dashboard route.

### `control_panel/services/filesystem_service.py`

Filesystem helper service.

Responsibilities:

- Read project-local files safely.
- List proposal files.
- Read `registry/workers.json`.
- Keep all paths rooted at `/Users/happyfamily/OpenClawBrain`.

### `control_panel/rendering.py`

Small HTML rendering helpers for the current no-template MVP.

Responsibilities:

- Render page layout.
- Render sections.
- Render pass/fail badges.
- Escape user-provided and file-provided text.

This can later be replaced by templates if approved, but the first refactor should keep the current direct HTML approach.

## Proposed Modified Files

### `control_panel/app.py`

Change `app.py` into a minimal FastAPI entrypoint.

Allowed responsibilities after refactor:

- Create `FastAPI(...)`.
- Include routers from route modules.
- Define global app metadata.

`app.py` should not contain:

- validation logic,
- proposal creation logic,
- worker health logic,
- Git command logic,
- long HTML string construction.

### `control_panel/command_whitelist.py`

Keep command whitelist centralized.

Allowed changes:

- Preserve fixed argument arrays.
- Add names for any existing fixed validation commands if needed.
- Continue forbidding `shell=True`, arbitrary shell execution, `docker run`, and destructive Git commands.

### `control_panel/services/validation_service.py`

Move validation workflow here if not already fully centralized.

Required behavior:

- Fixed validation only.
- base-worker health check.
- doc-worker health check.
- base dispatcher test.
- doc-worker routing test.
- pass/fail output plus optional raw details.

### `control_panel/services/proposal_service.py`

Move proposal filesystem behavior here.

Required behavior:

- Dynamically list `memory/proposals/*.md`.
- Determine next proposal id from existing files.
- Create proposal drafts only.
- Never approve or implement proposals.

### `control_panel/services/worker_service.py`

Move worker metadata and health behavior here.

Required behavior:

- Dynamically read `registry/workers.json`.
- Show registered workers.
- Check local worker health based on registry metadata.
- Keep base-worker and doc-worker behavior unchanged.

### `scripts/start_control_panel.sh`

Use reload mode during development.

Required command:

```bash
exec .venv/bin/uvicorn control_panel.app:app --host 127.0.0.1 --port 8890 --reload
```

The script must continue binding only to `127.0.0.1:8890`, never `0.0.0.0`.

## Why This Shape

This refactor keeps the current MVP small while removing the main design bottleneck.

`app.py` should be stable. New Control Panel behavior should usually be added through route modules or service modules. That makes future changes easier to review, easier to test, and less likely to accidentally break unrelated pages.

Dynamic filesystem reads matter because TaskDock is driven by external memory and registry files:

- proposals live in `memory/proposals/`,
- workers live in `registry/workers.json`,
- task history lives under `memory/tasks/`.

The Control Panel should reflect those files instead of hardcoding every item into `app.py`.

## Risk Level

Medium.

Reasons:

- Refactoring route structure can break the existing MVP page if route wiring is wrong.
- Dynamic file reads can expose confusing output if parsing errors are not handled clearly.
- Worker metadata from `registry/workers.json` must not be treated as permission to run arbitrary commands.

Risk controls:

- Keep `app.py` small and route-only.
- Keep command execution centralized in the whitelist.
- Keep dynamic file reads project-rooted.
- Preserve current MVP behavior before adding any new capabilities.
- Keep Control Panel bound to `127.0.0.1:8890`.
- Do not change base-worker or doc-worker behavior.

## Validation Plan

### Static checks

Run:

```bash
python3 -m py_compile control_panel/app.py
python3 -m py_compile control_panel/routes/dashboard.py
python3 -m py_compile control_panel/routes/validation.py
python3 -m py_compile control_panel/routes/proposals.py
python3 -m py_compile control_panel/routes/workers.py
python3 -m py_compile control_panel/services/dashboard_service.py
python3 -m py_compile control_panel/services/filesystem_service.py
python3 -m py_compile control_panel/rendering.py
```

Expected result:

- All files compile successfully.

### Startup check

Run:

```bash
./scripts/start_control_panel.sh
```

Expected result:

- Uvicorn starts with `--reload`.
- The server binds to `127.0.0.1:8890`.
- The server does not bind to `0.0.0.0`.

### Page checks

Open:

```text
http://127.0.0.1:8890
```

Expected result:

- Dashboard renders.
- Git status section renders.
- Worker status section renders.
- Proposal files section renders from `memory/proposals/`.
- Validation section renders.

### Dynamic proposal check

Add a new proposal markdown file through the existing proposal creation flow or manually during testing.

Expected result:

- Refreshing the Control Panel shows the new proposal without modifying `app.py`.

### Dynamic worker check

Read `registry/workers.json` through the workers route.

Expected result:

- Registered workers are shown from registry data.
- base-worker and doc-worker are shown.
- No worker behavior is changed.

### Validation behavior check

Click Run Validation.

Expected result:

- base-worker health: pass/fail.
- doc-worker health: pass/fail.
- base dispatcher: pass/fail.
- doc-worker routing: pass/fail.
- overall: pass/fail.
- Details remain available without showing long JSON as the main result.

## Approval

This proposal is not approved yet.

No code should be modified until the human explicitly approves Proposal 005.
