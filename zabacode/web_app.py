"""WebView shell for the ZABACODE v1.2.0 core — Modular Python core + Oracle."""

import functools
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from waitress import serve

from zabacode.core.ai_provider import ALLOWED_PROVIDERS, PROVIDER_HANDLERS
from zabacode.core.executor import (
    PRELUDE_LINE_COUNT,
    execute_code_isolated,
    start_interactive_session,
    send_interactive_input,
    get_interactive_output,
    stop_interactive_session
)
from zabacode.core.checker import check_code
from zabacode.core.net import TLS_HELP_MESSAGE, ca_bundle_available
from zabacode.core.oracle import analyze_buffer, humanize_traceback, offline_reply
from zabacode.core.file_manager import delete_file, list_files, read_file, save_file
from zabacode.core.security import AUTH_TOKEN, load_keys, save_key, verify_token
from zabacode.lib_manager import get_all_libraries, install_library
from zabacode.plugins.registry import get_all_plugins
from zabacode.plugins.implementations import PluginExecutor
from zabacode.themes.definitions import get_theme, list_themes

APP_VERSION = "1.2.0"
MAX_AI_FIELD_CHARS = 100_000

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "assets"),
    static_url_path="/static",
)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024


@app.after_request
def _security_headers(resp):
    """Lock the WebView down: no third-party origins, no framing, no sniffing."""
    resp.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "font-src 'self' data:; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'",
    )
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    return resp


def require_auth(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        if not verify_token(request.headers.get("X-Zabacode-Token", "")):
            return jsonify({"ok": False, "message": "Access denied: invalid authentication token."}), 401
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
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400

    result = execute_code_isolated(code, stdin_data=stdin_data)

    # Offline Oracle: explain the crash in plain language, no network needed.
    if not result.get("ok") and result.get("stderr"):
        explanation = humanize_traceback(result["stderr"], line_offset=PRELUDE_LINE_COUNT)
        if explanation.get("ok"):
            result["explain"] = explanation
    return jsonify(result)


# ---------------------------------------------------------------------------
# Interactive Execution & Check Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/run/interactive/start")
@require_auth
def run_interactive_start():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    return jsonify(start_interactive_session(code))


@app.get("/api/run/interactive/output")
@require_auth
def run_interactive_output():
    return jsonify(get_interactive_output())


@app.post("/api/run/interactive/input")
@require_auth
def run_interactive_input():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    if not isinstance(text, str):
        return jsonify({"ok": False, "message": "Field 'text' must be a string."}), 400
    return jsonify(send_interactive_input(text))


@app.post("/api/run/interactive/stop")
@require_auth
def run_interactive_stop():
    return jsonify(stop_interactive_session())


@app.post("/api/check")
@require_auth
def check_code_endpoint():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    return jsonify(check_code(code))




# ---------------------------------------------------------------------------
# Other Core Endpoints
# ---------------------------------------------------------------------------

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
        return jsonify({"ok": False, "message": "Theme not found"}), 404
    return jsonify({"ok": True, "theme": result})


@app.get("/api/tls/status")
def tls_status():
    """Report whether outbound HTTPS can verify certificates on this device."""
    ok = ca_bundle_available()
    return jsonify({"ok": ok, "message": "" if ok else TLS_HELP_MESSAGE})


@app.get("/api/marketplace/plugins")
def plugins():
    return jsonify({"ok": True, "plugins": get_all_plugins()})


@app.post("/api/plugins/execute")
@require_auth
def execute_plugin():
    payload = request.get_json(silent=True) or {}
    plugin_id = payload.get("plugin_id", "")
    code = payload.get("code", "")
    if not isinstance(plugin_id, str) or not isinstance(code, str):
        return jsonify({"ok": False, "message": "Fields 'plugin_id' and 'code' must be strings."}), 400

    try:
        result = PluginExecutor.execute_plugin(plugin_id, code)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "message": f"Failed to execute plugin: {str(e)}"}), 500


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
    if provider not in ALLOWED_PROVIDERS or not isinstance(api_key, str):
        return jsonify({"ok": False, "message": "Invalid provider or API key."}), 400
    save_key(provider, api_key)
    return jsonify({"ok": True})


@app.post("/api/ai/chat")
@require_auth
def ai_chat():
    payload = request.get_json(silent=True) or {}
    provider = payload.get("provider", "openrouter")
    model = payload.get("model", "")
    message = payload.get("message", "")
    code = payload.get("code", "")
    if provider not in ALLOWED_PROVIDERS or not isinstance(message, str) or not isinstance(code, str):
        return jsonify({"ok": False, "message": "Invalid AI request."}), 400
    if len(message) > MAX_AI_FIELD_CHARS or len(code) > MAX_AI_FIELD_CHARS:
        return jsonify({"ok": False, "message": "AI context is too large."}), 413
    allow_offline = payload.get("allow_offline", True)

    api_key = load_keys().get(provider)
    # Ollama is offline-first (no key required), custom requires URL as key
    is_offline_provider = provider in ("ollama",)
    if not api_key and not is_offline_provider:
        if allow_offline:
            fallback = offline_reply(message, code)
            fallback["fallback_reason"] = "no_api_key"
            return jsonify(fallback)
        return jsonify({"ok": False, "needs_key": True, "provider": provider}), 401
    # For offline providers, empty key is fine
    if not api_key:
        api_key = ""

    result = PROVIDER_HANDLERS[provider](api_key, message, code, model=model)

    # Cloud unreachable (TLS, rate limit, airplane mode)? The Oracle still answers.
    if not result.get("ok") and allow_offline:
        fallback = offline_reply(message, code)
        fallback["fallback_reason"] = result.get("message", "provider_error")
        fallback["reply"] = (
            f"_{provider} unavailable — answering locally._\n\n" + fallback["reply"]
        )
        return jsonify(fallback)
    return jsonify(result)


@app.post("/api/oracle/explain")
@require_auth
def oracle_explain():
    """Explain a traceback in plain language. Works with zero network."""
    payload = request.get_json(silent=True) or {}
    stderr = payload.get("stderr", "")
    if not isinstance(stderr, str):
        return jsonify({"ok": False, "message": "Field 'stderr' must be a string."}), 400
    return jsonify(humanize_traceback(stderr))


@app.post("/api/oracle/analyze")
@require_auth
def oracle_analyze():
    """Static AST analysis of the editor buffer. Works with zero network."""
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    return jsonify(analyze_buffer(code))


def run_webview_server():
    serve(app, host="127.0.0.1", port=5000, threads=4)
