"""WebView shell for the ZABACODE v1.0.0 core."""

import functools
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from waitress import serve

from zabacode.core.ai_provider import ALLOWED_PROVIDERS, PROVIDER_HANDLERS
from zabacode.core.executor import execute_code_isolated
from zabacode.core.file_manager import delete_file, list_files, read_file, save_file
from zabacode.core.security import AUTH_TOKEN, load_keys, save_key, verify_token
from zabacode.lib_manager import get_all_libraries, install_library
from zabacode.plugins.registry import get_all_plugins
from zabacode.themes.definitions import get_theme, list_themes

APP_VERSION = "1.0.0"
MAX_AI_FIELD_CHARS = 100_000

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024


def require_auth(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        if not verify_token(request.headers.get("X-Zabacode-Token", "")):
            return jsonify({"ok": False, "message": "Akses ditolak: token autentikasi tidak valid."}), 401
        return func(*args, **kwargs)
    return wrapped


@app.get("/")
def index():
    return render_template("index.html", auth_token=AUTH_TOKEN)


@app.get("/api/health")
def health_check():
    return jsonify({"ok": True, "version": APP_VERSION, "providers": sorted(ALLOWED_PROVIDERS), "ui": "webview"})


@app.post("/api/run")
@require_auth
def run_code():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    stdin_data = payload.get("stdin_data", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field code harus berupa string."}), 400
    return jsonify(execute_code_isolated(code, stdin_data=stdin_data))


@app.get("/api/libraries")
@require_auth
def libraries():
    return jsonify(get_all_libraries())


@app.post("/api/libraries/install")
@require_auth
def install():
    payload = request.get_json(silent=True) or {}
    return jsonify(install_library(payload.get("name", "")))


@app.get("/api/files")
@require_auth
def files():
    return jsonify({"files": list_files()})


@app.route("/api/files/<path:filename>", methods=["GET", "POST", "DELETE"])
@require_auth
def file_item(filename):
    if request.method == "GET":
        result = read_file(filename)
    elif request.method == "POST":
        payload = request.get_json(silent=True) or {}
        result = save_file(filename, payload.get("content", ""))
    else:
        result = delete_file(filename)
    return jsonify(result), (200 if result.get("ok") else 400)


@app.get("/api/themes")
def themes():
    return jsonify({"themes": list_themes()})


@app.get("/api/themes/<name>")
def theme(name):
    result = get_theme(name)
    if result is None:
        return jsonify({"ok": False, "message": "Theme tidak ditemukan"}), 404
    return jsonify({"ok": True, "theme": result})


@app.get("/api/marketplace/plugins")
def plugins():
    return jsonify({"ok": True, "plugins": get_all_plugins()})


@app.get("/api/keys/status")
@require_auth
def keys_status():
    keys = load_keys()
    return jsonify({provider: bool(keys.get(provider)) for provider in ALLOWED_PROVIDERS})


@app.post("/api/keys")
@require_auth
def set_key():
    payload = request.get_json(silent=True) or {}
    provider = payload.get("provider", "")
    api_key = payload.get("api_key", "")
    if provider not in ALLOWED_PROVIDERS or not isinstance(api_key, str) or not api_key.strip():
        return jsonify({"ok": False, "message": "Provider atau API key tidak valid."}), 400
    save_key(provider, api_key)
    return jsonify({"ok": True})


@app.post("/api/ai/chat")
@require_auth
def ai_chat():
    payload = request.get_json(silent=True) or {}
    provider = payload.get("provider", "openrouter")
    message = payload.get("message", "")
    code = payload.get("code", "")
    if provider not in ALLOWED_PROVIDERS or not isinstance(message, str) or not isinstance(code, str):
        return jsonify({"ok": False, "message": "Permintaan AI tidak valid."}), 400
    if len(message) > MAX_AI_FIELD_CHARS or len(code) > MAX_AI_FIELD_CHARS:
        return jsonify({"ok": False, "message": "Konteks AI terlalu besar."}), 413
    api_key = load_keys().get(provider)
    if not api_key:
        return jsonify({"ok": False, "needs_key": True, "provider": provider}), 401
    return jsonify(PROVIDER_HANDLERS[provider](api_key, message, code))


def run_webview_server():
    serve(app, host="127.0.0.1", port=5000, threads=4)
