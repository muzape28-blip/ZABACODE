"""WebView shell for the ZABACODE v1.2.0 core — Modular Python core + Oracle.

Architecture (v1.2.1+): VSCode-inspired event system + command registry + service container.
  - Events:    core modules fire events, web_app routes and plugins listen
  - Commands:  plugins register as commands, no more hardcoded if/elif
  - Services:  lazy-loaded, testable, decoupled dependency injection
"""

import functools
import hashlib
from pathlib import Path
from typing import Any, Dict, Tuple, Union

from flask import Flask, jsonify, render_template, request
from waitress import serve  # type: ignore[import-untyped]

from zabacode.core.ai_provider import ALLOWED_PROVIDERS, PROVIDER_HANDLERS
from zabacode.core.checker import check_code
from zabacode.core.commands import get_command_registry
from zabacode.core.diff import compute_line_diff
from zabacode.core.events import get_app_events
from zabacode.core.executor import (
    MAX_CODE_BYTES,
    MAX_INTERACTIVE_BYTES,
    PRELUDE_LINE_COUNT,
    execute_code_isolated,
    get_interactive_output,
    send_interactive_input,
    start_interactive_session,
    stop_interactive_session,
)
from zabacode.core.file_manager import delete_file, list_files, read_file, save_file
from zabacode.core.net import TLS_HELP_MESSAGE, ca_bundle_available
from zabacode.core.diagnostics import (
    Diagnostic,
    DiagnosticSeverity,
    diagnostics_to_ace_annotations,
    make_diagnostic,
)
from zabacode.core.oracle import analyze_buffer, auto_fix_code, humanize_traceback, offline_reply
from zabacode.core.security import AUTH_TOKEN, load_keys, save_key, verify_token
from zabacode.core.services import get_service_container
from zabacode.lib_manager import get_all_libraries, install_library
from zabacode.plugins.implementations import PluginExecutor
from zabacode.plugins.registry import get_all_plugins
from zabacode.themes.definitions import get_theme, list_themes

APP_VERSION = "1.2.1"
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


# ---------------------------------------------------------------------------
# JSON Validation Helper — Fix #23
# ---------------------------------------------------------------------------

def _get_json_payload() -> Tuple[Union[Dict[str, Any], None], Union[tuple[Any, int], None]]:
    """
    Parse and validate JSON body — must be an object, not array or primitive.
    Returns (payload_dict, error_response). If error_response is not None, return it.
    """
    data = request.get_json(silent=True)
    if data is None:
        # A body that was sent but could not be parsed must never be treated as
        # empty: that turns a client bug (e.g. a missing Content-Type header)
        # into a misleading "field is empty" reply. Fail loudly instead.
        if request.get_data(cache=True, as_text=True).strip():
            return None, (
                jsonify(
                    {
                        "ok": False,
                        "message": (
                            "Request body could not be parsed as JSON. "
                            "Send it with the header 'Content-Type: application/json'."
                        ),
                        "code": "invalid_json",
                    }
                ),
                400,
            )
        # Genuinely empty body — routes with defaults may proceed.
        return {}, None
    if not isinstance(data, dict):
        # JSON arrays or primitives are not allowed — previously treated as {} silently
        return None, (
            jsonify(
                {
                    "ok": False,
                    "message": "JSON body must be an object",
                    "code": "invalid_json_type",
                }
            ),
            400,
        )
    return data, None


def _validate_string_field(payload: dict, field: str, required: bool = False, max_len: int | None = None):
    """Validate a field is string if present, return error if not."""
    if field not in payload:
        if required:
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": f"Field '{field}' is required",
                        "code": "missing_field",
                    }
                ),
                400,
            )
        return None
    val = payload.get(field)
    if not isinstance(val, str):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"Field '{field}' must be a string",
                    "code": "invalid_type",
                }
            ),
            400,
        )
    if max_len is not None and len(val) > max_len:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"Field '{field}' too large (max {max_len} chars)",
                    "code": "too_large",
                }
            ),
            413,
        )
    return None


@app.get("/")
def index():
    return render_template("index.html", auth_token=AUTH_TOKEN)


@app.get("/api/health")
def health_check():
    return jsonify(
        {"ok": True, "version": APP_VERSION, "providers": sorted(ALLOWED_PROVIDERS), "ui": "webview"}
    )


