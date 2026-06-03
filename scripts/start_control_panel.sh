#!/usr/bin/env bash
set -euo pipefail

cd /Users/happyfamily/OpenClawBrain
exec .venv/bin/uvicorn control_panel.app:app --host 127.0.0.1 --port 8890
