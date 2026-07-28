"""
ZABACODE v1.0.0 — Comprehensive Unit Tests (WebView Edition)

Run: pytest test_main.py -v
"""

import sys
from pathlib import Path

import pytest

# Ensure the project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from zabacode import __version__
from zabacode.core.ai_provider import ALLOWED_PROVIDERS, PROVIDER_HANDLERS, PROVIDER_INFO
from zabacode.core.checker import check_code
from zabacode.core.executor import (
    execute_code_isolated,
    get_interactive_output,
    normalize_code,
    send_interactive_input,
    start_interactive_session,
    stop_interactive_session,
)
from zabacode.core.file_manager import delete_file, read_file, save_file, secure_filename
from zabacode.core.security import AUTH_TOKEN, verify_token
from zabacode.lib_manager import (
    _PACKAGE_NAME_RE,
    KNOWN_LIBRARIES,
    get_all_libraries,
    get_library_info,
    install_library,
)

# Translations removed
from zabacode.plugins.registry import (
    MARKETPLACE_PLUGINS,
    get_all_plugins,
    get_snippets,
    is_plugin_active,
    toggle_plugin,
)
from zabacode.themes.definitions import DEFAULT_THEME, THEMES, get_theme, list_themes

# ===================================================================
# Test Code Execution Engine
# ===================================================================

class TestCodeExecution:
    """Test code execution & isolation."""

    def test_simple_print(self):
        result = execute_code_isolated('print("hello")')
        assert result["ok"] is True
        assert "hello" in result["stdout"]

    def test_syntax_error(self):
        result = execute_code_isolated('print("missing quote')
        assert result["ok"] is False
        assert "SyntaxError" in result["stderr"] or "syntax" in result["stderr"].lower()

    def test_timeout(self):
        result = execute_code_isolated('while True: pass', timeout=2)
        assert result["timeout"] is True
        assert result["ok"] is False

    def test_import_standard_lib(self):
        result = execute_code_isolated('import sys, os\nprint("ok:", os.path.exists("_active_run.py"))')
        assert result["ok"] is True

    def test_windows_line_endings_normalized(self):
        code_windows = 'print("test 1")\r\nprint("test 2")\r\n'
        normalized = normalize_code(code_windows)
        assert '\r\n' not in normalized
        assert '\r' not in normalized
        result = execute_code_isolated(code_windows)
        assert result["ok"] is True

    def test_trailing_whitespace_normalized(self):
        code = 'print("test")   \nprint("next")   \n'
        normalized = normalize_code(code)
        lines = normalized.split('\n')
        assert lines[-3] == 'print("test")'
        assert lines[-2] == 'print("next")'
        assert lines[-1] == ''

    def test_bom_removed(self):
        code_with_bom = '\ufeffprint("hello")'
        normalized = normalize_code(code_with_bom)
        assert not normalized.startswith('\ufeff')
        assert 'print("hello")' in normalized

    def test_code_too_large(self):
        result = execute_code_isolated("x = 1\n" * 100000)  # Large code
        assert result["ok"] is False

    def test_non_string_code(self):
        result = execute_code_isolated(12345)
        assert result["ok"] is False

    def test_file_resolution(self):
        result = execute_code_isolated('from pathlib import Path\nprint(Path(__file__).name)')
        assert result["ok"] is True


# ===================================================================
# Test Code Checker
# ===================================================================

class TestCodeChecker:
    """Test code syntax validation."""

    def test_valid_code(self):
        result = check_code("print('hello')\nprint('world')")
        assert result["valid"] is True
        assert len(result["issues"]) == 0

    def test_unbalanced_parens(self):
        result = check_code("print('hello'")
        assert result["valid"] is False
        assert any("Parenthesis" in i or "()" in i for i in result["issues"])

    def test_unbalanced_brackets(self):
        result = check_code("x = [1, 2, 3")
        assert result["valid"] is False
        assert any("[]" in i or "Brackets" in i for i in result["issues"])

    def test_unbalanced_braces(self):
        result = check_code("d = {1: 2")
        assert result["valid"] is False

    def test_unbalanced_quotes(self):
        result = check_code("x = 'hello")
        assert result["valid"] is False


# ===================================================================
# Test File Manager & Security
# ===================================================================

class TestFileManager:
    """Test file operations and path traversal prevention."""

    def test_secure_filename_valid(self):
        assert secure_filename("test") == "test.py"
        assert secure_filename("script.py") == "script.py"

    def test_secure_filename_path_traversal(self):
        assert secure_filename("../etc/passwd") is None
        assert secure_filename("..\\secret") is None

    def test_secure_filename_dotfile(self):
        assert secure_filename(".zabacode_keys") is None
        assert secure_filename(".env") is None

    def test_secure_filename_null_bytes(self):
        assert secure_filename("test\x00.py") is None

    def test_secure_filename_empty(self):
        assert secure_filename("") is None
        assert secure_filename(".py") is None

    def test_secure_filename_system_file(self):
        assert secure_filename("_active_run") is None

    def test_save_and_read_file(self):
        result = save_file("test_unit_file", "print('hello from test')")
        assert result["ok"] is True

        read_result = read_file("test_unit_file.py")
        assert read_result["ok"] is True
        assert "hello from test" in read_result["content"]

        # Cleanup
        delete_file("test_unit_file.py")

    def test_delete_nonexistent_file(self):
        result = delete_file("nonexistent_xyz_12345.py")
        assert result["ok"] is False

    def test_read_nonexistent_file(self):
        result = read_file("nonexistent_xyz_12345.py")
        assert result["ok"] is False


# ===================================================================
# Test Security Module
# ===================================================================

class TestSecurity:
    """Test authentication and encryption."""

    def test_auth_token_exists(self):
        assert AUTH_TOKEN is not None
        assert len(AUTH_TOKEN) >= 16

    def test_verify_valid_token(self):
        assert verify_token(AUTH_TOKEN) is True

    def test_verify_invalid_token(self):
        assert verify_token("invalid_token_12345") is False
        assert verify_token("") is False


# ===================================================================
# Test Library Manager
# ===================================================================