# ---------------------------------------------------------------------------
# VSCode-inspired API endpoints — Command Registry & Event System
# ---------------------------------------------------------------------------


@app.get("/api/commands")
@require_auth
def list_commands():
    """List all registered commands (VSCode CommandsRegistry pattern)."""
    registry = get_command_registry()
    return jsonify({"ok": True, "commands": registry.get_all_commands_info()})


@app.post("/api/commands/execute")
@require_auth
def execute_command():
    """Execute a registered command by ID (VSCode CommandService pattern)."""
    payload, err = _get_json_payload()
    if err:
        return err

    command_id = payload.get("command_id", "")
    args = payload.get("args", [])

    if not isinstance(command_id, str):
        return jsonify({"ok": False, "message": "Field 'command_id' must be a string."}), 400
    if not isinstance(args, list):
        return jsonify({"ok": False, "message": "Field 'args' must be an array."}), 400

    registry = get_command_registry()
    if not registry.has_command(command_id):
        return jsonify({"ok": False, "message": f"Command '{command_id}' not found."}), 404

    try:
        result = registry.execute_command(command_id, *args)
        if isinstance(result, tuple) and len(result) == 2:
            new_code, report = result
            return jsonify({"ok": True, "code": new_code, "report": "\n".join(report) if isinstance(report, list) else str(report)})
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Command execution failed: {e}"}), 500


@app.get("/api/events/status")
@require_auth
def events_status():
    """Report event system status — listener counts for debugging."""
    events = get_app_events()
    return jsonify({
        "ok": True,
        "events": {
            "onWillRunCode": events._onWillRunCode.listener_count,
            "onDidRunCode": events._onDidRunCode.listener_count,
            "onDidSaveFile": events._onDidSaveFile.listener_count,
            "onDidDeleteFile": events._onDidDeleteFile.listener_count,
            "onWillAIChat": events._onWillAIChat.listener_count,
            "onDidAIChat": events._onDidAIChat.listener_count,
            "onDidTogglePlugin": events._onDidTogglePlugin.listener_count,
            "onDidInstallLibrary": events._onDidInstallLibrary.listener_count,
        },
    })


@app.post("/api/run")
@require_auth
def run_code():
    """Batch execution: run to completion, then return everything at once.

    Not what the RUN button uses — the editor drives ``/api/run/interactive/*``
    so that ``input()`` genuinely blocks and output streams live. This endpoint
    is the non-interactive counterpart, kept for automation, plugins and tests:

    * ``input()`` is stubbed by ``SAFE_INPUT_PATCH`` (returns ``""``) because
      nobody is there to type, which is why the reported traceback line needs
      ``line_offset=PRELUDE_LINE_COUNT`` below;
    * the whole run is bounded by a single 30 s timeout rather than the
      interactive session's idle/lifetime limits;
    * the response is one JSON blob (stdout, stderr, images, explain).

    The two paths deliberately do *not* share an execution flow — only the
    image capture in ``collect_new_images()`` is common.
    """
    payload, err = _get_json_payload()
    if err:
        return err

    # Validate code field must be string if present
    if "code" in payload and not isinstance(payload.get("code"), str):
        return (
            jsonify({"ok": False, "message": "Field 'code' must be a string", "code": "invalid_type"}),
            400,
        )
    if "stdin_data" in payload and not isinstance(payload.get("stdin_data"), str):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Field 'stdin_data' must be a string",
                    "code": "invalid_type",
                }
            ),
            400,
        )

    code = payload.get("code", "")
    stdin_data = payload.get("stdin_data", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    # Enforce size bound already in executor, but also early 413
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"Source too large: {len(code.encode('utf-8'))} bytes > {MAX_CODE_BYTES} limit",
                    "code": "too_large",
                }
            ),
            413,
        )

    result = execute_code_isolated(code, stdin_data=stdin_data)

    # Fire events (VSCode-inspired event bus)
    events = get_app_events()
    events.fire_did_run_code({
        "mode": "isolated",
        "ok": result.get("ok"),
        "timeout": result.get("timeout"),
        "code_size": len(code.encode("utf-8")),
    })

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
    payload, err = _get_json_payload()
    if err:
        return err

    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    # Early 413 for oversized source — Fix #18
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"Source too large: {len(code.encode('utf-8'))} bytes > {MAX_CODE_BYTES} limit",
                    "code": "too_large",
                }
            ),
            413,
        )
    result = start_interactive_session(code)
    # Fire event (VSCode-inspired event bus)
    if result.get("ok"):
        events = get_app_events()
        events.fire_will_run_code({"mode": "interactive", "code_size": len(code.encode("utf-8"))})
    return jsonify(result)


