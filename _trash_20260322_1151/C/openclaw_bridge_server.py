"""
OpenClaw Bridge Server for FSales Chat
Run:
    uvicorn openclaw_bridge_server:app --host 127.0.0.1 --port 8765
"""

import json
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="FSales OpenClaw Bridge")

HISTORY_FILE = Path(__file__).resolve().parent / "fsales_chat_history.json"
MAX_HISTORY_PER_USER = 200

# Force bridge to run against Anna's main OpenClaw brain/runtime.
OPENCLAW_AGENT_ID = os.getenv("OPENCLAW_AGENT_ID", "main")
OPENCLAW_SESSION_ID = os.getenv("OPENCLAW_SESSION_ID", "agent:main:main")

# Prefix to keep FSales chat grounded to the real runtime capabilities.
FSALES_ROUTING_PREFIX = (
    "[FSALES BRIDGE POLICY]\n"
    "Bạn là Anna trên OpenClaw main brain (workspace C:\\Users\\Admin\\.openclaw\\workspace). "
    "Khi người dùng hỏi dữ liệu FSales, PHẢI ưu tiên truy vấn dữ liệu thật qua fsales_connector "
    "(dùng tool exec nếu cần), không tự suy đoán và không mặc định trả lời rằng thiếu connector khi chưa thử truy vấn. "
    "Nếu truy vấn lỗi, nêu lỗi kỹ thuật ngắn gọn + bước xử lý.\n\n"
)


class ChatReq(BaseModel):
    message: str
    user: str | None = None


class HistoryReq(BaseModel):
    user: str | None = None
    limit: int | None = 50


def _load_history_store() -> dict:
    if not HISTORY_FILE.exists():
        return {}
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_history_store(data: dict):
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_history(user: str, role: str, text: str):
    data = _load_history_store()
    bucket = data.get(user, [])
    bucket.append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "role": role,
        "text": text,
    })
    if len(bucket) > MAX_HISTORY_PER_USER:
        bucket = bucket[-MAX_HISTORY_PER_USER:]
    data[user] = bucket
    _save_history_store(data)


def _get_history(user: str, limit: int = 50):
    data = _load_history_store()
    rows = data.get(user, [])
    return rows[-max(1, min(limit, 200)):]


def _resolve_openclaw_exe() -> str:
    # 1) explicit env override
    env_path = os.getenv("OPENCLAW_EXE", "").strip()
    if env_path and Path(env_path).exists():
        return env_path

    # 2) PATH lookup
    in_path = shutil.which("openclaw") or shutil.which("openclaw.cmd")
    if in_path:
        return in_path

    # 3) common Windows npm global location
    common = Path(os.environ.get("APPDATA", "")) / "npm" / "openclaw.cmd"
    if common.exists():
        return str(common)

    raise RuntimeError(
        "Không tìm thấy lệnh openclaw. Hãy thêm openclaw vào PATH hoặc set OPENCLAW_EXE"
    )


def _safe_session_suffix(user: str) -> str:
    raw = (user or 'default').strip().lower()
    normalized = unicodedata.normalize('NFKD', raw)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    ascii_text = re.sub(r'[^a-z0-9]+', '-', ascii_text).strip('-')
    return ascii_text or 'default'


def _resolve_openclaw_runtime() -> tuple[str | None, str | None, str | None]:
    """Return (config_path, state_dir, gateway_token)."""
    # Ưu tiên config chuẩn của máy đang chạy OpenClaw.
    config_candidates = [
        Path(os.getenv("OPENCLAW_CONFIG_PATH", "")),
        Path.home() / ".openclaw" / "openclaw.json",
        Path("C:/Users/Admin/.openclaw/openclaw.json"),
    ]

    config_path: str | None = None
    for p in config_candidates:
        if str(p).strip() and p.exists() and p.is_file():
            config_path = str(p)
            break

    state_dir: str | None = None
    token: str | None = None

    if config_path:
        try:
            data = json.loads(Path(config_path).read_text(encoding="utf-8"))
            state_dir = str(Path(config_path).parent)
            token = (
                data.get("gateway", {}).get("auth", {}).get("token")
                or data.get("gateway", {}).get("token")
                or data.get("auth", {}).get("token")
            )
        except Exception:
            pass

    return config_path, state_dir, token


def _call_openclaw_agent(message: str, user: str) -> str:
    # Dùng session main để kế thừa đúng "brain" của Anna.
    session_id = OPENCLAW_SESSION_ID

    openclaw_exe = _resolve_openclaw_exe()
    bridged_message = f"{FSALES_ROUTING_PREFIX}{message}"

    cmd = [
        openclaw_exe,
        "agent",
        "--agent",
        OPENCLAW_AGENT_ID,
        "--session-id",
        session_id,
        "--message",
        bridged_message,
        "--json",
    ]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    config_path, state_dir, gateway_token = _resolve_openclaw_runtime()
    if config_path:
        env["OPENCLAW_CONFIG_PATH"] = config_path
    if state_dir:
        env["OPENCLAW_STATE_DIR"] = state_dir

    # Chốt đích gateway local để tránh trượt profile/runtime.
    env.setdefault("OPENCLAW_GATEWAY_URL", "ws://127.0.0.1:18789")
    if gateway_token:
        env.setdefault("OPENCLAW_GATEWAY_TOKEN", gateway_token)

    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return "Đợi em chút nhé, em đang xử lý."

    if p.returncode != 0:
        # Trả về message mềm để UI không văng lỗi 500
        err = (p.stderr or p.stdout or "openclaw agent failed").strip()
        return f"Anna tạm thời lỗi khi xử lý yêu cầu: {err[:300]}"

    raw = (p.stdout or "").strip()
    # openclaw có thể in banner trước JSON; nếu không parse được thì fallback text thô
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return raw or "(Anna chưa có phản hồi)"

    try:
        data = json.loads(raw[start:end+1])
        payloads = data.get("result", {}).get("payloads", [])
        if not payloads:
            return "(Anna chưa có phản hồi)"

        # Ghép các payload text
        texts = [x.get("text", "") for x in payloads if x.get("text")]
        return "\n".join(texts).strip() or "(Anna chưa có phản hồi)"
    except Exception:
        return raw or "(Anna chưa có phản hồi)"


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/anna/history")
def anna_history(req: HistoryReq):
    user = req.user or "default"
    rows = _get_history(user, req.limit or 50)
    return {"ok": True, "history": rows}


@app.post("/anna/chat")
def anna_chat(req: ChatReq):
    user = req.user or "default"
    _append_history(user, "user", req.message)
    try:
        reply = _call_openclaw_agent(req.message, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    _append_history(user, "assistant", reply)
    return {"ok": True, "reply": reply}
