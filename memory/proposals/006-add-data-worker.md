# Proposal 005: Add data-worker

Status: proposed

Requires approval before implementation: yes

## Goal

Add a future `data-worker` Docker worker proposal for `data` tasks.

## Motivation

Purpose: CSV,Database

## Proposed New Files

- `workers/data-worker/Dockerfile`: Docker image definition for the proposed worker.
- `workers/data-worker/app.py`: FastAPI worker with `/health` and `/run-task`.
- `workers/data-worker/requirements.txt`: Worker dependencies.
- `memory/prompts/data-worker.md`: Worker role, constraints, and future model notes.

## Proposed Modified Files

- `docker-compose.yml`: Add the proposed worker service on port `9913` after approval.
- `registry/workers.json`: Register `data-worker` with `model: none` for the first version after approval.
- `brain/worker_registry.py`: Add minimal routing for `data` tasks after approval.
- `README.md`: Document startup and testing instructions after approval.

## Worker Draft

- worker_name: `data-worker`
- worker_type: `data`
- port: `9913`
- model: `none`
- risk_level: `low`

## Skills

- csv
- excel
- data analysis

## Why This Shape

This proposal only describes a future worker. It does not create `workers/data-worker`, does not modify Docker Compose, and does not modify the worker registry. The worker should remain disposable and stateless, while the Brain remains responsible for memory loading, routing, approval, and task history.

## Risk Level

low

The main risks are incorrect routing, port collision, and accidentally giving the worker access to long-term memory. The first implementation should use `model: none` and should only use `memory_context` passed by the Brain.

## Validation Plan

After approval and implementation:

1. Compile the worker Python file.
2. Validate `registry/workers.json`.
3. Validate Docker Compose config.
4. Build and start the worker.
5. Check `/health` on `127.0.0.1:9913`.
6. Call `/run-task` with explicit `memory_context`.
7. Confirm the worker does not read `memory/`.
8. Confirm existing base-worker and doc-worker behavior is unchanged.

## Approval

This proposal is not approved yet.

No code should be modified, no `workers/data-worker` directory should be created, and no Docker Compose or registry changes should be made until the human explicitly approves this proposal.