@app.get("/api/run/interactive/output")
@require_auth
def run_interactive_output():
    return jsonify(get_interactive_output())


@app.post("/api/run/interactive/input")
@require_auth
def run_interactive_input():
    payload, err = _get_json_payload()
    if err:
        return err

    text = payload.get("text", "")
    if not isinstance(text, str):
        return jsonify({"ok": False, "message": "Field 'text' must be a string."}), 400
    # Bound input size
    if len(text.encode("utf-8")) > MAX_INTERACTIVE_BYTES:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Input too large (max 8KB)",
                    "code": "too_large",
                }
            ),
            413,
        )
    return jsonify(send_interactive_input(text))


@app.post("/api/run/interactive/stop")
@require_auth
def run_interactive_stop():
    return jsonify(stop_interactive_session())


@app.post("/api/check")
@require_auth
def check_code_endpoint():
    payload, err = _get_json_payload()
    if err:
        return err

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
    payload, err = _get_json_payload()
    if err:
        return err

    # Fix #23: Validate 'name' must be string
    if "name" in payload and not isinstance(payload.get("name"), str):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Field 'name' must be a string",
                    "code": "invalid_type",
                }
            ),
            400,
        )
    result = install_library(payload.get("name", ""))
    # Fire event (VSCode-inspired event bus)
    if result.get("ok"):
        get_app_events().fire_did_install_library({"name": payload.get("name", "")})
    return jsonify(result)


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
        payload, err = _get_json_payload()
        if err:
            return err
        if "content" in payload and not isinstance(payload.get("content"), str):
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": "Field 'content' must be a string",
                        "code": "invalid_type",
                    }
                ),
                400,
            )
        result = save_file(filename, payload.get("content", ""))
        # Fire event (VSCode-inspired event bus)
        if result.get("ok"):
            get_app_events().fire_did_save_file({"filename": result.get("filename", filename)})
    else:
        result = delete_file(filename)
        # Fire event (VSCode-inspired event bus)
        if result.get("ok"):
            get_app_events().fire_did_delete_file({"filename": filename})
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
    payload, err = _get_json_payload()
    if err:
        return err

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
    payload, err = _get_json_payload()
    if err:
        return err

    # Fix #23: Validate provider and api_key are strings
    if "provider" in payload and not isinstance(payload.get("provider"), str):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Field 'provider' must be a string",
                    "code": "invalid_type",
                }
            ),
            400,
        )
    if "api_key" in payload and not isinstance(payload.get("api_key"), str):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Field 'api_key' must be a string",
                    "code": "invalid_type",
                }
            ),
            400,
        )

    provider = payload.get("provider", "")
    api_key = payload.get("api_key", "")
    if provider not in ALLOWED_PROVIDERS or not isinstance(api_key, str):
        return jsonify({"ok": False, "message": "Invalid provider or API key."}), 400
    save_key(provider, api_key)
    return jsonify({"ok": True})


