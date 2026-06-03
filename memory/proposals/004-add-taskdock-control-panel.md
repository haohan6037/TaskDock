# Proposal 004: Add TaskDock Control Panel

Status: proposed

Proposed at: 2026-06-03

Requires approval before implementation: yes

## Goal

Add a local TaskDock Control Panel that turns the current manual OpenClawBrain workflow into a browser-based UI.

The first version should let the human use a local web page to:

- View Git status.
- View worker status.
- View proposal list.
- Create a proposal.
- Automatically check whether a proposal is well formed.
- Run the approved validation flow.
- Display validation results.
- Execute commit and push only after validation passes.

The UI must listen only on `127.0.0.1:8890`.

## Motivation

OpenClawBrain is moving toward controlled task orchestration. The current workflow works, but it is still mostly manual: checking Git, checking workers, reading proposals, validating changes, and committing results all require separate terminal commands.

A small local web UI makes the workflow easier to inspect and reduces mistakes. It also creates a clear control surface where every step can show:

- what will be checked,
- which whitelisted operation will run,
- what result came back,
- whether the next action is allowed.

This proposal does not add autonomous behavior. It creates a local control panel for explicit human-driven operations.

## Proposed New Files

### `control-panel/app.py`

FastAPI application for the local TaskDock Control Panel.

Responsibilities:

- Bind only to `127.0.0.1:8890`.
- Render HTML pages.
- Call only approved internal service functions.
- Never accept arbitrary shell commands from the browser.
- Never execute commands outside the whitelist.
- Show status, validation state, and action availability.

Expected routes:

- `GET /`
- `GET /git`
- `GET /workers`
- `GET /proposals`
- `GET /proposals/{proposal_id}`
- `GET /proposals/new`
- `POST /proposals`
- `GET /validate`
- `POST /validate/run`
- `GET /commit`
- `POST /commit`
- `POST /push`

### `control-panel/command_whitelist.py`

Defines the only operations the control panel may run.

Allowed operations:

- `git status`
- `git diff --stat`
- `git add`
- `git commit`
- `git push`
- `docker compose ps`
- `docker compose up --build -d`
- worker health checks using `curl` or structured HTTP requests to local worker health endpoints
- known test scripts
- list proposals
- read proposal
- create proposal

Rules:

- No arbitrary shell strings.
- No user-supplied command execution.
- No `shell=True`.
- Commands must be represented as fixed argument arrays or internal Python functions.
- Operations must run from `/Users/happyfamily/OpenClawBrain`.
- External network management interfaces are not allowed.

### `control-panel/services/git_service.py`

Git workflow service.

Responsibilities:

- Show status using whitelisted `git status`.
- Show summary using whitelisted `git diff --stat`.
- Stage files using whitelisted `git add`.
- Commit with a human-provided commit message.
- Push only after validation has passed.

Safety rules:

- No destructive Git commands.
- No reset.
- No checkout.
- No rebase.
- No force push.
- Commit and push buttons must show the latest validation result before execution.

### `control-panel/services/worker_service.py`

Worker status service.

Responsibilities:

- Show Docker Compose service status using whitelisted `docker compose ps`.
- Start configured workers using whitelisted `docker compose up --build -d`.
- Check local worker health endpoints.

Allowed health endpoints:

- `http://127.0.0.1:8811/health`
- `http://127.0.0.1:8812/health`

Safety rules:

- No `docker run`.
- No arbitrary Docker commands.
- No access to external management interfaces.
- Do not change base-worker or doc-worker behavior.

### `control-panel/services/proposal_service.py`

Proposal service.

Responsibilities:

- List proposals from `memory/proposals/`.
- Read a proposal by id.
- Create a proposal using the existing proposal structure.
- Validate proposal quality.

Proposal quality checks:

- File name starts with a three-digit id.
- Title is present.
- Status is present.
- Goal is present.
- Motivation is present.
- Proposed New Files section is present and non-empty.
- Proposed Modified Files section is present and non-empty.
- Why This Shape section is present and non-empty.
- Risk Level section is present and non-empty.
- Validation Plan section is present and non-empty.
- Approval section is present.
- The proposal text contains no `TBD`.
- The proposal states whether implementation requires approval.

