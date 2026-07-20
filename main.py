"""
Zabacode — Python backend (Milestone 1, fixed for Android p4a webview bootstrap)
"""

import contextlib
import io
import json
import sys
import traceback
import urllib.request
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from waitress import serve

# PERBAIKAN ANDROID PATH: Gunakan direktori data aplikasi yang bisa ditulis (Writable),
# bukan APP_DIR yang sifatnya read-only di dalam APK.
try:
    from jnius import autoclass
    Context = autoclass('android.content.Context')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    APP_DIR = Path(activity.getFilesDir().getAbsolutePath())
except Exception:
    # Fallback kalau dites di komputer lokal/development
    APP_DIR = Path(__file__).parent

KEYS_FILE = APP_DIR / ".zabacode_keys.json"
USER_PACKAGES_DIR = APP_DIR / "user_packages"

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Milestone 1: eksekusi kode Python yang diketik user
# ---------------------------------------------------------------------------

@app.route("/api/run", methods=["POST"])
def run_code():
    payload = request.get_json(silent=True) or {}
    source = payload.get("code", "")

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    ok = True

    exec_globals = {"__name__": "__main__"}
    try:
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            exec(compile(source, "<zabacode>", "exec"), exec_globals)
    except Exception:
        ok = False
        stderr_buf.write(traceback.format_exc())

    return jsonify({"ok": ok, "stdout": stdout_buf.getvalue(), "stderr": stderr_buf.getvalue()})


# ---------------------------------------------------------------------------
# Milestone 2 (starter): Library Manager
# ---------------------------------------------------------------------------

KNOWN_LIBRARIES = {
    "requests": {"tier": "runtime", "reason": "Pure Python, aman di-install kapan aja."},
    "beautifulsoup4": {"tier": "runtime", "reason": "Pure Python."},
    "numpy": {"tier": "buildtime", "reason": "C-extension — tambahin ke buildozer.spec + rebuild CI."},
}


@app.route("/api/libraries", methods=["GET"])
def list_libraries():
    return jsonify(KNOWN_LIBRARIES)


@app.route("/api/libraries/install", methods=["POST"])
def install_library():
    name = (request.get_json(silent=True) or {}).get("name", "")
    info = KNOWN_LIBRARIES.get(name)

    if info is None:
        return jsonify({"ok": False, "message": f"'{name}' belum ada di manifest."}), 404

    if info["tier"] == "buildtime":
        return jsonify({
            "ok": False,
            "needs_rebuild": True,
            "message": f"'{name}' butuh compiled extension — tambahin ke requirements buildozer.spec.",
        })

    try:
        import subprocess
        USER_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--target", str(USER_PACKAGES_DIR), name],
            check=True, capture_output=True, text=True,
        )
        if str(USER_PACKAGES_DIR) not in sys.path:
            sys.path.insert(0, str(USER_PACKAGES_DIR))
        return jsonify({"ok": True, "message": f"'{name}' ke-install."})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Gagal install: {e}"}), 500


# ---------------------------------------------------------------------------
# Milestone 4 (starter): AI Assistant
# ---------------------------------------------------------------------------

def load_keys() -> dict:
    if KEYS_FILE.exists():
        try:
            return json.loads(KEYS_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_key(provider: str, api_key: str) -> None:
    keys = load_keys()
    keys[provider] = api_key
    try:
        KEYS_FILE.write_text(json.dumps(keys))
    except Exception as e:
        print(f"Gagal simpan key: {e}")


@app.route("/api/keys/status", methods=["GET"])
def keys_status():
    keys = load_keys()
    providers = ["openrouter", "gemini", "groq", "mistral"]
    return jsonify({p: bool(keys.get(p)) for p in providers})


@app.route("/api/keys", methods=["POST"])
def set_key():
    payload = request.get_json(silent=True) or {}
    provider, api_key = payload.get("provider"), payload.get("api_key", "")
    if not provider or not api_key:
        return jsonify({"ok": False, "message": "provider & api_key wajib diisi"}), 400
    save_key(provider, api_key)
    return jsonify({"ok": True})


@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    code_context = payload.get("code", "")
    provider = payload.get("provider", "openrouter")

    api_key = load_keys().get(provider)
    if not api_key:
        return jsonify({"ok": False, "needs_key": True, "provider": provider}), 401

    handler = PROVIDER_HANDLERS.get(provider)
    if handler is None:
        return jsonify({"ok": False, "message": f"Provider '{provider}' belum diimplementasi."}), 501
    return handler(api_key, message, code_context)


def _call_openrouter(api_key: str, message: str, code_context: str):
    system_prompt = (
        "Anda adalah Zabacode AI, asisten coding adaptif, bermulut tajam/tsundere, "
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android ARMv7."
    )
    user_content = f"Kode yang lagi dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}"
    body = json.dumps({
        "model": "qwen/qwen3-coder:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return jsonify({"ok": True, "reply": data["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"ok": False, "message": f"OpenRouter error: {e}"}), 502


PROVIDER_HANDLERS = {
    "openrouter": _call_openrouter,
}


if __name__ == "__main__":
    # Pake waitress server untuk WebView Android agar thread tidak freeze/force close
    serve(app, host="127.0.0.1", port=8080)
