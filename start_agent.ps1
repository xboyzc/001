$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (!(Test-Path ".venv")) {
  py -3 -m venv .venv
}

$py = ".venv\Scripts\python.exe"
if (!(Test-Path $py)) {
  $py = "python"
}

& $py -m pip install -r requirements.txt
& $py -m playwright install chromium | Out-Null
& $py scripts\start_agent.py
