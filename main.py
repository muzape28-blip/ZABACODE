"""
Zabacode — Python backend (Milestone 1-4, production-ready starter)

Dijalanin sama p4a webview bootstrap. Seluruh UI adalah satu halaman HTML
yang di-serve dari sini dan ditampilin di WebView bawaan Android
(lihat templates/index.html).

FASE SEKARANG: Milestone 1-4 COMPLETE
- Milestone 1: Code execution dengan process isolation & timeout
- Milestone 2: Library Manager 2-tier (runtime + buildtime)
- Milestone 3: Enhanced UI (Monaco Editor, Save/Open, Themes)
- Milestone 4: Multi-provider AI (OpenRouter, Gemini, Groq, Mistral)
"""

import contextlib
import io
import json
import os
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
from pathlib import Path
from functools import wraps

from flask import Flask, jsonify, render_template, request

# ============================================================================
# CONFIG & PATHS
# ============================================================================

APP_DIR = Path(__file__).parent
KEYS_FILE = APP_DIR / ".zabacode_keys_encrypted.json"
USER_PACKAGES_DIR = APP_DIR / "user_packages"
USER_FILES_DIR = APP_DIR / "user_files"
EXECUTION_TIMEOUT = 30  # detik

# Encryption (fallback ke plaintext kalau pyjnius ga available di dev)
USE_ENCRYPTED_STORAGE = True
try:
    from pyjnius import autoclass, cast
    from jnius import JavaException
    PythonActivity = autoclass('org.renpy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    EncryptedSharedPreferences = autoclass(
        'androidx.security.crypto.EncryptedSharedPreferences'
    )
    MasterKey = autoclass('androidx.security.crypto.MasterKey')
    ENCRYPTION_AVAILABLE = True
except (ImportError, JavaException):
    ENCRYPTION_AVAILABLE = False
    print("[WARN] pyjnius/Android Keystore not available — using plaintext (dev mode)")

app = Flask(__name__)
USER_PACKAGES_DIR.mkdir(exist_ok=True)
USER_FILES_DIR.mkdir(exist_ok=True)


# ============================================================================
# ENCRYPTION/DECRYPTION HELPERS (Android Keystore via pyjnius)
# ============================================================================