### `control-panel/services/validation_service.py`

Validation service for known checks.

Responsibilities:

- Run only the approved validation flow.
- Capture command output.
- Record pass/fail for each check.
- Expose the latest validation result to the UI.

First validation flow:

- `python3 -m py_compile workers/doc-worker/app.py brain/worker_registry.py`
- `python3 -m json.tool registry/workers.json`
- `docker compose config`
- `docker compose ps`
- health check for `base-worker`
- health check for `doc-worker`
- route check proving document tasks route to `doc-worker`
- route check proving generic tasks fall back to `base-worker`

The route checks should be implemented as known Python checks, not arbitrary shell.

### `control-panel/templates/base.html`

Shared HTML layout.

Required UI elements:

- Navigation links for Git, Workers, Proposals, Validation, Commit.
- Clear local-only notice: `TaskDock Control Panel listens only on 127.0.0.1:8890`.
- Current validation status indicator.
- Current worker status summary.

### `control-panel/templates/index.html`

Dashboard page.

Displays:

- Git status summary.
- Worker status summary.
- Proposal count by status.
- Latest validation result.
- Whether commit/push is currently allowed.

### `control-panel/templates/git.html`

Git status page.

Displays:

- What will be checked.
- `git status` result.
- `git diff --stat` result.
- Files staged for commit.
- Commit message form.
- Commit and push buttons disabled unless validation has passed.

### `control-panel/templates/workers.html`

Worker status page.

Displays:

- What worker state is being checked.
- Docker Compose status.
- `base-worker` health result.
- `doc-worker` health result.
- Button to run whitelisted `docker compose up --build -d`.

### `control-panel/templates/proposals.html`

Proposal list page.

Displays:

- Proposal id.
- Title.
- Status.
- Whether the proposal passes structure validation.
- Link to read each proposal.
- Link to create a new proposal.

### `control-panel/templates/proposal_detail.html`

Proposal detail page.

Displays:

- Proposal content.
- Proposal quality checks.
- Missing or invalid sections.
- Whether the proposal is eligible for human review.

### `control-panel/templates/proposal_new.html`

Create proposal page.

Displays:

- Form fields for title, goal, motivation, proposed files, modified files, risk, and validation plan.
- Preview of the generated proposal.
- Clear note that creating a proposal does not approve or implement it.

### `control-panel/templates/validation.html`

Validation page.

Displays:

- Every validation step.
- What each step checks.
- Whitelisted operation used.
- Latest output.
- Pass/fail status.
- Overall validation result.

### `control-panel/templates/commit.html`

Commit and push page.

Displays:

- Latest validation result.
- Git status.
- Files to be committed.
- Commit message input.
- Commit button.
- Push button.
- Clear notice that push is allowed only after validation passes.

### `control-panel/static/style.css`

Simple local CSS for readable status pages.

Requirements:

- No external CSS.
- No CDN.
- No remote assets.
- Clear pass/fail badges.
- Compact layout suitable for local operational use.

### `control-panel/requirements.txt`

Dependencies for the control panel.

Expected first version:

- `fastapi`
- `uvicorn[standard]`
- `jinja2`
- `requests`

### `scripts/start_control_panel.sh`

Starts the local UI.

Required behavior:

- Change directory to `/Users/happyfamily/OpenClawBrain`.
- Start FastAPI with Uvicorn.
- Bind host to `127.0.0.1`.
- Bind port to `8890`.
- Do not expose the UI on `0.0.0.0`.

Expected command shape:

```bash
uvicorn control-panel.app:app --host 127.0.0.1 --port 8890
```

The final implementation may need a Python package-safe directory name such as `control_panel/` instead of `control-panel/`. If so, the code path should use the package-safe name while README and UI labels may still call the feature `TaskDock Control Panel`.

## Proposed Modified Files

### `README.md`

Document how to start and use TaskDock Control Panel.

Required content:

- Local URL: `http://127.0.0.1:8890`
- Startup command.
- Local-only security note.
- Description of Git, Workers, Proposals, Validation, Commit/Push pages.
- Statement that commands are whitelisted and arbitrary shell execution is forbidden.

### `brain/proposal_manager.py`

