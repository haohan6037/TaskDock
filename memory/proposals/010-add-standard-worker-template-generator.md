# Proposal 010: Add Standard Worker Template Generator

Status: proposed

Proposed at: 2026-06-04

Requires approval before implementation: yes

## Goal

Add a standard worker template generator to TaskDock.

The first version should provide a reusable `fastapi-basic` worker adapter template and allow the Control Panel to generate a runnable worker from a draft worker spec.

This shifts TaskDock away from hand-writing each worker and toward controlled worker generation from specs.

## Motivation

TaskDock already has enough signals that one-off worker creation will not scale. Each new worker needs the same baseline shape:

- Dockerfile
- FastAPI app
- requirements
- prompt memory
- Docker Compose service
- registry metadata
- health endpoint
- `/run-task` endpoint
- memory boundary rules

A standard template makes this repeatable. A generator can turn `registry/worker_specs/{worker_name}.json` into a consistent worker implementation after approval.

FastAPI is only the first worker adapter. It does not mean all future workers must be FastAPI internally. Later approved proposals can add adapter templates for `codex-cli`, `openclaw`, `ollama`, `python-tool`, or other runtimes.

## Proposed New Files

### `worker_templates/fastapi-basic/Dockerfile.template`

Dockerfile template for a basic FastAPI worker.

Required behavior:

- Use a Python slim base image.
- Copy `requirements.txt`.
- Install dependencies.
- Copy `app.py`.
- Expose the worker port from the worker spec.
- Start Uvicorn on `0.0.0.0` inside the container.

### `worker_templates/fastapi-basic/app.py.template`

FastAPI worker adapter template.

Required endpoints:

- `GET /health`
- `POST /run-task`

Required request fields:

- `task_id`
- `task_type`
- `input`
- `constraints`
- `memory_context`

Required environment variables:

- `WORKER_NAME`
- `WORKER_TYPE`
- `WORKER_MODEL`
- `WORKER_SKILLS`

Required behavior:

- Return `model: none` for the first version unless the worker spec says otherwise and that later model use has been approved.
- Do not call a real LLM.
- Do not read `memory/`.
- Use only `memory_context` passed in the request.
- Return structured JSON with task id, status, worker name, model, memory loaded flag, and a simple markdown/text result.

### `worker_templates/fastapi-basic/requirements.txt`

Dependencies for the generated FastAPI worker.