@app.post("/api/ai/chat")
@require_auth
def ai_chat():
    payload, err = _get_json_payload()
    if err:
        return err

    provider = payload.get("provider", "openrouter")
    model = payload.get("model", "")
    message = payload.get("message", "")
    code = payload.get("code", "")

    # Fix #23 + #24: Strict validation for AI chat fields
    if not isinstance(provider, str):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Field 'provider' must be a string",
                    "code": "invalid_type",
                }
            ),
            400,
        )
    if not isinstance(model, str):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Field 'model' must be a string",
                    "code": "invalid_type",
                }
            ),
            400,
        )
    if not isinstance(message, str):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Field 'message' must be a string",
                    "code": "invalid_type",
                }
            ),
            400,
        )
    if not isinstance(code, str):
        return (
            jsonify(
                {"ok": False, "message": "Field 'code' must be a string", "code": "invalid_type"}
            ),
            400,
        )

    if provider not in ALLOWED_PROVIDERS:
        return jsonify({"ok": False, "message": "Invalid AI provider."}), 400
    if len(message) > MAX_AI_FIELD_CHARS or len(code) > MAX_AI_FIELD_CHARS:
        return jsonify({"ok": False, "message": "AI context is too large."}), 413

    # allow_offline should be bool if present
    allow_offline = payload.get("allow_offline", True)
    if not isinstance(allow_offline, bool):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Field 'allow_offline' must be a boolean",
                    "code": "invalid_type",
                }
            ),
            400,
        )

    # Fix #24: Separate Custom Endpoint URL validation, warn cleartext HTTP
    # For custom provider, we now support separate 'endpoint_url' field in addition to api_key
    # api_key may still be URL for backward compat, but we encourage endpoint_url
    endpoint_url = None
    if provider == "custom":
        # Accept both 'endpoint_url' and legacy 'api_key' as URL
        candidate = payload.get("endpoint_url") or payload.get("api_key") or ""
        if candidate:
            if not isinstance(candidate, str):
                return (
                    jsonify(
                        {
                            "ok": False,
                            "message": "Field 'endpoint_url' must be a string URL",
                            "code": "invalid_type",
                        }
                    ),
                    400,
                )
            # Basic URL validation — must be http:// or https://
            if not (candidate.startswith("http://") or candidate.startswith("https://")):
                return (
                    jsonify(
                        {
                            "ok": False,
                            "message": "Custom endpoint URL must start with http:// or https://",
                            "code": "invalid_url",
                        }
                    ),
                    400,
                )
            endpoint_url = candidate
            # Warn for cleartext HTTP — will be surfaced in UI, but also log
            if candidate.startswith("http://"):
                # Allow loopback/private network without hard fail, but warn
                # For now we allow but will include warning in response if needed
                pass

    api_key = load_keys().get(provider)
    # Ollama is offline-first (no key required)
    is_offline_provider = provider in ("ollama",)
    if not api_key and not is_offline_provider:
        # For custom, if endpoint_url provided in request payload, allow even if no saved key
        if provider == "custom" and endpoint_url:
            api_key = endpoint_url
        else:
            if allow_offline:
                fallback = offline_reply(message, code)
                fallback["fallback_reason"] = "no_api_key"
                return jsonify(fallback)
            return jsonify({"ok": False, "needs_key": True, "provider": provider}), 401
    # For offline providers, empty key is fine
    if not api_key:
        api_key = ""

    # If custom and endpoint_url provided in payload, override api_key with endpoint_url for this request
    if provider == "custom" and endpoint_url:
        api_key = endpoint_url

    result = PROVIDER_HANDLERS[provider](api_key, message, code, model=model)

    # Fire events (VSCode-inspired event bus)
    events = get_app_events()
    events.fire_did_ai_chat({
        "provider": provider,
        "ok": result.get("ok"),
        "fallback": result.get("fallback_reason"),
    })

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
    payload, err = _get_json_payload()
    if err:
        return err

    stderr = payload.get("stderr", "")
    if not isinstance(stderr, str):
        return jsonify({"ok": False, "message": "Field 'stderr' must be a string."}), 400
    return jsonify(humanize_traceback(stderr))


@app.post("/api/oracle/analyze")
@require_auth
def oracle_analyze():
    """Static AST analysis of the editor buffer. Works with zero network."""
    payload, err = _get_json_payload()
    if err:
        return err

    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    return jsonify(analyze_buffer(code))

