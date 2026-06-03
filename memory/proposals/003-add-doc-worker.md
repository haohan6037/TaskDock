# Proposal 003: Add doc-worker

Status: proposed

Proposed at: 2026-06-03

Requires approval before implementation: yes

## Goal

Add doc-worker

## Motivation

TaskDock needs a document-focused worker for summarisation, Markdown drafting, report writing, and proposal formatting. This step should only create a proposal and must not implement the worker yet.

## Proposed New Files

### `workers/doc-worker/Dockerfile`

Build a lightweight Docker image for the document worker.

Expected first version:

- Python slim base image.
- Install FastAPI, Uvicorn, and Pydantic.
- Copy `app.py`.
- Expose the worker HTTP port.
- Start Uvicorn.

### `workers/doc-worker/app.py`

Implement the first doc-worker HTTP API.

Expected endpoints:

- `GET /health`
- `POST /run-task`

Expected first-version behavior:

- Accept `task_id`, `task_type`, `input`, `constraints`, and `memory_context`.
- Do not store long-term memory inside the worker.
- Only use memory passed by the Brain in `memory_context`.
- Return structured Markdown-oriented output.
- Support simple document tasks without a real LLM, such as:
  - Markdown formatting.
  - Summary structure generation.
  - Proposal formatting.
  - Section outline generation.

### `workers/doc-worker/requirements.txt`

Declare runtime dependencies for the doc-worker.

Expected first version:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`

### `memory/prompts/doc-worker.md`

Describe the doc-worker role and boundaries for future prompt/model integration.

Expected content:

- The worker is document-focused.
- The worker must remain stateless.
- The worker must not own long-term memory.
- The worker may only use `memory_context` provided by the Brain.
- The worker can later be connected to different models.

## Proposed Modified Files

### `docker-compose.yml`

Add a `doc-worker` service.

Expected change:

- Build from `./workers/doc-worker`.
- Expose a dedicated local port.
- Mount `./workspaces:/workspaces` if needed for disposable task workspaces.
- Set `WORKER_NAME=doc-worker`.

### `registry/workers.json`

Register `doc-worker` so the Brain can route document-focused tasks to it.

Expected metadata:

- `type`: `doc`
- `endpoint`: local `/run-task` URL for doc-worker
- `docker_service`: `doc-worker`
- `model`: `none` for the first version
- `skills`: Markdown formatting, summarization structure, proposal formatting
- `cost_level`: `free`
- `risk_level`: `low`

### `brain/worker_registry.py`

Add minimal routing support for document tasks.

Expected change:

- Keep `base-worker` as fallback.
- Route obvious documentation/proposal/Markdown tasks to `doc-worker` when registered.

### `README.md`

Document how to start and test doc-worker.

Expected content:

- Docker compose startup.
- Health check command.
- Dispatcher test command.
- Current limitation: first version does not call a real LLM.

## Why This Shape

This is the smallest useful doc-worker step.

It adds one specialized worker without changing the broader architecture. The worker stays disposable and stateless, while the Brain remains responsible for memory retrieval, routing, and task history.

The first version deliberately avoids a real LLM. That keeps the worker cheap, deterministic, and easy to validate. It can still provide value by producing structured Markdown outputs, proposal skeletons, and summary formats.

The shape also keeps future model routing open. The worker metadata can start with `model: none`, then later evolve to support local models, hosted APIs, or per-task model choices without changing the core worker API.

Most importantly, this design keeps long-term memory outside the worker. The doc-worker receives only the `memory_context` that the Brain chooses to pass for a specific task.

## Risk Level

Medium.

Reasons:

- Low runtime risk because the first version does not call external models and should only expose a local HTTP worker.
- Medium integration risk because adding a new worker touches Docker Compose, registry metadata, and routing behavior.
- Medium governance risk because proposal formatting could accidentally look like implementation authority unless the worker clearly treats proposals as drafts only.

Main constraints:

- The worker must not persist long-term memory.
- The worker must not scan `memory/` directly.
- The worker must not modify proposal approval status.
- The Brain must remain the authority for memory loading, routing, approval, and task history.

## Validation Plan

### Static checks

Run Python syntax checks:

```bash
python3 -m py_compile workers/doc-worker/app.py brain/worker_registry.py
```

### Docker build check

Build the doc-worker image through Compose:

```bash
docker compose build doc-worker
```

### Service startup check

Start the worker:

```bash
docker compose up -d doc-worker
```

Check health:

```bash
curl http://localhost:<doc-worker-port>/health
```

Expected result:

- JSON response with `status: ok`.
- Worker name should be `doc-worker`.

### Direct API check

Call `/run-task` directly:

```bash
curl -X POST http://localhost:<doc-worker-port>/run-task \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test_doc_worker",
    "task_type": "proposal_formatting",
    "input": "Create a proposal structure for a new worker.",
    "constraints": {"output_format": "markdown"},
    "memory_context": "Project rule: new capabilities require approved proposals."
  }'
```

Expected result:

- JSON response with `status: success`.
- Markdown-oriented structured output.
- `memory_loaded: true`.
- No claim that memory was stored inside the worker.

### Dispatcher routing check

Run a document-focused task through dispatcher:

```bash
.venv/bin/python brain/dispatcher.py "Format this proposal as Markdown sections."
```

Expected result:

- Dispatcher chooses `doc-worker` for obvious document/proposal/Markdown tasks.
- Task history is saved under `memory/tasks/`.
- `base-worker` remains fallback for non-document tasks.

### Memory boundary check

Confirm `workers/doc-worker/app.py` does not read from:

```text
memory/
```

Expected result:

- The worker only uses `memory_context` from the request payload.

## Approval

This proposal is not approved yet.

No code should be modified until the human explicitly approves this proposal.
