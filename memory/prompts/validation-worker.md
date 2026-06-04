# validation-worker Prompt

Worker name: validation-worker

Worker type: validation

Runtime: docker FastAPI worker

Model: none

Purpose: run fixed TaskDock QA and validation gate checks.

## Boundaries

- Do not call a real LLM.
- Do not modify project files.
- Do not git commit.
- Do not git push.
- Do not run docker run.
- Do not own long-term memory.
- Do not read `memory/` as long-term memory.
- It may inspect project state and generated files such as `memory/tasks/*.json`.

## Output

Return structured JSON with overall pass/fail, checks, git summary, and commit advice.
