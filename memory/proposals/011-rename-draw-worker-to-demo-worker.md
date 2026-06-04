# Proposal 011: Rename draw-worker to demo-worker

Status: proposed

Proposed at: 2026-06-04

Requires approval before implementation: yes

## Goal

Rename the generated test worker `draw-worker` to `demo-worker`.

`demo-worker` should become the stable example worker for TaskDock Standard Worker Template Generator.

## Motivation

`draw-worker` was created as a generated validation worker for Proposal 010. Its current name suggests a specific drawing capability, but the implementation is actually a generic `model: none` FastAPI adapter generated from the standard worker template.

Renaming it to `demo-worker` makes its purpose clearer:

- it demonstrates generated worker structure
- it validates the standard worker template generator
- it is not a real drawing worker
- it remains safe because it calls no real LLM

## Proposed Renames

- `workers/draw-worker/` to `workers/demo-worker/`
- `memory/prompts/draw-worker.md` to `memory/prompts/demo-worker.md`
- `registry/worker_specs/draw-worker.json` to `registry/worker_specs/demo-worker.json`

## Proposed Modified Files

- `docker-compose.yml`
- `registry/workers.json`
- `workers/demo-worker/app.py`
- `memory/prompts/demo-worker.md`
- `registry/worker_specs/demo-worker.json`

## Docker Compose Plan

Rename the service from `draw-worker` to `demo-worker`.

Required values:

- service name: `demo-worker`
- build context: `./workers/demo-worker`
- container name: `openclawbrain-demo-worker`
- port binding: keep `8817:8817`
- `WORKER_NAME=demo-worker`
- `WORKER_TYPE=demo`
- `WORKER_MODEL=none`

## Registry Plan

Rename the registry key from `draw-worker` to `demo-worker`.

Required metadata:

- type: `demo`
- endpoint: `http://localhost:8817/run-task`
- docker_service: `demo-worker`
- model: `none`
- skills: keep the generated demo skills list
- cost_level: `free`
- risk_level: `low`

Existing `base-worker` and `doc-worker` entries must be preserved unchanged.

## Worker Spec Plan

If `registry/worker_specs/draw-worker.json` exists, rename it to `registry/worker_specs/demo-worker.json`.

The renamed spec should describe `demo-worker` as a draft generated demo worker spec and keep `preferred_model: none`.

## Template Generator Scope

Do not change the core worker template generator logic in this proposal.

Allowed changes are limited to renaming the generated example worker and updating metadata that points to it.

## Safety Rules

- Do not modify `workers/base-worker/`.
- Do not modify `workers/doc-worker/`.
- Do not call a real LLM.
- Keep generated worker model as `none`.
- Keep generated worker memory behavior: it must not read `memory/` and may only use request `memory_context`.
- Do not git push.

## Validation Plan

1. Compile changed Python files.
2. Run `docker compose config`.
3. Validate `registry/workers.json` as JSON.
4. Start or rebuild `demo-worker`.
5. Check base-worker health.
6. Check doc-worker health.
7. Check demo-worker health.
8. Call demo-worker `POST /run-task` with explicit `memory_context`.
9. Confirm `workers/base-worker/` and `workers/doc-worker/` were not modified.

## Approval

This proposal is approved by the user in the current request if it is complete and within scope.

Implementation may proceed after confirming there is no missing detail or placeholder text.