Expose reusable proposal helpers for the control panel if needed.

Allowed changes:

- Add functions for proposal quality validation.
- Add functions for proposal creation from structured fields.
- Preserve existing CLI behavior.
- Do not implement approval changes unless explicitly approved by a later proposal.

### `brain/worker_registry.py`

Expose reusable worker metadata helpers if needed.

Allowed changes:

- Add a function to list registered workers.
- Preserve existing routing behavior.
- Do not change base-worker or doc-worker behavior.

## Why This Shape

FastAPI with simple HTML templates is the smallest useful control panel for the current project.

It avoids a frontend build system, avoids external assets, and keeps the interface inspectable. The panel can be run locally by the host Brain while leaving Docker workers disposable and unchanged.

The command whitelist is central to the design. The UI should never become a generic terminal in the browser. Each action maps to a known operation with fixed arguments or a structured service function. This protects the host system while still making the workflow easier to operate.

The first version focuses on visibility and explicit human control:

- show current state,
- show what will be checked,
- run known validation,
- display results,
- allow commit and push only after validation passes.

This shape does not alter `base-worker` or `doc-worker`. It adds a host-level UI around the existing workflow rather than changing worker behavior.

## Risk Level

Medium.

Reasons:

- The UI is local-only, but it controls Git and Docker operations.
- Commit and push are external effects and must remain gated by validation and human action.
- A poorly implemented command runner could become unsafe if it accepted arbitrary user input.
- Proposal creation must not imply proposal approval.

Risk controls:

- Bind only to `127.0.0.1:8890`.
- Do not expose the panel on `0.0.0.0`.
- Use fixed command arrays or internal Python functions.
- Never use arbitrary shell execution.
- Do not include `docker run`.
- Do not include destructive Git operations.
- Show validation results before commit and push.
- Keep base-worker and doc-worker behavior unchanged.

## Validation Plan

### Static checks

Run:

```bash
python3 -m py_compile control_panel/app.py
python3 -m py_compile control_panel/services/git_service.py
python3 -m py_compile control_panel/services/worker_service.py
python3 -m py_compile control_panel/services/proposal_service.py
python3 -m py_compile control_panel/services/validation_service.py
```

Expected result:

- All files compile successfully.

### Whitelist checks

Inspect `control_panel/command_whitelist.py`.

Expected result:

- Only approved operations are represented.
- No arbitrary command strings.
- No `shell=True`.
- No `docker run`.
- No destructive Git commands.
- No external management URLs.

### Local binding check

Start the control panel.

Expected result:

- The server listens on `127.0.0.1:8890`.
- The server does not listen on `0.0.0.0`.

### Page checks

Open:

```text
http://127.0.0.1:8890
http://127.0.0.1:8890/git
http://127.0.0.1:8890/workers
http://127.0.0.1:8890/proposals
http://127.0.0.1:8890/validate
http://127.0.0.1:8890/commit
```

Expected result:

- Every page renders.
- Every page clearly states what it checks.
- Validation page shows each validation step and latest result.
- Commit page shows validation status before allowing commit or push.

### Worker status checks

From the Workers page, run worker status refresh.

Expected result:

- `base-worker` status is shown.
- `doc-worker` status is shown.
- Worker health uses only local health endpoints.
- Existing worker behavior is unchanged.

### Proposal checks

From the Proposals page:

- List proposals.
- Read an existing proposal.
- Create a new proposal draft.
- Run proposal quality validation.

Expected result:

- Created proposal has no placeholder sections.
- Created proposal status is `proposed`.
- Created proposal is not treated as approved.
- Proposal quality validation reports pass/fail by section.

### Validation flow checks

From the Validation page, run validation.

Expected result:

- Git status check runs.
- Worker status check runs.
- Proposal checks run.
- Known test scripts or known validation functions run.
- Results are displayed per step.
- Overall validation result is visible.

### Commit and push gating checks

Before validation passes:

- Commit is disabled.
- Push is disabled.

After validation passes:

- Commit requires a human-provided message.
- Push requires a successful commit state.
- The page shows the exact whitelisted Git operation being used.

## Approval

This proposal is not approved yet.

No code should be modified until the human explicitly approves Proposal 004.
