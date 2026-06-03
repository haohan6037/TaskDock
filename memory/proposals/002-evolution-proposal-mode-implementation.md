# Proposal 002: Evolution Proposal Mode Implementation

Status: implemented

Proposed at: 2026-06-03

Approved by: human

Approved at: 2026-06-03

Implemented at: 2026-06-03

Requires approval before implementation: yes

## Goal

Implement the first controlled self-evolution feature for OpenClaw Brain: Evolution Proposal Mode.

This mode should make future capability changes explicit, reviewable, and gated by human approval before runtime code is changed.

## Motivation

OpenClaw Brain is intended to gradually improve itself, but self-improvement must stay controlled. The project already records the rule that new capabilities require approved proposals. The next step is to make that rule easier to follow from the host Brain workflow.

This proposal does not implement autonomous modification. It creates a small, inspectable workflow for drafting, listing, reading, and checking proposals.

## Proposed New Files

### `brain/proposal_manager.py`

Purpose:

- Manage proposal files under `memory/proposals/`.
- Create proposal drafts with consistent metadata.
- List proposals and their status.
- Read a proposal by id.
- Check whether a proposal is approved.

Expected responsibilities:

- No code modification.
- No automatic approval.
- No execution of proposed changes.
- Only file operations inside `memory/proposals/`.

### `scripts/propose_change.sh`

Purpose:

- Provide a simple host-level CLI wrapper for creating proposal drafts.
- Keep OpenClaw-to-project interaction simple before adding a full API.

Example intended usage:

```bash
./scripts/propose_change.sh "Add doc-worker" "Create a worker for documentation summaries and proposal review."
```

### `memory/proposals/TEMPLATE.md`

Purpose:

- Define the required structure for future proposals.
- Make it obvious what information must be present before review.

Required sections:

- title
- status
- goal
- motivation
- proposed new files
- proposed modified files
- risk level
- validation plan
- approval note

## Proposed Modified Files

### `README.md`

Reason:

- Document how Evolution Proposal Mode works.
- Explain that future new capabilities should start as proposals.
- Show basic commands for creating and inspecting proposals.

### `brain/dispatcher.py`

Reason:

- Add optional proposal awareness without changing normal dispatch behavior.
- The dispatcher should be able to include approved proposal context when a task references a proposal id.

Minimal intended change:

- Add an optional CLI flag such as `--proposal 002`.
- If provided, load that proposal into the task payload memory context.
- If the proposal is not approved and the task appears to request implementation, return a clear refusal instead of dispatching.

### `brain/memory_manager.py`

Reason:

- Allow loading proposal memory when explicitly requested.
- Keep normal task memory loading unchanged.

Minimal intended change:

- Add a helper for reading proposal files by id.
- Do not add broad or automatic proposal scanning.

## Why This Shape

This keeps self-evolution controlled but practical:

- Proposals live in external memory, not inside the agent.
- OpenClaw Brain can draft and inspect proposals without changing runtime code.
- Human approval remains the gate.
- Dispatcher gains just enough awareness to avoid implementing unapproved changes.
- The system stays small and easy to audit.

## Risk Level

Low to medium.

Low because the first implementation only adds proposal management and approval checks.

Medium because dispatcher gating affects future implementation tasks. The behavior must be explicit and easy to override only by human approval, not by vague task wording.

## Validation Plan

### Static checks

Run Python syntax checks:

```bash
python3 -m py_compile brain/proposal_manager.py brain/dispatcher.py brain/memory_manager.py
```

### Proposal manager checks

Verify proposal listing:

```bash
python3 brain/proposal_manager.py list
```

Verify reading a proposal:

```bash
python3 brain/proposal_manager.py read 002
```

Verify approval check:

```bash
python3 brain/proposal_manager.py status 002
```

### Dispatcher behavior checks

Normal dispatch should still work:

```bash
python3 brain/dispatcher.py "Test normal base-worker dispatch."
```

Approved proposal context should load:

```bash
python3 brain/dispatcher.py --proposal 001 "Summarize the approved evolution proposal rule."
```

Unapproved implementation should be blocked:

```bash
python3 brain/dispatcher.py --proposal 002 "Implement this proposed feature."
```

Expected result:

- If proposal 002 is still `proposed`, dispatcher should refuse implementation.
- If proposal 002 is later changed to `approved` by the human, dispatcher may proceed.

### Regression check

Confirm new task history files are still saved under:

```text
memory/tasks/
```

## Approval

This proposal is implemented.

Implementation was completed within the scope described above.
