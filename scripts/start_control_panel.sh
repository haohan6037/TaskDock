#!/usr/bin/env bash
set -euo pipefail

cd /Users/happyfamily/OpenClawBrain

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

pip install -r control_panel/requirements.txt

uvicorn control_panel.app:app --host 127.0.0.1 --port 8890
