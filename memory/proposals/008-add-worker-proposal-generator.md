# Proposal 008: Add Worker Proposal Generator

Status: proposed

Proposed at: 2026-06-04

Requires approval before implementation: yes

## Goal

Add a Worker Proposal Generator to TaskDock Control Panel.

The generator should create a worker implementation proposal from an existing draft worker spec in `registry/worker_specs/{worker_name}.json`.

The first version only generates proposal markdown. It must not implement a real worker.

## Motivation

Worker specs describe intended workers, but they are not implementation plans. TaskDock needs a controlled bridge from a draft worker spec to a human-reviewable implementation proposal.

Generating the proposal from the spec keeps worker planning consistent and reduces manual copy/paste. It also preserves the approval workflow: a spec can become a proposal, but the proposal must still be reviewed and approved before any runtime files change.

## Proposed New Files

### `control_panel/services/worker_proposal_service.py`

Service for generating worker implementation proposals from worker specs.

Responsibilities:

- Read `registry/worker_specs/{worker_name}.json`.
- Validate that the worker spec exists.
- Validate that the worker spec status is `draft`.
- Determine the next proposal id from `memory/proposals/`.
- Generate `memory/proposals/{next_id}-add-{worker_name}.md`.
- Include all required proposal sections.

Forbidden behavior:

- Do not create `workers/{worker_name}`.
- Do not modify `docker-compose.yml`.
- Do not modify `registry/workers.json`.
- Do not implement any worker.
- Do not commit.
- Do not push.

## Proposed Modified Files

### `control_panel/routes/worker_specs.py`

Add a Generate Proposal action for each draft worker spec.

Required behavior:

- Show a Generate Proposal button or link next to each draft spec.
- Submit `worker_name` to the proposal generation route.
- Render a short success message with the generated proposal path.

### `control_panel/rendering_worker_specs.py`

Update worker spec rendering to show the Generate Proposal operation.

Required behavior:

- Show Generate Proposal only for specs with `status: draft`.
- Make clear that this action creates only a proposal markdown file.
- Do not imply that the worker has been implemented.

### `control_panel/app.py`

If needed, include any new route wiring.

Allowed change:

- Keep `app.py` as FastAPI entrypoint only.
- Do not add business logic to `app.py`.

## Generated Proposal Requirements

The generated proposal must include these sections:

- `Goal`
- `Motivation`
- `Worker Spec Summary`
- `Proposed New Files`
- `Proposed Modified Files`
- `Docker Service Plan`
- `Registry Plan`
- `Permission Plan`
- `Risk Level`
- `Validation Plan`
- `Approval`

## Generated Proposal Content Rules

### Goal

Describe implementing the worker named in the spec.

### Motivation

Use the spec `purpose` field and explain why the worker is useful.

### Worker Spec Summary

Include:

- worker_name
- worker_type
- runtime
- preferred_model
- port
- skills
- purpose
- risk_level
- permissions
- status
- created_at

### Proposed New Files

List the files that would be created after approval, such as:

- `workers/{worker_name}/Dockerfile`
- `workers/{worker_name}/app.py`
- `workers/{worker_name}/requirements.txt`
- `memory/prompts/{worker_name}.md`

### Proposed Modified Files

List files that would be modified after approval:

- `docker-compose.yml`
- `registry/workers.json`
- `brain/worker_registry.py`
- `README.md`

### Docker Service Plan

Describe the planned Docker service:

- service name
- image build context
- exposed port
- environment variables
- no real service creation until approval

### Registry Plan

Describe the planned `registry/workers.json` entry:

- type
- endpoint
- docker_service
- model
- skills
- risk_level
- cost level if known

### Permission Plan

Describe how the permissions from the worker spec should constrain the worker.

The proposal must state that the worker must not access long-term memory directly unless a later approved proposal explicitly allows it.

### Risk Level

Use the spec `risk_level` field and explain the risk.

### Validation Plan

Include validation checks for:

1. Python compile.
2. Docker Compose config.
3. Docker build.
4. Worker health endpoint.
5. Direct `/run-task` call.
6. Dispatcher routing.
7. Memory boundary check.
8. Existing base-worker and doc-worker behavior remains unchanged.

### Approval

State clearly:

- This generated proposal is not approved yet.
- No worker code should be created before approval.
- `docker-compose.yml` must not be modified before approval.
- `registry/workers.json` must not be modified before approval.
- `workers/{worker_name}` must not be created before approval.

## Why This Shape

This is the smallest useful bridge from worker specs to implementation proposals.

Worker specs remain draft intent. Generated proposals become reviewable implementation plans. Real worker creation remains blocked until the human explicitly approves the generated proposal.

This keeps TaskDock's worker lifecycle controlled:

1. Create worker spec.
2. Generate implementation proposal.
3. Human reviews proposal.
4. Human approves proposal.
5. Only then implement worker.

## Risk Level

Low.

The feature only reads draft JSON specs and writes proposal markdown files.

Main risks:

- A generated proposal could be mistaken for approval.
- A malformed spec could produce a weak proposal.
- Duplicate proposal files could be created for the same worker.

Risk controls:

- Generated proposal status must be `proposed`.
- UI must clearly say Generate Proposal does not implement a worker.
- Service must validate required spec fields.
- Service must use the next available proposal id.
- No runtime files may be changed by this feature.

## Validation Plan

### Static checks

Run:

```bash
python3 -m py_compile control_panel/services/worker_proposal_service.py
python3 -m py_compile control_panel/routes/worker_specs.py
python3 -m py_compile control_panel/rendering_worker_specs.py
python3 -m py_compile control_panel/app.py
```

Expected result:

- All files compile successfully.

### Spec read check

Create or use an existing draft worker spec:

```text
registry/worker_specs/data-worker.json
```

Expected result:

- Worker Specs page shows the draft spec.
- Generate Proposal action is visible for the draft spec.

### Proposal generation check

Click Generate Proposal for `data-worker`.

Expected result:

- A new proposal is created under `memory/proposals/`.
- File name follows `{next_id}-add-data-worker.md`.
- Status is `proposed`.
- All required sections are present.
- The proposal includes the worker spec summary.

### Boundary check

After generating a proposal, confirm:

```text
docker-compose.yml is unchanged
registry/workers.json is unchanged
workers/data-worker does not exist
```

Expected result:

- No real worker was created.
- No Docker service was added.
- No runtime registry entry was added.

### Existing flow check

Run existing Control Panel validation.

Expected result:

- base-worker health still passes.
- doc-worker health still passes.
- base dispatcher still routes to base-worker.
- doc-worker routing still routes to doc-worker.

## Approval

This proposal is not approved yet.

No code should be modified until the human explicitly approves Proposal 008.