class TestLibraryManager:
    """Test library management system."""

    def test_known_libraries_not_empty(self):
        assert len(KNOWN_LIBRARIES) >= 30  # We expanded significantly

    def test_libraries_have_required_fields(self):
        for name, info in KNOWN_LIBRARIES.items():
            assert "tier" in info, f"Missing 'tier' in {name}"
            assert "category" in info, f"Missing 'category' in {name}"
            assert "mode" in info, f"Missing 'mode' in {name}"
            assert "reason" in info, f"Missing 'reason' in {name}"
            assert info["tier"] in ["runtime", "buildtime"], f"Invalid tier in {name}"
            assert info["mode"] in ["offline", "online", "hybrid"], f"Invalid mode in {name}"

    def test_required_libraries_present(self):
        required = ["requests", "beautifulsoup4", "numpy", "tinydb", "fastapi", "rich",
                    "flask", "sympy", "pydantic", "pillow", "pyjwt"]
        for lib in required:
            assert lib in KNOWN_LIBRARIES, f"Missing library: {lib}"

    def test_get_all_libraries(self):
        libs = get_all_libraries()
        assert isinstance(libs, dict)
        assert len(libs) >= 30
        for name, info in libs.items():
            assert "installed" in info

    def test_get_library_info(self):
        info = get_library_info("requests")
        assert info is not None
        assert info["mode"] == "online"

    def test_get_nonexistent_library(self):
        info = get_library_info("nonexistent_package_xyz")
        assert info is None

    def test_offline_libraries_exist(self):
        offline_libs = [name for name, info in KNOWN_LIBRARIES.items() if info["mode"] == "offline"]
        assert len(offline_libs) >= 5  # At least 5 offline libs

    def test_online_libraries_exist(self):
        online_libs = [name for name, info in KNOWN_LIBRARIES.items() if info["mode"] == "online"]
        assert len(online_libs) >= 5  # At least 5 online libs

    def test_hybrid_libraries_exist(self):
        hybrid_libs = [name for name, info in KNOWN_LIBRARIES.items() if info["mode"] == "hybrid"]
        assert len(hybrid_libs) >= 3  # At least 3 hybrid libs

    def test_buildtime_libraries(self):
        buildtime = [name for name, info in KNOWN_LIBRARIES.items() if info["tier"] == "buildtime"]
        assert len(buildtime) >= 3

    def test_package_name_regex(self):
        assert _PACKAGE_NAME_RE.fullmatch("requests") is not None
        assert _PACKAGE_NAME_RE.fullmatch("my-package") is not None
        assert _PACKAGE_NAME_RE.fullmatch("") is None
        assert _PACKAGE_NAME_RE.fullmatch("../../../etc") is None

    def test_install_invalid_package(self):
        result = install_library("")
        assert result["ok"] is False

    def test_install_buildtime_package(self):
        result = install_library("numpy")
        assert result["ok"] is False
        assert result.get("needs_rebuild") is True


# ===================================================================
# Test Themes
# ===================================================================

class TestThemes:
    """Test theme system."""

    def test_themes_not_empty(self):
        assert len(THEMES) >= 6

    def test_default_theme_exists(self):
        assert DEFAULT_THEME in THEMES

    def test_theme_has_required_colors(self):
        required_keys = ["bg", "bg_panel", "border", "border_bright", "text",
                        "text_bright", "text_dim", "err", "ai", "editor_bg",
                        "editor_fg", "line_number_fg"]
        for name, theme in THEMES.items():
            for key in required_keys:
                assert key in theme, f"Missing '{key}' in theme '{name}'"

    def test_theme_colors_are_tuples(self):
        for name, theme in THEMES.items():
            for key, value in theme.items():
                if key not in ["display_name", "icon"]:
                    assert isinstance(value, tuple), f"{name}.{key} is not tuple"
                    assert len(value) == 4, f"{name}.{key} doesn't have 4 components"

    def test_get_theme(self):
        theme = get_theme("retro")
        assert theme is not None
        assert "bg" in theme

    def test_get_nonexistent_theme(self):
        assert get_theme("nonexistent_theme") is None

    def test_list_themes(self):
        themes = list_themes()
        assert isinstance(themes, dict)
        assert "retro" in themes
        assert "cyberpunk" in themes

    def test_new_themes_present(self):
        """v1.0.0 added new themes."""
        for t in ["tokyo_night", "one_dark", "gruvbox", "catppuccin"]:
            assert t in THEMES, f"New theme '{t}' missing"


# ===================================================================
# Test Plugin System
# ===================================================================

class TestPlugins:
    """Test plugin registry and marketplace."""

    def test_plugins_not_empty(self):
        assert len(MARKETPLACE_PLUGINS) >= 4

    def test_core_plugins_present(self):
        core = ["auto_formatter", "snippet_pack", "syntax_linter", "symbol_bar"]
        for pid in core:
            assert pid in MARKETPLACE_PLUGINS, f"Core plugin '{pid}' missing"

    def test_new_v1_plugins(self):
        """v1.0.0 added new plugins."""
        new_plugins = ["code_minifier", "json_formatter", "regex_tester", "todo_manager"]
        for pid in new_plugins:
            assert pid in MARKETPLACE_PLUGINS, f"New plugin '{pid}' missing"

    def test_plugin_has_required_fields(self):
        for pid, info in MARKETPLACE_PLUGINS.items():
            assert "id" in info
            assert "name" in info
            assert "description" in info
            assert "version" in info
            assert "mode" in info

    def test_toggle_plugin(self):
        # Toggle off
        result = toggle_plugin("auto_formatter")
        assert result["ok"] is True
        assert result["active"] is False

        # Toggle back on
        result = toggle_plugin("auto_formatter")
        assert result["ok"] is True
        assert result["active"] is True

    def test_toggle_nonexistent_plugin(self):
        result = toggle_plugin("nonexistent_plugin")
        assert result["ok"] is False

    def test_is_plugin_active(self):
        assert is_plugin_active("auto_formatter") is True

    def test_get_all_plugins(self):
        plugins = get_all_plugins()
        assert isinstance(plugins, dict)
        for pid, info in plugins.items():
            assert "active" in info

    def test_snippets_available(self):
        snippets = get_snippets()
        assert isinstance(snippets, dict)
        assert len(snippets) >= 5

    def test_snippets_have_code(self):
        for sid, snippet in get_snippets().items():
            assert "name" in snippet
            assert "code" in snippet
            assert len(snippet["code"]) > 0


# ===================================================================
# Test AI Provider System
# ===================================================================

class TestAIProviders:
    """Test AI provider configuration."""

    def test_providers_not_empty(self):
        assert len(PROVIDER_HANDLERS) >= 4

    def test_core_providers(self):
        for p in ["openrouter", "gemini", "groq", "mistral"]:
            assert p in PROVIDER_HANDLERS, f"Provider '{p}' missing"

    def test_new_v1_providers(self):
        """v1.0.0 added DeepSeek and Ollama."""
        assert "deepseek" in PROVIDER_HANDLERS
        assert "ollama" in PROVIDER_HANDLERS

    def test_provider_info(self):
        for pid, info in PROVIDER_INFO.items():
            assert "name" in info
            assert "mode" in info
            assert info["mode"] in ["online", "offline"]

    def test_allowed_providers(self):
        for p in PROVIDER_HANDLERS:
            assert p in ALLOWED_PROVIDERS

    def test_ollama_is_offline(self):
        assert PROVIDER_INFO["ollama"]["mode"] == "offline"


# ===================================================================
# Test Version
# ===================================================================

