"""
Zabacode — Python backend (Milestone 1-4, fixed for Android p4a webview bootstrap)
"""

import contextlib
import io
import json
import os
import sys
import traceback
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from waitress import serve

# PERBAIKAN ANDROID PATH: Gunakan direktori data aplikasi yang bisa ditulis (Writable),
# ANDROID_PRIVATE diatur oleh python-for-android secara otomatis.
if "ANDROID_PRIVATE" in os.environ:
    APP_DIR = Path(os.environ["ANDROID_PRIVATE"])
else:
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
FILES_DIR = APP_DIR / "files"

# Ensure directories exist
USER_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)

# Add user packages dir to sys.path so installed packages can be imported
if str(USER_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(USER_PACKAGES_DIR))

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Milestone 1 & 2: eksekusi kode Python terisolasi (Subprocess)
# ---------------------------------------------------------------------------

def execute_code_isolated(code, timeout=30):
    """
    Eksekusi kode Python secara terisolasi menggunakan subprocess
    untuk mencegah infinite loop menyandera server Flask utama.
    """
    try:
        env = os.environ.copy()
        python_path = f"{USER_PACKAGES_DIR}:{FILES_DIR}:{env.get('PYTHONPATH', '')}".strip(":")
        env["PYTHONPATH"] = python_path
        env["PYTHONNOUSERSITE"] = "1"
        env["TMPDIR"] = str(APP_DIR / "cache")
        
        # Kita melewatkan kode via -c dan menjalankan di dalam FILES_DIR
        # agar user bisa import / open file .py yang mereka simpan di File Manager!
        res = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(FILES_DIR),
            env=env
        )
        return {
            "ok": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "timeout": False
        }
    except subprocess.TimeoutExpired as e:
        # Kembalikan penanda timeout
        return {
            "ok": False,
            "stdout": e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
            "stderr": (e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")) + "\n[Process timed out after {}s]".format(timeout),
            "timeout": True
        }
    except Exception as e:
        return {
            "ok": False,
            "stdout": "",
            "stderr": str(e),
            "timeout": False
        }


@app.route("/api/run", methods=["POST"])
def run_code():
    payload = request.get_json(silent=True) or {}
    source = payload.get("code", "")

    # Gunakan eksekusi terisolasi demi stabilitas
    result = execute_code_isolated(source, timeout=30)
    return jsonify(result)


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "ok": True,
        "version": "0.2.0",
        "providers": ["openrouter", "gemini", "groq", "mistral"]
    })


# ---------------------------------------------------------------------------
# Milestone 2: Library Manager
# ---------------------------------------------------------------------------

KNOWN_LIBRARIES = {
    "requests": {"tier": "runtime", "reason": "Pure Python, aman di-install kapan aja."},
    "beautifulsoup4": {"tier": "runtime", "reason": "Pure Python."},
    "numpy": {"tier": "buildtime", "reason": "C-extension — tambahin ke buildozer.spec + rebuild CI."},
}


def _is_package_installed(package_name):
    """Cek apakah package sudah terinstall dan bisa diimport."""
    try:
        # Coba import package
        __import__(package_name)
        return True
    except ImportError:
        return False


@app.route("/api/libraries", methods=["GET"])
def list_libraries():
    result = {}
    for name, info in KNOWN_LIBRARIES.items():
        item = info.copy()
        item["installed"] = _is_package_installed(name)
        result[name] = item
    return jsonify(result)


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

    # CEK CEPAT: Jika package sudah terinstal bawaan p4a atau user_packages, langsung return sukses!
    if _is_package_installed(name):
        return jsonify({"ok": True, "message": f"'{name}' sudah terinstall & siap pakai di ZABACODE!"})

    try:
        cache_dir = APP_DIR / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        env = os.environ.copy()
        env["TMPDIR"] = str(cache_dir)
        env["TEMP"] = str(cache_dir)
        env["TMP"] = str(cache_dir)
        env["PIP_NO_CACHE_DIR"] = "1"
        env["PYTHONNOUSERSITE"] = "1"
        # Mencegah pip mengakses keyring/DBus yang menyebabkan SIGSEGV di ARMv7 Android
        env["PYTHONKEYRINGBACKEND"] = "keyring.backends.null.Keyring"
        
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--target", str(USER_PACKAGES_DIR),
            name
        ]
        
        res = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        if res.returncode == 0:
            return jsonify({"ok": True, "message": f"'{name}' berhasil diinstall ke user_packages."})
        else:
            return jsonify({"ok": False, "message": f"Pip error ({res.returncode}): {res.stderr or res.stdout}"}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "message": "Proses instalasi timeout (>120s)."}), 500
    except Exception as e:
        return jsonify({"ok": False, "message": f"Gagal install: {e}"}), 500


# ---------------------------------------------------------------------------
# Milestone 3: File Manager & Themes
# ---------------------------------------------------------------------------

def secure_filename_py(filename):
    """Validasi dan amankan nama file untuk mencegah directory traversal, null bytes, dan ekstensi non-.py."""
    if not filename or ".." in filename or "/" in filename or "\\" in filename or "\x00" in filename:
        return None
    filename = filename.strip()
    if not filename or filename == ".py":
        return None
    if not filename.endswith(".py"):
        filename += ".py"
    return filename


@app.route("/api/files", methods=["GET"])
def list_files():
    files = []
    for p in FILES_DIR.glob("*.py"):
        files.append({"name": p.name})
    return jsonify({"files": files})


