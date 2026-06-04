#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

info() {
  printf '[bootstrap] %s\n' "$1"
}

fail() {
  printf '[bootstrap] ERROR: %s\n' "$1" >&2
  exit 1
}

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  fail "Python is not available. Install Python 3 before bootstrapping TaskDock."
fi

info "Python: $("$PYTHON_BIN" --version)"

if ! command -v docker >/dev/null 2>&1; then
  fail "Docker is not available. Install Docker before bootstrapping TaskDock."
fi
info "Docker: $(docker --version)"

if ! docker compose version >/dev/null 2>&1; then
  fail "docker compose is not available. Install Docker Compose before bootstrapping TaskDock."
fi
info "Docker Compose: $(docker compose version)"

if [ ! -d ".venv" ]; then
  info "Creating .venv"
  "$PYTHON_BIN" -m venv .venv
else
  info ".venv already exists"
fi

VENV_PYTHON=".venv/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
  fail ".venv Python is missing or not executable."
fi

info "Installing brain requirements"
"$VENV_PYTHON" -m pip install -r brain/requirements.txt

info "Installing Control Panel requirements"
"$VENV_PYTHON" -m pip install -r control_panel/requirements.txt

for required_file in \
  "config/brain.json" \
  "config/permissions.json" \
  "registry/workers.json" \
  "docker-compose.yml"
do
  if [ ! -f "$required_file" ]; then
    fail "Required file is missing: $required_file"
  fi
  info "Found $required_file"
done

info "Bootstrap complete."
cat <<'NEXT_STEPS'

Next steps:
  Start Control Panel:
    .venv/bin/uvicorn control_panel.app:app --host 127.0.0.1 --port 8890 --reload

  Start Docker workers when ready:
    docker compose up --build -d

  Run validation:
    curl -X POST http://127.0.0.1:8818/run-task -H 'Content-Type: application/json' -d '{}'
NEXT_STEPS