@app.post("/api/oracle/fix")
@require_auth
def oracle_fix():
    """Automatically patch code based on syntax error/traceback. Works offline."""
    payload, err = _get_json_payload()
    if err:
        return err

    code = payload.get("code", "")
    stderr = payload.get("stderr", "")
    tab_id = payload.get("tab_id")
    revision = payload.get("revision")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    if not isinstance(stderr, str):
        return jsonify({"ok": False, "message": "Field 'stderr' must be a string."}), 400
    if tab_id is not None and (not isinstance(tab_id, str) or not tab_id or len(tab_id) > 128):
        return jsonify({"ok": False, "message": "Field 'tab_id' must be a non-empty string up to 128 chars."}), 400
    # bool is a subclass of int in Python, but never a valid document revision.
    if revision is not None and (isinstance(revision, bool) or not isinstance(revision, int) or revision < 0):
        return jsonify({"ok": False, "message": "Field 'revision' must be a non-negative integer."}), 400

    # The server owns this fingerprint: the client must only apply this result
    # while its current buffer still hashes to the exact source we analyzed.
    result = auto_fix_code(code, stderr)
    result["source_hash"] = hashlib.sha256(code.encode("utf-8")).hexdigest()
    if result.get("ok") and isinstance(result.get("fixed_code"), str):
        result["diff"] = compute_line_diff(code, result["fixed_code"])
    if tab_id is not None:
        result["tab_id"] = tab_id
    if revision is not None:
        result["revision"] = revision
    return jsonify(result)


# ---------------------------------------------------------------------------
# P1: Diagnostics — VSCode-inspired Diagnostic Collection
# ---------------------------------------------------------------------------


@app.post("/api/diagnostics")
@require_auth
def get_diagnostics():
    """Analyze code and return diagnostics with quick-fixes (VSCode DiagnosticCollection pattern)."""
    payload, err = _get_json_payload()
    if err:
        return err
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400

    from zabacode.core.diagnostics import analyze_code_diagnostics, get_diagnostic_engine
    diags = analyze_code_diagnostics(code)

    # Update the diagnostic engine's "checker" collection
    engine = get_diagnostic_engine()
    collection = engine.create_collection("checker")
    collection.set(diags)

    return jsonify({
        "ok": True,
        "diagnostics": [d.to_dict() for d in diags],
        "counts": engine.get_diagnostics_severity_counts(),
    })


@app.get("/api/diagnostics")
@require_auth
def get_current_diagnostics():
    """Get all current diagnostics from all collections (VSCode aggregated diagnostics)."""
    from zabacode.core.diagnostics import get_diagnostic_engine
    engine = get_diagnostic_engine()
    diags = engine.get_all_diagnostics()
    return jsonify({
        "ok": True,
        "diagnostics": [d.to_dict() for d in diags],
        "counts": engine.get_diagnostics_severity_counts(),
    })


@app.post("/api/diagnostics/aggregate")
@require_auth
def diagnostics_aggregate():
    """
    Aggregate diagnostics from multiple sources (Oracle + checker).
    Returns a unified list of Diagnostic objects + Ace annotations.

    This is the foundation for Problems bottom sheet + Ace gutter annotations.
    """
    payload, err = _get_json_payload()
    if err:
        return err

    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400

    diagnostics: list[Diagnostic] = []

    # 1. Syntax / static analysis via Oracle
    analysis = analyze_buffer(code)
    if not analysis.get("ok"):
        if analysis.get("syntax_error"):
            diagnostics.append(
                make_diagnostic(
                    start_line=max(0, (analysis.get("line") or 1) - 1),
                    start_col=0,
                    end_line=max(0, (analysis.get("line") or 1) - 1),
                    end_col=80,
                    message=analysis.get("message", "Syntax error"),
                    severity=DiagnosticSeverity.ERROR,
                    source="oracle",
                    code="syntax-error",
                    fixable=True,
                    quick_fix_id="oracle-fix",
                    explanation="Oracle detected a syntax problem.",
                )
            )

    # 2. Run the existing checker (if it returns structured issues)
    try:
        chk = check_code(code)
        if chk.get("ok") is False and chk.get("issues"):
            for issue in chk.get("issues", [])[:20]:
                diagnostics.append(
                    make_diagnostic(
                        start_line=0,
                        start_col=0,
                        end_line=0,
                        end_col=80,
                        message=str(issue),
                        severity=DiagnosticSeverity.WARNING,
                        source="checker",
                        fixable=False,
                    )
                )
    except Exception:
        pass

    # Convert to Ace-friendly annotations
    annotations = diagnostics_to_ace_annotations(diagnostics)

    return jsonify(
        {
            "ok": True,
            "diagnostics": [d.to_dict() for d in diagnostics],
            "annotations": annotations,
            "count": len(diagnostics),
            "sources": ["oracle", "checker"],
        }
    )


