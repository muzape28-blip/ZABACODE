"""
Zabacode — Python backend (Milestone 1, plus starter hooks buat Milestone 2 & 4)

Dijalanin sama p4a webview bootstrap. Seluruh UI adalah satu halaman HTML
yang di-serve dari sini dan ditampilin di WebView bawaan Android
(lihat templates/index.html).

CATATAN JUJUR: kode ini ditulis berdasar riset, TANPA bisa di-compile/dites
beneran di sandbox Claude (ga ada akses internet buat fetch Android SDK/NDK/
buildozer di situ). Anggap ini starting point yang solid, bukan kode yang
udah pernah jalan di HP asli. Baca komentar TODO/CATATAN sebelum FASE 5.
"""

import contextlib
import io
import json
import sys
import traceback
import urllib.request
from pathlib import Path

from flask import Flask, jsonify, render_template, request

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

    # CATATAN: exec() jalan di process yang SAMA dengan Flask server-nya.
    # Cukup buat Milestone 1 (script pendek), tapi belum ter-isolasi —
    # infinite loop / crash berat di kode user bisa nge-hang seluruh app.
    # Isolasi ke subprocess terpisah itu kandidat kuat buat Milestone 2,
    # bukan sesuatu yang gue klaim udah beres di sini.
    exec_globals = {"__name__": "__main__"}
    try:
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            exec(compile(source, "<zabacode>", "exec"), exec_globals)
    except Exception:
        ok = False
        stderr_buf.write(traceback.format_exc())

    return jsonify({"ok": ok, "stdout": stdout_buf.getvalue(), "stderr": stderr_buf.getvalue()})


# ---------------------------------------------------------------------------
# Milestone 2 (starter): Library Manager, dua tingkat —
#   "runtime"   -> pure Python, aman dicoba install langsung saat itu juga
#   "buildtime" -> butuh C-extension (numpy, dst), WAJIB masuk
#                  buildozer.spec + rebuild lewat GitHub Actions. Ini
#                  keterbatasan asli arsitektur p4a, bukan hal yang bisa
#                  di-workaround gampang (udah dijelasin di roadmap).
# Lengkapi dict ini sesuai manifest.json di roadmap kalau mau ditampilin.
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
        return jsonify({"ok": False, "message": f"'{name}' belum ada di manifest. Cek dulu ke daftar p4a recipes."}), 404

    if info["tier"] == "buildtime":
        return jsonify({
            "ok": False,
            "needs_rebuild": True,
            "message": f"'{name}' butuh compiled extension — tambahin ke requirements di buildozer.spec, push, GitHub Actions yang rebuild APK-nya.",
        })

    # Tier "runtime": coba install pure-python package ke folder lokal yang
    # ditambahin ke sys.path. BELUM PERNAH DITES di p4a beneran — masuk akal
    # secara teori, tapi wajib divalidasi di HP asli sebelum diandalkan.
    try:
        import subprocess
        USER_PACKAGES_DIR.mkdir(exist_ok=True)
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
# Milestone 4 (starter): AI Assistant.
# Baru OpenRouter yang diimplementasi penuh sebagai contoh — Gemini/Groq/
# Mistral tinggal bikin fungsi _call_<provider>() dengan pola yang sama
# terus daftarin di PROVIDER_HANDLERS.
# ---------------------------------------------------------------------------

def load_keys() -> dict:
    if KEYS_FILE.exists():
        return json.loads(KEYS_FILE.read_text())
    return {}


def save_key(provider: str, api_key: str) -> None:
    keys = load_keys()
    keys[provider] = api_key
    # TODO KEAMANAN (WAJIB sebelum FASE 5 / rilis publik): ini masih
    # plaintext JSON biar gampang buat Milestone 1. Ganti ke penyimpanan
    # terenkripsi asli (misal Android Keystore lewat pyjnius) sebelum
    # dipakai beneran — sesuai keputusan di FASE 0 roadmap. Jangan skip.
    KEYS_FILE.write_text(json.dumps(keys))


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
        # Frontend pakai status 401 + needs_key ini buat munculin dialog
        # auto-prompt API key (keputusan UX yang udah disepakati).
        return jsonify({"ok": False, "needs_key": True, "provider": provider}), 401

    handler = PROVIDER_HANDLERS.get(provider)
    if handler is None:
        return jsonify({"ok": False, "message": f"Provider '{provider}' belum diimplementasi — contek pola _call_openrouter()."}), 501
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
    # "gemini": _call_gemini,   # TODO: bikin sesuai pola di atas
    # "groq": _call_groq,      # TODO
    # "mistral": _call_mistral, # TODO
}


if __name__ == "__main__":
    # p4a webview bootstrap: cek dokumentasi bootstrap-nya buat port yang
    # dia expect (default umumnya 5000, tapi verifikasi pas build pertama).
    app.run(host="127.0.0.1", port=5000)