def _get_encrypted_prefs():
    """Return EncryptedSharedPreferences instance (Android only)."""
    if not ENCRYPTION_AVAILABLE:
        return None
    try:
        activity = PythonActivity.mActivity
        context = cast(activity, Context)
        master_key = MasterKey.Builder(context).setKeyScheme(
            MasterKey.KeyScheme.AES256_GCM
        ).build()
        return EncryptedSharedPreferences.create(
            context,
            "zabacode_keys",
            master_key,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    except Exception as e:
        print(f"[ERROR] Encrypted prefs init failed: {e}")
        return None


def load_keys() -> dict:
    """Load API keys from encrypted storage (or plaintext fallback)."""
    if ENCRYPTION_AVAILABLE:
        prefs = _get_encrypted_prefs()
        if prefs:
            try:
                all_prefs = prefs.getAll()
                return {str(k): str(v) for k, v in all_prefs.items()}
            except Exception as e:
                print(f"[ERROR] Reading encrypted keys failed: {e}")
    
    # Fallback ke plaintext (dev mode)
    if KEYS_FILE.exists():
        try:
            return json.loads(KEYS_FILE.read_text())
        except:
            return {}
    return {}


def save_key(provider: str, api_key: str) -> None:
    """Save API key to encrypted storage (or plaintext fallback)."""
    if ENCRYPTION_AVAILABLE:
        prefs = _get_encrypted_prefs()
        if prefs:
            try:
                prefs.edit().putString(provider, api_key).apply()
                print(f"[OK] Key for '{provider}' saved to Android Keystore")
                return
            except Exception as e:
                print(f"[ERROR] Saving encrypted key failed: {e}")
    
    # Fallback ke plaintext (dev mode)
    keys = load_keys()
    keys[provider] = api_key
    KEYS_FILE.write_text(json.dumps(keys, indent=2))
    print(f"[WARN] Key for '{provider}' saved to plaintext file (dev mode)")


# ============================================================================
# PROCESS ISOLATION & EXECUTION
# ============================================================================

def execute_code_isolated(source: str, timeout: int = EXECUTION_TIMEOUT) -> dict:
    """
    Execute Python code dalam subprocess terpisah (isolasi dari Flask).
    
    Returns:
        dict: {"ok": bool, "stdout": str, "stderr": str, "timeout": bool}
    """
    import tempfile
    
    result = {
        "ok": True,
        "stdout": "",
        "stderr": "",
        "timeout": False,
    }
    
    # Buat temp file buat kode user
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        temp_file = f.name
    
    try:
        # Jalanin subprocess dengan timeout
        proc = subprocess.Popen(
            [sys.executable, temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            result["stdout"] = stdout
            result["stderr"] = stderr
            result["ok"] = proc.returncode == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            result["timeout"] = True
            result["ok"] = False
            result["stderr"] = f"[TIMEOUT] Kode exceeds {timeout}s limit"
    
    except Exception as e:
        result["ok"] = False
        result["stderr"] = f"Execution error: {traceback.format_exc()}"
    
    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_file)
        except:
            pass
    
    return result


@app.route("/")
def index():
    return render_template("index.html")


# ============================================================================
# MILESTONE 1: Execution dengan Process Isolation
# ============================================================================

@app.route("/api/run", methods=["POST"])
def run_code():
    """Execute user code dalam isolated subprocess."""
    payload = request.get_json(silent=True) or {}
    source = payload.get("code", "")
    
    result = execute_code_isolated(source, timeout=EXECUTION_TIMEOUT)
    return jsonify(result)


# ============================================================================
# MILESTONE 2: Library Manager (2-tier: runtime vs buildtime)
# ============================================================================

KNOWN_LIBRARIES = {
    # RUNTIME: Pure Python, aman install live
    "requests": {
        "tier": "runtime",
        "reason": "Pure Python HTTP library",
        "version": "latest"
    },
    "beautifulsoup4": {
        "tier": "runtime",
        "reason": "HTML/XML parsing",
        "version": "latest"
    },
    "pillow": {
        "tier": "runtime",
        "reason": "Image processing (pure Python fallback)",
        "version": "latest"
    },
    "pandas": {
        "tier": "buildtime",
        "reason": "C-extension (NumPy dependency) — butuh rebuild",
        "version": "latest"
    },
    "numpy": {
        "tier": "buildtime",
        "reason": "NumPy C-extension — tambah ke buildozer.spec + rebuild CI",
        "version": "latest"
    },
    "scipy": {
        "tier": "buildtime",
        "reason": "C-extension (NumPy dependency)",
        "version": "latest"
    },
    "matplotlib": {
        "tier": "buildtime",
        "reason": "C-extension plotting library",
        "version": "latest"
    },
    "lxml": {
        "tier": "buildtime",
        "reason": "C-extension XML library",
        "version": "latest"
    },
    "cryptography": {
        "tier": "buildtime",
        "reason": "C-extension crypto library",
        "version": "latest"
    },
    "pycryptodome": {
        "tier": "buildtime",
        "reason": "C-extension crypto suite",
        "version": "latest"
    },
    "yaml": {
        "tier": "buildtime",
        "reason": "PyYAML C-extension",
        "version": "latest"
    },
    "click": {
        "tier": "runtime",
        "reason": "CLI utility library (pure Python)",
        "version": "latest"
    },
    "colorama": {
        "tier": "runtime",
        "reason": "Terminal color support",
        "version": "latest"
    },
    "pytest": {
        "tier": "runtime",
        "reason": "Testing framework (pure Python)",
        "version": "latest"
    },
}


@app.route("/api/libraries", methods=["GET"])
def list_libraries():
    """List available libraries dengan info tier."""
    return jsonify(KNOWN_LIBRARIES)


@app.route("/api/libraries/install", methods=["POST"])
def install_library():
    """Install library (runtime only — buildtime harus via rebuild)."""
    name = (request.get_json(silent=True) or {}).get("name", "")
    info = KNOWN_LIBRARIES.get(name)
    
    if info is None:
        return jsonify({
            "ok": False,
            "message": f"'{name}' tidak ada di manifest. Cek p4a recipes.",
            "error": "unknown_library"
        }), 404
    
    if info["tier"] == "buildtime":
        return jsonify({
            "ok": False,
            "needs_rebuild": True,
            "message": f"'{name}' butuh C-extension — tambahin ke buildozer.spec + push, GitHub Actions rebuild.",
            "error": "needs_rebuild"
        }), 202
    
    # Runtime tier: coba install via pip
    try:
        USER_PACKAGES_DIR.mkdir(exist_ok=True)
        
        # Check if already installed
        if _is_package_installed(name):
            return jsonify({
                "ok": True,
                "message": f"'{name}' sudah terinstall.",
                "already_installed": True
            })
        
        # Install
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--target", str(USER_PACKAGES_DIR), name],
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        if result.returncode != 0:
            return jsonify({
                "ok": False,
                "message": f"Install gagal: {result.stderr[:200]}",
                "error": "install_failed"
            }), 500
        
        # Add to sys.path kalau belum
        if str(USER_PACKAGES_DIR) not in sys.path:
            sys.path.insert(0, str(USER_PACKAGES_DIR))
        
        return jsonify({
            "ok": True,
            "message": f"'{name}' berhasil diinstall!",
            "installed": True
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({
            "ok": False,
            "message": "Install timeout (>2 menit)",
            "error": "timeout"
        }), 500
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"Error: {str(e)[:200]}",
            "error": "exception"
        }), 500


def _is_package_installed(package_name: str) -> bool:
    """Check if package is already installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


# ============================================================================
# MILESTONE 3: File Manager (Save/Open)
# ============================================================================

@app.route("/api/files", methods=["GET"])
def list_files():
    """List all saved Python files."""
    files = []
    try:
        for fpath in USER_FILES_DIR.glob("*.py"):
            files.append({
                "name": fpath.name,
                "size": fpath.stat().st_size,
                "modified": fpath.stat().st_mtime,
            })
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
    
    return jsonify({"ok": True, "files": files})


@app.route("/api/files/<filename>", methods=["GET"])
def read_file(filename):
    """Read a saved Python file."""
    if ".." in filename or "/" in filename:
        return jsonify({"ok": False, "message": "Invalid filename"}), 400
    
    fpath = USER_FILES_DIR / filename
    if not fpath.exists() or not fpath.suffix == ".py":
        return jsonify({"ok": False, "message": "File not found"}), 404
    
    try:
        content = fpath.read_text()
        return jsonify({"ok": True, "content": content, "filename": filename})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/files/<filename>", methods=["POST"])
def save_file(filename):
    """Save code to a Python file."""
    if ".." in filename or "/" in filename:
        return jsonify({"ok": False, "message": "Invalid filename"}), 400
    
    if not filename.endswith(".py"):
        filename = filename + ".py"
    
    payload = request.get_json(silent=True) or {}
    content = payload.get("content", "")
    
    try:
        fpath = USER_FILES_DIR / filename
        fpath.write_text(content)
        return jsonify({
            "ok": True,
            "message": f"File '{filename}' tersimpan",
            "filename": filename
        })
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/files/<filename>", methods=["DELETE"])
def delete_file(filename):
    """Delete a saved Python file."""
    if ".." in filename or "/" in filename:
        return jsonify({"ok": False, "message": "Invalid filename"}), 400
    
    fpath = USER_FILES_DIR / filename
    if not fpath.exists():
        return jsonify({"ok": False, "message": "File not found"}), 404
    
    try:
        fpath.unlink()
        return jsonify({"ok": True, "message": f"File '{filename}' dihapus"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


# ============================================================================
# MILESTONE 4: Multi-Provider AI Assistant
# ============================================================================

@app.route("/api/keys/status", methods=["GET"])
def keys_status():
    """Check which AI providers have keys configured."""
    keys = load_keys()
    providers = ["openrouter", "gemini", "groq", "mistral"]
    return jsonify({p: bool(keys.get(p)) for p in providers})


@app.route("/api/keys", methods=["POST"])
def set_key():
    """Save API key for a provider."""
    payload = request.get_json(silent=True) or {}
    provider = payload.get("provider")
    api_key = payload.get("api_key", "")
    
    if not provider or not api_key:
        return jsonify({"ok": False, "message": "provider & api_key wajib diisi"}), 400
    
    if provider not in ["openrouter", "gemini", "groq", "mistral"]:
        return jsonify({"ok": False, "message": "Invalid provider"}), 400
    
    save_key(provider, api_key)
    return jsonify({"ok": True, "message": f"Key untuk '{provider}' tersimpan"})


@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    """Chat dengan AI assistant (multi-provider)."""
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    code_context = payload.get("code", "")
    provider = payload.get("provider", "openrouter")
    
    if not message:
        return jsonify({"ok": False, "message": "Message tidak boleh kosong"}), 400
    
    api_key = load_keys().get(provider)
    if not api_key:
        return jsonify({
            "ok": False,
            "needs_key": True,
            "provider": provider,
            "message": f"API key untuk '{provider}' belum ada"
        }), 401
    
    handler = PROVIDER_HANDLERS.get(provider)
    if handler is None:
        return jsonify({
            "ok": False,
            "message": f"Provider '{provider}' tidak diimplementasi"
        }), 501
    
    return handler(api_key, message, code_context)


def _call_openrouter(api_key: str, message: str, code_context: str):
    """OpenRouter API (Qwen3 Coder / DeepSeek)."""
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
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/muzape28-blip/ZABACODE",
            "X-Title": "Zabacode",
        },
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        
        if "error" in data:
            return jsonify({
                "ok": False,
                "message": f"OpenRouter error: {data['error'].get('message', 'Unknown')}"
            }), 502
        
        reply = data["choices"][0]["message"]["content"]
        return jsonify({"ok": True, "reply": reply, "provider": "openrouter"})
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return jsonify({
            "ok": False,
            "message": f"OpenRouter HTTP {e.code}: {error_body[:200]}"
        }), 502
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"OpenRouter error: {str(e)[:200]}"
        }), 502


def _call_gemini(api_key: str, message: str, code_context: str):
    """Google Gemini API (1M context window)."""
    system_prompt = (
        "Anda adalah Zabacode AI, asisten coding adaptif, bermulut tajam/tsundere, "
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android ARMv7. "
        "Konteks code dibawah ini — bantu user debug, optimize, atau implementasi fitur."
    )
    
    body = json.dumps({
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"{system_prompt}\n\nKode terkini:\n```python\n{code_context}\n```\n\n{message}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
        }
    }).encode()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        
        if "error" in data:
            return jsonify({
                "ok": False,
                "message": f"Gemini error: {data['error'].get('message', 'Unknown')}"
            }), 502
        
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"ok": True, "reply": reply, "provider": "gemini"})
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return jsonify({
            "ok": False,
            "message": f"Gemini HTTP {e.code}: {error_body[:200]}"
        }), 502
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"Gemini error: {str(e)[:200]}"
        }), 502


def _call_groq(api_key: str, message: str, code_context: str):
    """Groq API (ultra-fast inference)."""
    system_prompt = (
        "Anda adalah Zabacode AI, asisten coding adaptif, bermulut tajam/tsundere, "
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android ARMv7."
    )
    user_content = f"Kode:\n```python\n{code_context}\n```\n\nTanya: {message}"
    
    body = json.dumps({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "model": "mixtral-8x7b-32768",
        "temperature": 0.7,
        "max_tokens": 1024,
    }).encode()
    
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        
        if "error" in data:
            return jsonify({
                "ok": False,
                "message": f"Groq error: {data['error'].get('message', 'Unknown')}"
            }), 502
        
        reply = data["choices"][0]["message"]["content"]
        return jsonify({"ok": True, "reply": reply, "provider": "groq"})
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return jsonify({
            "ok": False,
            "message": f"Groq HTTP {e.code}: {error_body[:200]}"
        }), 502
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"Groq error: {str(e)[:200]}"
        }), 502


def _call_mistral(api_key: str, message: str, code_context: str):
    """Mistral API (Codestral specialized for code)."""
    system_prompt = (
        "Anda adalah Zabacode AI, asisten coding adaptif, bermulut tajam/tsundere, "
        "suka mengejek Zaba, namun sangat ahli membantu coding Python di Android ARMv7."
    )
    user_content = f"Kode:\n```python\n{code_context}\n```\n\nTanya: {message}"
    
    body = json.dumps({
        "model": "codestral-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
    }).encode()
    
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        
        if "error" in data:
            return jsonify({
                "ok": False,
                "message": f"Mistral error: {data['error'].get('message', 'Unknown')}"
            }), 502
        
        reply = data["choices"][0]["message"]["content"]
        return jsonify({"ok": True, "reply": reply, "provider": "mistral"})
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return jsonify({
            "ok": False,
            "message": f"Mistral HTTP {e.code}: {error_body[:200]}"
        }), 502
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"Mistral error: {str(e)[:200]}"
        }), 502


PROVIDER_HANDLERS = {
    "openrouter": _call_openrouter,
    "gemini": _call_gemini,
    "groq": _call_groq,
    "mistral": _call_mistral,
}


# ============================================================================
# THEMES & SETTINGS
# ============================================================================

THEMES = {
    "retro": {
        "name": "Retro Green",
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
        "name": "Solarized Dark",
        "bg": "#002B36",
        "bg_panel": "#073642",
        "border": "#586E75",
        "border_bright": "#93A1A1",
        "text": "#839496",
        "text_bright": "#B58900",
        "text_dim": "#586E75",
        "err": "#DC322F",
        "ai": "#2AA198",
    },
    "dracula": {
        "name": "Dracula",
        "bg": "#282A36",
        "bg_panel": "#44475A",
        "border": "#6272A4",
        "border_bright": "#8BE9FD",
        "text": "#F8F8F2",
        "text_bright": "#50FA7B",
        "text_dim": "#6272A4",
        "err": "#FF5555",
        "ai": "#FFB86C",
    },
}


@app.route("/api/themes", methods=["GET"])
def list_themes():
    """Return available themes."""
    return jsonify({
        "themes": {name: theme["name"] for name, theme in THEMES.items()}
    })


@app.route("/api/themes/<name>", methods=["GET"])
def get_theme(name):
    """Get theme colors."""
    if name not in THEMES:
        return jsonify({"ok": False, "message": "Theme not found"}), 404
    return jsonify({"ok": True, "theme": THEMES[name]})


# ============================================================================
# HEALTH & DEBUG
# ============================================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "ok": True,
        "version": "0.2.0",
        "encryption_available": ENCRYPTION_AVAILABLE,
        "execution_timeout": EXECUTION_TIMEOUT,
        "providers": list(PROVIDER_HANDLERS.keys()),
    })


if __name__ == "__main__":
    # p4a webview bootstrap: cek dokumentasi bootstrap-nya buat port yang
    # dia expect (default umumnya 5000, tapi verifikasi pas build pertama).
    app.run(host="127.0.0.1", port=5000, debug=False)