# ---------------------------------------------------------------------------
# P2: Editor Intelligence — VSCode-inspired Language Features
# ---------------------------------------------------------------------------


@app.post("/api/editor/outline")
@require_auth
def editor_outline():
    """Get AST symbol outline for the current file (VSCode DocumentSymbolProvider)."""
    payload, err = _get_json_payload()
    if err:
        return err
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400

    from zabacode.core.editor_intelligence import get_symbol_outline
    symbols = get_symbol_outline(code)
    return jsonify({
        "ok": True,
        "symbols": [s.to_dict() for s in symbols],
    })


@app.post("/api/editor/symbols")
@require_auth
def editor_symbols():
    """Search for symbols in the current file (VSCode workspace/symbol)."""
    payload, err = _get_json_payload()
    if err:
        return err
    code = payload.get("code", "")
    query = payload.get("query", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    if not isinstance(query, str):
        return jsonify({"ok": False, "message": "Field 'query' must be a string."}), 400

    from zabacode.core.editor_intelligence import find_symbol
    symbols = find_symbol(code, query)
    return jsonify({
        "ok": True,
        "symbols": [s.to_dict() for s in symbols],
    })


@app.post("/api/editor/completions")
@require_auth
def editor_completions():
    """Get autocomplete completions for the cursor position (VSCode CompletionItemProvider)."""
    payload, err = _get_json_payload()
    if err:
        return err
    code = payload.get("code", "")
    line = payload.get("line", 1)
    column = payload.get("column", 1)
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    if not isinstance(line, int):
        return jsonify({"ok": False, "message": "Field 'line' must be an integer."}), 400
    if not isinstance(column, int):
        return jsonify({"ok": False, "message": "Field 'column' must be an integer."}), 400

    from zabacode.core.editor_intelligence import get_completions
    completions = get_completions(code, line, column)
    return jsonify({
        "ok": True,
        "completions": [c.to_dict() for c in completions],
    })


@app.post("/api/editor/rename")
@require_auth
def editor_rename():
    """Rename a symbol at the given position (VSCode RenameProvider, local one-file)."""
    payload, err = _get_json_payload()
    if err:
        return err
    code = payload.get("code", "")
    line = payload.get("line", 1)
    column = payload.get("column", 1)
    new_name = payload.get("new_name", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400
    if not isinstance(line, int):
        return jsonify({"ok": False, "message": "Field 'line' must be an integer."}), 400
    if not isinstance(column, int):
        return jsonify({"ok": False, "message": "Field 'column' must be an integer."}), 400
    if not isinstance(new_name, str):
        return jsonify({"ok": False, "message": "Field 'new_name' must be a string."}), 400

    from zabacode.core.editor_intelligence import rename_symbol
    result = rename_symbol(code, line, column, new_name)
    return jsonify(result)


@app.post("/api/editor/rename-workspace")
@require_auth
def editor_rename_workspace():
    """Rename a symbol across all user files (VSCode WorkspaceEdit)."""
    payload, err = _get_json_payload()
    if err:
        return err
    filename = payload.get("filename", "")
    line = payload.get("line", 1)
    column = payload.get("column", 1)
    new_name = payload.get("new_name", "")
    if not isinstance(filename, str):
        return jsonify({"ok": False, "message": "Field 'filename' must be a string."}), 400
    if not isinstance(line, int):
        return jsonify({"ok": False, "message": "Field 'line' must be an integer."}), 400
    if not isinstance(column, int):
        return jsonify({"ok": False, "message": "Field 'column' must be an integer."}), 400
    if not isinstance(new_name, str):
        return jsonify({"ok": False, "message": "Field 'new_name' must be a string."}), 400

    from zabacode.core.editor_intelligence import rename_symbol_workspace
    result = rename_symbol_workspace(filename, line, column, new_name)
    return jsonify(result)


@app.post("/api/editor/organize-imports")
@require_auth
def editor_organize_imports():
    """Organize imports: sort, group, and remove unused (VSCode organizeImports)."""
    payload, err = _get_json_payload()
    if err:
        return err
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"ok": False, "message": "Field 'code' must be a string."}), 400

    from zabacode.core.editor_intelligence import organize_imports
    result = organize_imports(code)
    if result.get("ok") and isinstance(result.get("code"), str):
        result["diff"] = compute_line_diff(code, result["code"])
    return jsonify(result)


