# Proposal 015: Add validation-worker

Status: proposed

Proposed at: 2026-06-04

Requires approval before implementation: yes

## Goal

Add a formal `validation-worker` to TaskDock.

The worker should act as an independent QA and validation gate worker for the Brain and Control Panel.

## Motivation

TaskDock currently runs validation logic inside the Control Panel process. That makes validation less reusable and keeps QA concerns mixed with UI concerns.

Moving the fixed validation flow into a dedicated Docker worker gives TaskDock a clearer separation:

- the Brain dispatches and coordinates work
- workers perform bounded responsibilities
- `validation-worker` performs QA checks
- Control Panel asks the validation worker for a report

## Worker Responsibilities

`validation-worker` should:

- receive validation requests from the Brain or Control Panel
- run a fixed validation flow
- return structured JSON validation reports
- inspect project state and generated files
- avoid modifying project files
- avoid git commit
- avoid git push
- avoid `docker run`
- avoid real LLM calls
- use `model: none`

## Required Endpoints

- `GET /health`
- `POST /run-task`

## Validation Checks

The first version should check:

1. Python compile checks.
2. `docker compose config`.
3. `registry/workers.json` JSON validity.
4. `base-worker` health.
5. `doc-worker` health.
6. `demo-worker` health.
7. Dispatcher generic task routes to `base-worker`.
8. Dispatcher document task routes to `doc-worker`.
9. Dispatcher demo/template task routes to `demo-worker`.
10. Git status summary.
11. `memory/tasks/*.json` are generated task history files and should not be committed.
12. Forbidden paths such as `.venv`, `logs`, and `workspaces` are not tracked or staged.

## Report Shape

The worker should return JSON shaped like:

```json
{
  "worker": "validation-worker",
  "overall": "pass",
  "checks": [
    {
      "name": "base-worker health",
      "status": "pass",
      "summary": "base-worker returned ok"
    }
  ],
  "git_summary": {},
  "commit_advice": {
    "ready": true,
    "include": [],
    "exclude": ["memory/tasks/*.json"]
  }
}
```

## Proposed New Files

- `workers/validation-worker/Dockerfile`
- `workers/validation-worker/app.py`
- `workers/validation-worker/requirements.txt`
- `memory/prompts/validation-worker.md`

## Proposed Modified Files

- `docker-compose.yml`
- `registry/workers.json`
- `control_panel/services/validation_service.py`
- `README.md`

## Docker Plan

Add a Docker Compose service named `validation-worker`.

Required behavior:

- service name: `validation-worker`
- container name: `openclawbrain-validation-worker`
- port: `8818`
- model: `none`
- mount the project directory read-only or minimally enough to inspect project state
- mount Docker socket only so fixed `docker compose config` and status checks can run
- do not run `docker run`

## Registry Plan

Add `validation-worker` to `registry/workers.json`.

Required metadata:

- type: `validation`
- endpoint: `http://localhost:8818/run-task`
- docker_service: `validation-worker`
- model: `none`
- skills include validation and qa gate terms
- cost_level: `free`
- risk_level: `medium`

Existing `base-worker`, `doc-worker`, and `demo-worker` entries must remain unchanged.

## Control Panel Plan

Update Run Validation so the Control Panel asks `validation-worker` for the validation report.

The UI should continue to show concise pass/fail results and keep details collapsible.

If `validation-worker` is unavailable, the Control Panel should return a clear validation failure instead of silently passing.

## Safety Rules

- Do not modify `workers/base-worker/`.
- Do not modify `workers/doc-worker/`.
- Do not modify `workers/demo-worker/`.
- Do not let validation-worker modify project files.
- Do not let validation-worker git commit.
- Do not let validation-worker git push.
- Do not let validation-worker run `docker run`.
- Do not call a real LLM.
- Keep `model: none`.
- Do not git push.

## Validation Plan

1. Compile changed Python files.
2. Run `docker compose config`.
3. Validate `registry/workers.json` as JSON.
4. Build and start `validation-worker`.
5. Check `base-worker` health.
6. Check `doc-worker` health.
7. Check `demo-worker` health.
8. Check `validation-worker` health.
9. Call `validation-worker` `POST /run-task`.
10. Confirm returned report is structured JSON and overall pass.
11. Confirm Control Panel `run_validation()` calls validation-worker and returns steps.
12. Confirm worker code for base/doc/demo is unchanged.

## Approval

This proposal is approved by the user in the current request if it is complete and within scope.

Implementation may proceed after confirming there is no missing detail or placeholder text.
