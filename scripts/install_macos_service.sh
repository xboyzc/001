#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$HOME/Library/Application Support/DouyinWorkflow"
LABEL="com.a001.douyin.workflow"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PY="$ROOT/.venv/bin/python"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/data/logs"

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude ".git" \
    --exclude ".DS_Store" \
    --exclude "data/tmp_media" \
    --exclude "data/logs" \
    "$SOURCE_ROOT/" "$ROOT/"
else
  ditto "$SOURCE_ROOT" "$ROOT"
fi

if [ ! -x "$PY" ]; then
  python3 -m venv "$ROOT/.venv"
  PY="$ROOT/.venv/bin/python"
fi

"$PY" -m pip install -r "$ROOT/requirements.txt" >/dev/null
chmod +x "$ROOT/scripts/install_macos_service.sh" 2>/dev/null || true

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>$ROOT/scripts/serve_workflow_app.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$ROOT</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PYTHONUNBUFFERED</key>
    <string>1</string>
  </dict>
  <key>StandardOutPath</key>
  <string>$ROOT/data/logs/workflow_service.out.log</string>
  <key>StandardErrorPath</key>
  <string>$ROOT/data/logs/workflow_service.err.log</string>
</dict>
</plist>
EOF

UID_VALUE="$(id -u)"
launchctl bootout "gui/$UID_VALUE" "$PLIST" >/dev/null 2>&1 || true

if command -v lsof >/dev/null 2>&1; then
  EXISTING_PIDS="$(lsof -nP -iTCP:8787 -sTCP:LISTEN -t 2>/dev/null || true)"
  if [ -n "$EXISTING_PIDS" ]; then
    echo "$EXISTING_PIDS" | xargs kill >/dev/null 2>&1 || true
    sleep 1
  fi
fi

launchctl bootstrap "gui/$UID_VALUE" "$PLIST"
launchctl enable "gui/$UID_VALUE/$LABEL" >/dev/null 2>&1 || true
launchctl kickstart -k "gui/$UID_VALUE/$LABEL"

echo "已安装并启动系统后台服务：$LABEL"
echo "后台运行目录：$ROOT"
ACCESS_KEY="$("$PY" - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1]) / "data" / "workflow_server_config.json"
try:
    print(json.loads(config_path.read_text(encoding="utf-8")).get("access_key", ""))
except Exception:
    print("")
PY
)"
if [ -n "$ACCESS_KEY" ]; then
  echo "管理地址：http://127.0.0.1:8787/?key=$ACCESS_KEY"
else
  echo "管理地址：http://127.0.0.1:8787/"
fi
echo "日志：$ROOT/data/logs/workflow_service.out.log"
