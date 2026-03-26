import json
import subprocess
import sys
import time
from pathlib import Path
from urllib import request, error

BRIDGE_URL = "http://127.0.0.1:8766"
CHAT_URL = f"{BRIDGE_URL}/anna/chat"
HISTORY_URL = f"{BRIDGE_URL}/anna/history"
HEALTH_URL = f"{BRIDGE_URL}/health"


def _health_ok(timeout_sec: float = 1.5) -> bool:
    try:
        with request.urlopen(HEALTH_URL, timeout=timeout_sec) as resp:
            return resp.status == 200
    except Exception:
        return False


def _start_bridge_hidden():
    project_dir = Path(__file__).resolve().parents[1]  # D:\Fsales_PCCC
    py_exe = project_dir / ".venv" / "Scripts" / "python.exe"

    # Fallback to current Python if local venv is missing
    if not py_exe.exists():
        py_exe = Path(sys.executable)

    cmd = [
        str(py_exe),
        "-m",
        "uvicorn",
        "openclaw_bridge_server:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8766",
    ]

    kwargs = {
        "cwd": str(project_dir),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }

    # Chạy ẩn trên Windows (không hiện cửa sổ console)
    if sys.platform.startswith("win"):
        creationflags = 0
        creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
        kwargs["creationflags"] = creationflags

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs["startupinfo"] = si

    subprocess.Popen(cmd, **kwargs)


def _ensure_bridge_running():
    if _health_ok():
        return

    _start_bridge_hidden()

    # đợi bridge lên tối đa ~15 giây
    for _ in range(30):
        time.sleep(0.5)
        if _health_ok():
            return

    raise RuntimeError("Bridge chưa sẵn sàng sau khi tự khởi động")


def ask_openclaw_bridge(question: str, user_name: str = "") -> str:
    _ensure_bridge_running()

    payload = {
        "message": question,
        "user": user_name or "fsales-user",
    }

    req = request.Request(
        CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=180) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            return data.get("reply", "(Không có phản hồi từ OpenClaw)")
    except error.URLError as e:
        raise RuntimeError(f"Không kết nối được OpenClaw bridge ({e})")
    except Exception as e:
        raise RuntimeError(f"Lỗi bridge: {e}")


def fetch_openclaw_history(user_name: str = "", limit: int = 50):
    _ensure_bridge_running()

    payload = {
        "user": user_name or "fsales-user",
        "limit": int(limit),
    }

    req = request.Request(
        HISTORY_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            return data.get("history", [])
    except Exception:
        return []