class TestVersion:
    """Test version info."""

    def test_version_is_1_0_0(self):
        # After Arena integration, version is 1.2.0-arena, but still valid semver-like
        assert __version__ in ("1.0.0", "1.1.0", "1.2.0-arena") or __version__.startswith("1.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ===================================================================
# Test Interactive Subprocess Execution
# ===================================================================

class TestInteractiveExecution:
    """Test interactive unbuffered code execution engine."""

    def test_interactive_start_and_stop(self):
        code = "import sys\nline = sys.stdin.readline()\nprint('ECHO:', line)"
        res = start_interactive_session(code)
        assert res["ok"] is True

        # Stop session
        stop_res = stop_interactive_session()
        assert stop_res["ok"] is True

    def test_interactive_communication(self):
        code = "import sys\nline = sys.stdin.readline().strip()\nprint('HELLO ' + line)\n"
        start_res = start_interactive_session(code)
        assert start_res["ok"] is True

        # Send input
        send_res = send_interactive_input("ZAQI\n")
        assert send_res["ok"] is True

        # Wait a bit and get output
        import time
        time.sleep(0.5)

        out_res = get_interactive_output()
        assert out_res["ok"] is True

        # Collect stdout chars
        stdout_chars = "".join([char for stype, char in out_res["output"] if stype == "stdout"])
        assert "HELLO ZAQI" in stdout_chars

        stop_interactive_session()

    def test_interactive_multiple_inputs(self):
        code = "name = input('Name: ')\nage = input('Age: ')\nprint(f'{name} is {age}')\n"
        assert start_interactive_session(code)["ok"] is True
        assert send_interactive_input("Zaqi\n")["ok"] is True
        assert send_interactive_input("20\n")["ok"] is True

        import time
        time.sleep(0.5)
        out_res = get_interactive_output()
        stdout_chars = "".join(char for stream, char in out_res["output"] if stream == "stdout")
        assert "Name: Age: Zaqi is 20" in stdout_chars
        assert out_res["done"] is True


# ===================================================================
# Test New Transform Plugins (v1.1.0)
# ===================================================================

class TestNewPlugins:
    """Test suite for the 5 new transform plugins and PluginExecutor."""

    def test_auto_import_optimizer(self):
        from zabacode.plugins.implementations import AutoImportOptimizer
        code = "import os\nimport sys\nimport math\nprint(os.name)\n"
        new_code, report = AutoImportOptimizer.optimize(code)
        assert "import sys" in new_code
        assert "# import sys" in new_code or "#import sys" in new_code or "unused import" in "".join(report)
        assert "math" in "".join(report)

    def test_duplicate_line_detector(self):
        from zabacode.plugins.implementations import DuplicateLineDetector
        code = "x = 10\ny = 20\nx = 10\n"
        new_code, report = DuplicateLineDetector.detect(code)
        assert "WARNING: Duplicate line" in new_code
        assert len(report) > 1

    def test_smart_comment_generator(self):
        from zabacode.plugins.implementations import SmartCommentGenerator
        code = "def greet(name):\n    print('Hello', name)\n"
        new_code, report = SmartCommentGenerator.generate(code)
        assert '"""Docstring for greet.' in new_code
        assert "name" in new_code

    def test_code_beautifier_pro(self):
        from zabacode.plugins.implementations import CodeBeautifierPro
        code = "x=5\ny  =  10\nprint(x,y)\n"
        new_code, report = CodeBeautifierPro.beautify(code)
        assert "x = 5" in new_code
        assert "y = 10" in new_code
        assert "x, y" in new_code

    def test_variable_type_hint_generator(self):
        from zabacode.plugins.implementations import VariableTypeHintGenerator
        code = "def add(a=5, b=''):\n    return a + b\n"
        new_code, report = VariableTypeHintGenerator.generate(code)
        assert "a: int" in new_code
        assert "b: str" in new_code
        assert "from typing import Any" in new_code

    def test_plugin_executor(self):
        from zabacode.plugins.implementations import PluginExecutor
        code = "x=5\n"
        res = PluginExecutor.execute_plugin("code_beautifier_pro", code)
        assert res["ok"] is True
        assert "code" in res

# ===================================================================
# Test API Keys Clearing
# ===================================================================

class TestApiKeysClearing:
    # Test empty API key clearing.

    def test_clear_api_key(self):
        from zabacode.core.security import load_keys, save_key
        # Save a valid key
        save_key("openrouter", "my-test-api-key")
        assert load_keys().get("openrouter") == "my-test-api-key"

        # Save empty key to clear/delete it
        save_key("openrouter", "")
        # Since empty key is treated as truthy fallback, verify it is empty/cleared
        assert not load_keys().get("openrouter")


# ---------------------------------------------------------------------------
# TLS / SSL Regression Tests (fix: CERTIFICATE_VERIFY_FAILED on all providers)
# ---------------------------------------------------------------------------

class TestTLSHardening:
    """Guards the Android CA-bundle fix and forbids unverified SSL fallbacks."""

    def test_ssl_context_verifies_certificates(self):
        import ssl as _ssl

        from zabacode.core.net import get_ssl_context
        ctx = get_ssl_context()
        assert ctx.verify_mode == _ssl.CERT_REQUIRED
        assert ctx.check_hostname is True

    def test_no_unverified_ssl_context_in_codebase(self):
        """_create_unverified_context() would reopen the MITM/RCE hole."""
        import pathlib
        root = pathlib.Path(__file__).parent / "zabacode"
        offenders = [
            str(f) for f in root.rglob("*.py")
            if "_create_unverified_context" in f.read_text(encoding="utf-8")
        ]
        assert offenders == [], f"Unverified SSL context found in: {offenders}"

    def test_all_ai_providers_use_shared_context(self):
        """Every urlopen must pass context= or Android fails to verify certs."""
        import pathlib
        import re

        from zabacode.core.ai_provider import ALLOWED_PROVIDERS
        src = (pathlib.Path(__file__).parent / "zabacode" / "core" / "ai_provider.py").read_text()
        calls = re.findall(r"urllib\.request\.urlopen\([^)]*\)", src)
        assert len(calls) == len(ALLOWED_PROVIDERS), f"expected {len(ALLOWED_PROVIDERS)} provider calls (one per provider), found {len(calls)}: {calls}"
        for call in calls:
            assert "context=get_ssl_context()" in call, f"missing context: {call}"

    def test_tls_error_returns_actionable_message(self):
        import ssl as _ssl

        from zabacode.core.ai_provider import _handle_url_error
        res = _handle_url_error(_ssl.SSLCertVerificationError("certificate verify failed"), "OpenRouter")
        assert res["ok"] is False
        assert res.get("tls_error") is True
        assert "certifi" in res["message"]

    def test_certifi_declared_for_apk_build(self):
        import pathlib
        spec = (pathlib.Path(__file__).parent / "buildozer.spec").read_text()
        req_line = next(l for l in spec.splitlines() if l.startswith("requirements ="))
        assert "certifi" in req_line, "certifi missing from buildozer.spec -> APK will fail TLS"


class TestNoServerErrors:
    """Every route must respond without a 5xx (regression: /api/translations)."""

    def test_no_route_returns_5xx(self):
        from zabacode.core.security import AUTH_TOKEN
        from zabacode.web_app import app
        client = app.test_client()
        headers = {"X-Zabacode-Token": AUTH_TOKEN}
        failures = []
        for rule in app.url_map.iter_rules():
            if "static" in rule.endpoint or "<" in str(rule):
                continue
            for method in (rule.methods & {"GET", "POST", "DELETE"}):
                resp = client.open(str(rule), method=method, json={}, headers=headers)
                if resp.status_code >= 500:
                    failures.append(f"{method} {rule} -> {resp.status_code}")
        assert failures == [], f"5xx responses: {failures}"


# ---------------------------------------------------------------------------
# Offline-First / Asset Bundling (C-2)
# ---------------------------------------------------------------------------

class TestOfflineFirst:
    """The IDE must be fully usable with zero network access."""

    def test_no_cdn_references_in_template(self):
        import pathlib
        html = (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        for cdn in ("cdnjs.cloudflare.com", "unpkg.com", "jsdelivr.net", "googleapis.com"):
            assert cdn not in html, f"External CDN '{cdn}' breaks offline-first"

    def test_ace_bundled_on_disk(self):
        import pathlib
        vendor = pathlib.Path(__file__).parent / "assets" / "vendor" / "ace"
        for f in ("ace.js", "mode-python.js", "theme-tomorrow_night_eighties.js",
                  "ext-settings_menu.js", "ext-language_tools.js", "ext-searchbox.js"):
            path = vendor / f
            assert path.exists() and path.stat().st_size > 1000, f"missing/empty: {f}"

    def test_ace_served_by_flask(self):
        from zabacode.web_app import app
        client = app.test_client()
        for f in ("ace.js", "mode-python.js", "ext-language_tools.js"):
            resp = client.get(f"/static/vendor/ace/{f}")
            assert resp.status_code == 200, f"/static/vendor/ace/{f} -> {resp.status_code}"

    def test_security_headers_present(self):
        from zabacode.web_app import app
        resp = app.test_client().get("/")
        csp = resp.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"


# ---------------------------------------------------------------------------
# Encrypted Key Storage (H-1)
# ---------------------------------------------------------------------------

class TestKeystoreEncryption:
    """API keys must not be recoverable from a hardcoded source-code key."""

    def test_roundtrip(self):
        from zabacode.core.keystore import decrypt_payload, encrypt_payload
        data = {"openrouter": "sk-or-v1-secret", "groq": "gsk_abc123"}
        assert decrypt_payload(encrypt_payload(data)) == data

    def test_plaintext_never_appears_in_ciphertext(self):
        from zabacode.core.keystore import encrypt_payload
        blob = encrypt_payload({"openrouter": "sk-or-v1-SUPERSECRET"})
        assert "SUPERSECRET" not in blob

    def test_nonce_makes_output_unique(self):
        from zabacode.core.keystore import encrypt_payload
        data = {"gemini": "same-key"}
        assert encrypt_payload(data) != encrypt_payload(data)

    def test_tampered_payload_rejected(self):
        import json

        from zabacode.core.keystore import decrypt_payload, encrypt_payload
        env = json.loads(encrypt_payload({"groq": "gsk_real"}))
        flipped = bytearray(bytes.fromhex(env["data"]))
        flipped[0] ^= 0xFF
        env["data"] = flipped.hex()
        assert decrypt_payload(json.dumps(env)) == {}, "tampered ciphertext must be rejected"

    def test_no_hardcoded_encryption_key(self):
        import pathlib
        src = (pathlib.Path(__file__).parent / "zabacode" / "core" / "security.py").read_text()
        assert "zabacode_local_keys_salt" not in src

    def test_master_key_not_tracked_by_git(self):
        import pathlib
        gitignore = (pathlib.Path(__file__).parent / ".gitignore").read_text()
        assert ".zabacode_master_key" in gitignore


# ---------------------------------------------------------------------------
# Dead Code Removal (C-3) & Concurrency (M-1)
# ---------------------------------------------------------------------------

class TestCleanupAndConcurrency:

    def test_kivy_ui_package_removed(self):
        import pathlib
        assert not (pathlib.Path(__file__).parent / "zabacode" / "ui").exists()

    def test_interactive_session_is_lock_guarded(self):
        import pathlib
        src = (pathlib.Path(__file__).parent / "zabacode" / "core" / "executor.py").read_text()
        assert "_session_lock" in src
        assert src.count("with _session_lock:") >= 4

    def test_concurrent_stop_calls_are_safe(self):
        import threading

        from zabacode.core.executor import stop_interactive_session
        errors = []

        def worker():
            try:
                stop_interactive_session()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        assert errors == [], f"concurrency errors: {errors}"


# ---------------------------------------------------------------------------
# ZABA ORACLE — Offline Code Intelligence
# ---------------------------------------------------------------------------

class TestOracleTracebackHumanizer:
    """Plain-language error explanations must work with zero network."""

    def test_name_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback('File "main.py", line 7\nNameError: name \'qty\' is not defined')
        assert r["ok"] and "qty" in r["what"] and r["line"] == 7

    def test_permission_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("PermissionError: [Errno 13] Permission denied: '/root/secret.txt'")
        assert r["ok"] and "Access Denied" in r["title"]

    def test_unicode_decode_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte")
        assert r["ok"] and "Encoding Mismatch" in r["title"]

    def test_json_decode_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)")
        assert r["ok"] and "JSON" in r["title"]

    def test_import_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("ImportError: cannot import name 'nonexistent' from 'math'")
        assert r["ok"] and "Import" in r["title"]

    def test_assertion_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("AssertionError: 2 == 3")
        assert r["ok"] and "Assertion" in r["title"]

    def test_module_not_found(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("ModuleNotFoundError: No module named 'pandas'")
        assert r["ok"] and "pandas" in r["what"]
        assert "Library Manager" in r["fix"]

    def test_type_error_captures_both_types(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("TypeError: unsupported operand type(s) for +: 'int' and 'str'")
        assert r["ok"] and "int" in r["what"] and "str" in r["what"]

    def test_unknown_error_still_helpful(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("WeirdCustomError: something exploded")
        assert r["ok"] and r["fix"]

    def test_empty_input_is_not_ok(self):
        from zabacode.core.oracle import humanize_traceback
        assert humanize_traceback("")["ok"] is False

    def test_every_rule_is_a_valid_regex_and_formats(self):
        import re

        from zabacode.core.oracle import _ERROR_RULES
        for pattern, title, what, fix in _ERROR_RULES:
            re.compile(pattern)          # must not raise
            assert title and what and fix


class TestOracleBufferAnalysis:

    def test_detects_smells(self):
        from zabacode.core.oracle import analyze_buffer
        code = (
            "def f(a, b, c, d, e, g):\n"
            "    for i in range(3):\n"
            "        for j in range(3):\n"
            "            for k in range(3):\n"
            "                try:\n"
            "                    pass\n"
            "                except:\n"
            "                    pass\n"
        )
        r = analyze_buffer(code)
        assert r["ok"] and r["loop_depth"] == 3
        joined = " ".join(r["notes"])
        assert "6 arguments" in joined and "bare `except:`" in joined

    def test_detects_mutable_defaults(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("def f(x=[]):\n    pass")
        assert r["ok"]
        assert any("Mutable default" in note for note in r["notes"])

    def test_detects_unreachable_code(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("def f():\n    return 42\n    print('hello')")
        assert r["ok"]
        assert any("Unreachable code" in note for note in r["notes"])

    def test_detects_static_division_by_zero(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("x = 10 / 0")
        assert r["ok"]
        assert any("division or modulo by zero" in note for note in r["notes"])

    def test_detects_security_risk(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("eval('1+1')")
        assert r["ok"]
        assert any("Security risk" in note for note in r["notes"])

    def test_reports_syntax_error_with_line(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("def broken(:\n    pass")
        assert r["ok"] is False and r["syntax_error"] is True and r["line"]

    def test_clean_code_has_no_notes(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer('def add(a, b):\n    """Add two numbers."""\n    return a + b\n')
        assert r["ok"] and r["notes"] == []

    def test_empty_buffer(self):
        from zabacode.core.oracle import analyze_buffer
        assert analyze_buffer("   ")["ok"] is False


class TestOracleOfflineAssistant:

    def test_never_fails(self):
        from zabacode.core.oracle import offline_reply
        for q in ["", "asdkjhasd", "how do I loop?", "review my code", "explain classes"]:
            r = offline_reply(q, "x = 1")
            assert r["ok"] is True and r["reply"] and r["offline"] is True

    def test_knowledge_lookup(self):
        from zabacode.core.oracle import offline_reply
        assert "savefig" in offline_reply("how do I plot a chart?")["reply"]
        assert "with open" in offline_reply("how to read a file?")["reply"]

    def test_new_knowledge_lookup(self):
        from zabacode.core.oracle import offline_reply
        assert "decorator" in offline_reply("what is a decorator?")["reply"].lower()
        assert "yield" in offline_reply("explain generator")["reply"].lower()
        assert "flask" in offline_reply("how to use flask?")["reply"].lower()
        assert "lambda" in offline_reply("how to write lambda?")["reply"].lower()
        assert "pypi" in offline_reply("how to install library using pip")["reply"].lower()
        assert "asyncio" in offline_reply("tell me about async await")["reply"].lower()

    def test_review_uses_real_analysis(self):
        from zabacode.core.oracle import offline_reply
        reply = offline_reply("review my code", "def f(a,b,c,d,e,g):\n    pass\n")["reply"]
        assert "6 arguments" in reply

    def test_requires_no_network(self, monkeypatch):
        """Hard guarantee: the Oracle must not open a socket."""
        import socket
        def boom(*a, **k):
            raise AssertionError("Oracle attempted a network connection")
        monkeypatch.setattr(socket.socket, "connect", boom)
        from zabacode.core.oracle import analyze_buffer, humanize_traceback, offline_reply
        assert offline_reply("review my code", "x=1")["ok"]
        assert humanize_traceback("KeyError: 'a'")["ok"]
        assert analyze_buffer("x = 1")["ok"]


class TestOracleEndpoints:

    def _client(self):
        from zabacode.core.security import AUTH_TOKEN
        from zabacode.web_app import app
        return app.test_client(), {"X-Zabacode-Token": AUTH_TOKEN}

    def test_explain_endpoint(self):
        c, h = self._client()
        r = c.post("/api/oracle/explain",
                   json={"stderr": "NameError: name 'foo' is not defined"}, headers=h)
        assert r.status_code == 200 and r.get_json()["ok"] and "foo" in r.get_json()["what"]

    def test_analyze_endpoint(self):
        c, h = self._client()
        r = c.post("/api/oracle/analyze", json={"code": "def f():\n    pass\n"}, headers=h)
        assert r.status_code == 200 and r.get_json()["ok"]

    def test_endpoints_require_auth(self):
        from zabacode.web_app import app
        c = app.test_client()
        for ep in ("/api/oracle/explain", "/api/oracle/analyze"):
            assert c.post(ep, json={}).status_code == 401

    def test_run_attaches_explanation_on_crash(self):
        c, h = self._client()
        r = c.post("/api/run", json={"code": "print(undefined_thing)"}, headers=h)
        body = r.get_json()
        assert body["ok"] is False
        assert body["explain"]["ok"] and "undefined_thing" in body["explain"]["what"]

    def test_successful_run_has_no_explanation(self):
        c, h = self._client()
        body = c.post("/api/run", json={"code": "print('hi')"}, headers=h).get_json()
        assert body["ok"] is True and "explain" not in body

    def test_ai_chat_falls_back_to_oracle_without_key(self):
        """Regression for the screenshot: user must never hit a dead end."""
        c, h = self._client()
        r = c.post("/api/ai/chat",
                   json={"provider": "openrouter", "message": "review my code",
                         "code": "def f(a,b,c,d,e,g): pass"}, headers=h)
        body = r.get_json()
        assert r.status_code == 200 and body["ok"] is True
        assert body["offline"] is True and body["fallback_reason"] == "no_api_key"

    def test_ai_chat_can_opt_out_of_fallback(self):
        c, h = self._client()
        r = c.post("/api/ai/chat",
                   json={"provider": "groq", "message": "hi", "allow_offline": False}, headers=h)
        assert r.status_code == 401 and r.get_json()["needs_key"] is True


class TestOracleUI:

    def test_oracle_card_rendered_in_frontend(self):
        import pathlib
        html = (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        assert "renderOracleCard" in html and ".oracle-card" in html
        assert "/api/oracle/explain" in html

    def test_ui_is_english_only(self):
        import pathlib
        html = (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        for word in ("BENERIN", "Kode saya mengalami"):
            assert word not in html


class TestOracleLineMapping:
    """Reported line numbers must match the editor, not the injected prelude."""

    def test_line_number_matches_user_editor(self):
        from zabacode.core.security import AUTH_TOKEN
        from zabacode.web_app import app
        c = app.test_client()
        body = c.post("/api/run", json={"code": "prices = [1, 2]\nprint(prices[9])"},
                      headers={"X-Zabacode-Token": AUTH_TOKEN}).get_json()
        assert body["explain"]["line"] == 2, "line must map to the editor, not the prelude"

    def test_offset_never_goes_below_one(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback('File "m.py", line 2\nKeyError: 1', line_offset=99)
        assert r["line"] == 1

    def test_prelude_count_matches_actual_patch(self):
        from zabacode.core.executor import PRELUDE_LINE_COUNT, SAFE_INPUT_PATCH
        assert PRELUDE_LINE_COUNT == SAFE_INPUT_PATCH.count("\n")


class TestOracleAutoFix:
    """Verify Zaba Oracle's offline Auto-Fix capabilities."""

    def test_missing_quotes_in_print(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("print(hello world)")
        assert r["ok"] is True
        assert r["fixed_code"] == 'print("hello world")'
        assert any("quotes" in fix for fix in r["applied_fixes"])

    def test_single_equals_conditional(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("if x = 5:")
        assert r["ok"] is True
        assert r["fixed_code"] == "if x == 5:"
        assert any("==" in fix for fix in r["applied_fixes"])

    def test_missing_colon(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("if x == 5")
        assert r["ok"] is True
        assert r["fixed_code"] == "if x == 5:"
        assert any("colon" in fix or ":" in fix for fix in r["applied_fixes"])

    def test_unterminated_string_literal(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("print(\"hello")
        assert r["ok"] is True
        assert r["fixed_code"] == 'print("hello")'
        assert any("unterminated" in fix or "string" in fix for fix in r["applied_fixes"])

    def test_unclosed_brackets(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("x = [1, 2")
        assert r["ok"] is True
        assert r["fixed_code"] == "x = [1, 2]"
        assert any("bracket" in fix or "parenthesis" in fix for fix in r["applied_fixes"])

    def test_fix_endpoint_auth(self):
        from zabacode.web_app import app
        c = app.test_client()
        r = c.post("/api/oracle/fix", json={"code": "print(hello)"})
        assert r.status_code == 401

    def test_fix_endpoint_success(self):
        from zabacode.core.security import AUTH_TOKEN
        from zabacode.web_app import app
        c = app.test_client()
        r = c.post(
            "/api/oracle/fix",
            json={"code": "print(hello world)"},
            headers={"X-Zabacode-Token": AUTH_TOKEN}
        )
        assert r.status_code == 200
        body = r.get_json()
        assert body["ok"] is True
        assert body["fixed_code"] == 'print("hello world")'

    def test_ui_contains_auto_fix_functions(self):
        import pathlib
        html = (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        assert "renderAutoFixButton" in html
        assert "renderDiffView" in html
        assert "renderAutoFixResult" in html


# ===========================================================================
# Regression coverage for the audit findings (AUDIT_REPORT.md F-01 .. F-08)
# ===========================================================================


class TestJsonContentTypeContract:
    """F-01: a body sent without Content-Type must never be read as empty.

    The browser helper used to omit the header, so Flask's get_json() returned
    None and the payload was silently discarded — the Oracle then reported
    "the editor is empty" for a buffer that was full.
    """

    def _client(self):
        from zabacode.web_app import app

        return app.test_client()

    def _auth(self):
        from zabacode.core.security import AUTH_TOKEN

        return {"X-Zabacode-Token": AUTH_TOKEN}

    def test_unparseable_body_is_rejected_not_silently_emptied(self):
        import json as _json

        r = self._client().post(
            "/api/oracle/fix",
            headers=self._auth(),
            data=_json.dumps({"code": "print(hello world)"}),
            content_type="text/plain",
        )
        assert r.status_code == 400
        body = r.get_json()
        assert body["ok"] is False
        assert body["code"] == "invalid_json"
        # The reply must name the real cause, not blame the user's buffer.
        assert "Content-Type" in body["message"]
        assert "empty" not in body["message"].lower()

    def test_genuinely_empty_body_still_allowed(self):
        r = self._client().post("/api/check", headers=self._auth())
        assert r.status_code == 200

    def test_correct_content_type_still_works(self):
        r = self._client().post(
            "/api/oracle/fix",
            headers=self._auth(),
            json={"code": "print(hello world)"},
        )
        assert r.status_code == 200
        assert r.get_json()["ok"] is True


class TestFrontendSendsJsonHeader:
    """F-01: every POST issued by the UI must carry a JSON content type."""

    def _html(self):
        import pathlib

        return (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")

    def test_fetch_helper_sets_content_type_for_bodies(self):
        html = self._html()
        helper = html.split("function fetchApi(")[1].split("\n}")[0]
        assert "Content-Type" in helper, "fetchApi must default Content-Type for JSON bodies"
        assert "application/json" in helper

    def test_no_post_call_relies_on_browser_default_mimetype(self):
        """Either the caller sets the header or the shared helper must."""
        html = self._html()
        helper = html.split("function fetchApi(")[1].split("\n}")[0]
        centrally_handled = "Content-Type" in helper and "options.body" in helper
        assert centrally_handled, (
            "fetchApi no longer guarantees Content-Type; every POST caller must "
            "now set it explicitly or the request body will be dropped."
        )


class TestAutoFixSafety:
    """F-02/F-03/F-04: the fixer must never corrupt working code."""

    VALID_SNIPPETS = [
        "prices = [1, 2]\nprint(prices[9])",
        "x = 5\nprint(x + 1)",
        "import math\nprint(math.pi)",
        "def f():\n    return 1\nprint(f())",
        "a = 1\nb = 0\nprint(a / b)",
        "print(len([1, 2, 3]))",
        "d = {}\nprint(d['k'])",
        "name = 'bob'\nprint(f'hi {name}')",
        "if d.get('k', default=1):\n    pass",
        "while retry(timeout=5):\n    pass",
    ]

    def test_syntactically_valid_code_is_never_rewritten(self):
        from zabacode.core.oracle import auto_fix_code

        for snippet in self.VALID_SNIPPETS:
            result = auto_fix_code(snippet, "IndexError: list index out of range")
            assert result["fixed_code"] == snippet, f"auto-fix mutated valid code: {snippet!r}"
            assert result["ok"] is False
            assert result["applied_fixes"] == []

    def test_runtime_error_is_reported_as_such(self):
        from zabacode.core.oracle import auto_fix_code

        result = auto_fix_code("prices = [1, 2]\nprint(prices[9])")
        assert result.get("runtime_error") is True

    def test_keyword_arguments_are_not_turned_into_comparisons(self):
        from zabacode.core.oracle import auto_fix_code

        result = auto_fix_code("if f(timeout=5)\n    pass")
        assert "timeout==5" not in result["fixed_code"]

    def test_ok_implies_result_actually_parses(self):
        from zabacode.core.oracle import _is_valid_python, auto_fix_code

        samples = [
            "print(hello world)",
            "if x = 5:",
            "if x == 5",
            'print("hello',
            "x = [1, 2",
            'def f(:\n    print("a"\n',
            "for i in range(3)\n    print(i)",
        ]
        for snippet in samples:
            result = auto_fix_code(snippet)
            if result["ok"]:
                # A block header the user hasn't filled in yet is incomplete,
                # not broken, so use the same tolerance the fixer applies.
                assert _is_valid_python(result["fixed_code"]), (
                    f"claimed success but result does not parse: {result['fixed_code']!r}"
                )
                assert result["applied_fixes"]

    def test_hash_inside_string_is_not_treated_as_comment(self):
        from zabacode.core.oracle import auto_fix_code

        result = auto_fix_code('print("a#b"')
        if result["ok"]:
            assert "a#b" in result["fixed_code"]


class TestCheckerLineNumbers:
    """F-07: reported lines must match the user's buffer, not the prelude."""

    def test_indentation_issue_points_at_real_line(self):
        from zabacode.core.checker import check_code

        issues = check_code("if True:\nprint('x')")["issues"]
        assert issues, "missing indentation should be reported"
        assert "Line 2" in issues[0]
        assert "line 1" in issues[0]

    def test_valid_code_reports_no_issues(self):
        from zabacode.core.checker import check_code

        assert check_code("x = 1\nprint(x)")["issues"] == []


class TestInteractiveTracebackMasking:
    """F-08: the scratch filename must not leak in interactive mode."""

    def test_streamed_chunks_are_masked(self):
        from zabacode.core.executor import _mask_runner_filename

        streamed = [("stderr", ch) for ch in '  File "_active_run.py", line 2']
        out = _mask_runner_filename(streamed)
        joined = "".join(text for _, text in out)
        assert "_active_run.py" not in joined
        assert "main.py" in joined

    def test_stream_ordering_and_types_preserved(self):
        from zabacode.core.executor import _mask_runner_filename

        out = _mask_runner_filename([("stdout", "a"), ("stdout", "b"), ("stderr", "x")])
        assert out == [("stdout", "ab"), ("stderr", "x")]

    def test_empty_batch_is_safe(self):
        from zabacode.core.executor import _mask_runner_filename

        assert _mask_runner_filename([]) == []


# ===========================================================================
# Auto-Fix coverage expansion — error-directed repair
#
# The original fixer recognised five hard-coded line shapes. Everything else
# (Python 2 syntax, smart quotes off a phone keyboard, C-style operators,
# mixed tabs, a bracket opened three lines up) fell through to "I couldn't
# produce a patch". These tests pin the widened coverage *and* the safety
# invariants that must survive it.
# ===========================================================================


def _fix(code, stderr=""):
    from zabacode.core.oracle import auto_fix_code

    return auto_fix_code(code, stderr)


def _assert_fixed(code, expected_substrings=(), stderr=""):
    """The patch must be applied, must parse, and must contain the expected text."""
    from zabacode.core.oracle import _is_valid_python

    result = _fix(code, stderr)
    assert result["ok"] is True, f"auto-fix gave up on {code!r}: {result.get('error_message')}"
    assert _is_valid_python(result["fixed_code"]), f"claimed success but does not parse: {result['fixed_code']!r}"
    assert result["applied_fixes"], "a successful fix must say what it changed"
    for needle in expected_substrings:
        assert needle in result["fixed_code"], (
            f"expected {needle!r} in fixed code, got {result['fixed_code']!r}"
        )
    return result


class TestAutoFixPython2Syntax:
    """Tutorials and old Stack Overflow answers are full of Python 2."""

    def test_print_statement_becomes_call(self):
        _assert_fixed("print 'hello world'", ["print('hello world')"])

    def test_print_statement_with_variable(self):
        _assert_fixed("x = 5\nprint x", ["print(x)"])

    def test_print_with_multiple_values(self):
        _assert_fixed("a = 1\nb = 2\nprint a, b", ["print(a, b)"])

    def test_except_comma_becomes_as(self):
        _assert_fixed(
            "try:\n    pass\nexcept ValueError, e:\n    print(e)",
            ["except ValueError as e:"],
        )


class TestAutoFixForeignLanguageSyntax:
    """Muscle memory from C, Java and JavaScript."""

    def test_else_if_becomes_elif(self):
        result = _assert_fixed(
            "x = 1\nif x == 1:\n    pass\nelse if x == 2:\n    pass",
            ["elif x == 2:"],
        )
        # `else: if ...` would also parse but silently changes the structure.
        assert "else if" not in result["fixed_code"]

    def test_double_ampersand_becomes_and(self):
        _assert_fixed("a = 1\nb = 2\nif a == 1 && b == 2:\n    pass", ["and"])

    def test_double_pipe_becomes_or(self):
        _assert_fixed("a = 1\nb = 2\nif a == 1 || b == 2:\n    pass", [" or "])

    def test_bang_becomes_not(self):
        _assert_fixed("x = 1\nif !x:\n    pass", ["not x"])

    def test_slash_comment_becomes_hash(self):
        _assert_fixed("// a note\nx = 1", ["# a note"])

    def test_increment_becomes_augmented_assignment(self):
        _assert_fixed("x = 1\nx++", ["x += 1"])

    def test_decrement_becomes_augmented_assignment(self):
        _assert_fixed("x = 1\nx--", ["x -= 1"])

    def test_var_declaration_is_dropped_not_annotated(self):
        result = _assert_fixed("var x = 5\nprint(x)", ["x = 5"])
        # Inserting a colon would produce the valid-but-wrong `var: x = 5`.
        assert "var" not in result["fixed_code"]

    def test_brace_block_becomes_colon_block(self):
        result = _assert_fixed("def f() {\n    return 1\n}", ["def f():"])
        assert "{" not in result["fixed_code"]
        assert "}" not in result["fixed_code"]


class TestAutoFixMobileKeyboardDamage:
    """Text pasted from chat apps and phone keyboards."""

    def test_smart_double_quotes_are_normalised(self):
        result = _assert_fixed("msg = \u201chello world\u201d\nprint(msg)", ['"hello world"'])
        assert "\u201c" not in result["fixed_code"]
        assert "\u201d" not in result["fixed_code"]

    def test_fullwidth_parentheses_are_normalised(self):
        _assert_fixed("print\uff08'hi'\uff09", ["print('hi')"])

    def test_non_breaking_space_indentation(self):
        result = _assert_fixed("def f():\n\u00a0\u00a0\u00a0\u00a0return 1", ["return 1"])
        assert "\u00a0" not in result["fixed_code"]

    def test_smart_quotes_inside_a_working_string_are_left_alone(self):
        """Typographic quotes are legitimate *data* — only broken code is touched."""
        code = 'print("she said \u201chi\u201d")'
        result = _fix(code)
        assert result["fixed_code"] == code
        assert result.get("runtime_error") is True


class TestAutoFixIndentation:
    """The single most common beginner failure on a phone keyboard."""

    def test_missing_indent_after_block_header(self):
        _assert_fixed("def f():\nreturn 1", ["    return 1"])

    def test_missing_indent_after_if(self):
        _assert_fixed("x = 1\nif x:\nprint(x)", ["    print(x)"])

    def test_unexpected_indent_is_realigned(self):
        result = _assert_fixed("x = 1\n  y = 2", ["y = 2"])
        assert result["fixed_code"].split("\n")[1].startswith("y")

    def test_mixed_tabs_and_spaces(self):
        result = _assert_fixed("def f():\n\tx = 1\n        y = 2", ["x = 1", "y = 2"])
        assert "\t" not in result["fixed_code"]


class TestAutoFixBracketsAcrossLines:
    """An unclosed bracket is reported on a later line than the typo."""

    def test_bracket_closed_at_end_of_continuation(self):
        result = _assert_fixed(
            "result = sum(\n    1,\n    2\n\nprint(result)",
            ["print(result)"],
        )
        assert "2)" in result["fixed_code"]

    def test_stray_closing_bracket_is_removed(self):
        _assert_fixed("print('a'))", ["print('a')"])

    def test_unclosed_dict_literal(self):
        _assert_fixed("d = {'a': 1,\nprint(d)", ["print(d)"])


class TestAutoFixMissingTokens:
    def test_missing_in_keyword_in_for_loop(self):
        _assert_fixed("for i range(3):\n    print(i)", ["for i in range(3):"])

    def test_missing_comma_in_list(self):
        _assert_fixed("x = [1 2, 3]", ["1, 2"])

    def test_missing_colon_in_lambda(self):
        _assert_fixed("f = lambda x x + 1", ["lambda x:"])

    def test_unquoted_prose_is_quoted_not_comma_separated(self):
        """`print(hello world)` means text, not two undefined names.

        Inserting a comma also parses, but produces a NameError at runtime —
        trading a syntax error for a crash is not a fix.
        """
        result = _assert_fixed("print(hello world)", ['print("hello world")'])
        assert "hello, world" not in result["fixed_code"]


class TestAutoFixMultipleErrors:
    def test_four_separate_typos_in_one_file(self):
        result = _assert_fixed(
            "def f()\n    x = 1\n    if x = 1\n        print(x\n",
            ["def f():", "if x == 1:", "print(x)"],
        )
        assert len(result["applied_fixes"]) >= 3


class TestAutoFixRefusalIsInformative:
    """When no safe patch exists, hand over what the parser already told us."""

    AMBIGUOUS = [
        "def f(:\n    pass",
        'print("he said "hi"")',
    ]

    def test_refusal_reports_line_and_parser_message(self):
        for code in self.AMBIGUOUS:
            result = _fix(code)
            if result["ok"]:
                continue
            assert result["fixed_code"] == code, "a refusal must not modify the buffer"
            assert result["applied_fixes"] == []
            assert result.get("error_line"), f"no line reported for {code!r}"
            assert result.get("error_message"), f"no parser message reported for {code!r}"
            assert str(result["error_line"]) in result["explanation"]

    def test_refusal_explanation_is_not_the_old_generic_text(self):
        result = _fix("def f(:\n    pass")
        assert result["ok"] is False
        assert "Here's exactly what Python choked on" in result["explanation"]


class TestAutoFixSafetyUnderExpandedCoverage:
    """Wider coverage must not cost correctness. These are the invariants."""

    VALID = [
        "prices = [1, 2]\nprint(prices[9])",
        "import math\nprint(math.pi)",
        "d = {}\nprint(d['k'])",
        "def f(a, b=1, *args, **kw):\n    return a + b\nprint(f(1))",
        "s = 'he said \"hi\"'\nprint(s)",
        "s = \"tab\\there # not a comment\"\nprint(s)",
        "class A:\n    def m(self):\n        return lambda x: x + 1",
        "x = [i for i in range(10) if i % 2 == 0]",
        "try:\n    pass\nexcept (ValueError, TypeError) as e:\n    print(e)",
        "def f():\n\tx = 1\n\treturn x",
        "print('a' 'b')",
        "a = 1 if True else 2",
        "matrix = [[1, 2],\n          [3, 4]]",
        "while retry(timeout=5):\n    pass",
        "print(f'{1 + 1}')",
    ]

    def test_valid_code_is_never_touched(self):
        for snippet in self.VALID:
            result = _fix(snippet, "IndexError: list index out of range")
            assert result["fixed_code"] == snippet, f"mutated valid code: {snippet!r}"
            assert result["ok"] is False
            assert result["applied_fixes"] == []

    def test_ok_always_implies_the_result_parses(self):
        """Fuzz: break valid code one character at a time, never lie about success."""
        from zabacode.core.oracle import _is_valid_python

        checked = 0
        for snippet in self.VALID:
            for char in (":", ")", "]", "}", "'", '"', ","):
                idx = snippet.find(char)
                while idx != -1:
                    broken = snippet[:idx] + snippet[idx + 1:]
                    if not _is_valid_python(broken):
                        result = _fix(broken)
                        checked += 1
                        if result["ok"]:
                            assert _is_valid_python(result["fixed_code"]), (
                                f"claimed success on {broken!r} -> {result['fixed_code']!r}"
                            )
                    idx = snippet.find(char, idx + 1)
        assert checked > 20, "fuzz corpus degenerated — it is no longer testing anything"

    def test_fixes_never_delete_user_content(self):
        """A patch may add or reshape, but must not quietly drop code."""
        from zabacode.core.oracle import _is_valid_python

        for snippet in self.VALID:
            for char in (":", ")", "]"):
                idx = snippet.find(char)
                if idx == -1:
                    continue
                broken = snippet[:idx] + snippet[idx + 1:]
                if _is_valid_python(broken):
                    continue
                result = _fix(broken)
                if not result["ok"]:
                    continue
                before = sum(c.isalnum() for c in broken)
                after = sum(c.isalnum() for c in result["fixed_code"])
                assert after >= before, f"content lost: {broken!r} -> {result['fixed_code']!r}"

    def test_large_unfixable_file_stays_responsive(self):
        """The repair sweep is bounded — an unbounded one froze the UI for seconds."""
        import time

        code = "\n".join([f"x{i} = {i}" for i in range(800)] + ["@@@ ??? %%%"])
        started = time.time()
        result = _fix(code)
        elapsed = time.time() - started
        assert result["ok"] is False
        assert elapsed < 1.5, f"auto-fix took {elapsed:.2f}s on an 800-line buffer"

    def test_comment_only_and_empty_edge_cases(self):
        assert _fix("")["ok"] is False
        assert _fix("   \n\n  ")["ok"] is False
        assert _fix("# just a comment")["ok"] is False


class TestAutoFixEndpointExposesRefusalDetail:
    """The UI can only show the parser's diagnosis if the API forwards it."""

    def _post(self, payload):
        from zabacode.core.security import AUTH_TOKEN
        from zabacode.web_app import app

        return app.test_client().post(
            "/api/oracle/fix",
            json=payload,
            headers={"X-Zabacode-Token": AUTH_TOKEN},
        )

    def test_expanded_fix_reaches_the_client(self):
        body = self._post({"code": "print 'hello'"}).get_json()
        assert body["ok"] is True
        assert body["fixed_code"] == "print('hello')"

    def test_refusal_carries_line_and_message(self):
        body = self._post({"code": "def f(:\n    pass"}).get_json()
        assert body["ok"] is False
        assert body["error_line"] == 1
        assert body["error_message"]
        assert body["explanation"]


class TestAutoFixRefusalRendering:
    """F-01 taught us that a fix nobody can see is not a fix."""

    def _html(self):
        import pathlib

        return (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")

    def test_refusal_card_is_rendered_instead_of_a_toast(self):
        html = self._html()
        assert "renderAutoFixRefusal(data, container, 'NO SAFE PATCH')" in html, (
            "a refusal with an explanation must render the detailed card, not a generic toast"
        )

    def test_refusal_card_preserves_the_caret_pointer_block(self):
        html = self._html()
        helper = html.split("function renderAutoFixRefusal(")[1].split("\n}")[0]
        assert "<pre" in helper, "the caret pointer needs pre-formatted whitespace to line up"
        assert "white-space:pre" in helper