# ---------------------------------------------------------------------------
# P3: Navigation UX — VSCode-inspired Command Palette & Quick Open
# ---------------------------------------------------------------------------


@app.get("/api/palette")
@require_auth
def command_palette():
    """Get command palette items, optionally filtered (VSCode Command Palette)."""
    query = request.args.get("q", "")
    from zabacode.core.navigation import get_command_palette_items
    items = get_command_palette_items(query)
    return jsonify({
        "ok": True,
        "items": [i.to_dict() for i in items],
    })


@app.get("/api/quickopen")
@require_auth
def quick_open():
    """Get Quick Open items — files and symbols (VSCode Quick Open Ctrl+P)."""
    query = request.args.get("q", "")
    from zabacode.core.navigation import get_quick_open_items
    items = get_quick_open_items(query)
    return jsonify({
        "ok": True,
        "items": [i.to_dict() for i in items],
    })


@app.get("/api/settings")
@require_auth
def get_settings():
    """Get all settings, optionally filtered (VSCode Searchable Settings)."""
    query = request.args.get("q", "")
    from zabacode.core.navigation import get_all_settings
    settings = get_all_settings(query)
    return jsonify({
        "ok": True,
        "settings": [s.to_dict() for s in settings],
    })


@app.post("/api/settings")
@require_auth
def update_setting_endpoint():
    """Update a searchable setting's value."""
    payload, err = _get_json_payload()
    if err:
        return err

    key = payload.get("key")
    value = payload.get("value")

    if not key or not isinstance(key, str):
        return jsonify({"ok": False, "message": "Field 'key' must be a non-empty string."}), 400

    from zabacode.core.navigation import save_setting
    save_setting(key, value)
    return jsonify({"ok": True, "message": f"Setting '{key}' successfully updated."})


# ---------------------------------------------------------------------------
# P4: Workspace — VSCode-inspired Search & Symbol Index
# ---------------------------------------------------------------------------


@app.get("/api/search")
@require_auth
def search_in_files_endpoint():
    """Search across all user files (VSCode Search in Files Ctrl+Shift+F)."""
    query = request.args.get("q", "")
    case_sensitive = request.args.get("case", "0") == "1"
    regex = request.args.get("regex", "0") == "1"
    if not query:
        return jsonify({"ok": True, "results": []})

    from zabacode.core.navigation import search_in_files
    results = search_in_files(query, case_sensitive=case_sensitive, regex=regex)
    return jsonify({
        "ok": True,
        "results": [r.to_dict() for r in results],
        "total": len(results),
    })


@app.get("/api/workspace/symbols")
@require_auth
def workspace_symbols():
    """Get symbols across all user files (VSCode workspace/symbol Ctrl+T)."""
    query = request.args.get("q", "")
    from zabacode.core.navigation import get_workspace_symbols
    symbols = get_workspace_symbols(query)
    return jsonify({
        "ok": True,
        "symbols": [s.to_dict() for s in symbols],
    })


@app.get("/api/workspace/imports")
@require_auth
def workspace_import_graph():
    """Get the import graph for all user files (VSCode dependency view)."""
    from zabacode.core.navigation import get_import_graph
    graph = get_import_graph()
    return jsonify({
        "ok": True,
        "graph": graph,
    })


#: The p4a webview bootstrap polls *exactly* this port (p4a.port = 5000) and
#: loads http://127.0.0.1:5000/ once it answers. On Android we must therefore
#: serve on this port — silently moving to another port leaves the WebView
#: waiting forever or, worse, cross-loads another ZABA app sharing the same
#: loopback (the "ketuker" bug reported when Zabacode + Zmux both on 5000).
P4A_HTTP_PORT = 5000
#: How long to wait for the p4a port to become free on Android (zombie process).
P4A_BIND_TIMEOUT_SECONDS = 30.0


def _is_android() -> bool:
    import os
    return any(k in os.environ for k in ("ANDROID_PRIVATE", "ANDROID_ARGUMENT", "ANDROID_APP_PATH"))


