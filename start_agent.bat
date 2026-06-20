@echo off
cd /d "%~dp0"

if not exist ".venv" (
  py -3 -m venv .venv
)

set PY=.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

"%PY%" -m pip install -r requirements.txt
"%PY%" -m playwright install chromium >nul 2>nul
"%PY%" scripts\start_agent.py
