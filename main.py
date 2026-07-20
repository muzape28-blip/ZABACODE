"""
ZABACODE — Standalone Anti-Capitalist Mobile Python IDE
Copyright (C) 2026 Zaqi (muzape28-blip) and ZABACODE Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See LICENSE file for full legal terms and Indonesian summary guide.
"""

import base64
import contextlib
import glob
import io
import json
import os
import re
import signal
import sys
import traceback
import urllib.request
import urllib.error
import zipfile
import subprocess
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from waitress import serve

# ---------------------------------------------------------------------------
# Path Initialization
# ANDROID_PRIVATE diatur oleh python-for-android secara otomatis.
# ---------------------------------------------------------------------------
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
        APP_DIR = Path(__file__).parent.resolve()

KEYS_FILE = APP_DIR / ".zabacode_keys.json"
USER_PACKAGES_DIR = APP_DIR / "user_packages"
FILES_DIR = APP_DIR / "files"
CACHE_DIR = APP_DIR / "cache"

# Dipastikan seluruh direktori krusial dibuat sejak awal server aktif
for directory in [USER_PACKAGES_DIR, FILES_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Tambahkan user_packages ke sys.path agar paket terinstal langsung bisa di-import
if str(USER_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(USER_PACKAGES_DIR))

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Isolation Engine: Exec via File untuk __file__ Definition & Line Tracking
# ---------------------------------------------------------------------------

def execute_code_isolated(code, timeout=30):
    """
    Eksekusi kode Python secara terisolasi menggunakan file temporary '_active_run.py'.
    Menjamin __file__ terdefinisi sempurna sehingga script yang mengakses Path(__file__)
    tidak akan pernah mengalami NameError!
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temp_script = FILES_DIR / "_active_run.py"
    
    try:
        # Tulis kode aktif ke file script fisik agar __file__ otomatis terdefinisi oleh Python interpreter
        temp_script.write_text(code, encoding="utf-8")
        
        env = os.environ.copy()
        python_path = f"{USER_PACKAGES_DIR}:{FILES_DIR}:{env.get('PYTHONPATH', '')}".strip(":")
        env["PYTHONPATH"] = python_path
        env["PYTHONNOUSERSITE"] = "1"
        env["TMPDIR"] = str(CACHE_DIR)
        env["TEMP"] = str(CACHE_DIR)
        env["TMP"] = str(CACHE_DIR)
        
        existing_images = set(FILES_DIR.glob("*.png")) | set(FILES_DIR.glob("*.jpg"))
        
        res = subprocess.run(
            [sys.executable, "_active_run.py"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            cwd=str(FILES_DIR),
            env=env,
            start_new_session=True if os.name != 'nt' else False
        )
        
        # Deteksi otomatis output file gambar baru hasil eksekusi (seperti Matplotlib/PIL)
        new_images = (set(FILES_DIR.glob("*.png")) | set(FILES_DIR.glob("*.jpg"))) - existing_images
        image_data = []
        for img_path in sorted(new_images):
            try:
                b64 = base64.b64encode(img_path.read_bytes()).decode("utf-8")
                mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
                image_data.append({"name": img_path.name, "data_uri": f"data:{mime};base64,{b64}"})
            except Exception:
                pass

        # Bersihkan pesan traceback agar tidak menampilkan nama file temporary '_active_run.py'
        stderr_cleaned = res.stderr.replace('_active_run.py', 'main.py') if res.stderr else ""

        return {
            "ok": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": stderr_cleaned,
            "timeout": False,
            "images": image_data
        }
    except subprocess.TimeoutExpired as e:
        stdout_text = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr_text = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        stderr_cleaned = stderr_text.replace('_active_run.py', 'main.py')
        return {
            "ok": False,
            "stdout": stdout_text,
            "stderr": stderr_cleaned + f"\n[Process timed out after {timeout}s]",
            "timeout": True,
            "images": []
        }
    except Exception as e:
        return {
            "ok": False,
            "stdout": "",
            "stderr": str(e),
            "timeout": False,
            "images": []
        }


@app.route("/api/run", methods=["POST"])
def run_code():
    payload = request.get_json(silent=True) or {}
    source = payload.get("code", "")
    result = execute_code_isolated(source, timeout=30)
    return jsonify(result)


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "ok": True,
        "version": "0.3.3",
        "providers": ["openrouter", "gemini", "groq", "mistral"]
    })


# ---------------------------------------------------------------------------
# Library Manager (`zabapip`) + PyPI Direct Extractor (Bypass SIGSEGV -11)
# ---------------------------------------------------------------------------

KNOWN_LIBRARIES = {
    # --- Web & Networking ---
    "requests": {"tier": "runtime", "category": "Web & API", "reason": "HTTP client paling populer untuk Python."},
    "beautifulsoup4": {"tier": "runtime", "category": "Web & Scraping", "reason": "Pustaka HTML/XML parsing untuk web scraping."},
    "httpx": {"tier": "runtime", "category": "Web & API", "reason": "Async & sync HTTP client modern dengan HTTP/2."},
    "urllib3": {"tier": "runtime", "category": "Web & API", "reason": "HTTP client tangguh penyokong requests."},
    "flask": {"tier": "runtime", "category": "Web & API", "reason": "Micro web framework yang ringan."},
    "fastapi": {"tier": "runtime", "category": "Web & API", "reason": "Web framework berperforma tinggi berbasis ASGI."},
    "aiohttp": {"tier": "runtime", "category": "Web & API", "reason": "HTTP client/server asinkronus."},
    "mechanize": {"tier": "runtime", "category": "Web & Scraping", "reason": "Stateful programmatic web browsing."},

    # --- Data, Math & Science ---
    "numpy": {"tier": "buildtime", "category": "Data & Math", "reason": "Komputasi matriks C-extension — tambahkan ke buildozer.spec."},
    "pandas": {"tier": "buildtime", "category": "Data & Math", "reason": "Pustaka analisis & manipulasi data spreadsheet."},
    "scipy": {"tier": "buildtime", "category": "Data & Math", "reason": "Modul ilmiah & sains C-extension."},
    "matplotlib": {"tier": "buildtime", "category": "Data & Math", "reason": "Visualisasi grafik & diagram 2D."},
    "sympy": {"tier": "runtime", "category": "Data & Math", "reason": "Matematika simbolik & aljabar murni dalam Python."},

    # --- Database & Storage ---
    "tinydb": {"tier": "runtime", "category": "Database", "reason": "Dokumen NoSQL JSON ringan murni Python."},
    "peewee": {"tier": "runtime", "category": "Database", "reason": "ORM ORM sederhana & ekspresif."},
    "sqlalchemy": {"tier": "runtime", "category": "Database", "reason": "Toolkit SQL & ORM standar industri."},
    "redis": {"tier": "runtime", "category": "Database", "reason": "Client untuk in-memory data store Redis."},

    # --- AI & Automation ---
    "openai": {"tier": "runtime", "category": "AI & Automation", "reason": "Pustaka API resmi OpenAI ChatGPT & Embeddings."},
    "google-generativeai": {"tier": "runtime", "category": "AI & Automation", "reason": "SDK resmi Google Gemini AI."},
    "schedule": {"tier": "runtime", "category": "AI & Automation", "reason": "Penjadwalan job/task berkala yang fleksibel."},

    # --- Formatting & Utilities ---
    "rich": {"tier": "runtime", "category": "Utilities", "reason": "Teks berformat, warna terminal, dan tabel kaya."},
    "colorama": {"tier": "runtime", "category": "Utilities", "reason": "Format warna ANSI terminal silang platform."},
    "tabulate": {"tier": "runtime", "category": "Utilities", "reason": "Format cetak tabel dari array/dict."},
    "pydantic": {"tier": "runtime", "category": "Utilities", "reason": "Validasi data & pengaturan bertipe."},
    "pytz": {"tier": "runtime", "category": "Utilities", "reason": "Pengelolaan zona waktu dunia."},
    "pyjwt": {"tier": "runtime", "category": "Utilities", "reason": "Enkodasi dan dekodasi JSON Web Tokens."},

    # --- Media, Image & GUI ---
    "pillow": {"tier": "buildtime", "category": "Media & Images", "reason": "Pustaka pemrosesan gambar PIL C-extension."},
    "pygame": {"tier": "buildtime", "category": "Games & Media", "reason": "Engine pembuatan game 2D & grafik."},
    "pydub": {"tier": "runtime", "category": "Games & Media", "reason": "Manipulasi audio sederhana dengan antarmuka bersih."},
}


def _is_package_installed(package_name):
    """Cek apakah package sudah terinstall dan bisa diimport secara aman."""
    import_map = {
        "beautifulsoup4": "bs4",
        "google-generativeai": "google.generativeai",
        "python-dotenv": "dotenv",
        "pillow": "PIL",
        "pyjwt": "jwt",
    }
    module_to_check = import_map.get(package_name.lower(), package_name.lower().replace("-", "_"))
    try:
        __import__(module_to_check)
        return True
    except ImportError:
        return False


def _fallback_pypi_download(name: str) -> tuple[bool, str]:
    """
    Fallback penyelamat jika subprocess pip mengalami SIGSEGV (-11) di Android.
    Langsung mengunduh Pure Python Wheel (.whl) dari PyPI JSON API dan mengekstraknya via zipfile.
    """
    try:
        pypi_url = f"https://pypi.org/pypi/{name}/json"
        req = urllib.request.Request(pypi_url, headers={"User-Agent": "Zabacode/0.3.3"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        
        urls = data.get("urls", [])
        target_wheel_url = None
        for item in urls:
            fn = item.get("filename", "").lower()
            if fn.endswith("none-any.whl"):
                target_wheel_url = item.get("url")
                break
        
        if not target_wheel_url:
            return False, f"'{name}' tidak memiliki pure-python wheel (.whl) di PyPI (memerlukan C-compiler)."

        wheel_req = urllib.request.Request(target_wheel_url, headers={"User-Agent": "Zabacode/0.3.3"})
        with urllib.request.urlopen(wheel_req, timeout=45) as resp:
            wheel_bytes = resp.read()

        with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as z:
            z.extractall(USER_PACKAGES_DIR)

        return True, f"'{name}' berhasil diinstall via Direct PyPI Extractor!"
    except Exception as e:
        return False, f"Direct PyPI Extractor error: {e}"


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
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "").strip()

    if not name:
        return jsonify({"ok": False, "message": "Nama package tidak boleh kosong."}), 400

    info = KNOWN_LIBRARIES.get(name)

    if info and info.get("tier") == "buildtime":
        return jsonify({
            "ok": False,
            "needs_rebuild": True,
            "message": f"'{name}' memerlukan compiled C-extension. Tambahkan ke requirements di buildozer.spec lalu rebuild APK.",
        })

    if _is_package_installed(name):
        return jsonify({"ok": True, "message": f"'{name}' sudah terinstall & siap digunakan di ZABACODE!"})

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        env = os.environ.copy()
        env["TMPDIR"] = str(CACHE_DIR)
        env["TEMP"] = str(CACHE_DIR)
        env["TMP"] = str(CACHE_DIR)
        env["PIP_NO_CACHE_DIR"] = "1"
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONKEYRINGBACKEND"] = "keyring.backends.null.Keyring"
        
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--prefer-binary",
            "--only-binary=:all:",
            "--target", str(USER_PACKAGES_DIR),
            name
        ]
        
        res = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=180
        )
        
        if res.returncode == 0:
            return jsonify({"ok": True, "message": f"'{name}' berhasil diinstall!"})
        else:
            # Jika subprocess pip crash (misal exit code -11 SIGSEGV), gunakan Direct PyPI Extractor
            ok, msg = _fallback_pypi_download(name)
            if ok:
                return jsonify({"ok": True, "message": msg})
            return jsonify({"ok": False, "message": f"Gagal install: {msg} (Pip exit: {res.returncode})"}), 500
    except subprocess.TimeoutExpired:
        ok, msg = _fallback_pypi_download(name)
        if ok:
            return jsonify({"ok": True, "message": msg})
        return jsonify({"ok": False, "message": "Proses instalasi pip timeout (>180s)."}), 500
    except Exception as e:
        ok, msg = _fallback_pypi_download(name)
        if ok:
            return jsonify({"ok": True, "message": msg})
        return jsonify({"ok": False, "message": f"Gagal menginstall package: {e}"}), 500


# ---------------------------------------------------------------------------
# Safe File System & Path Traversal Security Protection
# ---------------------------------------------------------------------------

def secure_filename_py(filename):
    """Validasi dan amankan nama file untuk mencegah directory traversal, null bytes, dan pengaksesan file tersembunyi/sistem."""
    if not filename or ".." in filename or "/" in filename or "\\" in filename or "\x00" in filename:
        return None
    filename = filename.strip()
    if filename.startswith(".") or filename.startswith("_"):
        return None
    if not filename or filename == ".py":
        return None
    if not filename.endswith(".py"):
        filename += ".py"
    return filename


@app.route("/api/files", methods=["GET"])
def list_files():
    files = []
    for p in FILES_DIR.glob("*.py"):
        if not p.name.startswith(".") and not p.name.startswith("_"):
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
        content = file_path.read_text(encoding="utf-8", errors="replace")
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
# Multi-Provider AI Engine
# ---------------------------------------------------------------------------

def load_keys() -> dict:
    if KEYS_FILE.exists():
        try:
            return json.loads(KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_key(provider: str, api_key: str) -> None:
    keys = load_keys()
    keys[provider] = api_key.strip()
    try:
        KEYS_FILE.write_text(json.dumps(keys), encoding="utf-8")
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
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android."
    )
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}"
    body = json.dumps({
        "model": "qwen/qwen-2.5-coder-32b-instruct:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/muzape28-blip/ZABACODE",
            "X-Title": "Zabacode Mobile IDE"
        },
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
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android."
    )
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}"
    body = json.dumps({
        "contents": [{
            "parts": [
                {"text": system_prompt + "\n\n" + user_content}
            ]
        }]
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
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
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android."
    )
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}"
    body = json.dumps({
        "model": "llama-3.1-8b-instant",
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
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android."
    )
    user_content = f"Kode yang sedang dibuka:\n```python\n{code_context}\n```\n\nPertanyaan: {message}"
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
    port = int(os.environ.get("PORT", 5000))
    print(f"[ZABACODE] Starting local server bound strictly to 127.0.0.1 on port {port}...")
    serve(app, host="127.0.0.1", port=port, threads=4)
