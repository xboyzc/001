import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "workflow_server_config.json"
HOST = "127.0.0.1"
PORT = int(os.environ.get("DOUYIN_AGENT_PORT", "8787"))


def python_executable():
    candidates = [
        ROOT / ".venv" / "bin" / "python",
        ROOT / ".venv" / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def port_open():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((HOST, PORT)) == 0


def access_key():
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if data.get("access_key"):
                return data["access_key"]
        except Exception:
            pass
    return ""


def main():
    py = python_executable()
    if not port_open():
        subprocess.Popen(
            [py, "scripts/serve_workflow_app.py"],
            cwd=str(ROOT),
        )
        for _ in range(30):
            if port_open():
                break
            time.sleep(0.5)

    key = access_key()
    url = f"http://{HOST}:{PORT}/" + (f"?key={key}" if key else "")
    print(f"抖音内容智能体已启动：{url}")
    webbrowser.open(url)


if __name__ == "__main__":
    main()
