# Proposal 009: Add draw-worker

Status: proposed

Requires approval before implementation: yes

## Goal

Implement `draw-worker` as a Docker worker for `draw` tasks.

## Motivation

generate picture

## Worker Spec Summary

- worker_name: `draw-worker`
- worker_type: `draw`
- runtime: `python`
- preferred_model: `none`
- port: `8817`
- skills:
- python
- purpose: generate picture
- risk_level: `low`
- permissions:
- none
- status: `draft`
- created_at: `2026-06-03T12:11:36.296545+00:00`

## Proposed New Files

- `workers/draw-worker/Dockerfile`
- `workers/draw-worker/app.py`
- `workers/draw-worker/requirements.txt`
- `memory/prompts/draw-worker.md`

## Proposed Modified Files

- `docker-compose.yml`
- `registry/workers.json`
- `brain/worker_registry.py`
- `README.md`

## Docker Service Plan

- service name: `draw-worker`
- build context: `./workers/draw-worker`
- exposed port: `8817`
- environment:
  - `WORKER_NAME=draw-worker`
  - `WORKER_MODEL=none`
- no Docker service should be created until this proposal is approved.

## Registry Plan

- type: `draw`
- endpoint: `http://localhost:8817/run-task`
- docker_service: `draw-worker`
- model: `none`
- skills:
- python
- risk_level: `low`
- cost_level: `unknown`

## Permission Plan

Requested permissions:
- none

The worker must not access long-term memory directly unless a later approved proposal explicitly allows it. The Brain remains responsible for selecting and passing `memory_context` for each task.

## Risk Level

low

The main risks are incorrect routing, incorrect permissions, port conflicts, and accidental access to long-term memory.

## Validation Plan

1. Compile `workers/draw-worker/app.py`.
2. Validate Docker Compose config.
3. Build the `draw-worker` Docker image.
4. Check the worker health endpoint on `127.0.0.1:8817`.
5. Call `/run-task` directly with explicit `memory_context`.
6. Verify dispatcher routing for `draw` tasks.
7. Verify the worker does not read `memory/` directly.
8. Verify existing base-worker and doc-worker behavior remains unchanged.

## Approval

This generated proposal is not approved yet.

No worker code should be created before approval.
`docker-compose.yml` must not be modified before approval.
`registry/workers.json` must not be modified before approval.
`workers/draw-worker` must not be created before approval.