Expected dependencies:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`

### `worker_templates/fastapi-basic/prompt.md.template`

Prompt template for `memory/prompts/{worker_name}.md`.

Required content:

- worker name
- worker type
- purpose
- skills
- runtime
- model
- permissions
- memory boundary
- statement that long-term memory is owned by the Brain, not the worker

### `control_panel/services/worker_template_service.py`

Service for loading templates.

Responsibilities:

- Read files from `worker_templates/fastapi-basic/`.
- Verify required template files exist.
- Render templates with worker spec values.
- Keep all template access project-rooted.

### `control_panel/services/worker_generator_service.py`

Service for generating workers from worker specs.

Responsibilities:

- Read `registry/worker_specs/{worker_name}.json`.
- Refuse to overwrite an existing `workers/{worker_name}/` directory.
- Render worker files from `worker_templates/fastapi-basic/`.
- Create `workers/{worker_name}/`.
- Create `memory/prompts/{worker_name}.md`.
- Prepare Docker Compose service metadata.
- Prepare registry worker metadata.
- Apply Docker Compose and registry changes only as part of this approved generation flow.

Forbidden behavior:

- Do not modify `base-worker`.
- Do not modify `doc-worker`.
- Do not overwrite existing workers.
- Do not call a real LLM.
- Do not commit.
- Do not push.

### `control_panel/routes/worker_generator.py`

Control Panel route for worker generation.

Responsibilities:

- Show Generate Worker action for draft worker specs.
- Confirm target files and changes before generation.
- Trigger generation only for a selected worker spec.
- Display generated files and modified files after generation.

## Proposed Modified Files

### `control_panel/app.py`

Include the worker generator route.

Allowed change:

- Import and include the route module.

`app.py` must remain only the FastAPI entrypoint.

### `control_panel/routes/worker_specs.py`

Add a Generate Worker action for specs that are ready for implementation.

Required behavior:

- Show that generation creates real worker files.
- Keep Generate Proposal separate from Generate Worker.
- Do not auto-generate a worker when creating a spec.

### `control_panel/rendering_worker_specs.py`

Display worker generation controls and warnings.

Required behavior:

- Clearly distinguish draft specs, generated proposals, and generated workers.
- Warn that generation modifies Docker Compose and registry metadata.

### `docker-compose.yml`

Add a service for the generated worker.

Required behavior:

- Add only the new worker service.
- Preserve existing `base-worker`.
- Preserve existing `doc-worker`.
- Bind the generated worker to its spec port.
- Set environment variables:
  - `WORKER_NAME`
  - `WORKER_TYPE`
  - `WORKER_MODEL`
  - `WORKER_SKILLS`

### `registry/workers.json`

Add metadata for the generated worker.

Required fields:

- `type`
- `endpoint`
- `docker_service`
- `model`
- `skills`
- `cost_level`
- `risk_level`

Required behavior:

- Preserve existing `base-worker`.
- Preserve existing `doc-worker`.
- Do not remove fallback behavior.

### `README.md`

Document the standard worker template generator.

Required content:

- Worker specs are the input.
- `fastapi-basic` is the first adapter template.
- Generated workers use `model: none` in the first version.
- Generated workers do not read `memory/`.
- Generated workers use only request `memory_context`.
- Future adapters may include codex-cli, openclaw, ollama, python-tool, or other runtimes.

## Generated Worker Files

For a worker spec named `data-worker`, generation should create:

```text
workers/data-worker/Dockerfile
workers/data-worker/app.py
workers/data-worker/requirements.txt
memory/prompts/data-worker.md
```

It should also update:

```text
docker-compose.yml
registry/workers.json
```

## Runtime Model

The first version must use:

```text
model: none
```

No real LLM should be called by generated workers in the first version.

Future model use requires a separate approved proposal.

## Memory Boundary

Generated workers must not read from:

```text
memory/
```

Generated workers may only use:

```text
memory_context
```

passed in the `/run-task` request by the Brain.

The Brain remains responsible for memory retrieval and task history.

## Why This Shape

This is the right next step because TaskDock needs worker lifecycle management, not one-off worker creation.

A template generator provides a repeatable path:

1. Create worker spec.
2. Generate implementation proposal.
3. Approve implementation.
4. Generate worker from a standard template.
5. Validate worker behavior.

FastAPI is a practical first adapter because the current workers already use HTTP APIs. The design still leaves room for future non-FastAPI runtimes.

## Risk Level

Medium.

Reasons:

- This feature creates real worker files.
- It modifies Docker Compose.
- It modifies runtime registry metadata.
- A faulty generator could overwrite existing workers or break existing services.

Risk controls:

- Refuse to overwrite existing `workers/{worker_name}/`.
- Preserve `base-worker`.
- Preserve `doc-worker`.
- Preserve existing registry entries.
- Validate worker spec before generation.
- Validate Docker Compose after generation.
- Validate generated worker health endpoint.
- Keep model as `none`.
- Keep memory access limited to request `memory_context`.

## Validation Plan

### Static checks

Run:

```bash
python3 -m py_compile control_panel/services/worker_template_service.py
python3 -m py_compile control_panel/services/worker_generator_service.py
python3 -m py_compile control_panel/routes/worker_generator.py
python3 -m py_compile control_panel/routes/worker_specs.py
python3 -m py_compile control_panel/app.py
```

Expected result:

- All files compile successfully.

### Template check

Verify required template files exist:

```text
worker_templates/fastapi-basic/Dockerfile.template
worker_templates/fastapi-basic/app.py.template
worker_templates/fastapi-basic/requirements.txt
worker_templates/fastapi-basic/prompt.md.template
```

Expected result:

- All template files are present.

### Generation check

Use a draft worker spec such as:

```text
registry/worker_specs/data-worker.json
```

Run generation through the Control Panel.

Expected result:

- `workers/data-worker/` is created.
- `memory/prompts/data-worker.md` is created.
- Existing workers are not modified.
- Existing worker directories are not overwritten.

### Docker Compose check

Run:

```bash
docker compose config
```

Expected result:

- Compose config is valid.
- Existing base-worker and doc-worker services remain present.
- New generated worker service is present.

### Registry check

Validate:

```bash
python3 -m json.tool registry/workers.json
```

Expected result:

- JSON is valid.
- Existing base-worker entry remains.
- Existing doc-worker entry remains.
- Generated worker metadata is present.

### Generated worker check

Build and start:

```bash
docker compose up --build -d
```

Expected result:

- base-worker remains healthy.
- doc-worker remains healthy.
- generated worker health endpoint responds.

### Memory boundary check

Inspect generated worker code.

Expected result:

- It does not read `memory/`.
- It only uses request `memory_context`.

### Dispatcher check

Run an appropriate dispatcher task for the generated worker type.

Expected result:

- Dispatcher can route to the generated worker after routing metadata is updated.
- Existing base-worker and doc-worker routing still works.

## Approval

This proposal is not approved yet.

No code should be modified until the human explicitly approves Proposal 010.
