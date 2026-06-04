# demo-worker Prompt

Worker name: demo-worker

Worker type: demo

Runtime: python

Model: none

Purpose: demonstrate the standard model:none FastAPI worker template

Skills:
- python

Permissions:
- none

Risk level: low

## Memory Boundary

Long-term memory is owned by the Brain, not this worker.

This worker must not read `memory/` directly. It may only use the `memory_context` field passed in each `/run-task` request.
