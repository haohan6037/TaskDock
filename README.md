# OpenClawBrain

Host-based OpenClaw Brain architecture.

## Goal

- OpenClaw runs on the Mac host as the main brain.
- Docker containers are lightweight disposable workers.
- Long-term memory is stored outside agents.
- Each task loads only the memory it needs.
- Workers are stateless by default.

## First runnable flow

```text
User command
 -> brain/dispatcher.py
 -> registry/workers.json
 -> memory/*.md
 -> POST /run-task on base-worker or doc-worker
 -> worker result
 -> memory/tasks/*.json
```

## Run

### 1. Start workers

```bash
cd ~/OpenClawBrain
docker compose up --build -d
```

### 2. Test dispatcher

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r brain/requirements.txt
python brain/dispatcher.py "Create a simple plan for the first OpenClaw Brain worker."
```

### 3. Check task history

```bash
ls memory/tasks
cat memory/tasks/*.json
```

## Evolution Proposal Mode

New capabilities and meaningful behavior changes should start as proposals under `memory/proposals/`.

Create a proposal draft:

```bash
./scripts/propose_change.sh "Add doc-worker" "Create a worker for documentation summaries and proposal review."
```

List proposals:

```bash
python3 brain/proposal_manager.py list
```

Read a proposal:

```bash
python3 brain/proposal_manager.py read 002
```

Check proposal status:

```bash
python3 brain/proposal_manager.py status 002
```

Load an approved proposal as explicit dispatcher context:

```bash
python3 brain/dispatcher.py --proposal 001 "Summarize the approved evolution proposal rule."
```

If a task asks to implement an unapproved proposal, the dispatcher should block it and save a blocked task record.

## Doc Worker

`doc-worker` is a lightweight document-focused Docker worker.

Current capabilities:

- Markdown formatting
- Summary structure generation
- Proposal formatting
- Section outline generation

Current limits:

- It does not call a real LLM.
- Its model is `none`.
- It does not read `memory/`.
- It only uses `memory_context` sent by the Brain in the task request.

Start doc-worker:

```bash
docker compose up --build -d doc-worker
```

Check health:

```bash
curl http://localhost:8812/health
```

Call doc-worker directly:

```bash
curl -X POST http://localhost:8812/run-task \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test_doc_worker",
    "task_type": "proposal_formatting",
    "input": "Create a proposal structure for a new worker.",
    "constraints": {"output_format": "markdown"},
    "memory_context": "Project rule: new capabilities require approved proposals."
  }'
```

Test dispatcher routing:

```bash
.venv/bin/python brain/dispatcher.py "Format this proposal as Markdown sections."
```

## Next stage

- Add code-worker
- Add data-worker
- Add Docker Controller
- Add model routing
- Add cost tracking