@app.route("/api/files/<path:filename>", methods=["GET"])
def read_file_api(filename):
    secured = secure_filename_py(filename)
    if not secured:
        return jsonify({"ok": False, "message": "Nama file tidak valid"}), 400

    file_path = FILES_DIR / secured
    if not file_path.exists():
        return jsonify({"ok": False, "message": f"File '{filename}' tidak ditemukan"}), 404

    try:
        content = file_path.read_text(encoding="utf-8")
        return jsonify({"ok": True, "content": content})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Gagal membaca file: {e}"}), 500


@app.route("/api/files/<path:filename>", methods=["POST"])
def save_file_api(filename):
    secured = secure_filename_py(filename)
    if not secured:
        return jsonify({"ok": False, "message": "Nama file tidak valid"}), 400

    payload = request.get_json(silent=True) or {}
    content = payload.get("content", "")

    file_path = FILES_DIR / secured
    try:
        file_path.write_text(content, encoding="utf-8")
        return jsonify({"ok": True, "filename": secured, "message": f"File '{secured}' berhasil disimpan."})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Gagal menyimpan file: {e}"}), 500


@app.route("/api/files/<path:filename>", methods=["DELETE"])
def delete_file_api(filename):
    secured = secure_filename_py(filename)
    if not secured:
        return jsonify({"ok": False, "message": "Nama file tidak valid"}), 400

    file_path = FILES_DIR / secured
    if not file_path.exists():
        return jsonify({"ok": False, "message": f"File '{filename}' tidak ditemukan"}), 404

    try:
        file_path.unlink()
        return jsonify({"ok": True, "message": f"File '{secured}' berhasil dihapus."})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Gagal menghapus file: {e}"}), 500


THEMES = {
    "retro": {
        "bg": "#050806",
        "bg_panel": "#0A100D",
        "border": "#1B4D2E",
        "border_bright": "#2E8B4F",
        "text": "#B9F5C4",
        "text_bright": "#39FF14",
        "text_dim": "#4D7A5A",
        "err": "#FF4B4B",
        "ai": "#FFB000",
    },
    "solarized": {
        "bg": "#002b36",
        "bg_panel": "#073642",
        "border": "#586e75",
        "border_bright": "#93a1a1",
        "text": "#839496",
        "text_bright": "#2aa198",
        "text_dim": "#586e75",
        "err": "#dc322f",
        "ai": "#b58900",
    },
    "dracula": {
        "bg": "#282a36",
        "bg_panel": "#21222c",
        "border": "#44475a",
        "border_bright": "#6272a4",
        "text": "#f8f8f2",
        "text_bright": "#50fa7b",
        "text_dim": "#6272a4",
        "err": "#ff5555",
        "ai": "#ffb86c",
    }
}


@app.route("/api/themes", methods=["GET"])
def list_themes():
    return jsonify({
        "themes": {
            "retro": "Retro Green",
            "solarized": "Solarized Dark",
            "dracula": "Dracula"
        }
    })


@app.route("/api/themes/<name>", methods=["GET"])
def get_theme(name):
    theme = THEMES.get(name)
    if not theme:
        return jsonify({"ok": False, "message": "Theme tidak ditemukan"}), 404
    return jsonify({"ok": True, "theme": theme})


# ---------------------------------------------------------------------------
# Milestone 4: AI Assistant
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


def _handle_url_error(e, provider_name):
    if isinstance(e, urllib.error.HTTPError):
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
            err_json = json.loads(err_body)
            if isinstance(err_json.get("error"), dict):
                msg = err_json["error"].get("message", str(e))
            else:
                msg = err_json.get("error") or str(e)
            return jsonify({"ok": False, "message": f"{provider_name} error ({e.code}): {msg}"}), 502
        except Exception:
            return jsonify({"ok": False, "message": f"{provider_name} error ({e.code})"}), 502
    return jsonify({"ok": False, "message": f"{provider_name} error: {e}"}), 502


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
        return _handle_url_error(e, "OpenRouter")


def _call_gemini(api_key: str, message: str, code_context: str):
    system_prompt = (
        "Anda adalah Zabacode AI, asisten coding adaptif, bermulut tajam/tsundere, "
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android ARMv7."
    )
    user_content = f"Kode yang lagi dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}"
    body = json.dumps({
        "contents": [{
            "parts": [
                {"text": system_prompt + "\n\n" + user_content}
            ]
        }]
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"ok": True, "reply": reply})
    except Exception as e:
        return _handle_url_error(e, "Gemini")


def _call_groq(api_key: str, message: str, code_context: str):
    system_prompt = (
        "Anda adalah Zabacode AI, asisten coding adaptif, bermulut tajam/tsundere, "
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android ARMv7."
    )
    user_content = f"Kode yang lagi dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}"
    body = json.dumps({
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return jsonify({"ok": True, "reply": data["choices"][0]["message"]["content"]})
    except Exception as e:
        return _handle_url_error(e, "Groq")


def _call_mistral(api_key: str, message: str, code_context: str):
    system_prompt = (
        "Anda adalah Zabacode AI, asisten coding adaptif, bermulut tajam/tsundere, "
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android ARMv7."
    )
    user_content = f"Kode yang lagi dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}"
    body = json.dumps({
        "model": "codestral-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return jsonify({"ok": True, "reply": data["choices"][0]["message"]["content"]})
    except Exception as e:
        return _handle_url_error(e, "Mistral")


PROVIDER_HANDLERS = {
    "openrouter": _call_openrouter,
    "gemini": _call_gemini,
    "groq": _call_groq,
    "mistral": _call_mistral,
}


if __name__ == "__main__":
    # Pake waitress server untuk WebView Android agar thread tidak freeze/force close
    # Unifikasi port ke 5000 agar sinkron dengan p4a.port bawaan/custom
    port = int(os.environ.get("PORT", 5000))
    print(f"[ZABACODE] Starting local server on port {port}...")
    serve(app, host="0.0.0.0", port=port, threads=4)
