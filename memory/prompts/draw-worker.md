# draw-worker Prompt

Worker name: draw-worker

Worker type: draw

Runtime: python

Model: none

Purpose: generate picture

Skills:
- python

Permissions:
- none

Risk level: low

## Memory Boundary

Long-term memory is owned by the Brain, not this worker.

This worker must not read `memory/` directly. It may only use the `memory_context` field passed in each `/run-task` request.
