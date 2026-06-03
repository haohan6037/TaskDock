# Proposal 007: Add Worker Spec Manager

Status: proposed

Proposed at: 2026-06-03

Requires approval before implementation: yes

## Goal

Add Worker Spec Manager to TaskDock Control Panel.

The first version should let TaskDock create and view worker specs that can later be used to dynamically generate workers after explicit approval.

This proposal only manages worker specs. It does not create real workers.

## Motivation

TaskDock should stop treating each new worker as a hand-written one-off implementation. Before creating any real worker, the system needs a safe intermediate artifact that records worker intent, runtime expectations, model preference, skills, risk, and permissions.

A worker spec gives TaskDock a structured draft that can later feed proposals, scaffolding, registry updates, or Docker Compose changes. Keeping specs separate from actual workers preserves control: creating a spec is not the same as implementing a worker.

## Proposed New Files

### `registry/worker_specs/.gitkeep`

Ensures the worker specs directory exists in the repository.

### `control_panel/routes/worker_specs.py`

Adds Control Panel routes for worker spec management.

Required routes:

- `GET /worker-specs`
- `POST /worker-specs`

Responsibilities:

- Show existing worker specs read dynamically from `registry/worker_specs/`.
- Render a simple Create Worker Spec form.
- Create `registry/worker_specs/` if it does not exist.
- Save submitted worker specs as JSON files.

Forbidden behavior:

- Do not create `workers/{worker_name}`.
- Do not modify `docker-compose.yml`.
- Do not modify `registry/workers.json`.
- Do not implement any specific worker.
- Do not commit.
- Do not push.

### `control_panel/services/worker_spec_service.py`

Service module for worker spec filesystem operations.

Responsibilities:

- Ensure `registry/worker_specs/` exists.
- Read worker specs dynamically from `registry/worker_specs/*.json`.
- Validate and normalize worker spec form input.
- Save worker specs as `registry/worker_specs/{worker_name}.json`.
- Keep worker spec status as `draft`.
- Add `created_at` when writing a new spec.

### `control_panel/rendering_worker_specs.py`

Small HTML rendering helpers for worker specs.

Responsibilities:

- Render the Worker Specs area.
- Render the Create Worker Spec form.
- Render existing worker specs in a readable table or compact list.
- Clearly label every worker spec as a draft.

## Proposed Modified Files

### `control_panel/app.py`

Include the worker specs router.

Allowed change:

- Import the worker specs route module.
- Add `app.include_router(...)`.

`app.py` must remain a FastAPI entrypoint only.

### `control_panel/routes/dashboard.py`

Add the Worker Specs area to the dashboard.

Required behavior:

- Show a summary of specs read from `registry/worker_specs/`.
- Link to the Worker Specs page.

### `control_panel/rendering.py`

If needed, add a navigation link to `/worker-specs`.

Allowed change:

- Add the Worker Specs link to the existing navigation.

### `README.md`

Document Worker Spec Manager.

Required content:

- Worker specs live in `registry/worker_specs/`.
- Creating a worker spec does not create a real worker.
- Creating a worker spec does not modify Docker Compose.
- Creating a worker spec does not modify `registry/workers.json`.
- Creating a worker spec does not create `workers/{worker_name}`.

## Worker Spec Fields

Each worker spec JSON file must include:

- `worker_name`
- `worker_type`
- `runtime`
- `preferred_model`
- `port`
- `skills`
- `purpose`
- `risk_level`
- `permissions`
- `status`
- `created_at`

`status` must be `draft` in the MVP.

## Worker Spec Example

```json
{
  "worker_name": "data-worker",
  "worker_type": "data",
  "runtime": "python",
  "preferred_model": "none",
  "port": 8813,
  "skills": ["csv", "excel", "python-analysis"],
  "purpose": "CSV / Excel / Python analysis",
  "risk_level": "low",
  "permissions": ["read-workspace-files"],
  "status": "draft",
  "created_at": "2026-06-03T00:00:00+00:00"
}
```

## Why This Shape

This is the smallest useful Worker Spec Manager.

It creates a structured place for future worker intent without touching runtime configuration. The Control Panel can show existing specs and create new specs, but it cannot turn those specs into real workers yet.

This keeps TaskDock controlled:

- worker ideas become specs,
- specs can be reviewed,
- implementation still requires a separate approved proposal,
- runtime files stay unchanged until explicit approval.

## Risk Level

Low.

The feature only reads and writes draft JSON files under `registry/worker_specs/`.

Main risks:

- A draft spec might be mistaken for an implemented worker.
- Invalid worker names could create confusing filenames.
- Skills or permissions might be stored inconsistently.

Risk controls:

- Every generated spec must use `status: draft`.
- UI must clearly label specs as drafts.
- Worker names must be normalized before writing filenames.
- The service must write only under `registry/worker_specs/`.
- No Docker Compose changes are allowed.
- No registry runtime changes are allowed.
- No worker directory creation is allowed.

## Validation Plan

### Static checks

Run:

```bash
python3 -m py_compile control_panel/routes/worker_specs.py
python3 -m py_compile control_panel/services/worker_spec_service.py
python3 -m py_compile control_panel/rendering_worker_specs.py
python3 -m py_compile control_panel/app.py
```

Expected result:

- All files compile successfully.

### Directory creation check

Start with `registry/worker_specs/` missing.

Open the Worker Specs page or submit the form.

Expected result:

- `registry/worker_specs/` is created.
- No other registry files are changed.

### Create spec check

Submit a worker spec form with:

- worker_name: `data-worker`
- worker_type: `data`
- runtime: `python`
- preferred_model: `none`
- port: `8813`
- skills: `csv, excel, python-analysis`
- purpose: `CSV / Excel / Python analysis`
- risk_level: `low`
- permissions: `read-workspace-files`

Expected result:

- `registry/worker_specs/data-worker.json` is created.
- The JSON contains all required fields.
- `status` is `draft`.
- `created_at` is present.

### Dynamic read check

Refresh the Worker Specs page.

Expected result:

- The new worker spec appears without modifying code.
- Existing specs are read dynamically from `registry/worker_specs/`.

### Boundary check

After creating a spec, confirm:

```text
docker-compose.yml is unchanged
registry/workers.json is unchanged
workers/data-worker does not exist
```

Expected result:

- No real worker was created.
- No runtime registry entry was added.
- No Docker Compose service was added.

## Approval

This proposal is not approved yet.

No code should be modified until the human explicitly approves Proposal 007: Add Worker Spec Manager.
