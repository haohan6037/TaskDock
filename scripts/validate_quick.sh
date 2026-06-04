#!/usr/bin/env bash
set -uo pipefail

ROOT="/Users/happyfamily/OpenClawBrain"
cd "$ROOT" || exit 1

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  echo "[PASS] $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  echo "[FAIL] $1"
  echo "       $2"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

run_cmd_check() {
  local name="$1"
  shift
  local output

  output="$("$@" 2>&1)"
  local code=$?

  if [ "$code" -eq 0 ]; then
    pass "$name"
  else
    fail "$name" "$output"
  fi
}

echo "========================================"
echo " TaskDock Quick Validation"
echo " Project: $ROOT"
echo "========================================"
echo ""

echo "== 1. Config checks =="
run_cmd_check "registry/workers.json is valid JSON" python3 -m json.tool registry/workers.json
run_cmd_check "docker compose config is valid" docker compose config

if [ -f "config/brain.json" ]; then
  run_cmd_check "config/brain.json is valid JSON" python3 -m json.tool config/brain.json
else
  fail "config/brain.json exists" "Missing config/brain.json"
fi

if [ -f "config/permissions.json" ]; then
  run_cmd_check "config/permissions.json is valid JSON" python3 -m json.tool config/permissions.json
else
  fail "config/permissions.json exists" "Missing config/permissions.json"
fi

echo ""
echo "== 2. Python compile checks =="

PY_FILES=$(find brain control_panel workers \
  -type f \
  -name "*.py" \
  -not -path "*/__pycache__/*" \
  -not -path "*/.venv/*" \
  2>/dev/null)

if [ -z "$PY_FILES" ]; then
  fail "Python files found" "No Python files found under brain/control_panel/workers"
else
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    run_cmd_check "compile $file" python3 -m py_compile "$file"
  done <<< "$PY_FILES"
fi

echo ""
echo "== 3. Worker health checks from registry =="

python3 - <<'PY' > /tmp/taskdock_worker_endpoints.txt
import json
from pathlib import Path

path = Path("registry/workers.json")
data = json.loads(path.read_text())

for name, meta in data.items():
    endpoint = meta.get("endpoint", "")
    if endpoint.endswith("/run-task"):
        health = endpoint[:-len("/run-task")] + "/health"
    else:
        health = endpoint.rstrip("/") + "/health"
    print(f"{name}\t{health}")
PY

while IFS=$'\t' read -r worker health_url; do
  [ -z "$worker" ] && continue

  output=$(curl -fsS --max-time 5 "$health_url" 2>&1)
  code=$?

  if [ "$code" -eq 0 ]; then
    pass "$worker health"
  else
    fail "$worker health" "$output"
  fi
done < /tmp/taskdock_worker_endpoints.txt

rm -f /tmp/taskdock_worker_endpoints.txt

echo ""
echo "== 4. Dispatcher route checks =="

route_check() {
  local name="$1"
  local task_text="$2"
  local expected_worker="$3"

  python3 - "$task_text" "$expected_worker" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

task_text = sys.argv[1]
expected_worker = sys.argv[2]
root = Path("/Users/happyfamily/OpenClawBrain")

candidates = [
    root / "brain" / "task_dispatcher.py",
    root / "brain" / "dispatcher.py",
]

dispatcher = None
for candidate in candidates:
    if candidate.exists():
        dispatcher = candidate
        break

if dispatcher is None:
    print("No dispatcher found: expected brain/task_dispatcher.py or brain/dispatcher.py")
    sys.exit(2)

venv_python = root / ".venv" / "bin" / "python"
python_bin = str(venv_python) if venv_python.exists() else sys.executable

proc = subprocess.run(
    [python_bin, str(dispatcher), task_text],
    cwd=str(root),
    text=True,
    capture_output=True,
)

combined = (proc.stdout or "") + "\n" + (proc.stderr or "")

start = combined.find("{")
end = combined.rfind("}")

if start == -1 or end == -1 or end <= start:
    print("Could not find JSON object in dispatcher output.")
    print(combined[-2000:])
    sys.exit(3)

raw_json = combined[start:end + 1]

try:
    data = json.loads(raw_json)
except Exception as exc:
    print(f"Could not parse dispatcher JSON: {exc}")
    print(raw_json[-2000:])
    sys.exit(4)

status = data.get("status")
actual_worker = None

result = data.get("result")
if isinstance(result, dict):
    actual_worker = result.get("worker")

if actual_worker is None:
    worker_meta = data.get("worker")
    if isinstance(worker_meta, dict):
        actual_worker = worker_meta.get("docker_service") or worker_meta.get("name")

if status == "success" and actual_worker == expected_worker:
    print(f"OK: routed to {actual_worker}")
    sys.exit(0)

print(f"Expected worker: {expected_worker}")
print(f"Actual worker: {actual_worker}")
print(f"Status: {status}")
print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
sys.exit(5)
PY

  code=$?
  if [ "$code" -eq 0 ]; then
    pass "$name routes to $expected_worker"
  else
    fail "$name routes to $expected_worker" "Dispatcher route check failed"
  fi
}

route_check "generic task" "Run a generic scaffold test." "base-worker"
route_check "document task" "Format this proposal as Markdown sections." "doc-worker"
route_check "demo/template task" "Run a demo template worker test." "demo-worker"
route_check "validation task" "Run validation QA check gate." "validation-worker"

echo ""
echo "== 5. Git safety checks =="

echo "Current git status:"
git status --short

STAGED_FILES=$(git diff --cached --name-only)

if echo "$STAGED_FILES" | grep -E '^(\.venv/|logs/|workspaces/)' >/dev/null 2>&1; then
  fail "no forbidden staged files" "Forbidden staged files found in .venv/, logs/, or workspaces/"
else
  pass "no forbidden staged files"
fi

UNTRACKED_TASKS=$(git status --short | grep '?? memory/tasks/.*\.json' || true)
if [ -n "$UNTRACKED_TASKS" ]; then
  echo "[INFO] Generated task history files detected. Do not commit these:"
  echo "$UNTRACKED_TASKS"
else
  pass "no untracked generated task history files"
fi

echo ""
echo "========================================"
echo " Quick Validation Summary"
echo " PASS: $PASS_COUNT"
echo " FAIL: $FAIL_COUNT"
echo "========================================"

if [ "$FAIL_COUNT" -eq 0 ]; then
  echo "QUICK VALIDATION: PASS"
  exit 0
else
  echo "QUICK VALIDATION: FAIL"
  exit 1
fi
