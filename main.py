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
import functools
import glob
import hmac
import io
import json
import os
import re
import secrets
import signal
import ssl
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
# Path & Auth Token Initialization
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

KEYS_FILE = APP_DIR / ".zabacode_keys_encrypted.json"
USER_PACKAGES_DIR = APP_DIR / "user_packages"
FILES_DIR = APP_DIR / "files"
CACHE_DIR = APP_DIR / "cache"
TOKEN_FILE = APP_DIR / ".zabacode_auth_token"

# Pastikan direktori krusial tersedia
for directory in [USER_PACKAGES_DIR, FILES_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Generate / Load Local Session Authentication Token
if TOKEN_FILE.exists():
    try:
        AUTH_TOKEN = TOKEN_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        AUTH_TOKEN = secrets.token_hex(16)
        TOKEN_FILE.write_text(AUTH_TOKEN, encoding="utf-8")
else:
    AUTH_TOKEN = secrets.token_hex(16)
    try:
        TOKEN_FILE.write_text(AUTH_TOKEN, encoding="utf-8")
    except Exception:
        pass

if str(USER_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(USER_PACKAGES_DIR))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

MAX_CODE_BYTES = 512 * 1024
MAX_FILE_BYTES = 512 * 1024
MAX_OUTPUT_CHARS = 256 * 1024
MAX_AI_FIELD_CHARS = 100_000
ALLOWED_PROVIDERS = {"openrouter", "gemini", "groq", "mistral"}
_PACKAGE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + "\n[Output truncated]"


def require_auth(f):
    """Decorator untuk memverifikasi header X-Zabacode-Token pada endpoint sensitif."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Zabacode-Token")
        if not token or not hmac.compare_digest(token, AUTH_TOKEN):
            return jsonify({"ok": False, "message": "Akses ditolak: token autentikasi tidak valid."}), 401
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    return render_template("index.html", auth_token=AUTH_TOKEN)


# ---------------------------------------------------------------------------
# Isolation Subprocess Code Execution Engine
# ---------------------------------------------------------------------------

def execute_code_isolated(code, timeout=30):
    """Run user code in a separate process; this is not a security sandbox."""
    if not isinstance(code, str) or len(code.encode("utf-8")) > MAX_CODE_BYTES:
        return {"ok": False, "stdout": "", "stderr": "Source code terlalu besar.", "timeout": False, "images": []}

    # This isolates process lifetime, not filesystem/network privileges.
    # Treat code as trusted unless a platform-level sandbox is added.
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temp_script = FILES_DIR / "_active_run.py"
    
    try:
        temp_script.write_text(code, encoding="utf-8")
        
        env = os.environ.copy()
        python_path = f"{USER_PACKAGES_DIR}:{FILES_DIR}:{env.get('PYTHONPATH', '')}".strip(":")
        env["PYTHONPATH"] = python_path
        env["PYTHONNOUSERSITE"] = "1"
        env["TMPDIR"] = str(CACHE_DIR)
        env["TEMP"] = str(CACHE_DIR)
        env["TMP"] = str(CACHE_DIR)
        
        existing_images = set(FILES_DIR.glob("*.png")) | set(FILES_DIR.glob("*.jpg"))
        
        proc = subprocess.Popen(
            [sys.executable, "_active_run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            cwd=str(FILES_DIR),
            env=env,
            start_new_session=os.name != "nt",
        )
        try:
            stdout_text, stderr_text = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
            stdout_text, stderr_text = proc.communicate()
            return {
                "ok": False,
                "stdout": _truncate(stdout_text or ""),
                "stderr": _truncate((stderr_text or "").replace("_active_run.py", "main.py") + f"\n[Process timed out after {timeout}s]"),
                "timeout": True,
                "images": [],
            }

        new_images = (set(FILES_DIR.glob("*.png")) | set(FILES_DIR.glob("*.jpg"))) - existing_images
        image_data = []
        for img_path in sorted(new_images):
            try:
                b64 = base64.b64encode(img_path.read_bytes()).decode("utf-8")
                mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
                image_data.append({"name": img_path.name, "data_uri": f"data:{mime};base64,{b64}"})
            except Exception:
                pass

        stderr_cleaned = stderr_text.replace('_active_run.py', 'main.py') if stderr_text else ""

        return {
            "ok": proc.returncode == 0,
            "stdout": _truncate(stdout_text or ""),
            "stderr": _truncate(stderr_cleaned),
            "timeout": False,
            "images": image_data
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
@require_auth
def run_code():
    payload = request.get_json(silent=True) or {}
    source = payload.get("code", "")
    if not isinstance(source, str):
        return jsonify({"ok": False, "message": "Field code harus berupa string."}), 400
    result = execute_code_isolated(source, timeout=30)
    return jsonify(result)


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "ok": True,
        "version": "0.3.5",
        "providers": ["openrouter", "gemini", "groq", "mistral"]
    })


# ---------------------------------------------------------------------------
# Library Manager (`zabapip`) + PyPI Direct Extractor (Bypass SSL & SIGSEGV)
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
    """Install only a pure-Python wheel after TLS and archive-path validation."""
    try:
        pypi_url = f"https://pypi.org/pypi/{name}/json"
        req = urllib.request.Request(pypi_url, headers={"User-Agent": "Zabacode/0.3.5"})
        
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        
        urls = data.get("urls", [])
        target_wheel_url = None
        for item in urls:
            fn = item.get("filename", "").lower()
            if fn.endswith("none-any.whl"):
                target_wheel_url = item.get("url")
                break
        
        if not target_wheel_url:
            return False, f"'{name}' memerlukan ekstensi compiled C. Tambahkan ke buildozer.spec."

        wheel_req = urllib.request.Request(target_wheel_url, headers={"User-Agent": "Zabacode/0.3.5"})
        with urllib.request.urlopen(wheel_req, timeout=60) as resp:
            wheel_bytes = resp.read()

        with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as z:
            base = USER_PACKAGES_DIR.resolve()
            for member in z.infolist():
                target = (base / member.filename).resolve()
                if target != base and base not in target.parents:
                    raise ValueError("Wheel berisi path tidak aman.")
            z.extractall(base)

        return True, f"'{name}' berhasil terinstall via Direct PyPI Extractor!"
    except Exception as e:
        return False, f"Direct Extractor Error: {e}"


@app.route("/api/libraries", methods=["GET"])
def list_libraries():
    result = {}
    for name, info in KNOWN_LIBRARIES.items():
        item = info.copy()
        item["installed"] = _is_package_installed(name)
        result[name] = item
    return jsonify(result)


@app.route("/api/libraries/install", methods=["POST"])
@require_auth
def install_library():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "").strip().lower()

    if not name or not _PACKAGE_NAME_RE.fullmatch(name):
        return jsonify({"ok": False, "message": "Nama package tidak valid."}), 400

    info = KNOWN_LIBRARIES.get(name)

    if info and info.get("tier") == "buildtime":
        return jsonify({
            "ok": False,
            "needs_rebuild": True,
            "message": f"'{name}' memerlukan compiled C-extension. Tambahkan ke buildozer.spec lalu rebuild APK.",
        })

    if _is_package_installed(name):
        return jsonify({"ok": True, "message": f"'{name}' sudah terinstall & siap digunakan di ZABACODE!"})

    # Jalankan Direct PyPI Extractor terlebih dahulu untuk bypass SIGSEGV (-11)
    ok, msg = _fallback_pypi_download(name)
    if ok:
        return jsonify({"ok": True, "message": msg})

    # Jika wheel pure python tidak ditemukan di PyPI, coba pip subprocess sebagai cadangan
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["TMPDIR"] = str(CACHE_DIR)
        env["PIP_NO_CACHE_DIR"] = "1"
        env["PYTHONKEYRINGBACKEND"] = "keyring.backends.null.Keyring"
        
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--prefer-binary",
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
            return jsonify({"ok": True, "message": f"'{name}' berhasil diinstall via Pip!"})
        else:
            return jsonify({"ok": False, "message": f"Instalasi gagal: {msg}"}), 500
    except Exception as e:
        return jsonify({"ok": False, "message": f"Gagal menginstall package: {e}"}), 500


# ---------------------------------------------------------------------------
# Safe File System & Path Traversal Security Protection
# ---------------------------------------------------------------------------

def secure_filename_py(filename):
    """Validasi dan amankan nama file untuk mencegah directory traversal, null bytes, dan dotfiles."""
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
@require_auth
def list_files():
    files = []
    for p in FILES_DIR.glob("*.py"):
        if not p.name.startswith(".") and not p.name.startswith("_"):
            files.append({"name": p.name})
    return jsonify({"files": files})


@app.route("/api/files/<path:filename>", methods=["GET"])
@require_auth
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
@require_auth
def save_file_api(filename):
    secured = secure_filename_py(filename)
    if not secured:
        return jsonify({"ok": False, "message": "Nama file tidak valid"}), 400

    payload = request.get_json(silent=True) or {}
    content = payload.get("content", "")
    if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_FILE_BYTES:
        return jsonify({"ok": False, "message": "Isi file terlalu besar."}), 413

    file_path = FILES_DIR / secured
    try:
        file_path.write_text(content, encoding="utf-8")
        return jsonify({"ok": True, "filename": secured, "message": f"File '{secured}' berhasil disimpan."})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Gagal menyimpan file: {e}"}), 500


@app.route("/api/files/<path:filename>", methods=["DELETE"])
@require_auth
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


# ---------------------------------------------------------------------------
# Marketplace Plugins & Themes Engine
# ---------------------------------------------------------------------------

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
    },
    "cyberpunk": {
        "bg": "#0d0221",
        "bg_panel": "#190535",
        "border": "#ff007f",
        "border_bright": "#00f0ff",
        "text": "#00f0ff",
        "text_bright": "#ff007f",
        "text_dim": "#7000ff",
        "err": "#ff003c",
        "ai": "#ffe600",
    },
    "nord": {
        "bg": "#2e3440",
        "bg_panel": "#3b4252",
        "border": "#4c566a",
        "border_bright": "#88c0d0",
        "text": "#d8dee9",
        "text_bright": "#8fbcbb",
        "text_dim": "#4c566a",
        "err": "#bf616a",
        "ai": "#ebcb8b",
    },
    "monokai": {
        "bg": "#272822",
        "bg_panel": "#1e1f1c",
        "border": "#3e3d32",
        "border_bright": "#a6e22e",
        "text": "#f8f8f2",
        "text_bright": "#a6e22e",
        "text_dim": "#75715e",
        "err": "#f92672",
        "ai": "#e6db74",
    }
}

MARKETPLACE_PLUGINS = {
    "auto_formatter": {
        "id": "auto_formatter",
        "name": "⚡ Auto-Code Formatter (Pure PEP-8)",
        "author": "Zaba Core",
        "version": "1.2.0",
        "description": "Secara otomatis merapikan indentasi spasi dan struktur kode Python sesuai standar PEP-8.",
        "type": "plugin"
    },
    "snippet_pack": {
        "id": "snippet_pack",
        "name": "📜 Pro Python Snippets Pack",
        "author": "Zaba Core",
        "version": "1.0.5",
        "description": "Kumpulan template kode cepat untuk Flask, Web Scraper BeautifulSoup, AsyncIO, dan Rest API.",
        "type": "plugin"
    },
    "syntax_linter": {
        "id": "syntax_linter",
        "name": "🔍 Static Syntax Linter",
        "author": "Zaba Core",
        "version": "1.1.0",
        "description": "Mendeteksi kesalahan titik dua ':', tanda kurung menggantung, dan typo indentasi sebelum kode di-run.",
        "type": "plugin"
    },
    "symbol_bar": {
        "id": "symbol_bar",
        "name": "⌨️ Extended Mobile Symbol Bar",
        "author": "Zaba Core",
        "version": "1.3.0",
        "description": "Menampilkan bilah tombol simbol cepat (: , ( ), [ ], { }, =, TAB) di atas keyboard HP.",
        "type": "plugin"
    }
}


@app.route("/api/themes", methods=["GET"])
def list_themes():
    return jsonify({
        "themes": {
            "retro": "Retro Green",
            "solarized": "Solarized Dark",
            "dracula": "Dracula",
            "cyberpunk": "Cyberpunk Neon",
            "nord": "Nord Arctic",
            "monokai": "Monokai Pro"
        }
    })


@app.route("/api/themes/<name>", methods=["GET"])
def get_theme(name):
    theme = THEMES.get(name)
    if not theme:
        return jsonify({"ok": False, "message": "Theme tidak ditemukan"}), 404
    return jsonify({"ok": True, "theme": theme})


@app.route("/api/marketplace/plugins", methods=["GET"])
def list_marketplace_plugins():
    return jsonify({"ok": True, "plugins": MARKETPLACE_PLUGINS})


# ---------------------------------------------------------------------------
# Android Keystore / Encrypted Preferences API Key Storage
# ---------------------------------------------------------------------------

def _xor_cipher(data_str: str, key_str: str) -> str:
    """Enkripsi/dekripsi XOR-Base64 ringan untuk dev environment."""
    key_bytes = key_str.encode("utf-8")
    data_bytes = data_str.encode("utf-8")
    res = bytearray()
    for i, b in enumerate(data_bytes):
        res.append(b ^ key_bytes[i % len(key_bytes)])
    return base64.b64encode(bytes(res)).decode("utf-8")


def _xor_decipher(b64_str: str, key_str: str) -> str:
    try:
        key_bytes = key_str.encode("utf-8")
        data_bytes = base64.b64decode(b64_str.encode("utf-8"))
        res = bytearray()
        for i, b in enumerate(data_bytes):
            res.append(b ^ key_bytes[i % len(key_bytes)])
        return res.decode("utf-8")
    except Exception:
        return ""


def load_keys() -> dict:
    """Membaca kunci API terenkripsi dari Android Keystore (Production) atau Fernet/XOR (Dev)."""
    # 1. Coba Android EncryptedSharedPreferences via Pyjnius
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        MasterKey = autoclass('androidx.security.crypto.MasterKey')
        EncryptedSharedPreferences = autoclass('androidx.security.crypto.EncryptedSharedPreferences')
        
        activity = PythonActivity.mActivity
        masterKey = MasterKey.Builder(activity).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
        prefs = EncryptedSharedPreferences.create(
            activity, "zabacode_secure_keys", masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SKEY,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
        keys = {}
        for p in ["openrouter", "gemini", "groq", "mistral"]:
            val = prefs.getString(p, "")
            if val:
                keys[p] = val
        if keys:
            return keys
    except Exception:
        pass

    # 2. Fallback Enkripsi Terdekripsi untuk Dev Mode
    if KEYS_FILE.exists():
        try:
            raw_text = KEYS_FILE.read_text(encoding="utf-8")
            decrypted = _xor_decipher(raw_text, AUTH_TOKEN)
            return json.loads(decrypted) if decrypted else {}
        except Exception:
            return {}
    return {}


def save_key(provider: str, api_key: str) -> None:
    """Menyimpan kunci API terenkripsi."""
    provider = provider.strip()
    api_key = api_key.strip()
    
    # 1. Coba simpan ke Android Keystore via EncryptedSharedPreferences
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        MasterKey = autoclass('androidx.security.crypto.MasterKey')
        EncryptedSharedPreferences = autoclass('androidx.security.crypto.EncryptedSharedPreferences')
        
        activity = PythonActivity.mActivity
        masterKey = MasterKey.Builder(activity).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
        prefs = EncryptedSharedPreferences.create(
            activity, "zabacode_secure_keys", masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SKEY,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
        editor = prefs.edit()
        editor.putString(provider, api_key)
        editor.apply()
    except Exception:
        pass

    # 2. Simpan cadangan terenkripsi ke KEYS_FILE
    keys = load_keys()
    keys[provider] = api_key
    try:
        encrypted_text = _xor_cipher(json.dumps(keys), AUTH_TOKEN)
        KEYS_FILE.write_text(encrypted_text, encoding="utf-8")
    except Exception as e:
        print(f"Gagal simpan encrypted key: {e}")


@app.route("/api/keys/status", methods=["GET"])
@require_auth
def keys_status():
    keys = load_keys()
    providers = ["openrouter", "gemini", "groq", "mistral"]
    return jsonify({p: bool(keys.get(p)) for p in providers})


@app.route("/api/keys", methods=["POST"])
@require_auth
def set_key():
    payload = request.get_json(silent=True) or {}
    provider, api_key = payload.get("provider"), payload.get("api_key", "")
    if provider not in ALLOWED_PROVIDERS or not isinstance(api_key, str) or not api_key.strip():
        return jsonify({"ok": False, "message": "Provider atau API key tidak valid."}), 400
    save_key(provider, api_key)
    return jsonify({"ok": True})


@app.route("/api/ai/chat", methods=["POST"])
@require_auth
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
