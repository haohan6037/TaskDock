# Decision Memory: OpenClaw Brain

## Decision 1: OpenClaw runs on host

Reason:
The Brain needs to control Docker workers and access host-level project files.

Status:
Accepted.

## Decision 2: Workers are lightweight HTTP services

Reason:
Avoid running full OpenClaw inside every worker. Reduce complexity and improve isolation.

Status:
Accepted.

## Decision 3: Memory is external

Reason:
Agents and workers should not own long-term memory. Each task should load only the relevant memory.

Status:
Accepted.

## Decision 4: New capabilities require approved proposals

Reason:
OpenClaw Brain should evolve gradually and only with human approval. Any new capability or meaningful behavior change must first be proposed, reviewed, and approved before implementation.

Status:
Accepted.

Reference:
`memory/proposals/001-evolution-proposal-mode.md`
