from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")
PROPOSALS_DIR = PROJECT_ROOT / "memory" / "proposals"
WORKER_SPECS_DIR = PROJECT_ROOT / "registry" / "worker_specs"

REQUIRED_SPEC_FIELDS = [
    "worker_name",
    "worker_type",
    "runtime",
    "preferred_model",
    "port",
    "skills",
    "purpose",
    "risk_level",
    "permissions",
    "status",
    "created_at",
]


def next_proposal_id() -> str:
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    existing = []
    for path in PROPOSALS_DIR.glob("[0-9][0-9][0-9]-*.md"):
        try:
            existing.append(int(path.name.split("-", 1)[0]))
        except ValueError:
            continue
    return str(max(existing, default=0) + 1).zfill(3)


def load_worker_spec(worker_name: str) -> dict:
    path = WORKER_SPECS_DIR / f"{worker_name}.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    missing = [field for field in REQUIRED_SPEC_FIELDS if field not in spec]
    if missing:
        raise ValueError(f"Worker spec is missing fields: {', '.join(missing)}")
    if spec["status"] != "draft":
        raise ValueError("Only draft worker specs can generate proposals.")
    return spec


def list_items(value: list[str]) -> str:
    return "\n".join(f"- {item}" for item in value) if value else "- none"


def generate_worker_proposal(worker_name: str) -> Path:
    spec = load_worker_spec(worker_name)
    proposal_id = next_proposal_id()
    name = spec["worker_name"]
    path = PROPOSALS_DIR / f"{proposal_id}-add-{name}.md"

    content = f"""# Proposal {proposal_id}: Add {name}

Status: proposed

Requires approval before implementation: yes

## Goal

Implement `{name}` as a Docker worker for `{spec['worker_type']}` tasks.

## Motivation

{spec['purpose']}

## Worker Spec Summary

- worker_name: `{spec['worker_name']}`
- worker_type: `{spec['worker_type']}`
- runtime: `{spec['runtime']}`
- preferred_model: `{spec['preferred_model']}`
- port: `{spec['port']}`
- skills:
{list_items(spec['skills'])}
- purpose: {spec['purpose']}
- risk_level: `{spec['risk_level']}`
- permissions:
{list_items(spec['permissions'])}
- status: `{spec['status']}`
- created_at: `{spec['created_at']}`

## Proposed New Files

- `workers/{name}/Dockerfile`
- `workers/{name}/app.py`
- `workers/{name}/requirements.txt`
- `memory/prompts/{name}.md`

## Proposed Modified Files

- `docker-compose.yml`
- `registry/workers.json`
- `brain/worker_registry.py`
- `README.md`

## Docker Service Plan

- service name: `{name}`
- build context: `./workers/{name}`
- exposed port: `{spec['port']}`
- environment:
  - `WORKER_NAME={name}`
  - `WORKER_MODEL={spec['preferred_model']}`
- no Docker service should be created until this proposal is approved.

## Registry Plan

- type: `{spec['worker_type']}`
- endpoint: `http://localhost:{spec['port']}/run-task`
- docker_service: `{name}`
- model: `{spec['preferred_model']}`
- skills:
{list_items(spec['skills'])}
- risk_level: `{spec['risk_level']}`
- cost_level: `unknown`

## Permission Plan

Requested permissions:
{list_items(spec['permissions'])}

The worker must not access long-term memory directly unless a later approved proposal explicitly allows it. The Brain remains responsible for selecting and passing `memory_context` for each task.

## Risk Level

{spec['risk_level']}

The main risks are incorrect routing, incorrect permissions, port conflicts, and accidental access to long-term memory.

## Validation Plan

1. Compile `workers/{name}/app.py`.
2. Validate Docker Compose config.
3. Build the `{name}` Docker image.
4. Check the worker health endpoint on `127.0.0.1:{spec['port']}`.
5. Call `/run-task` directly with explicit `memory_context`.
6. Verify dispatcher routing for `{spec['worker_type']}` tasks.
7. Verify the worker does not read `memory/` directly.
8. Verify existing base-worker and doc-worker behavior remains unchanged.

## Approval

This generated proposal is not approved yet.

No worker code should be created before approval.
`docker-compose.yml` must not be modified before approval.
`registry/workers.json` must not be modified before approval.
`workers/{name}` must not be created before approval.
"""
    path.write_text(content, encoding="utf-8")
    return path