def _bind_listener(host: str, port: int, family: int = None, reuse_port: bool = False):
    import socket as _socket
    if family is None:
        family = _socket.AF_INET
    sock = _socket.socket(family, _socket.SOCK_STREAM)
    if family == _socket.AF_INET6 and hasattr(_socket, "IPV6_V6ONLY"):
        sock.setsockopt(_socket.IPPROTO_IPV6, _socket.IPV6_V6ONLY, 1)
    sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    if reuse_port and hasattr(_socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    sock.bind((host, port))
    sock.listen(min(_socket.SOMAXCONN, 128))
    return sock


def _bind_ipv6_loopback(port: int, reuse_port: bool = False):
    try:
        import socket as _socket
        return _bind_listener("::1", port, family=_socket.AF_INET6, reuse_port=reuse_port)
    except OSError:
        return None


def _bind_http_socket():
    """Bind HTTP listener, honouring Android WebView port contract."""
    import socket as _socket
    import time as _time
    import os as _os
    if _is_android():
        deadline = _time.monotonic() + P4A_BIND_TIMEOUT_SECONDS
        while True:
            for host in ("127.0.0.1", "localhost"):
                try:
                    return _bind_listener(host, P4A_HTTP_PORT, reuse_port=True)
                except OSError:
                    continue
            if _time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Could not bind 127.0.0.1:{P4A_HTTP_PORT} within "
                    f"{int(P4A_BIND_TIMEOUT_SECONDS)}s. The Android WebView "
                    "shell waits for this exact port, so ZABACODE cannot start. "
                    "Close other ZABA app instances (ZMUX) or force-stop them. "
                    "For coexistence, ensure ZMUX uses 6000, ZABACODE uses 5000."
                )
            print(f"[WARN] Port {P4A_HTTP_PORT} occupied, retrying...")
            _time.sleep(0.2)
    # Desktop dev fallback: try range 5000-5010
    for port in range(P4A_HTTP_PORT, P4A_HTTP_PORT + 11):
        try:
            return _bind_listener("127.0.0.1", port)
        except OSError as e:
            print(f"[WARN] Port {port} occupied ({e}), trying next...")
    raise RuntimeError(f"All ports {P4A_HTTP_PORT}-{P4A_HTTP_PORT + 10} occupied.")


def run_webview_server():
    """Run WebView server — strict port contract matching WebViewLoader.

    Prior implementation tried ports 5000-5010 after a probe-bind-close cycle.
    That left a TOCTOU race and, more critically, broke co-existence with ZMUX:
    both apps used p4a.port=5000, so second app's Python would bind 5001 while
    its Java WebViewLoader still polled 5000 and loaded the first app's UI.
    This is the root cause of "buka zmux muncul zabacode" and vice versa.

    Fix: On Android, bind exactly P4A_HTTP_PORT (5000) with retry loop and pass
    the live socket to Waitress (no probe-then-bind race). On desktop, fall back
    to range scan. See ZMUX server.py for precedent — it implements the same
    strict contract and documents it.
    """
    import time

    # Bootstrap service container (VSCode-inspired DI)
    get_service_container()
    print("[INFO] Service container bootstrapped — events, commands, services ready")

    http_sock = _bind_http_socket()
    http_port = http_sock.getsockname()[1]

    listeners = [http_sock]
    ipv6_sock = _bind_ipv6_loopback(http_port)
    if ipv6_sock is not None:
        listeners.append(ipv6_sock)
        print(f"[INFO] Also listening on [::1]:{http_port} (localhost may resolve to IPv6)")

    print(f"[INFO] Starting ZABACODE WebView server on 127.0.0.1:{http_port} (strict P4A contract)")
    print("[INFO] Loopback-only: exposure reduction, not full app-private boundary (see SECURITY.md #27)")
    print("[INFO] Token delivery: AUTH_TOKEN embedded in root HTML JS, validated via constant-time compare, sensitive routes require X-Zabacode-Token")
    print(f"[INFO] Coexistence: Zabacode=5000, Zmux=6000 — distinct ports prevent cross-talk")

    try:
        serve(app, sockets=listeners, threads=4)
    finally:
        for lst in listeners:
            try:
                lst.close()
            except OSError:
                pass
