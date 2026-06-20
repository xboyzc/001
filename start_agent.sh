#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

$PY -m pip install -r requirements.txt
$PY -m playwright install chromium >/dev/null 2>&1 || true
$PY scripts/start_agent.py
